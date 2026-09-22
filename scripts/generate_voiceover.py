#!/usr/bin/env python3
"""
逐镜配音生成器（MiniMax T2A · Phase 1.2）

要点（依据 2026-09-19 实测）：
- 逐镜一次 T2A 调用 → 每镜一个 mp3；extra_info.audio_length 给出**毫秒级实测时长**，
  直接回填 audio.duration_sec_actual，作为字幕/画面的唯一时间源（§4.2）。
- MiniMax 的 subtitle_enable 不按句切分（每次请求一个 segment），故不做句级对齐，
  逐镜时长累加即确定性对齐。
- **样音先行**：--sample-only 只生成第一镜，供试听确认音色，满意后再批量（借鉴 OpenReelbench）。

用法：
  generate_voiceover.py --storyboard sb.json --output-dir DIR \
      [--voice-id ID] [--model speech-2.8-hd] [--speed 1.0] [--emotion] \
      [--sample-only] [--update-storyboard]

密钥来源：环境变量 MINIMAX_API_KEY，或 ~/.dsh/secrets/minimax.env
"""
import argparse
import json
import os
import sys
import time
import urllib.request

API_URL = "https://api.minimaxi.com/v1/t2a_v2"


def load_api_key(cli_key=None):
    """密钥取值优先级：--api-key > ~/.dsh/secrets/minimax.env > 环境变量

    ⚠️ 环境变量优先是危险的：本机环境里残留着废弃的 sk-cp（Token Plan）key，
       取到它会直接触发 2056 配额错误（B1 复发根因）。故以受管密钥文件为准，
       并在环境变量与之冲突时告警。
    """
    if cli_key:
        return cli_key.strip()
    file_key = ""
    envf = os.path.expanduser("~/.dsh/secrets/minimax.env")
    if os.path.exists(envf):
        for line in open(envf):
            line = line.strip()
            if line.startswith("export MINIMAX_API_KEY="):
                file_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    env_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if file_key and env_key and file_key != env_key:
        print(f"⚠️  环境变量 MINIMAX_API_KEY({env_key[:8]}…) 与受管密钥文件不一致，"
              f"已采用密钥文件（避免取到废弃的 Token Plan key）", file=sys.stderr)
    return file_key or env_key


def tts_once(text, voice_id, model, speed, emotion, api_key, timeout=120):
    """单次 T2A，返回 (mp3_bytes, duration_sec)；失败抛异常"""
    body = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice_id, "speed": speed,
                          "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000,
                          "format": "mp3", "channel": 1},
    }
    if emotion:
        body["voice_setting"]["emotion"] = emotion
    req = urllib.request.Request(
        API_URL, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.load(r)
    br = resp.get("base_resp", {})
    if br.get("status_code") != 0:
        raise RuntimeError(f"MiniMax API 错误: {br}")
    audio_hex = (resp.get("data") or {}).get("audio")
    if not audio_hex:
        raise RuntimeError(f"响应无音频数据: {str(resp)[:200]}")
    dur_ms = (resp.get("extra_info") or {}).get("audio_length")
    return bytes.fromhex(audio_hex), (dur_ms / 1000.0 if dur_ms else 0.0)


def main():
    ap = argparse.ArgumentParser(description="逐镜配音生成器（MiniMax T2A）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--voice-id", default=None,
                    help="音色ID；显式指定时**优先于**分镜 voice.voice_id")
    ap.add_argument("--model", default=None,
                    help="模型名；默认按 provider 取（minimax=speech-2.8-hd / "
                         "dashscope=qwen3-tts-flash / edge=无）")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--emotion", default=None)
    ap.add_argument("--sample-only", action="store_true",
                    help="样音先行：只生成第一镜供试听")
    ap.add_argument("--update-storyboard", action="store_true",
                    help="把 audio_path / duration_sec_actual 回填分镜 JSON")
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--tts-provider", default=None,
                    help="TTS provider：edge(免费) / minimax / dashscope；"
                         "默认取分镜 voice.provider，再兜底 edge")
    ap.add_argument("--shots", default=None,
                    help="增量重生成：只处理这些镜号（逗号分隔，如 3,5,7）")
    ap.add_argument("--only-missing", action="store_true",
                    help="增量重生成：跳过「产物已存在且输入未变」的镜（按内容 hash 判断）")
    args = ap.parse_args()

    sb_path = os.path.expanduser(args.storyboard)
    with open(sb_path, "r", encoding="utf-8") as f:
        sb = json.load(f)

    # ── Provider / 音色 / 模型 解析（§1.1 原则 5+6）──
    # 优先级：命令行 > 分镜 > 项目配置(project_configs/<project_id>.json) > provider 默认
    try:
        from providers import (resolve_tts_provider, resolve_tts_params,
                                load_project_config)
    except ImportError:
        print("❌ 缺少 providers.py（provider 抽象层）", file=sys.stderr)
        sys.exit(1)
    pcfg = load_project_config(sb.get("project_id"))
    prov_name, prov = resolve_tts_provider(args.tts_provider, sb, pcfg)
    voice_id, src, args.model, msrc = resolve_tts_params(
        args.voice_id, args.model, sb, pcfg, prov)
    if pcfg and not args.tts_provider:
        print(f"📋 已加载项目配置: {sb.get('project_id')}"
              f"（{os.path.basename(pcfg and 'project_configs/')}"
              f"{sb.get('project_id')}.json）")

    # 契约校验（§2.1 / §16.4 R3）：把字段漂移挡在入口，避免"跑完才发现字段不对"
    try:
        from storyboard_schema import validate, summarize
        issues = validate(sb)
        for it in issues:
            mark = "❌" if it["level"] == "error" else "⚠️"
            print(f"{mark} 契约 {it['path']}: {it['msg']}", file=sys.stderr)
        if any(i["level"] == "error" for i in issues):
            print(f"❌ 分镜不符合 §2.1 契约（{summarize(issues)}），已中止",
                  file=sys.stderr)
            sys.exit(1)
        if issues:
            print(f"⚠️  契约提示（{summarize(issues)}），继续执行", file=sys.stderr)
    except ImportError:
        pass

    shots = sb.get("shots") or []
    if not shots:
        print("❌ 分镜为空", file=sys.stderr); sys.exit(1)

    out_dir = os.path.expanduser(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    # edge 没有模型概念：清掉从项目配置带过来的 model，避免显示成别的模型
    if prov_name == "edge":
        args.model, msrc = None, "edge 无需模型"
    # 档位(test/prod)给的音色：来源标注更准确（否则显示成"命令行"，误导）
    if os.environ.get("VIDEO_PROFILE") == "test" and not args.voice_id:
        src = "test 档位（免费优先）"
    # 音色与 provider 错配保护（如把 MiniMax 音色喂给 Edge、中文名喂给百炼）
    def _voice_ok(name, v):
        if not v:
            return False
        if name == "edge":
            return v.startswith(("zh-", "en-"))      # zh-CN-YunxiNeural
        if name == "dashscope":
            # 系统音色：首字母大写的英文名（Cherry / Serena / Ethan）
            # 克隆音色：`{model}-{prefix}-{id}` 全串（如 cosyvoice-v3.5-flash-pd35f-xxxx）
            # 注意：不能只用 isascii() —— MiniMax 的 male-qn-qingse 也是纯 ASCII
            return ((v.isascii() and v[:1].isupper())
                    or v.startswith(("cosyvoice-", "qwen-audio-", "qwen3-tts-vc")))
        return True                                   # minimax：系统音色或克隆 voice_id
    if not _voice_ok(prov_name, voice_id):
        print(f"⚠️  音色 {voice_id!r} 不适用于 {prov_name} provider，改用 "
              f"{prov['default_voice']}（可用：{prov['voices_hint']}）", file=sys.stderr)
        voice_id, src = prov["default_voice"], "provider 默认（错配回退）"

    # ── P1-c TTS 降级链 ──
    # 换家时**音色可能不通用**（克隆音色只在其家可用）：不匹配的家用该家默认音色，
    # 并在日志与分镜里留痕 —— 宁可"音色变了但片出来了"，不要"整条管线停"。
    from providers import fallback_chain, classify_call_failure, TTS_PROVIDERS, record_cost
    free_only = os.environ.get("VIDEO_PROFILE") == "test"

    def _tts_entry(n):
        p = TTS_PROVIDERS[n]
        v = voice_id if n == prov_name or _voice_ok(n, voice_id) else p.get("default_voice")
        m = args.model if n == prov_name else p.get("default_model")
        if n == "edge":
            m = None  # edge 无模型概念
        return {"name": n, "fn": p["fn"], "voice": v, "model": m,
                "voice_changed": v != voice_id}

    chain = [_tts_entry(n) for n in
             fallback_chain("tts", prov_name, pcfg, free_only=free_only)]

    targets = shots[:1] if args.sample_only else shots

    # ── 增量重生成：显式选镜 / 自动跳过未变镜 ──
    from providers import content_hash, select_shots
    want = None
    if args.shots:
        try:
            want = {int(x) for x in args.shots.replace("，", ",").split(",") if x.strip()}
        except ValueError:
            print("❌ --shots 格式应为逗号分隔镜号，如 3,5,7", file=sys.stderr)
            sys.exit(1)
    miss = None
    if args.only_missing:
        miss = {}
        for i, s in enumerate(targets, 1):
            sid = s.get("shot_id", i)
            au = s.get("audio") or {}
            t = (au.get("text") or s.get("script_line") or "").strip()
            fp = os.path.join(out_dir, f"shot_{sid:03d}.mp3")
            ch = content_hash(t, voice_id, prov_name, args.speed)
            used_p = au.get("tts_provider")
            used_v = au.get("voice_used")
            if (used_p and used_p != prov_name and os.path.exists(fp) and used_v
                    and au.get("source_hash") == content_hash(t, used_v, used_p, args.speed)):
                # P1-c：本镜由降级链产出且输入未变 → 视为未变，别为"换回主选"重烧
                miss[sid] = (ch, ch, True)
            else:
                miss[sid] = (ch, au.get("source_hash"), os.path.exists(fp))
    todo, skipped = select_shots(targets, only=want, missing_hash=miss)

    print(f"🎙️  provider={prov_name}（{prov['cost_note']}）")
    print(f"    音色={voice_id}（{src}） 模型={args.model}（{msrc}） 速度={args.speed}")
    if len(chain) > 1:
        marks = " → ".join(c["name"] + ("*" if c["voice_changed"] else "") for c in chain)
        print(f"    🔗 配音降级链：{marks}"
              + ("（*=该家音色不通用，将换默认音色）" if any(c["voice_changed"] for c in chain) else ""))
    if args.sample_only:
        print("    （样音先行：仅第 1 镜）")
    print(f"    待处理 {len(todo)} 镜" +
          (f"，跳过 {skipped} 镜（未变化/未选中）" if skipped else ""))

    results = []
    attempted = 0
    for i, shot in enumerate(todo, 1):
        au = shot.setdefault("audio", {})
        text = (au.get("text") or shot.get("script_line") or "").strip()
        if not text:
            print(f"  ⚠️  镜{shot.get('shot_id', i)} 无台词，跳过")
            continue
        attempted += 1
        fname = f"shot_{shot.get('shot_id', i):03d}.mp3"
        fpath = os.path.join(out_dir, fname)
        entry = None
        for ci, cand in enumerate(chain):
            try:
                audio, dur = cand["fn"](text, cand["voice"], speed=args.speed,
                                        model=cand["model"], emotion=args.emotion,
                                        api_key=args.api_key)
                entry = cand
                break
            except Exception as e:
                cls = classify_call_failure(e)
                if cls == "prompt" or ci == len(chain) - 1:
                    print(f"  ❌ 镜{shot.get('shot_id', i)} 失败（最后尝试 {cand['name']}）: {e}",
                          file=sys.stderr)
                    break
                try:
                    record_cost("tts", cand["name"], cand["model"], 0,
                                note=f"degrade-fail[{cls}]: {str(e)[:80]}")
                except Exception:
                    pass
                print(f"  ⚠️  镜{shot.get('shot_id', i)}: {cand['name']} 失败({cls})，"
                      f"降级 → {chain[ci + 1]['name']}", file=sys.stderr)
        if not entry:
            continue
        with open(fpath, "wb") as f:
            f.write(audio)
        au["audio_path"] = fpath
        au["duration_sec_actual"] = round(dur, 3)
        au["tts_provider"] = entry["name"]
        # P1-c：降级时记录实际音色（可能≠主选音色），--only-missing 据此认账
        if entry["voice_changed"]:
            au["voice_used"] = entry["voice"]
        # 记录输入指纹，供下次 --only-missing 安全跳过（用实际家/音色算）
        au["source_hash"] = content_hash(text, entry["voice"], entry["name"], args.speed)
        results.append({"shot_id": shot.get("shot_id", i), "path": fpath,
                        "duration_sec": round(dur, 3)})
        via = "" if entry["name"] == prov_name else f"（降级链·经由 {entry['name']}）"
        print(f"  ✅ 镜{shot.get('shot_id', i)}: {fname}  {dur:.2f}s{via}  "
              f"「{text[:14]}{'…' if len(text) > 14 else ''}」")
        time.sleep(0.2)

    # v5.2 P1-c：对齐生图的"全败即中止"守卫 —— 此前配音全失败也 exit 0，
    # 管线静默产出缺配音成片，要到 QC（甚至成片）才暴露。
    if attempted and not results:
        print(f"❌ 全部 {attempted} 镜配音失败 —— 中止（链="
              f"{'＞'.join(c['name'] for c in chain)}，检查各家额度/密钥）", file=sys.stderr)
        sys.exit(1)

    if args.update_storyboard and results:
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
        print(f"📝 已回填分镜: {sb_path}")

    total = sum(r["duration_sec"] for r in results)
    print(f"\n合计 {len(results)} 条，总时长 {total:.2f}s")
    print(json.dumps({"count": len(results), "total_sec": round(total, 3),
                      "sample_only": args.sample_only,
                      "files": results}, ensure_ascii=False))


if __name__ == "__main__":
    main()
