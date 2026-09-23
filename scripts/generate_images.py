#!/usr/bin/env python3
"""
分镜批量生图（MiniMax 文生图 · Phase 1.4）

为什么走 MiniMax 而不是 AI 绘图工作台：
  AI 绘图工作台的 kling/jimeng/runway adapter 存在，但 backend/.env 中
  KLING/JIMENG/RUNWAY_API_KEY 均未配置（实测）；而 MiniMax key 已可用。
  故本期直接用 MiniMax /v1/image_generation，**最省事且已验证**。
  （将来若在 AI 绘图工作台配好 key，可换回 generation router，契约不变。）

落实方案要求：
- §2.1 **风格契约**：style.preset 展开为统一前缀，注入每镜 prompt，保证全片画风一致
- §2.1 **镜头语言**：visual.shot_language 六字段拼入 prompt，增强镜头感一致性
- §4.5 **比例铁律**：按 aspect_ratio 出图（禁止默认 16:9）
- **样图先行**：--sample-only 只出第一镜，确认画风后再批量

用法：
  generate_images.py --storyboard sb.json --output-dir DIR \
      [--model image-01] [--sample-only] [--update-storyboard] \
      [--style-preset warm_humanities] [--concurrency 3]
"""
import argparse
import json
import os
import sys
import shutil
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API_URL = "https://api.minimaxi.com/v1/image_generation"

# 风格契约：preset → 统一风格前缀（§2.1）
STYLE_PRESETS = {
    "warm_humanities": "电影感历史人文插画，暖调，柔和侧光，细腻油画质感，庄重氛围。",
    "tech_cold": "科技感极简插画，冷蓝调，干净线条，高对比，未来感。",
    "brand_warm": "品牌宣传视觉，温暖明亮，干净构图，高级质感，浅景深。",
    "documentary": "纪实摄影风格，自然光，真实质感，略带颗粒。",
    "none": "",
}

# MiniMax 支持的常见比例
VALID_AR = {"1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"}



def _source_ref(shot):
    """安全读取 source_ref（LLM 分镜可能写成字符串，契约只保证 dict）"""
    try:
        from storyboard_schema import source_ref as _sr
        return _sr(shot)
    except Exception:
        ref = ((shot or {}).get("visual") or {}).get("source_ref")
        return ref if isinstance(ref, dict) else {}

def load_api_key(cli_key=None):
    if cli_key:
        return cli_key.strip()
    envf = os.path.expanduser("~/.dsh/secrets/minimax.env")
    file_key = ""
    if os.path.exists(envf):
        for line in open(envf):
            line = line.strip()
            if line.startswith("export MINIMAX_API_KEY="):
                file_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    env_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if file_key and env_key and file_key != env_key:
        print(f"⚠️  环境变量 MINIMAX_API_KEY 与受管密钥文件不一致，已采用密钥文件",
              file=sys.stderr)
    return file_key or env_key


def build_prompt(shot, style_prefix):
    """风格契约前缀 + 画面描述 + 镜头语言六字段（§2.1）"""
    vis = shot.get("visual") or {}
    parts = []
    if style_prefix:
        parts.append(style_prefix)
    if vis.get("prompt"):
        parts.append(vis["prompt"].strip())
    sl = vis.get("shot_language") or {}
    hints = []
    for k in ("shot_size", "camera_movement", "lighting",
              "color_temperature", "depth_of_field", "focal_length"):
        if sl.get(k):
            hints.append(str(sl[k]))
    if hints:
        parts.append("，".join(hints))
    return "，".join(p for p in parts if p).strip()


def gen_one(prompt, aspect_ratio, model, api_key, timeout=120):
    """调用 MiniMax 文生图，返回图片 URL"""
    body = json.dumps({
        "model": model, "prompt": prompt, "aspect_ratio": aspect_ratio,
        "response_format": "url", "n": 1,
    }).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.load(r)
    br = d.get("base_resp", {})
    if br.get("status_code") != 0:
        raise RuntimeError(f"MiniMax 生图错误: {br}")
    urls = (d.get("data") or {}).get("image_urls") or []
    if not urls:
        raise RuntimeError(f"响应无图片: {str(d)[:200]}")
    return urls[0]


def download(url, path, timeout=90):
    with urllib.request.urlopen(url, timeout=timeout) as r, open(path, "wb") as f:
        f.write(r.read())
    normalize_jpeg(path)
    return os.path.getsize(path)


def normalize_jpeg(path):
    """归一化为真正的 JPEG（硅基 Kolors 等网关返回 PNG 字节）。

    不做这步会导致：① 文件扩展名 .jpg 但内容是 PNG（"扩展名撒谎"，
    严格解码器/QC 可能误判）② PNG 体积约为 JPEG 的 3~5 倍，11 镜会
    多占几十 MB 并拖慢剪映/ffmpeg 合成。
    真实 JPEG（百炼万相）嗅探后原样保留，零开销。
    """
    try:
        from PIL import Image
        with Image.open(path) as im:
            if im.format == "JPEG":
                return
            im = im.convert("RGB")
            im.save(path, "JPEG", quality=90, optimize=True)
    except Exception as e:
        print(f"  ⚠️  图片格式归一化失败（保留原始字节）: {e}",
              file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="分镜批量生图（MiniMax 文生图）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--model", default=None,
                    help="模型名；默认按 provider 取"
                         "（dashscope=wanx2.1-t2i-turbo / minimax=image-01）")
    ap.add_argument("--image-provider", default=None,
                    help="生图 provider：dashscope(百炼万相·性价比) / minimax")
    ap.add_argument("--aspect-ratio", help="覆盖分镜中的比例（默认取 aspect_ratio）")
    ap.add_argument("--style-preset", help="覆盖风格预设名")
    ap.add_argument("--sample-only", action="store_true", help="样图先行：仅第 1 镜")
    ap.add_argument("--update-storyboard", action="store_true",
                    help="回填 visual.source_ref.path 与 image_path")
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--shots", default=None,
                    help="增量重生成：只处理这些镜号（逗号分隔，如 3,5,7）")
    ap.add_argument("--only-missing", action="store_true",
                    help="增量重生成：跳过「图已存在且输入未变」的镜（按内容 hash 判断）")
    args = ap.parse_args()

    sb_path = os.path.expanduser(args.storyboard)
    sb = json.load(open(sb_path, encoding="utf-8"))

    # 契约校验（§16.4 R3）
    try:
        from storyboard_schema import validate, summarize
        issues = validate(sb)
        errs = [i for i in issues if i["level"] == "error"]
        if errs:
            for it in errs:
                print(f"❌ 契约 {it['path']}: {it['msg']}", file=sys.stderr)
            print(f"❌ 分镜不符合 §2.1 契约（{summarize(issues)}），已中止",
                  file=sys.stderr)
            sys.exit(1)
    except ImportError:
        pass

    shots = sb.get("shots") or []
    if not shots:
        print("❌ 分镜为空", file=sys.stderr); sys.exit(1)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from providers import (load_project_config, resolve_image_params,
                                resolve_image_provider, content_hash,
                                select_shots, fallback_chain, classify_call_failure,
                                IMAGE_PROVIDERS, record_cost)
    except ImportError as _e:
        print(f"❌ 缺少 providers.py: {_e}", file=sys.stderr)
        sys.exit(1)
    pcfg = load_project_config(sb.get("project_id"))
    prov_name, prov = resolve_image_provider(args.image_provider, sb, pcfg)
    # P1-c 降级链（test 档只允许降到 ¥0 通道）；链条目延后构建（要等 args.model 解析完）
    free_only = os.environ.get("VIDEO_PROFILE") == "test"
    chain_names = fallback_chain("image", prov_name, pcfg, free_only=free_only)
    # 仅远程 provider 需要 API key；本地 provider（占位图）无需任何密钥
    # P1-c：有降级链时缺 key 只警告不中止——链上各 fn 自带密钥读取，缺哪家的会在
    # 调用处以 config 失败被跳过，比在入口一死了之更不容易整条中断。
    api_key = None
    if prov.get("requires_key", True):
        api_key = load_api_key(args.api_key)
        if not api_key:
            if len(chain_names) > 1:
                print(f"⚠️  provider={prov_name} 的 API key 缺失，依赖降级链继续：{chain_names}",
                      file=sys.stderr)
            else:
                print(f"❌ provider={prov_name} 需要 API key（~/.dsh/secrets/*.env）",
                      file=sys.stderr)
                sys.exit(1)
    args.model, msrc, cfg_style = resolve_image_params(
        args.model, sb, pcfg, prov)
    # 链条目：主选用解析出的模型，降级家各用自家默认模型
    chain = [{"name": n,
              "fn": IMAGE_PROVIDERS[n]["fn"],
              "local": bool(IMAGE_PROVIDERS[n].get("local")),
              "model": args.model if n == prov_name else IMAGE_PROVIDERS[n].get("default_model")}
             for n in chain_names]
    if pcfg and not args.image_provider:
        print(f"📋 已加载项目配置: {sb.get('project_id')}")

    ar = args.aspect_ratio or sb.get("aspect_ratio") or "9:16"
    if ar not in VALID_AR:
        print(f"⚠️  比例 {ar} 不在常见集合，仍按原值请求", file=sys.stderr)

    preset_name = (args.style_preset or cfg_style
                   or (sb.get("style") or {}).get("preset") or "none")
    # v4.0：项目配置可扩展/覆盖风格预设（image.style_presets: {name: 前缀}），新账号新风格不改代码
    presets = dict(STYLE_PRESETS)
    custom = ((pcfg or {}).get("image") or {}).get("style_presets") or {}
    if isinstance(custom, dict) and custom:
        presets.update({str(k): str(v) for k, v in custom.items()})
    style_prefix = presets.get(preset_name, "")
    if preset_name not in presets:
        print(f"⚠️  未内置风格预设 {preset_name!r}，按无前缀处理"
              f"（已内置：{list(presets)}；可在项目配置 image.style_presets 扩展）", file=sys.stderr)

    out_dir = os.path.expanduser(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)

    targets = shots[:1] if args.sample_only else shots

    # ── 实拍镜（混剪 M2，D5）：¥0 本地成帧，绝不调任何生图 provider ──
    # 从 real_clip 素材提取代表帧写 shot_NNN.jpg，让 draft/封面/QC 等一切
    # 「认图」的下游零改动；帧=剪辑区间中点，人一眼能看到该镜实际画面。
    try:
        from real_clip import (real_clip_of, resolve_clip, probe_duration,
                               clip_span, extract_frame)
    except ImportError:
        real_clip_of = None
    if real_clip_of:
        keep = []
        for i, s in enumerate(targets, 1):
            rc = real_clip_of(s)
            if not rc:
                keep.append(s)
                continue
            sid = int(s.get("shot_id", i))
            out_path = os.path.join(out_dir, f"shot_{sid:03d}.jpg")
            media, why = resolve_clip(rc)
            native = probe_duration(media) if media else None
            if media and native:
                st, du = clip_span(rc, native)
                if extract_frame(media, st + du / 2, out_path):
                    vis = s.setdefault("visual", {})
                    vis["real_clip_frame"] = out_path
                    print(f"  🎞 镜{sid}: 实拍成帧 {os.path.basename(media)}"
                          f"（@{(st + du / 2):.1f}s，¥0，不进出图队列）")
                    continue
            print(f"  ⚠️ 镜{sid}: 实拍成帧失败（{why or '探针失败'}），"
                  f"该镜回退生图/占位路径", file=sys.stderr)
            keep.append(s)
        targets = keep

    # ── 增量重生成（生图占单条成本约 94%，这里最关键）──
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
            vis = s.get("visual") or {}
            p = os.path.join(out_dir, f"shot_{sid:03d}.jpg")
            bp = build_prompt(s, style_prefix)
            ch = content_hash(bp, ar, args.model, preset_name)
            ref_path = _source_ref(s).get("path") or vis.get("image_path")
            used_m = vis.get("model_used")
            if vis.get("reused"):
                # 刻意复用（eagle_reuse 已指定素材）→ 判定"已存在且未变"，不再生图。
                # 不能靠 source_hash 比对：复用侧哈希原始 prompt，本侧哈希
                # build_prompt（含风格前缀），**两者天然不等**。
                miss[sid] = (ch, ch, True)
            elif (used_m and used_m != args.model and os.path.exists(p)
                    and vis.get("source_hash") == content_hash(bp, ar, used_m, preset_name)):
                # P1-c：该镜由降级链的另一模型产出且输入未变 → 视为未变。
                # 不这样认账的话，"主选恢复了"就会把已成功的镜全量重烧（真金白银）。
                miss[sid] = (ch, ch, True)
            else:
                exists = os.path.exists(p)
                # 分镜引用的图已存在（在别的产物目录）→ 复制过来，**不要重新生图**
                # （否则换一个 out-dir 就整批重烧，白白花钱）
                if not exists and ref_path and os.path.exists(ref_path) \
                        and vis.get("source_hash") == ch:
                    os.makedirs(out_dir, exist_ok=True)
                    shutil.copy2(ref_path, p)
                    exists = True
                miss[sid] = (ch, vis.get("source_hash"), exists)

    todo, skipped = select_shots(targets, only=want, missing_hash=miss)

    print(f"🎨 provider={prov_name}（{prov['cost_note']}） 模型={args.model}（{msrc}·仅主选） 比例={ar} 风格={preset_name}")
    if len(chain) > 1:
        print(f"    🔗 降级链：{' → '.join(c['name'] + '(' + (c.get('model') or '?') + ')' for c in chain)}"
              '（各家各用自己的模型）'
              + ('·test 档仅 ¥0 通道' if free_only else ''))
    if args.sample_only:
        print("    （样图先行：仅第 1 镜）")
    print(f"    待处理 {len(todo)} 镜" +
          (f"，跳过 {skipped} 镜（未变化/未选中，省下额度）" if skipped else ""))

    tasks = []
    for i, shot in enumerate(todo, 1):
        prompt = build_prompt(shot, style_prefix)
        if not prompt:
            print(f"  ⚠️  镜{shot.get('shot_id', i)} 无 prompt，跳过")
            continue
        sid = shot.get("shot_id", i)
        out_path = os.path.join(out_dir, f"shot_{sid:03d}.jpg")
        tasks.append((sid, prompt, out_path))

    def work(t):
        sid, prompt, out_path = t
        for idx, entry in enumerate(chain):
            try:
                if entry["local"]:
                    # 本地 provider（占位图）：fn 直接写文件，不发 HTTP/不下载
                    path = entry["fn"](prompt, aspect_ratio=ar, model=entry["model"],
                                       out_path=out_path, shot_id=sid)
                    return (sid, True, path, os.path.getsize(path), prompt, None,
                            entry["name"], entry["model"])
                # 远程 provider（dashscope=万相异步 / minimax=同步）：返回 URL 再下载
                url = entry["fn"](prompt, aspect_ratio=ar, model=entry["model"],
                                  api_key=api_key)
                size = download(url, out_path)
                return (sid, True, out_path, size, prompt, None,
                        entry["name"], entry["model"])
            except Exception as e:
                cls = classify_call_failure(e)
                if cls == "prompt" or idx == len(chain) - 1:
                    return (sid, False, None, 0, prompt, str(e),
                            entry["name"], entry["model"])
                # 换家留痕：零成本流水行（异步任务"已提交未取回"的隐性消费要靠它对账）
                try:
                    record_cost("image", entry["name"], entry["model"], 0,
                                note=f"degrade-fail[{cls}]: {str(e)[:80]}")
                except Exception:
                    pass
                print(f"  ⚠️  镜{sid}: {entry['name']} 失败({cls})，降级 → {chain[idx + 1]['name']}",
                      file=sys.stderr)
        return (sid, False, None, 0, prompt, "链耗尽（不应到达）", prov_name, args.model)

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        for r in ex.map(work, tasks):
            results.append(r)
            sid, ok, path, size, prompt, err, used_prov, used_model = r
            if ok:
                via = "" if used_prov == prov_name else f"（降级链·经由 {used_prov}）"
                print(f"  ✅ 镜{sid}: {os.path.basename(path)}  {size//1024}KB{via}")
                print(f"      prompt: {prompt[:60]}{'…' if len(prompt) > 60 else ''}")
            else:
                print(f"  ❌ 镜{sid} 失败（最后尝试 {used_prov}）: {err}", file=sys.stderr)

    ok_results = [r for r in results if r[1]]
    # 回填分镜
    if args.update_storyboard and ok_results:
        by_id = {r[0]: r[2] for r in ok_results}
        pr_by_id = {r[0]: r[4] for r in ok_results}
        used_by_id = {r[0]: (r[6], r[7]) for r in ok_results}  # (实际 provider, 实际 model)
        local_names = {c["name"] for c in chain if c["local"]}
        for i, shot in enumerate(shots, 1):
            sid = shot.get("shot_id", i)
            if sid in by_id:
                vis = shot.setdefault("visual", {})
                ref = vis.get("source_ref")
                if not isinstance(ref, dict):
                    ref = {}
                ref["path"] = by_id[sid]
                used_prov, used_model = used_by_id.get(sid, (prov_name, args.model))
                # 占位图显式打标：QC 在 prod 档据此阻断，UI 据此显示"占位/¥0"
                if used_prov in local_names:
                    ref["provider"] = used_prov
                    ref["placeholder"] = True
                vis["source_ref"] = ref
                vis["image_path"] = by_id[sid]
                if used_prov in local_names:
                    vis["placeholder"] = True
                # P1-c：记录实际产出者（主选或降级家），--only-missing 据此
                # 认账降级产物，不会因为"主选恢复了"就把已成功的镜再烧一遍
                vis["provider_used"] = used_prov
                vis["model_used"] = used_model
                # 记录输入指纹，供下次 --only-missing 安全跳过（用实际模型算）
                vis["source_hash"] = content_hash(
                    pr_by_id.get(sid), ar, used_model, preset_name)
        json.dump(sb, open(sb_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"📝 已回填分镜: {sb_path}")

    print(f"\n成功 {len(ok_results)}/{len(tasks)}")
    print(json.dumps({"success": len(ok_results), "total": len(tasks),
                      "aspect_ratio": ar, "style_preset": preset_name,
                      "sample_only": args.sample_only,
                      "files": [r[2] for r in ok_results]}, ensure_ascii=False))

    # v4.2 健壮性：全失败必须**显式失败**（此前 exit 0 → 管线继续用缺图产出"看似成功"的视频，
    # 实测：MiniMax 余额耗尽导致 13/13 失败，却一路跑到成片，问题被静默吞掉）。
    if tasks and not ok_results:
        print(f"❌ 全部 {len(tasks)} 镜生图失败 —— 中止（整链烧穿，检查 provider/额度："
              f"链={'>'.join(c['name'] for c in chain)}）", file=sys.stderr)
        sys.exit(1)
    if tasks and len(ok_results) < len(tasks):
        print(f"⚠️  部分失败: 成功 {len(ok_results)}/{len(tasks)}（管线将继续，缺图镜会以占位处理）",
              file=sys.stderr)


if __name__ == "__main__":
    main()
