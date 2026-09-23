#!/usr/bin/env python3
"""
素材复用：先查 Eagle，命中就复用（不生图，不花钱）——审计报告 P0-2 的价值闭环。

入库（eagle_ingest.py）只是"存"。**真正的省钱在"用"**：
    先查 Eagle → 命中就复用（¥0）→ 没命中才生图 → 生完入库

匹配方式（为什么不用向量/AI）：
  - 库内规模小（每项目几十~几百条），`item/list` 一次能拿全
  - annotation 里已存**完整 prompt + 台词**，信息量足够
  - 用**中文字符 bigram Jaccard 相似度**做打分：零依赖、零成本、可解释
  - 阈值可调（默认 0.50），并可要求 tags 必须同项目/同风格

用法：
  eagle_reuse.py --storyboard sb.json [--threshold 0.50] [--dry-run] [--update-storyboard]
  # 命中后会把 source_ref + source_hash 写好，使后续 --only-missing 跳过该镜（不生图）
"""
import argparse
import json
import os
import re
import shutil
import sys

EW_SRC = os.path.expanduser("~/Projects/tools/eagle-watcher/src")

CJK = re.compile(r"[\u4e00-\u9fff]")


def bigrams(s):
    s = re.sub(r"\s+", "", str(s or ""))
    if len(s) < 2:
        return {s} if s else set()
    return {s[i:i + 2] for i in range(len(s) - 1)}


def similarity(a, b):
    A, B = bigrams(a), bigrams(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def get_api():
    if os.path.isdir(EW_SRC):
        sys.path.insert(0, EW_SRC)
    try:
        from eagle_watcher.eagle_api import EagleAPI
    except ImportError as e:
        print(f"❌ 无法复用 eagle-watcher 客户端（{e}）", file=sys.stderr)
        sys.exit(1)
    tok = ""
    cfgp = os.path.expanduser("~/.eagle-watcher/config.yaml")
    if os.path.exists(cfgp):
        m = re.search(r"^\s*token:\s*[\"']?([^\s\"']+)", open(cfgp).read(), re.M)
        if m:
            tok = m.group(1)
    if not tok:
        print("❌ 未找到 Eagle token", file=sys.stderr)
        sys.exit(1)
    return EagleAPI(token=tok)


def main():
    ap = argparse.ArgumentParser(description="素材复用：先查 Eagle，命中则不生图")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--threshold", type=float, default=0.50,
                    help="相似度阈值（0~1），越高越严格；默认 0.50"
                         "（实测：近似画面 0.74~1.00，不相关 0.16——误复用比多生一张图代价更大）")
    ap.add_argument("--out-dir",
                    help="产物目录；命中后会把素材复制到 <out-dir>/shots/ 下，"
                         "使产物自包含，且能让后续 --only-missing 正确跳过")
    ap.add_argument("--folder", help="覆盖检索文件夹（默认取项目配置 eagle.folder）")
    ap.add_argument("--dry-run", action="store_true", help="只预览不写回")
    ap.add_argument("--update-storyboard", action="store_true",
                    help="把命中的 source_ref/source_hash 写回分镜")
    args = ap.parse_args()

    sb_path = os.path.expanduser(args.storyboard)
    sb = json.load(open(sb_path, encoding="utf-8"))
    project_id = sb.get("project_id") or ""

    pcfg = {}
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from providers import load_project_config, content_hash
        pcfg = load_project_config(project_id)
    except Exception:
        content_hash = None
    ecfg = pcfg.get("eagle") or {}
    folder_name = args.folder or ecfg.get("folder") or (pcfg.get("account") or project_id)
    ar = sb.get("aspect_ratio") or (pcfg.get("video") or {}).get("aspect_ratio") or "9:16"
    model = (pcfg.get("image") or {}).get("model") or "wanx2.1-t2i-turbo"
    preset = (pcfg.get("image") or {}).get("style_preset") or (sb.get("style") or {}).get("preset") or "none"

    api = get_api()
    folder_id = api.get_or_create_folder(folder_name)
    items = api.list_items(folders=folder_id)
    print(f"🔎 检索文件夹「{folder_name}」共 {len(items)} 条素材，阈值 {args.threshold}")

    reused, miss = 0, 0
    try:
        from real_clip import real_clip_of as _rc_of
    except ImportError:
        _rc_of = lambda _s: None
    for i, s in enumerate(sb.get("shots") or [], 1):
        sid = s.get("shot_id", i)
        vis = s.setdefault("visual", {})
        if _rc_of(s):
            # 实拍镜（混剪 M2）：主画面=用户素材，检索复用不适用，绝不可覆盖其 source_ref
            print(f"  🎞 镜{sid}: 实拍镜，跳过素材检索")
            continue
        ref = vis.get("source_ref")
        have = isinstance(ref, dict) and (ref.get("path") and os.path.exists(ref["path"]))
        if have:
            print(f"  ⏭  镜{sid}: 已有素材，跳过检索")
            continue
        prompt = (vis.get("prompt") or "").strip()
        if not prompt:
            miss += 1
            continue

        best, best_item = 0.0, None
        for it in items:
            ann = str(it.get("annotation") or "")
            # 占位图排除（v5.3.1）：占位图是 ¥0 开发档产物，绝不能被复用回真实视频。
            # 标记由 eagle_ingest --include-placeholders 写入（[placeholder] 头 / placeholder 标签）；
            # 双判据兼容手工打标与历史数据。
            if "[placeholder]" in ann or "placeholder" in (it.get("tags") or []):
                continue
            # 同项目标签优先；annotation 的 prompt 部分在第一行（占位标注之后取第一行会失真，
            # 但占位条目上面已 continue，这里维持原逻辑）
            cand = ann.split("\n")[0] if ann else (it.get("name") or "")
            sc = similarity(prompt, cand)
            if sc > best:
                best, best_item = sc, it

        if best_item is None or best < args.threshold:
            print(f"  ❌ 镜{sid}: 未命中（最高 {best:.2f}）→ 需生图")
            miss += 1
            continue

        item_id = best_item.get("id")
        path = api.get_item_file_path(item_id, best_item.get("name") or "",
                                      best_item.get("ext") or "jpg")
        if not path or not os.path.exists(path):
            print(f"  ⚠️  镜{sid}: 命中但取不到文件（{path}）→ 仍需生图")
            miss += 1
            continue

        # 复制到产物目录（关键：否则 --only-missing 因"产物目录无此文件"而重新生图，复用白做）
        final = path
        if args.out_dir:
            shots_dir = os.path.join(os.path.expanduser(args.out_dir), "shots")
            os.makedirs(shots_dir, exist_ok=True)
            ext = best_item.get("ext") or os.path.splitext(path)[1].lstrip(".") or "jpg"
            final = os.path.join(shots_dir, f"shot_{sid:03d}.{ext}")
            if os.path.abspath(final) != os.path.abspath(path):
                shutil.copy2(path, final)

        print(f"  ♻️  镜{sid}: 复用 {best_item.get('name')}（相似度 {best:.2f}）→ 省 1 张图")
        if args.dry_run:
            reused += 1
            continue

        vis["source_ref"] = {"eagle_id": item_id, "path": final}
        vis["image_path"] = final
        vis["reused"] = True
        vis["reuse_score"] = round(best, 3)
        # 关键：写 source_hash，让后续 --only-missing 认为"输入未变"从而跳过生图
        if content_hash:
            vis["source_hash"] = content_hash(prompt, ar, model, preset)
        reused += 1

    if args.update_storyboard and reused and not args.dry_run:
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
        print(f"📝 已回写复用到分镜: {sb_path}")

    print(f"\n素材复用: 复用 {reused} / 仍需生图 {miss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
