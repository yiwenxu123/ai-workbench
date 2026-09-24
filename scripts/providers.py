#!/usr/bin/env python3
"""
Provider 抽象层（TTS / 生图）—— 落实方案 §1.1 原则 5「Provider 不锁定」

为什么存在：
  评测期把 TTS/生图硬编码成 MiniMax，导致 ① 成本高（MiniMax speech-2.8-hd 3.5元/万字符，
  是国内主流里最贵档）② 余额耗尽即全线停摆 ③ 换供应商要改业务代码。
  本模块把「调哪家」与「怎么调」分离：业务脚本只说 provider 名，实现细节在此收敛。

设计原则：
  1. **统一签名**：所有 provider 返回 (audio_bytes, duration_sec) / (image_bytes_or_url, ...)
  2. **可插拔**：加一家 = 在注册表里加一条，不改调用方
  3. **免费优先可选**：`edge` 无需 API key、零成本，适合评测期
  4. **优先级**：命令行显式 > 分镜配置 > 项目默认 > 兜底（并回显实际取值）

已实现：edge（免费）/ minimax（当前生产）/ dashscope（阿里百炼，待 key）
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

FFPROBE = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
_DS_ENV = os.path.expanduser("~/.dsh/secrets/dashscope.env")
_MM_ENV = os.path.expanduser("~/.dsh/secrets/minimax.env")

# ── 密钥解析（统一走受管密钥文件，避免环境变量里的废弃 key）──────────

def _read_secret(env_name, secret_file=None):
    """从 ~/.dsh/secrets/<name>.env 或环境变量取密钥；文件优先"""
    f = secret_file or os.path.expanduser(f"~/.dsh/secrets/{env_name.lower()}.env")
    if os.path.exists(f):
        for line in open(f):
            line = line.strip()
            if line.startswith(f"export {env_name}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(env_name, "").strip()


def _ffprobe_duration(path):
    try:
        r = subprocess.run([FFPROBE, "-v", "quiet", "-show_entries",
                            "format=duration", "-of",
                            "default=noprint_wrappers=1:nokey=1", path],
                           capture_output=True, text=True, timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


# ── TTS providers ─────────────────────────────────────────────────────

def tts_edge(text, voice_id, speed=1.0, timing=None, **_):
    """
    Edge TTS（微软）——**完全免费、无需 API key**。
    评测期首选。音色如 zh-CN-YunxiNeural（男）/ zh-CN-XiaoxiaoNeural（女）。

    A1 镜内字幕对齐：edge-tts 7.x 默认 `boundary="SentenceBoundary"`，传入
    `timing={}` 时改要 `WordBoundary`，把逐词时间戳回填成 `timing["words"]`
    （`[{"w","s","e"}]`，秒，**相对本段音频起点**）给字幕用。
    总时长仍走 ffprobe（与改动前一致）——词表末端的时刻不含尾静音，
    拿它当镜时长会把画面切短。
    """
    try:
        import edge_tts
    except ImportError:
        raise RuntimeError("未安装 edge-tts：pip install edge-tts")
    voice = voice_id or "zh-CN-YunxiNeural"
    if not voice.startswith("zh-") and not voice.startswith("en-"):
        raise RuntimeError(f"Edge TTS 音色名不合法：{voice}（应形如 zh-CN-YunxiNeural）")
    pct = int(round((speed - 1.0) * 100))
    rate = f"{pct:+d}%"

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    want_words = isinstance(timing, dict)

    async def _go(boundary):
        c = edge_tts.Communicate(text, voice, rate=rate,
                                 **({"boundary": boundary} if boundary else {}))
        words = []
        with open(tmp, "wb") as f:
            async for chunk in c.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                    # offset/duration 单位为 100ns
                    words.append({"w": chunk.get("text") or "",
                                  "s": round(chunk["offset"] / 10_000_000.0, 4),
                                  "e": round((chunk["offset"] + chunk["duration"])
                                             / 10_000_000.0, 4)})
        return words

    # v4.2 健壮性：edge-tts 的 WebSocket 无内置超时，网络抖动会**永久挂起**
    # （实测：13 镜配音卡住 19 分钟不返回，整条管线停摆）。这里加超时 + 重试。
    async def _go_with_timeout(boundary):
        return await asyncio.wait_for(_go(boundary), timeout=45)

    last_err = None
    words = []
    for attempt in range(1, 4):
        try:
            # 词级边界偶发 NoAudioReceived：末次退回服务端默认边界，
            # 宁可"有声音没词表"，不能因为要词表把整镜配音弄失败。
            boundary = "WordBoundary" if (want_words and attempt < 3) else None
            words = asyncio.run(_go_with_timeout(boundary))
            break
        except Exception as e:  # 超时/网络错误 → 重试
            last_err = e
            print(f"⚠️  edge TTS 第 {attempt} 次失败（{type(e).__name__}: {str(e)[:60]}），重试…",
                  file=sys.stderr)
            try:
                os.unlink(tmp)
            except OSError:
                pass
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    else:
        raise RuntimeError(f"edge TTS 连续 3 次失败（最后一次: {last_err}）—— 检查网络后重试")

    data = open(tmp, "rb").read()
    os.unlink(tmp)
    record_cost("tts", "edge", None, len(text), voice)
    # 镜时长唯一来源：ffprobe 实测（边界末端不含尾静音，拿它当总时长会把画面切短）
    tmp2 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    open(tmp2, "wb").write(data)
    dur = _ffprobe_duration(tmp2)
    os.unlink(tmp2)
    if isinstance(timing, dict) and words:
        timing["words"] = words
        timing["provider"] = "edge"
    return data, round(dur, 3)


def tts_minimax(text, voice_id, speed=1.0, model="speech-2.8-hd", **_):
    """MiniMax T2A。**注意费率较高**（speech-2.8-hd 3.5元/万字符）"""
    key = _read_secret("MINIMAX_API_KEY", os.path.expanduser("~/.dsh/secrets/minimax.env"))
    if not key:
        raise RuntimeError("未找到 MINIMAX_API_KEY")
    body = json.dumps({
        "model": model, "text": text, "stream": False,
        "voice_setting": {"voice_id": voice_id or "male-qn-qingse",
                          "speed": speed, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000,
                          "format": "mp3", "channel": 1},
    }).encode()
    req = urllib.request.Request(
        "https://api.minimaxi.com/v1/t2a_v2", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    br = d.get("base_resp", {})
    if br.get("status_code") != 0:
        raise RuntimeError(f"MiniMax T2A: {br}")
    hx = (d.get("data") or {}).get("audio")
    if not hx:
        raise RuntimeError("MiniMax 响应无音频")
    dur = ((d.get("extra_info") or {}).get("audio_length") or 0) / 1000.0
    record_cost("tts", "minimax", model, len(text), voice_id)
    return bytes.fromhex(hx), round(dur, 3)


def _ds_collect_words(events):
    """从 CosyVoice 的 WebSocket 事件流里收词级时间戳（begin/end_time 单位毫秒，
    相对**本次合成的这段音频**，与 edge 侧车同口径）。
    同一句会在 sentence-synthesis / sentence-end 里重复出现 → 按 (起始毫秒, 文本) 去重。"""
    seen, out = set(), []
    stack = list(events)
    while stack:
        node = stack.pop()
        if isinstance(node, (str, bytes)):
            try:
                stack.append(json.loads(node))
            except Exception:
                pass
            continue
        if isinstance(node, list):
            stack.extend(node)
            continue
        if not isinstance(node, dict):
            continue
        for k, v in node.items():
            if k == "words" and isinstance(v, list):
                for w in v:
                    if not isinstance(w, dict):
                        continue
                    bt, et = w.get("begin_time"), w.get("end_time")
                    if bt is None or et is None:
                        continue
                    key = (int(bt), str(w.get("text") or ""))
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append({"w": str(w.get("text") or ""),
                                "s": round(int(bt) / 1000.0, 4),
                                "e": round(int(et) / 1000.0, 4)})
            else:
                stack.append(v)
    out.sort(key=lambda x: x["s"])
    return out


def tts_dashscope(text, voice_id, speed=1.0, model="qwen3-tts-flash", timing=None, **_):
    """
    阿里云百炼语音合成 —— 按模型自动分派两种协议：

    | 模型 | 协议 | 说明 |
    |---|---|---|
    | `qwen3-tts-*` / `qwen-tts-*` | **HTTP** | 系统音色，0.8~1元/万字符 |
    | `cosyvoice-*` / `qwen-audio-*-tts-*` | **WebSocket** | 支持**克隆音色**，0.8~2元/万字符 |

    ⚠️ 关键坑：CosyVoice **不走 HTTP**（HTTP 会报误导性的 `url error`），
       必须用 dashscope SDK 的 WebSocket（`SpeechSynthesizer`）。
       且**复刻时的 target_model 必须与合成时的 model 完全一致**，否则失败。

    音色：系统音色用英文名（Cherry/Serena/Ethan）；克隆音色用 `{model}-{prefix}-{id}` 全串。
    """
    key = _read_secret("DASHSCOPE_API_KEY", _DS_ENV)
    host = _read_secret("DASHSCOPE_HOST", _DS_ENV) or "dashscope.aliyuncs.com"
    if not key:
        raise RuntimeError(
            "未配置 DASHSCOPE_API_KEY（阿里云百炼）。配置方式：\n"
            "  echo 'export DASHSCOPE_API_KEY=sk-xxx' > ~/.dsh/secrets/dashscope.env\n"
            "  chmod 600 ~/.dsh/secrets/dashscope.env")
    voice = voice_id or "Cherry"
    model = model or "qwen3-tts-flash"

    # ── 分支 A：CosyVoice / Qwen-Audio-TTS（WebSocket，支持克隆音色）──
    if model.startswith(("cosyvoice", "qwen-audio")) :
        try:
            import dashscope
            from dashscope.audio.tts_v2 import SpeechSynthesizer
        except ImportError:
            raise RuntimeError("需安装 dashscope SDK：pip install dashscope")
        dashscope.api_key = key
        dashscope.base_websocket_api_url = f"wss://{host}/api-ws/v1/inference"
        # 语速：SDK 的 knob 是 speech_rate（请求体里的 parameters.rate）。
        # 以前这里根本不传 → 配置里的 speed 对克隆音色线完全无效。
        want_words = isinstance(timing, dict)
        if want_words:
            # 词级时间戳只在**流式（callback）路径**上给。注意 SDK 的坑：
            # 一旦设了 callback，async_call 保持 True，call() 就**不再返回音频**，
            # 音频必须自己从 on_data 收（见 speech_synthesizer.py:522/853）。
            from dashscope.audio.tts_v2 import ResultCallback

            chunks, events, failures = [], [], []

            class _Collect(ResultCallback):
                def on_data(self, data):
                    chunks.append(data)

                def on_event(self, message):
                    events.append(message)

                def on_error(self, message):
                    failures.append(message)

            syn = SpeechSynthesizer(
                model=model, voice=voice, speech_rate=speed, callback=_Collect(),
                additional_params={"word_timestamp_enabled": True})
            syn.call(text)
            if failures:
                raise RuntimeError(f"CosyVoice 合成失败: {str(failures[0])[:200]}")
            audio = b"".join(chunks)
        else:
            syn = SpeechSynthesizer(model=model, voice=voice, speech_rate=speed)
            audio = syn.call(text)
        if not audio:
            raise RuntimeError(f"CosyVoice 合成返回空: {syn.get_response()}")
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        open(tmp, "wb").write(audio)
        dur = _ffprobe_duration(tmp)
        os.unlink(tmp)
        record_cost("tts", "dashscope", model, len(text), voice)
        if isinstance(timing, dict):
            words = _ds_collect_words(events) if want_words else []
            if words:
                timing["words"] = words
                timing["provider"] = "dashscope"
            else:
                # 拿不到词表不是错误：字幕退回字符比例切分，但必须让人看得见为什么
                print("⚠️  CosyVoice 未返回词级时间戳，本镜字幕退回字符比例切分"
                      f"（模型 {model} 不在词表支持名单，或该音色未开放）", file=sys.stderr)
        return audio, round(dur, 3)

    # ── 分支 B：Qwen-TTS 系统音色（HTTP）──
    body = json.dumps({"model": model,
                       "input": {"text": text, "voice": voice}}).encode()
    req = urllib.request.Request(
        f"https://{host}/api/v1/services/aigc/multimodal-generation/generation",
        data=body, headers={"Authorization": f"Bearer {key}",
                            "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    if d.get("code"):
        raise RuntimeError(f"百炼 TTS: {d.get('code')} {d.get('message')}")
    url = ((d.get("output") or {}).get("audio") or {}).get("url")
    if not url:
        raise RuntimeError(f"百炼 TTS 响应无音频: {str(d)[:200]}")
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with urllib.request.urlopen(url, timeout=180) as r, open(tmp, "wb") as f:
        f.write(r.read())
    mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-y", "-loglevel",
                    "error", "-i", tmp, "-c:a", "libmp3lame", mp3],
                   capture_output=True)
    data = open(mp3, "rb").read()
    dur = _ffprobe_duration(mp3)
    os.unlink(tmp); os.unlink(mp3)
    if dur <= 0:
        raise RuntimeError("百炼 TTS 音频时长解析失败")
    record_cost("tts", "dashscope", model, len(text), voice)
    return data, round(dur, 3)


# ── 生图 providers ────────────────────────────────────────────────────

def img_minimax(prompt, aspect_ratio="9:16", model="image-01", **_):
    """MiniMax 文生图，返回图片 URL"""
    key = _read_secret("MINIMAX_API_KEY", os.path.expanduser("~/.dsh/secrets/minimax.env"))
    if not key:
        raise RuntimeError("未找到 MINIMAX_API_KEY")
    body = json.dumps({"model": model, "prompt": prompt,
                       "aspect_ratio": aspect_ratio,
                       "response_format": "url", "n": 1}).encode()
    req = urllib.request.Request(
        "https://api.minimaxi.com/v1/image_generation", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    if d.get("base_resp", {}).get("status_code") != 0:
        raise RuntimeError(f"MiniMax 生图: {d.get('base_resp')}")
    urls = (d.get("data") or {}).get("image_urls") or []
    if not urls:
        raise RuntimeError("MiniMax 生图响应无图片")
    record_cost("image", "minimax", model, 1)
    return urls[0]


def img_dashscope(prompt, aspect_ratio="9:16", model="wanx2.1-t2i-turbo", **_):
    """
    阿里云百炼 通义万相 文生图 —— **性价比档**（约 0.10~0.16 元/张，新用户送 100 张）。

    接口（已实测）：**异步任务式**
      ① POST /api/v1/services/aigc/text2image/image-synthesis  (Header: X-DashScope-Async: enable)
         → {"output":{"task_id":...,"task_status":"PENDING"}}
      ② 轮询 GET /api/v1/tasks/{task_id} → SUCCEEDED 时 output.results[0].url

    尺寸约束（实测踩坑）：宽高都必须在 **512~1440** 之间，用 `width*height`（星号）。
      注意 z-image-turbo 等同步模型**不走**本异步接口（会 AccessDenied）。
    """
    key = _read_secret("DASHSCOPE_API_KEY", _DS_ENV)
    host = _read_secret("DASHSCOPE_HOST", _DS_ENV) or "dashscope.aliyuncs.com"
    if not key:
        raise RuntimeError(
            "未配置 DASHSCOPE_API_KEY（阿里云百炼）。配置方式：\n"
            "  echo 'export DASHSCOPE_API_KEY=sk-xxx' > ~/.dsh/secrets/dashscope.env\n"
            "  chmod 600 ~/.dsh/secrets/dashscope.env")
    # 比例 → 合法尺寸。**不同模型允许的尺寸不同**：
    #   wanx-v1 只接受 1024*1024 / 720*1280 / 1280*720 / 768*1152
    #   （传 810*1440 会报 "The size does not match the allowed size"，踩过）
    SIZE_COMMON = {"9:16": "810*1440", "3:4": "1080*1440",
                   "16:9": "1440*810", "1:1": "1024*1024", "4:3": "1440*1080"}
    SIZE_WANXV1 = {"9:16": "720*1280", "3:4": "768*1152",
                   "16:9": "1280*720", "1:1": "1024*1024", "4:3": "1024*1024"}
    m = str(model or "").lower()
    size = (SIZE_WANXV1 if m.startswith("wanx-v1") else SIZE_COMMON).get(
        aspect_ratio, "720*1280" if m.startswith("wanx-v1") else "810*1440")

    body = json.dumps({"model": model, "input": {"prompt": prompt},
                       "parameters": {"size": size, "n": 1}}).encode()
    d = _post_json(
        f"https://{host}/api/v1/services/aigc/text2image/image-synthesis",
        body, headers={"Authorization": f"Bearer {key}",
                       "Content-Type": "application/json",
                       "X-DashScope-Async": "enable"})
    if d.get("code"):
        raise RuntimeError(f"百炼生图提交失败: {d.get('code')} {d.get('message')}")
    tid = (d.get("output") or {}).get("task_id")
    if not tid:
        raise RuntimeError(f"百炼生图无 task_id: {str(d)[:200]}")

    # 轮询（图片模型较慢，给足时间）
    last = None
    for _ in range(30):
        import time as _t
        _t.sleep(4)
        q = urllib.request.Request(f"https://{host}/api/v1/tasks/{tid}",
                                   headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(q, timeout=30) as r:
            last = json.load(r)
        out = last.get("output") or {}
        st = out.get("task_status")
        if st == "SUCCEEDED":
            res = out.get("results") or []
            if not res or not res[0].get("url"):
                raise RuntimeError("百炼生图成功但无图片 URL")
            record_cost("image", "dashscope", model, 1)
            return res[0]["url"]
        if st in ("FAILED", "CANCELED"):
            raise RuntimeError(f"百炼生图失败: {out.get('code')} {out.get('message')}")
    raise RuntimeError(f"百炼生图超时未完成: {str(last)[:200]}")


# 阶跃生图模型参数（2026-09 实测 /models 后仅剩这两个，且官方公告
# **2026-10-10 国内外同步永久关停全部文生图接口**，无后继图像模型）：
#   step-image-edit-2  0.02元/张  prompt≤512  steps 默认8  cfg 默认1.0
#   step-2x-large      0.10元/张  steps 默认50 cfg 默认7.5
# 下线前引擎已频繁 503（缩容），仅作应急通道，禁止作为长期生产依赖。
_STEPFUN_IMAGE_MODELS = {
    "step-image-edit-2": {
        # 官方尺寸表（声明格式 height×width）：竖版=1360x768，横版=768x1360
        "sizes": {"9:16": "1360x768", "3:4": "1184x896",
                  "16:9": "768x1360", "4:3": "896x1184",
                  "1:1": "1024x1024"},
        "steps": 8, "cfg_scale": 1.0, "prompt_limit": 512,
    },
    "step-2x-large": {
        # OpenAI 惯例 width×height：竖版 800x1280
        "sizes": {"9:16": "800x1280", "3:4": "800x1280",
                  "16:9": "1280x800", "4:3": "1280x800",
                  "1:1": "1024x1024"},
        "steps": 50, "cfg_scale": 7.5, "prompt_limit": 1024,
    },
}


def img_stepfun(prompt, aspect_ratio="9:16", model="step-image-edit-2", **_):
    """
    阶跃星辰文生图（OpenAI 兼容，同步返回 URL）。

    ⚠️ **下线倒计时通道**：官方公告 2026-10-10 起 /images/generations
       国内外同步停止服务，且无替代图像模型。2026-09 实测引擎已持续 503
       （下线前缩容）。仅适合下线前白嫖应急，必须有备用通道。

    两个在售模型见 _STEPFUN_IMAGE_MODELS；早期免费的 step-1x-medium
    已被平台移除（调用报 model not supported）。
    """
    mdl = model or "step-image-edit-2"
    spec = _STEPFUN_IMAGE_MODELS.get(mdl)
    if not spec:
        raise RuntimeError(
            f"阶跃生图模型 {mdl!r} 不可用（step-1x-medium 已下线；"
            f"仅余 {list(_STEPFUN_IMAGE_MODELS)}，且 2026-10-10 全部关停）")
    gw = (load_model_catalog().get("gateways") or {}).get("stepfun") or {}
    base = (gw.get("base_url") or "https://api.stepfun.com/v1").rstrip("/")
    key = (_read_gateway_secret(gw)
           or _read_secret("STEPFUN_API_KEY",
                           os.path.expanduser("~/.dsh/secrets/stepfun.env")))
    if not key:
        raise RuntimeError(
            "未配置 STEPFUN_API_KEY（阶跃星辰）。配置方式：\n"
            "  echo 'export STEPFUN_API_KEY=xxx' > ~/.dsh/secrets/stepfun.env\n"
            "  chmod 600 ~/.dsh/secrets/stepfun.env")
    # edit-2 prompt 上限 512 字符：超出截断（画面关键词通常前置），避免整镜 400
    p = str(prompt or "")
    if len(p) > spec["prompt_limit"]:
        print(f"  ⚠️  prompt {len(p)} 字超出 {mdl} 上限 "
              f"{spec['prompt_limit']}，已截断", file=sys.stderr)
        p = p[:spec["prompt_limit"]]
    size = spec["sizes"].get(aspect_ratio, spec["sizes"]["9:16"])
    body = json.dumps({
        "model": mdl, "prompt": p, "size": size, "n": 1,
        "response_format": "url",
        "steps": spec["steps"], "cfg_scale": spec["cfg_scale"],
    }).encode()
    # _post_json 自带 429/503 指数退避（下线前缩容期 503 高频，4 轮重试）
    d = _post_json(
        base + "/images/generations", body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    item = (d.get("data") or [{}])[0]
    if item.get("finish_reason") == "content_filtered":
        raise RuntimeError("阶跃生图被内容安全策略拦截"
                           "（finish_reason=content_filtered），请调整 prompt 后重试")
    if d.get("error"):
        raise RuntimeError(f"阶跃生图错误: {d['error']}")
    url = item.get("url")
    if not url:
        raise RuntimeError(f"阶跃生图未返回图片 URL: {str(d)[:200]}")
    record_cost("image", "stepfun", mdl, 1)
    return url


# 火山方舟 Agent Plan 生图（套餐 AFP 积分，边际 ¥0/张）
# 实测（2026-09）：plan 端点与后付费 /api/v3 不同——
#   ① 模型名只认套餐短名 doubao-seedream-5.0-lite（带日期版本号报
#      UnsupportedModel "does not support the agent plan feature"）
#   ② **强制总像素 ≥ 3,686,400（约 2K 档）**，低于即 InvalidParameter
#   ③ 同步返回 TOS URL（约 25s/张），JPEG 约 500KB，右下角自带「AI生成」
#      合规水印（正好满足平台 AIGC 标识要求，保留）
# 竖屏 9:16 → 1440x2560（=3,686,400，恰好下限）
_ARK_PLAN_SIZES = {
    "9:16": "1440x2560", "3:4": "1664x2220",
    "16:9": "2560x1440", "4:3": "2220x1664",
    "1:1": "1920x1920",
}


def img_ark_plan(prompt, aspect_ratio="9:16", model="doubao-seedream-5.0-lite", **_):
    """火山方舟 Agent Plan 文生图（Seedream 5.0 Lite，套餐积分内 ¥0/张）。"""
    gw = (load_model_catalog().get("gateways") or {}).get("ark-plan") or {}
    base = (gw.get("base_url") or "https://ark.cn-beijing.volces.com/api/plan/v3").rstrip("/")
    key = (_read_gateway_secret(gw)
           or _read_secret("ARK_API_KEY",
                           os.path.expanduser("~/.dsh/secrets/ark.env")))
    if not key:
        raise RuntimeError(
            "未配置 ARK_API_KEY（火山方舟 Agent Plan）。配置方式：\n"
            "  echo 'export ARK_API_KEY=ark-xxx' > ~/.dsh/secrets/ark.env\n"
            "  chmod 600 ~/.dsh/secrets/ark.env")
    size = _ARK_PLAN_SIZES.get(aspect_ratio, _ARK_PLAN_SIZES["9:16"])
    body = json.dumps({
        "model": model or "doubao-seedream-5.0-lite",
        "prompt": prompt, "size": size,
        "response_format": "url", "output_format": "jpeg",
    }).encode()
    # Seedream 同步约 25s/张，timeout 给足；429/5xx 由 _post_json 退避
    d = _post_json(
        base + "/images/generations", body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"},
        retries=3, timeout=300)
    if d.get("error"):
        raise RuntimeError(f"方舟生图错误: {d['error']}")
    item = (d.get("data") or [{}])[0]
    url = item.get("url")
    if not url:
        raise RuntimeError(f"方舟生图未返回 URL: {str(d)[:200]}")
    record_cost("image", "ark_plan", model, 1,
                note=f"Agent Plan AFP 积分 {size}")
    return url


# ── 项目级配置（§1.1 原则 6「项目级隔离」；免每次传长参数）────────────
# 位置：scripts/project_configs/<project_id>.json
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_configs")


def project_config_file(project_id):
    """返回**实际生效**的配置文件名（含别名反查），供日志显示真实来源。

    日志里凭 project_id 猜文件名会写出根本不存在的 project_configs/<PB id>.json，
    而内容中心传的是 PocketBase ID、文件按 slug 命名 —— 看错文件名正是排查
    「配置没生效」时最容易上当的一步。
    """
    if not project_id:
        return None
    p = os.path.join(CONFIG_DIR, f"{project_id}.json")
    if not os.path.exists(p):
        p = _resolve_project_config_by_alias(project_id)
    return os.path.basename(p) if p else None


def load_project_config(project_id):
    """
    读项目级配置。用于把 provider / model / voice_id / 风格 / 平台等
    固定下来，避免每次命令行传一长串参数。

    解析优先级（高 → 低）：
        命令行显式 > 分镜 storyboard 字段 > 本项目配置 > provider 默认
    """
    if not project_id:
        return {}
    p = os.path.join(CONFIG_DIR, f"{project_id}.json")
    if not os.path.exists(p):
        # v4.2：内容中心传的是 PocketBase 项目 ID（如 5hfgq183937ez71），
        # 而配置按 slug 命名（panduola）。无别名映射时配置**静默失效** →
        # provider 退回默认（曾导致生图误走已弃用的 MiniMax、风格丢失）。
        # 这里按 别名/账号名/slug 反查一次。
        p = _resolve_project_config_by_alias(project_id)
        if not p:
            print(f"⚠️  未找到项目配置（project_id={project_id}）；"
                  f"可在 project_configs/*.json 的 aliases 里登记该 ID", file=sys.stderr)
            return {}
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print(f"⚠️  项目配置解析失败 {p}: {e}", file=sys.stderr)
        return {}


def _resolve_project_config_by_alias(project_id):
    """按 aliases / account / project_id 字段反查配置文件名"""
    try:
        for fn in os.listdir(CONFIG_DIR):
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(CONFIG_DIR, fn)
            try:
                cfg = json.load(open(fp, encoding="utf-8"))
            except Exception:
                continue
            aliases = [str(a) for a in (cfg.get("aliases") or [])]
            if project_id in aliases or project_id == str(cfg.get("account") or ""):
                return fp
    except Exception:
        pass
    return None


# ── 注册表 ────────────────────────────────────────────────────────────

TTS_PROVIDERS = {
    "edge": {
        "fn": tts_edge, "free": True,
        "default_voice": "zh-CN-YunxiNeural",
        "default_model": None,          # Edge 无 model 概念
        "cost_note": "免费（微软 Edge，无需 key）",
        "voices_hint": "zh-CN-YunxiNeural(男) / zh-CN-XiaoxiaoNeural(女) / zh-CN-YunjianNeural(男·解说)",
    },
    "minimax": {
        "fn": tts_minimax, "free": False,
        "default_voice": "male-qn-qingse",
        "default_model": "speech-2.8-hd",
        "cost_note": "speech-2.8-hd 3.5元/万字符；speech-2.8-turbo 2元/万字符",
        "voices_hint": "系统音色 或 克隆音色 voice_id（如 panduola-narrator-v1）",
    },
    "dashscope": {
        "fn": tts_dashscope, "free": False,
        "default_voice": "Cherry",
        "default_model": "qwen3-tts-flash",
        "cost_note": "qwen3-tts-flash 0.8~1元/万字符（比 MiniMax HD 便宜约 4 倍）",
        "voices_hint": "Cherry(女)/Serena(女)/Ethan(男)/Chelsie/Dylan(北京话)",
    },
}

# ── 本地占位图 provider（v5.1：--profile test 零成本跑通用，绝不用于生产交付）──
# 不发任何网络请求、不花一分钱：用 Pillow 画一张带镜号与 prompt 摘要的占位 JPG，
# 让 validate→配音→字幕→草稿→成片→QC 全链路（尺寸/比例/时长/合成）都能真实跑通。
# 占位图在分镜里标 visual.placeholder=true，QC 据此：test=warning，prod=error 阻断。

# 占位图基准分辨率（短边 720，与真实生图同比例，ffmpeg/剪映均可正常消费）
_PLACEHOLDER_SIZES = {
    "9:16": (720, 1280), "3:4": (768, 1024), "4:3": (1024, 768),
    "16:9": (1280, 720), "1:1": (1024, 1024), "21:9": (1280, 548),
}
_PLACEHOLDER_FONTS = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def _placeholder_font(size):
    from PIL import ImageFont
    for fp in _PLACEHOLDER_FONTS:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_cn(text, font, max_width, draw):
    """按像素宽度对中英文混排做逐字折行"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        trial = cur + ch
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def img_placeholder(prompt, aspect_ratio="9:16", model=None, *,
                    out_path=None, shot_id=0, **_):
    """本地生成占位 JPG 并写到 out_path；返回文件路径（local provider，无 URL/下载）。"""
    from PIL import Image, ImageDraw
    w, h = _PLACEHOLDER_SIZES.get(aspect_ratio, (720, 1280))
    img = Image.new("RGB", (w, h), (37, 42, 56))
    d = ImageDraw.Draw(img)
    # 斜向色带，避免被误认为真实画面
    for y in range(0, h, 16):
        shade = 37 + (y // 16 % 2) * 8
        d.rectangle([0, y, w, y + 15], fill=(shade, shade + 5, shade + 18))
    # 外框
    d.rectangle([16, 16, w - 16, h - 16], outline=(120, 200, 255), width=4)

    f_tag = _placeholder_font(int(w * 0.045))
    f_id = _placeholder_font(int(w * 0.22))
    f_body = _placeholder_font(int(w * 0.045))
    cyan = (120, 200, 255)
    d.text((40, 46), "[TEST] PLACEHOLDER · 占位图（¥0 · 不可交付）", fill=cyan, font=f_tag)
    d.text((40, h * 0.30), f"SHOT {int(shot_id):02d}", fill=(230, 235, 245), font=f_id)
    summary = (prompt or "").strip().replace("，", "，\n")
    body_lines = _wrap_cn(summary, f_body, w - 80, d)[:8]
    y = int(h * 0.52)
    for ln in body_lines:
        d.text((40, y), ln, fill=(180, 190, 210), font=f_body)
        y += int(w * 0.075)
    d.text((40, h - 80), f"{aspect_ratio} · local placeholder provider",
           fill=(110, 120, 140), font=f_tag)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "JPEG", quality=88)
    record_cost("image", "placeholder", None, 1,
                note=f"占位图 镜{int(shot_id)}（test 档零成本）")
    return out_path


IMAGE_PROVIDERS = {
    "dashscope": {"fn": img_dashscope,
                  "default_model": "wanx2.1-t2i-turbo",
                  "cost_note": "百炼通义万相 约0.10~0.16元/张（新用户送100张）；"
                               "备选 wanx-v1 0.16元/张"},
    "minimax": {"fn": img_minimax, "default_model": "image-01",
                "cost_note": "MiniMax image-01 按张计费（余额已耗尽）"},
    "ark_plan": {"fn": img_ark_plan, "default_model": "doubao-seedream-5.0-lite",
                 "cost_note": "火山方舟 Agent Plan · Seedream 5.0 Lite（套餐 AFP 积分内 ¥0/张；"
                              "2K 竖版 1440x2560；约25s/张；自带AI生成水印）"},
    "stepfun": {"fn": img_stepfun, "default_model": "step-image-edit-2",
                "cost_note": "阶跃 step-image-edit-2 0.02元/张（⚠️2026-10-10 全线下线，"
                             "当前引擎频繁 503，仅应急）/ step-2x-large 0.1元/张"},
    # local=True：generate_images 不发 HTTP/不下载，直接用 fn 返回的本地路径；
    # requires_key=False：无需任何 API key。仅用于 --profile test 零成本链路。
    "placeholder": {"fn": img_placeholder, "default_model": None,
                    "local": True, "requires_key": False,
                    "cost_note": "本地占位图（¥0，仅开发档跑通流程；不可交付）"},
}

# ── 模型目录驱动（v5.1：加模型=改 JSON，不改代码）──────────────────────────
# model_catalog.json 声明网关（base_url+密钥文件）与各模态可用模型；这里把
# openai-* 协议的条目动态注册进上面的静态 PROVIDERS 表，并合并单价。
# 已静态实现私有协议的（dashscope 异步生图 / WS 克隆 / minimax）继续走专用 fn，
# 目录只负责元数据/单价；凡是标准 OpenAI 协议的（阶跃 TTS、自托管 new-api 等）
# 一律用下面的通用 fn，加一家只需在 JSON 登记一行。

CATALOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_catalog.json")
_catalog_loaded = False
_catalog_providers_inited = False
_model_catalog = {}
# (模态, provider, model) → 目录里的 label。同一个 provider 可以挂多个 model
# （阶跃就有 mini / tts-2 两档），而 TTS_PROVIDERS 每 provider 只有一条、
# 元数据取自**首个**登记条目 → 直接打 prov['cost_note'] 会把 tts-2 显示成 Mini。
_MODEL_LABEL = {}


def model_label(kind, provider, model):
    """查目录里登记的中文档位名；未登记返回 None（调用方自行回落）。"""
    return _MODEL_LABEL.get((kind, provider, model))


def load_model_catalog(force=False):
    """读取并缓存模型目录；缺失/损坏时优雅降级为空目录（不影响静态 provider）。"""
    global _model_catalog, _catalog_loaded
    if _catalog_loaded and not force:
        return _model_catalog
    _catalog_loaded = True
    try:
        with open(CATALOG_PATH, encoding="utf-8") as f:
            _model_catalog = json.load(f)
    except FileNotFoundError:
        print(f"⚠️  未找到模型目录 {CATALOG_PATH}，仅用内置 provider", file=sys.stderr)
        _model_catalog = {}
    except Exception as e:
        print(f"⚠️  模型目录解析失败: {e}", file=sys.stderr)
        _model_catalog = {}
    return _model_catalog


def _read_gateway_secret(gw):
    """从 ~/.dsh/secrets/<secret_file> 读 export <key_env>=，再退环境变量。"""
    env_name = (gw or {}).get("key_env") or "API_KEY"
    sf = (gw or {}).get("secret_file")
    if sf:
        p = os.path.expanduser(os.path.join("~/.dsh/secrets", sf))
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                line = line.strip()
                if line.startswith(f"export {env_name}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(env_name, "").strip()


def _probe_bytes_duration(data):
    """对音频字节临时落盘测时长（OpenAI /audio/speech 只回二进制，不带时长）。"""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    try:
        with open(tmp, "wb") as f:
            f.write(data)
        r = subprocess.run([FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", tmp],
                           capture_output=True, text=True, timeout=30)
        return round(float(r.stdout.strip()), 3)
    except Exception:
        return 0.0
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _make_openai_tts(provider_name, gw, price_per_wan):
    """构造一个 OpenAI 兼容 /audio/speech 的 TTS fn（阶跃、new-api 通用）。"""
    def fn(text, voice_id, speed=1.0, model=None, **_):
        base = (gw.get("base_url") or "").rstrip("/")
        key = _read_gateway_secret(gw)
        if not base:
            raise RuntimeError(f"{provider_name} 网关 base_url 未配置（model_catalog.json）")
        if not key:
            raise RuntimeError(f"未找到 {provider_name} 密钥（{gw.get('secret_file')} 的 {gw.get('key_env')}）")
        body = json.dumps({
            "model": model, "input": text, "voice": voice_id,
            "response_format": "mp3", "speed": float(speed or 1.0),
        }).encode()
        req = urllib.request.Request(
            base + "/audio/speech", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        record_cost("tts", provider_name, model, len(text))
        return data, _probe_bytes_duration(data)
    return fn


def _make_openai_image(provider_name, gw):
    """构造一个 OpenAI 兼容 /images/generations（同步、返回 URL）的生图 fn。

    适用于硅基流动、自托管 new-api 等标准网关。尺寸可被网关条目
    `sizes` 覆盖（不同模型白名单不同，如 Kolors 竖版用 720x1280）。
    429/5xx 走 _post_json 指数退避；错误体透传，额度/欠费问题一眼可见。
    """
    default_sizes = {"9:16": "720x1280", "3:4": "768x1024",
                     "4:3": "1024x768", "16:9": "1280x720",
                     "1:1": "1024x1024"}
    sizes = {**default_sizes, **(gw.get("sizes") or {})}
    default_size = gw.get("default_size") or sizes["9:16"]

    def fn(prompt, aspect_ratio="9:16", model=None, **_):
        base = (gw.get("base_url") or "").rstrip("/")
        key = _read_gateway_secret(gw)
        if not base or not key:
            raise RuntimeError(f"{provider_name} 网关未配置或缺密钥"
                               f"（model_catalog.json / ~/.dsh/secrets/）")
        wh = sizes.get(aspect_ratio, default_size)
        body = json.dumps({"model": model, "prompt": prompt, "size": wh,
                           "n": 1, "response_format": "url"}).encode()
        d = _post_json(
            base + "/images/generations", body,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"})
        item = ((d.get("data") or [{}])[0])
        url = item.get("url")
        if not url:
            raise RuntimeError(
                f"{provider_name} 未返回图片 URL（b64 模式暂不支持，"
                f"请在网关侧配置返回 URL）：{str(d)[:200]}")
        return url
    return fn


def init_catalog_providers():
    """把模型目录里 openai-* 协议条目合并进 PROVIDERS 与 _PRICE（幂等）。"""
    global _catalog_providers_inited
    if _catalog_providers_inited:
        return
    _catalog_providers_inited = True
    cat = load_model_catalog()
    gws = cat.get("gateways") or {}

    # TTS：同一 provider 可挂多个 model（一个通用 fn，model 由 resolve 传入）
    tts_seen = {}
    for e in cat.get("tts") or []:
        prov, model = e.get("provider"), e.get("model")
        price = float(e.get("price_per_wan") or 0)
        # model=null 表示「该 provider 的档位价」（如 edge 免费），同样要登记，
        # 否则 unit_price 查不到会回落成「未登记」——成本预估与费用标签都会失准。
        _PRICE[("tts", prov, model)] = price / 10000
        _MODEL_LABEL[("tts", prov, model)] = e.get("label") or prov
        if e.get("protocol") == "openai-audio" and e.get("gateway") in gws and prov not in TTS_PROVIDERS:
            gw = gws[e["gateway"]]
            TTS_PROVIDERS[prov] = {
                "fn": _make_openai_tts(prov, gw, price),
                "free": price == 0,
                "default_voice": e.get("default_voice") or "",
                "default_model": e.get("model"),
                "cost_note": f"{e.get('label') or prov}（OpenAI 兼容网关 {e.get('gateway')}）",
                "voices_hint": ", ".join(e.get("voices") or []),
            }
            tts_seen[prov] = True

    # 生图：openai-image 协议（new-api 这类标准同步网关）
    for e in cat.get("image") or []:
        prov, model = e.get("provider"), e.get("model")
        # price 缺省/null = 「单价未登记」：不写精确价，unit_price 兜底
        # 返回 estimate=True（面板显示『单价未登记』），绝不谎报 ¥0。
        if e.get("price") is not None:
            _PRICE[("image", prov, model)] = float(e["price"])
        _MODEL_LABEL[("image", prov, model)] = e.get("label") or prov
        if e.get("protocol") == "openai-image" and e.get("gateway") in gws and prov not in IMAGE_PROVIDERS:
            gw = gws[e["gateway"]]
            IMAGE_PROVIDERS[prov] = {
                "fn": _make_openai_image(prov, gw),
                "default_model": e.get("model"),
                "cost_note": e.get("label") or prov,
            }

    # 视频（B-roll）：目录里登记单价即可，调用实现仍在硬编码 provider 表中
    for e in cat.get("video") or []:
        _PRICE[("video", e.get("provider"), e.get("model"))] = float(e.get("price") or 0)


def resolve_tts_provider(cli=None, storyboard=None, project_cfg=None):
    """优先级：命令行 > 项目配置 > 分镜 > 默认(edge 免费优先)

    与 resolve_tts_params 一致：项目配置优先于分镜（音色/provider 属项目级资产）。"""
    init_catalog_providers()  # v5.1：先合并模型目录里的网关型 provider（阶跃/new-api）
    v = (storyboard or {}).get("voice") or {}
    pc = (project_cfg or {}).get("tts") or {}
    name = cli or pc.get("provider") or v.get("provider") or "edge"
    if name not in TTS_PROVIDERS:
        raise SystemExit(f"未知 TTS provider: {name}；可选 {list(TTS_PROVIDERS)}")
    return name, TTS_PROVIDERS[name]


def resolve_tts_params(cli_voice=None, cli_model=None,
                       storyboard=None, project_cfg=None, prov=None):
    """
    解析 TTS 的音色与模型，并**回显各自来源**（便于自查）。

    优先级（§2.1「音色存项目级配置，不散落在会话」）：
        命令行 > 项目配置 > 分镜 > provider 默认
    说明：**项目配置优先于分镜**是有意为之——音色是「项目级资产」，
    分镜里的 voice 字段属可选备注（历史遗留易失真），故让项目配置说话。
    需要单条视频特殊音色时，用命令行 --voice-id 覆盖。
    """
    sb_v = (storyboard or {}).get("voice") or {}
    pc = (project_cfg or {}).get("tts") or {}
    if cli_voice:
        voice, vsrc = cli_voice, "命令行 --voice-id"
    elif pc.get("voice_id"):
        voice, vsrc = pc["voice_id"], "项目配置 tts.voice_id"
    elif sb_v.get("voice_id"):
        voice, vsrc = sb_v["voice_id"], "分镜 voice.voice_id（备注）"
    else:
        voice, vsrc = (prov or {}).get("default_voice"), "provider 默认"

    if cli_model:
        model, msrc = cli_model, "命令行 --model"
    elif pc.get("model"):
        model, msrc = pc["model"], "项目配置 tts.model"
    else:
        model, msrc = (prov or {}).get("default_model"), "provider 默认"
    return voice, vsrc, model, msrc


def resolve_tts_speed(cli_speed=None, storyboard=None, project_cfg=None):
    """
    解析语速倍率，并回显来源。优先级与 resolve_tts_params 同口径：
        命令行 --speed > 项目配置 tts.speed > 分镜 voice.speed > 1.0

    为什么要单独一个函数：speed 此前**只有命令行一个入口**，配置表和分镜里写的
    speed 没有任何代码读取（配了不生效比没配置更误导）。上限 2.0/下限 0.5 是
    对 LLM 产出的分镜字段做边界钳制 —— 倍率写飞了会把整条片子的音画轴拉崩。
    """
    sb_v = (storyboard or {}).get("voice") or {}
    pc = (project_cfg or {}).get("tts") or {}
    raw, src = None, None
    if cli_speed is not None:
        raw, src = cli_speed, "命令行 --speed"
    elif pc.get("speed") is not None:
        raw, src = pc["speed"], "项目配置 tts.speed"
    elif sb_v.get("speed") is not None:
        raw, src = sb_v["speed"], "分镜 voice.speed"
    if raw is None:
        return 1.0, "默认 1.0"
    try:
        v = float(raw)
    except (TypeError, ValueError):
        print(f"⚠️  语速 {raw!r} 不是数字（{src}），退回 1.0", file=sys.stderr)
        return 1.0, "默认 1.0（配置值非法）"
    clamped = max(0.5, min(2.0, v))
    if clamped != v:
        print(f"⚠️  语速 {v} 超出 0.5~2.0（{src}），按 {clamped} 执行", file=sys.stderr)
    return round(clamped, 3), src


def resolve_image_provider(cli=None, storyboard=None, project_cfg=None):
    """优先级：命令行 > 项目配置 > 分镜 > 默认(minimax)"""
    init_catalog_providers()  # v5.1：合并模型目录里的网关型生图 provider
    v = (storyboard or {}).get("visual") or {}
    pc = (project_cfg or {}).get("image") or {}
    name = cli or pc.get("provider") or v.get("provider") or "minimax"
    if name not in IMAGE_PROVIDERS:
        raise SystemExit(f"未知生图 provider: {name}；可选 {list(IMAGE_PROVIDERS)}")
    return name, IMAGE_PROVIDERS[name]


def resolve_image_params(cli_model=None, storyboard=None, project_cfg=None, prov=None):
    """解析生图模型与风格预设，并回显来源"""
    pc = (project_cfg or {}).get("image") or {}
    sb_style = ((storyboard or {}).get("style") or {})
    if cli_model:
        model, msrc = cli_model, "命令行 --model"
    elif pc.get("model"):
        model, msrc = pc["model"], "项目配置 image.model"
    else:
        model, msrc = (prov or {}).get("default_model"), "provider 默认"
    return model, msrc, pc.get("style_preset") or sb_style.get("preset")


def _post_json(url, body, headers, retries=4, timeout=90):
    """
    带指数退避的 POST。解决实测遇到的 **HTTP 429 限流**（连续生图时必现）。
    只对 429/5xx 重试；4xx 业务错误立即抛出，避免掩盖参数问题。
    """
    import time as _t
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                wait = 4 * (2 ** i)
                print(f"  ⏳ HTTP {e.code}（限流/服务端），{wait}s 后退避重试 "
                      f"({i + 1}/{retries - 1})", file=sys.stderr)
                _t.sleep(wait)
                continue
            # 带上响应体——否则调用方只看到 "HTTP 403"，看不到真正原因
            # （如百炼视频模型未开通是 code=AccessDenied.Unpurchased）
            try:
                body = e.read().decode("utf-8", "ignore")[:300]
            except Exception:
                body = ""
            raise RuntimeError(f"HTTP {e.code}: {body}") from None
    raise last


# ── 成本核算（审计报告 P1）───────────────────────────────────────────
# 每条视频花了多少钱，以前只能靠口头估算。现在：每次调用记录用量与单价，
# 写入 JSONL 流水（路径由环境变量 VIDEO_COST_LOG 指定，由 run_pipeline 传给子进程），
# 最后汇总成 cost.json。
#
# 价格来源：官方文档单价；标注 ESTIMATE 的为估算值（未查到确切单价，按同档估计）。

COST_LOG_PATH = os.environ.get("VIDEO_COST_LOG", "")
_ledger = []

# (kind, provider, model) → 单价（元 / 单位）；单位是「字符」(tts) 或「张」(image/video)
_PRICE = {
    # TTS：元 / 每字符（= 官方「元/万字符」÷ 10000）
    ("tts", "edge", None): 0.0,
    ("tts", "dashscope", "qwen3-tts-flash"): 0.8 / 10000,
    ("tts", "dashscope", "cosyvoice-v3.5-flash"): 0.8 / 10000,
    ("tts", "dashscope", "cosyvoice-v3.5-plus"): 1.5 / 10000,
    ("tts", "dashscope", "cosyvoice-v3-flash"): 1.0 / 10000,
    ("tts", "dashscope", "cosyvoice-v3-plus"): 2.0 / 10000,
    ("tts", "dashscope", "cosyvoice-v2"): 2.0 / 10000,
    ("tts", "minimax", "speech-2.8-hd"): 3.5 / 10000,
    ("tts", "minimax", "speech-2.8-turbo"): 2.0 / 10000,
    ("tts", "minimax", "speech-02-hd"): 3.5 / 10000,
    ("tts", "minimax", "speech-02-turbo"): 2.0 / 10000,
    # 生图：元 / 张
    ("image", "dashscope", "wanx2.1-t2i-turbo"): 0.10,     # ESTIMATE
    ("image", "dashscope", "wanx-v1"): 0.16,
    ("image", "dashscope", "z-image-turbo"): 0.10,
    ("image", "minimax", "image-01"): 0.15,                # ESTIMATE
    ("image", "stepfun", "step-image-edit-2"): 0.02,       # 官方定价（2026-10-10 下线）
    ("image", "stepfun", "step-2x-large"): 0.10,           # 官方定价（2026-10-10 下线）
    ("image", "ark_plan", "doubao-seedream-5.0-lite"): 0.0,  # Agent Plan 套餐 AFP 积分，边际 ¥0
    ("image", "ark_plan", "doubao-seedream-5-0-pro"): 0.0,   # 同上（Large+ 套餐，如可用）
    # 视频：元 / 片段
    ("video", "dashscope", "wanx2.1-i2v-turbo"): 1.5,      # ESTIMATE（官方区间 0.5~3）
    ("video", "minimax", "video-01"): 2.0,                 # ESTIMATE
}


def unit_price(kind, provider, model):
    """查单价，未登记的按同类 provider 的默认值兜底（并标记为估算）

    先合并模型目录：run_pipeline 的成本预估/费用标签会直接调本函数，
    不保证此前有跑过 resolve_*（那才是触发合并的地方），漏合并会把
    「目录里登记的免费档」误报成「未登记」。
    """
    try:
        init_catalog_providers()
    except Exception:
        pass
    if (kind, provider, model) in _PRICE:
        return _PRICE[(kind, provider, model)], False
    for (k, p, m), v in _PRICE.items():
        if k == kind and p == provider and m is None:
            return v, True
    return 0.0, True


def record_cost(kind, provider, model, units, note=""):
    """
    记一笔账。units：tts=字符数，image=张数，video=片段数。
    同时写入 VIDEO_COST_LOG（若有），供 run_pipeline 跨进程汇总。
    """
    price, est = unit_price(kind, provider, model)
    e = {"kind": kind, "provider": provider, "model": model,
         "units": units, "unit_price": price, "estimate": est,
         "cost": round(price * units, 6), "note": note}
    _ledger.append(e)
    if COST_LOG_PATH:
        try:
            os.makedirs(os.path.dirname(COST_LOG_PATH) or ".", exist_ok=True)
            with open(COST_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return e


def cost_report(entries=None):
    """汇总账目 → {'total':..., 'by_kind': {...}, 'entries': n, 'has_estimate': bool}"""
    es = entries if entries is not None else _ledger
    total = 0.0
    by = {}
    est = False
    for e in es:
        total += e.get("cost", 0)
        k = e.get("kind")
        b = by.setdefault(k, {"n": 0, "units": 0, "cost": 0.0, "models": set()})
        b["n"] += 1
        b["units"] += e.get("units", 0)
        b["cost"] += e.get("cost", 0)
        m = e.get("model")
        b["models"].add(str(m) if m else "-")  # edge 等无模型概念的 provider 显示 "-"
        est = est or bool(e.get("estimate"))
    for b in by.values():
        b["cost"] = round(b["cost"], 4)
        b["models"] = sorted(b["models"])
    return {"total": round(total, 4), "by_kind": by,
            "entries": len(es), "has_estimate": est}


def load_cost_log(path):
    es = []
    if not path or not os.path.exists(path):
        return es
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                es.append(json.loads(line))
            except Exception:
                pass
    return es


# ── P1-c provider 降级链 ─────────────────────────────────────────────
# 设计纪律（P1 实施计划 §1 D6/D7）：
#  - provider fn 保持「单次调用」语义，**换家发生在子脚本的逐镜循环**，不在 fn 内；
#  - 失败分类决定是否换家：config（缺 key）/billing（余额·402·未开通）/transient
#    （429·5xx·超时）→ 换下一家；prompt（内容审核类）→ 不换家（换家也一样挂）；
#  - 链配置优先级：项目配置 {tts,image}.fallback > model_catalog.json.fallback_chains；
#  - test 档只准降级到**登记单价为 0** 的通道 —— 无人值守时绝不悄悄烧钱。

def classify_call_failure(err):
    """把一次调用的异常归类成 degrade / 不 degrade 的依据（对错误字符串做关键词判定）。"""
    s = str(err)
    low = s.lower()
    if "api_key" in low or "未配置" in s or "未找到" in s:
        return "config"
    if any(h in low for h in ("content_filter", "content_filtered", "sensitive",
                              "data_inspection", "datainspection")) \
            or any(h in s for h in ("审核", "不合规", "违规")):
        return "prompt"
    if any(h in low for h in ("unpurchased", "insufficient", "balance", "arrears",
                              "quota", "exceeded", "402")) \
            or any(h in s for h in ("余额", "欠费", "未开通", "限额")):
        return "billing"
    if any(h in low for h in ("429", "500", "502", "503", "504", "timed out",
                              "timeout", "urlerror", "connection", "reset by peer")):
        return "transient"
    return "unknown"


def provider_is_free(kind, name):
    """登记价确为 0（且非「未登记兜底 0」）才算免费通道；未登记价不敢当免费用。"""
    try:
        init_catalog_providers()
        reg = TTS_PROVIDERS if kind == "tts" else IMAGE_PROVIDERS
        default_model = (reg.get(name) or {}).get("default_model")
        price, est = unit_price(kind, name, default_model)
        return price == 0 and not est
    except Exception:
        return False


def fallback_chain(kind, primary, project_cfg=None, free_only=False):
    """返回自 primary 起有序尝试的 provider 名列表（primary 恒在链首）。

    只保留注册表里真实存在的候选；free_only（test 档）过滤掉一切付费通道。
    """
    try:
        init_catalog_providers()
    except Exception:
        pass
    reg = TTS_PROVIDERS if kind == "tts" else IMAGE_PROVIDERS
    pc = (project_cfg or {}).get(kind) or {}
    names = pc.get("fallback")
    if not names:
        try:
            names = (load_model_catalog().get("fallback_chains") or {}).get(kind) or []
        except Exception:
            names = []
    out = [primary]
    for p in names:
        if p == primary or p not in reg:
            continue
        if free_only and not provider_is_free(kind, p):
            continue
        out.append(p)
    return out


# ── 视频（动态 B-roll）providers ───────────────────────────────────────
# ⚠️ 现状（2026-09-19 实测）：百炼视频模型返回 `AccessDenied.Unpurchased`（未开通）；
#    MiniMax 余额耗尽。**代码已就位，开通/充值后即可用**；未开通时管线会明确提示并
#    回退到「静帧 + KenBurns」，不会静默失败。
# 成本提醒：视频比生图贵一个数量级（每 5s 片段约 ¥0.5~3），故默认关闭，
#           且支持 only 关键镜（`broll.mode: key`）。

def vid_dashscope(prompt, image_url=None, model="wanx2.1-i2v-turbo", **_):
    """
    百炼 通义万相 视频生成（异步任务式，与生图同构）。
    - 图生视频（i2v）：传 `image_url`（**必须是公网可访问 URL**）
    - 文生视频（t2v）：不传 image_url
    返回：视频 URL（调用方负责下载）
    """
    key = _read_secret("DASHSCOPE_API_KEY", _DS_ENV)
    host = _read_secret("DASHSCOPE_HOST", _DS_ENV) or "dashscope.aliyuncs.com"
    if not key:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY")
    inp = {"prompt": prompt}
    if image_url:
        inp["img_url"] = image_url
    d = _post_json(
        f"https://{host}/api/v1/services/aigc/video-generation/video-synthesis",
        json.dumps({"model": model, "input": inp}).encode(),
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json",
                 "X-DashScope-Async": "enable"})
    if d.get("code"):
        if "Unpurchased" in str(d.get("code")):
            raise RuntimeError("百炼视频模型未开通（AccessDenied.Unpurchased）"
                               "——请在百炼控制台开通后重试；当前回退到静帧+KenBurns")
        raise RuntimeError(f"百炼生视频: {d.get('code')} {d.get('message')}")
    tid = (d.get("output") or {}).get("task_id")
    if not tid:
        raise RuntimeError(f"百炼生视频无 task_id: {str(d)[:200]}")

    import time as _t
    last = None
    for _ in range(60):          # 视频更慢，给足轮询次数（约 4 分钟）
        _t.sleep(4)
        q = urllib.request.Request(f"https://{host}/api/v1/tasks/{tid}",
                                   headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(q, timeout=30) as r:
            last = json.load(r)
        out = last.get("output") or {}
        st = out.get("task_status")
        if st == "SUCCEEDED":
            res = out.get("results") or (out.get("video_url") and [{"url": out["video_url"]}])
            if not res:
                raise RuntimeError("百炼生视频成功但无视频地址")
            record_cost("video", "dashscope", model, 1)
            return (res[0].get("url") or res[0].get("video_url"))
        if st in ("FAILED", "CANCELED"):
            raise RuntimeError(f"百炼生视频失败: {out.get('code')} {out.get('message')}")
    raise RuntimeError(f"百炼生视频超时: {str(last)[:200]}")


def vid_minimax(prompt, image_url=None, model="video-01", **_):
    """MiniMax 视频生成（当前账户余额不足，保留实现待充值）"""
    key = _read_secret("MINIMAX_API_KEY", _MM_ENV)
    if not key:
        raise RuntimeError("未找到 MINIMAX_API_KEY")
    body = json.dumps({"model": model, "prompt": prompt}).encode()
    req = urllib.request.Request(
        "https://api.minimaxi.com/v1/video_generation", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    if d.get("base_resp", {}).get("status_code") != 0:
        raise RuntimeError(f"MiniMax 生视频: {d.get('base_resp')}")
    tid = d.get("task_id")
    if not tid:
        raise RuntimeError("MiniMax 生视频无 task_id")
    for _ in range(60):
        import time as _t
        _t.sleep(5)
        q = urllib.request.Request(f"https://api.minimaxi.com/v1/query/video_generation?task_id={tid}",
                                   headers={"Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(q, timeout=30) as r:
            st = json.load(r)
        if st.get("status") == "Success":
            fid = (st.get("file") or {}).get("download_url") or st.get("file_id")
            if not fid:
                raise RuntimeError("MiniMax 生视频完成但无下载地址")
            return fid
        if st.get("status") == "Failed":
            raise RuntimeError(f"MiniMax 生视频失败: {st}")
    raise RuntimeError("MiniMax 生视频超时")


VIDEO_PROVIDERS = {
    "dashscope": {"fn": vid_dashscope, "default_model": "wanx2.1-i2v-turbo",
                  "cost_note": "视频模型需先在百炼开通；每片段约 ¥0.5~3（比生图贵一个数量级）"},
    "minimax": {"fn": vid_minimax, "default_model": "video-01",
                "cost_note": "MiniMax video-01（当前余额不足）"},
}


def resolve_video_provider(cli=None, project_cfg=None):
    pc = (project_cfg or {}).get("video") or {}
    name = cli or pc.get("broll_provider") or "dashscope"
    if name not in VIDEO_PROVIDERS:
        raise SystemExit(f"未知视频 provider: {name}；可选 {list(VIDEO_PROVIDERS)}")
    return name, VIDEO_PROVIDERS[name]


def describe():
    print("TTS providers:")
    for k, v in TTS_PROVIDERS.items():
        tag = "免费" if v["free"] else "付费"
        print(f"  {k:<10s} [{tag}] {v['cost_note']}")
        print(f"             音色: {v['voices_hint']}")
    print("生图 providers:")
    for k, v in IMAGE_PROVIDERS.items():
        print(f"  {k:<10s} {v['cost_note']}")


def _price_label(kind, provider, model, entry=None):
    """把单价格式化成人类可读标签（元/张、元/万字符）。"""
    unit = "万字符" if kind == "tts" else "张"
    p, _estimated = unit_price(kind, provider, model)
    if p <= 0:
        # 套餐积分型（火山 Agent Plan）边际为 0，但耗的是套餐额度，标注清楚
        note = (entry or {}).get("cost_note") or ""
        return "¥0（套餐积分内）" if "积分" in note or "套餐" in note else "免费"
    if kind == "tts":
        return f"{p * 10000:.2f}元/万字符"
    return f"¥{p:.3f}/{unit}"


def selection_brief(tts_prov=None, tts_model=None, tts_voice=None,
                    img_prov=None, img_model=None, profile=None,
                    project_cfg=None):
    """
    决策时刻选型简报（v5.1 P1-7）——在开跑前把「当前选了什么 / 花多少钱 /
    还有哪些更省或更好的替代」一次讲清，而不是让人翻文档。

    设计取舍：
      · 只打印「当前 + 至多两条更优替代」，不铺全表（全表用 `python providers.py`）
      · 替代按「同 kind 单价升序」取，免费档优先展示
      · 不联网、不校验 key 可用性（那是运行期的事），纯本地价格表推导
    """
    init_catalog_providers()
    lines = []
    if profile:
        tag = "免费优先" if profile == "test" else "项目配置（可付费）"
        lines.append(f"   档位: --profile {profile}（{tag}）")

    def _alts(kind, cur_prov, model, registry):
        """同 kind 的替代候选（按价格升序，排除自身，至多 2 条）"""
        rows = []
        for name, entry in registry.items():
            m = entry.get("default_model")
            price, est = unit_price(kind, name, m)
            if name == cur_prov:
                continue
            rows.append((price, est, name, m, entry))
        rows.sort(key=lambda r: r[0])
        return rows[:2]

    if tts_prov:
        entry = TTS_PROVIDERS.get(tts_prov) or {}
        lines.append(f"   TTS : {tts_prov} / {tts_model or '(无 model)'} / "
                     f"{tts_voice or '(默认音色)'} — {_price_label('tts', tts_prov, tts_model, entry)}")
        for price, est, name, m, e in _alts("tts", tts_prov, tts_model, TTS_PROVIDERS):
            mark = "估算" if est else "官方"
            lines.append(f"         替代: {name} / {m or '-'} — "
                         f"{_price_label('tts', name, m, e)}（{mark}）{(e.get('cost_note') or '')[:40]}")
    if img_prov:
        entry = IMAGE_PROVIDERS.get(img_prov) or {}
        lines.append(f"   生图: {img_prov} / {img_model or '(默认)'} — "
                     f"{_price_label('image', img_prov, img_model, entry)}")
        for price, est, name, m, e in _alts("image", img_prov, img_model, IMAGE_PROVIDERS):
            mark = "估算" if est else "官方"
            lines.append(f"         替代: {name} / {m or '-'} — "
                         f"{_price_label('image', name, m, e)}（{mark}）{(e.get('cost_note') or '')[:40]}")
    return lines


# ── 增量重生成支持 ────────────────────────────────────────────────────

def content_hash(*parts):
    """
    计算「输入指纹」，用于增量重生成（§16.4 O3 / §24.5 P0）。

    为什么要 hash：日常改一处（比如第 5 镜的台词或画面描述）不该整片重跑——
    生图占单条成本约 94%，重跑 11 镜等于白烧 10 镜的钱。
    把「决定产物内容的全部输入」哈希后存进分镜，下次比对即可安全跳过。
    """
    import hashlib
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def select_shots(shots, only=None, missing_hash=None, need_changed=True):
    """
    挑选需要重跑的镜。

    only          —— 显式指定（set[int] 或 None）
    missing_hash  —— 形如 {shot_id: (当前hash, 已存hash, 产物是否存在)}；None 表示不启用
    返回 (待处理镜列表, 跳过数)
    """
    todo, skipped = [], 0
    for i, shot in enumerate(shots, 1):
        sid = shot.get("shot_id", i)
        if only and sid not in only:
            skipped += 1
            continue
        if missing_hash is not None:
            cur, old, exists = missing_hash.get(sid, (None, None, False))
            if exists and cur == old:
                skipped += 1
                continue
        todo.append(shot)
    return todo, skipped


if __name__ == "__main__":
    describe()
