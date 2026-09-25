#!/usr/bin/env python3
"""
动态 B-roll（AI 生视频）——把静帧变成会动的片段。**默认关闭**。

为什么默认关闭（审计报告：可选而非写死）：
  视频比生图贵一个数量级（每 5s 片段约 ¥0.5~3，生图仅 ¥0.1~0.16）。
  口播内容用「静帧 + KenBurns」已足够且极便宜，所以 B-roll 是**可选增强**。

三种模式（项目配置 `video.broll.mode`）：
  none —— 不动（默认），全部用静帧 + KenBurns
  key  —— 只给关键镜生成（钩子/转折/结尾，配置 `video.broll.key_shots`），其余静帧
  all  —— 每镜都生成（最贵）

⚠️ 现状：百炼视频模型未开通（AccessDenied.Unpurchased）、MiniMax 余额耗尽。
   本脚本会**明确提示并优雅退出（退出码 0）**，管线回退到静帧，不会静默失败。

图生视频（i2v）需要**公网可访问的图片 URL**。若配置 `video.broll.upload`
（形如 `my-server:/var/www/yiwenai` + `base_url`），会自动上传后清理；
否则退化为**文生视频**（不用图，画面一致性会差一些）。

用法：
  generate_broll.py --storyboard sb.json --out-dir <产物> [--mode key] [--shots 1,7]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def upload_public(path, upload_spec, base_url):
    """把本地图片临时传到公网（图生视频需要公网 URL），返回 (URL, 清理函数)"""
    if not upload_spec or not base_url:
        return None, lambda: None
    host, _, dest = upload_spec.partition(":")
    name = "broll_" + os.path.basename(path)
    subprocess.run(["scp", "-q", "-o", "ConnectTimeout=15", path,
                    f"{host}:{dest}/{name}"], check=True, capture_output=True)
    subprocess.run(["ssh", "-o", "ConnectTimeout=10", host,
                    f"chmod 644 {dest}/{name}"], capture_output=True)
    url = f"{base_url.rstrip('/')}/{name}"

    def cleanup():
        subprocess.run(["ssh", "-o", "ConnectTimeout=10", host,
                        f"rm -f {dest}/{name}"], capture_output=True)
    return url, cleanup


def main():
    ap = argparse.ArgumentParser(description="动态 B-roll（AI 生视频，默认关闭）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=["none", "key", "all"], help="覆盖配置中的模式")
    ap.add_argument("--shots", help="只处理这些镜号")
    ap.add_argument("--update-storyboard", action="store_true")
    args = ap.parse_args()

    sb_path = os.path.expanduser(args.storyboard)
    sb = json.load(open(sb_path, encoding="utf-8"))
    out = os.path.expanduser(args.out_dir)
    project_id = sb.get("project_id") or ""

    pcfg = {}
    try:
        from providers import load_project_config, resolve_video_provider
        pcfg = load_project_config(project_id)
    except Exception as e:
        print(f"❌ 缺少 providers: {e}", file=sys.stderr)
        sys.exit(1)

    vcfg = (pcfg.get("video") or {})
    bcfg = vcfg.get("broll") or {}
    mode = args.mode or bcfg.get("mode") or "none"
    if mode == "none":
        print("⏭  B-roll 模式 = none（默认）：全部使用静帧 + KenBurns，不产生视频费用")
        sys.exit(0)

    prov_name, prov = resolve_video_provider(bcfg.get("provider"), pcfg)
    model = bcfg.get("model") or prov["default_model"]
    print(f"🎬 B-roll provider={prov_name} 模型={model} 模式={mode}")
    print(f"   {prov['cost_note']}")

    # 选镜
    want = None
    if args.shots:
        want = {int(x) for x in args.shots.replace("，", ",").split(",") if x.strip()}
    elif mode == "key":
        want = set(bcfg.get("key_shots") or [1])
    shots = []
    for i, s in enumerate(sb.get("shots") or [], 1):
        sid = s.get("shot_id", i)
        if want is not None and sid not in want:
            continue
        vis = s.get("visual") or {}
        if vis.get("video_path") and os.path.exists(vis["video_path"]):
            continue                       # 幂等
        shots.append(s)
    if not shots:
        print("  ⏭  无待生成 B-roll 的镜")
        sys.exit(0)

    broll_dir = os.path.join(out, "broll")
    os.makedirs(broll_dir, exist_ok=True)
    ok, failed = 0, 0
    for i, s in enumerate(shots, 1):
        sid = s.get("shot_id", i)
        vis = s.get("visual") or {}
        img = vis.get("image_path") or (vis.get("source_ref") or {}).get("path")
        prompt = (vis.get("prompt") or "").strip()
        if not prompt:
            continue
        url, cleanup = (None, lambda: None)
        if img and os.path.exists(img):
            try:
                url, cleanup = upload_public(img, bcfg.get("upload"), bcfg.get("base_url"))
            except Exception as e:
                print(f"  ⚠️降级  镜{sid}: 上传失败，退化为文生视频（{type(e).__name__}）")
        try:
            vurl = prov["fn"](prompt, image_url=url, model=model)
            dst = os.path.join(broll_dir, f"shot_{sid:03d}.mp4")
            with urllib.request.urlopen(vurl, timeout=300) as r, open(dst, "wb") as f:
                f.write(r.read())
            vis["video_path"] = dst
            print(f"  ✅ 镜{sid}: {os.path.getsize(dst) // 1024}KB → {dst}")
            ok += 1
        except Exception as e:
            msg = str(e)
            if "Unpurchased" in msg or "未开通" in msg:
                print(f"  ⏭  镜{sid}: {msg}")
                print("     → 回退到静帧 + KenBurns（需在百炼开通视频模型才能用 B-roll）")
                failed += 1
                break                       # 未开通就没必要继续试
            print(f"  ❌ 镜{sid}: {type(e).__name__}: {msg[:120]}")
            failed += 1
        finally:
            try:
                cleanup()
            except Exception:
                pass

    if args.update_storyboard and ok:
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
        print(f"📝 已回填 video_path: {sb_path}")

    print(f"\nB-roll: 成功 {ok} / 失败或跳过 {failed}")
    # 未开通/余额不足不应让整条管线失败 → 始终返回 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
