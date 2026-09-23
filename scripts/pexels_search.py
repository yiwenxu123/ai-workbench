#!/usr/bin/env python3
"""
Pexels 免费素材兜底（v4.0 P2-4）——三级素材路由的第二级。

背景（§12.4 三级路由）：Eagle 复用（reuse，¥0）→ **Pexels/Pixabay 免费真实素材**（本脚本）
→ AI 生图（images，花钱）。reuse 未命中时先找免费真实素材，能省一张是一张。

定位与诚实边界：
  - 需要 PEXELS_API_KEY（免费申请：pexels.com/api，200 次/小时）。
    未配置时本阶段**优雅跳过**（exit 0），管线照常走 AI 生图。
  - Pexels 对英文关键词匹配最好：分镜 `visual.pexels_query`（英文）> `visual.keywords` >
    原始 prompt（中文大概率搜不到）。**建议在 storyboard 闸里顺手给重点镜填英文关键词。**
  - 命中后下载图片到 shots/ 并回填 source_ref + source_hash（与 generate_images 同一指纹，
    保证 `--only-missing` 增量逻辑一致，不会重复生成）。

用法：
  pexels_search.py --storyboard sb.json --output-dir shots/ [--update-storyboard]
  # run_pipeline 已内置 pexels 阶段（reuse → pexels → images），默认自动跑
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

API_URL = "https://api.pexels.com/v1/search"


def get_api_key():
    return (os.environ.get("PEXELS_API_KEY")
            or os.environ.get("PEXELS_API_TOKEN") or "").strip()


def search_photos(key, query, per_page=3, orientation="portrait"):
    q = urllib.parse.urlencode({"query": query, "per_page": per_page,
                                "orientation": orientation})
    req = urllib.request.Request(f"{API_URL}?{q}",
                                 headers={"Authorization": key})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data.get("photos") or []


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "video-workbench/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())
    return os.path.getsize(dest)


def main():
    ap = argparse.ArgumentParser(description="Pexels 免费素材兜底（reuse 未命中时）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--output-dir", required=True, help="shots 目录（与生图共用）")
    ap.add_argument("--orientation", default="portrait",
                    help="portrait（竖屏，默认）/ landscape / square")
    ap.add_argument("--update-storyboard", action="store_true")
    args = ap.parse_args()

    key = get_api_key()
    if not key:
        print("⏭  未配置 PEXELS_API_KEY，跳过 Pexels 兜底（免费申请: pexels.com/api；"
              "配置: echo 'export PEXELS_API_KEY=...' >> ~/.dsh/secrets/dashscope.env）")
        return 0

    sb_path = os.path.abspath(os.path.expanduser(args.storyboard))
    sb = json.load(open(sb_path, encoding="utf-8"))
    out_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    os.makedirs(out_dir, exist_ok=True)

    # 与 generate_images 同源的增量指纹参数
    try:
        from providers import load_project_config, content_hash
        pcfg = load_project_config(sb.get("project_id")) or {}
    except Exception:
        pcfg, content_hash = {}, None
    icfg = (pcfg.get("image") or {})
    model = icfg.get("model") or "wanx-v1"
    preset_name = (sb.get("style") or {}).get("preset") or "none"

    hits, misses = 0, 0
    try:
        from real_clip import real_clip_of as _rc_of
    except ImportError:
        _rc_of = lambda _s: None
    for i, s in enumerate(sb.get("shots") or [], 1):
        sid = s.get("shot_id", i)
        vis = s.get("visual") or {}
        if _rc_of(s):
            print(f"  🎞 镜{sid}: 实拍镜，跳过 Pexels 兜底")
            continue
        # 只处理没有产物的镜（reuse 未命中且未生成过）
        if (vis.get("source_ref") or {}).get("path") or vis.get("image_path"):
            continue
        prompt = (vis.get("prompt") or "").strip()
        if not prompt:
            continue
        query = (vis.get("pexels_query") or vis.get("keywords")
                 or vis.get("broll_query") or prompt)
        try:
            photos = search_photos(key, query, orientation=args.orientation)
        except Exception as e:
            print(f"  ⚠️  镜{sid}: Pexels 查询失败: {str(e)[:100]}")
            misses += 1
            continue
        if not photos:
            print(f"  ⏭  镜{sid}: 无结果（query={query[:40]}…）→ 留给 AI 生图")
            misses += 1
            continue
        photo = photos[0]
        src = (photo.get("src") or {}).get("large") or (photo.get("src") or {}).get("original")
        if not src:
            misses += 1
            continue
        dest = os.path.join(out_dir, f"shot_{sid:03d}.jpg")
        try:
            size = download(src, dest)
        except Exception as e:
            print(f"  ⚠️  镜{sid}: 下载失败: {str(e)[:100]}")
            misses += 1
            continue
        vis["type"] = vis.get("type") or "broll"
        vis["source_ref"] = {"path": dest, "pexels_id": photo.get("id"),
                             "pexels_url": photo.get("url") or ""}
        vis["image_path"] = dest
        if content_hash:
            # 指纹按"同一 prompt 输入"计算 → images 阶段 --only-missing 会正确跳过
            from generate_images import build_prompt, STYLE_PRESETS
            style_prefix = STYLE_PRESETS.get(preset_name, "")
            vis["source_hash"] = content_hash(
                build_prompt(s, style_prefix),
                sb.get("aspect_ratio") or "9:16", model, preset_name)
        hits += 1
        print(f"  ✅ 镜{sid}: Pexels 命中 id={photo.get('id')} ({size // 1024}KB) "
              f"→ {os.path.basename(dest)}（¥0）")

    if args.update_storyboard and hits:
        json.dump(sb, open(sb_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"📝 已回填分镜: {sb_path}")

    print(f"\nPexels 兜底: 命中 {hits} / 未命中 {misses}"
          + ("" if hits + misses else "（全部镜已有素材，无需兜底）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
