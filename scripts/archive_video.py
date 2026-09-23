#!/usr/bin/env python3
"""
归档搬文件脚本（P2-⑧）：把「归档」从纯状态位扩展为一次可选的物理收拢。

背景：视频任务的工作产物散落在 ~/Movies/AI视频素材/<内容线>/<日期-slug>/ 下
（粗剪 mp4、封面、字幕、分镜、成本、以及 shots/ 逐镜图、voiceover/ 逐镜配音等中间产物）。
Web/面板点「归档」只是把 status 改成 archived（软归档），磁盘上这些目录越堆越乱。
本脚本作为**批处理工具**：把已归档任务的整个 out_dir 移到归档根目录，
清理工作区，且**可一键还原**。

安全设计（这是会动真实素材文件的操作，务必谨慎）：
  - 默认 **DRY-RUN**：只打印「将移动什么、去哪、多大、有何风险」，绝不移动任何文件。
    加 --apply 才真正搬。
  - 永远 **移动而非删除**：整个 out_dir 用 shutil.move 搬到 <归档根>/<内容线>/<目录名>，
    并在 <归档根>/.archive_index.json 记一条 src→dst；--restore 按索引原路搬回。
  - **跳过测试/系统临时目录**（/tmp、/private/var/folders、/var/folders）：存量记录里
    有 out_dir=/tmp/... 这类 smoke 残留，绝不能当真素材搬。
  - **目标已存在即拒绝**（除非 --force），避免覆盖同名归档。
  - 不碰 out_dir 之外的东西：人工终剪成片 final_path 常在 ~/Movies 根而非 out_dir 里，
    本脚本只提示它的存在，不移动它。

用法：
  python3 archive_video.py                     # dry-run：扫 status=archived 的任务，打印计划
  python3 archive_video.py --status final_ready # dry-run：预览别的状态桶（只读，不搬）
  python3 archive_video.py --dir <out_dir>      # dry-run：预览/处理一个显式目录
  python3 archive_video.py --apply              # 真正搬移（写索引）
  python3 archive_video.py --restore            # 按索引把搬走的全部还原回原路径
  python3 archive_video.py --list-index         # 查看归档索引
"""
import json
import os
import shutil
import sys
import time
import urllib.request

BASE = os.environ.get("CONTENT_OPS_API_BASE", "http://localhost:3002/api/v1").rstrip("/")

APPLY = "--apply" in sys.argv
RESTORE = "--restore" in sys.argv
LIST_INDEX = "--list-index" in sys.argv
FORCE = "--force" in sys.argv


def _flag(name):
    """取 --key value 形式的参数值。"""
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


STATUS_CSV = _flag("--status") or "archived"
MANUAL_DIR = _flag("--dir")
DEFAULT_ARCHIVE_ROOT = os.environ.get(
    "VIDEO_ARCHIVE_ROOT",
    os.path.expanduser("~/Movies/AI视频素材/_archive"),
)
ARCHIVE_ROOT = os.path.abspath(os.path.expanduser(_flag("--archive-root") or DEFAULT_ARCHIVE_ROOT))

# 归档根自身不能被视为「待归档素材」，否则会把归档目录套进归档目录。
# 这些前缀下的 out_dir 一律视为非真实工作产物，跳过。
TEMP_PREFIXES = ("/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/")

# 内容分类（仅用于预览报告，帮助人判断「这里面都是什么、动它安不安全」）。
# 移动时整目录一起搬，保证 --restore 能原样还原，不做外科手术式拆分。
DELIVERABLE_NAMES = {
    "storyboard.mp4", "cover.jpg", "cover.png", "cover.json", "cover_titles.json",
    "subtitles.srt", "script.md", "storyboard.json", "cost.json", "compliance.json",
    "qc_report.json", "publish_bundle", ".cost.jsonl",
}
INTERMEDIATE_NAMES = {"shots", "voiceover", "voice_all.mp3", "images", "audio"}


def human(n):
    for unit in ("B", "K", "M", "G"):
        if n < 1024 or unit == "G":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}G"


def dir_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def fetch_videos():
    try:
        with urllib.request.urlopen(f"{BASE}/videos?limit=500", timeout=10) as f:
            return (json.load(f) or {}).get("data") or []
    except Exception as e:
        print(f"⚠️  读取任务列表失败（{type(e).__name__}: {e}）——"
              f"可改用 --dir <out_dir> 显式处理单个目录。", file=sys.stderr)
        return None


def index_path():
    return os.path.join(ARCHIVE_ROOT, ".archive_index.json")


def load_index():
    try:
        with open(index_path(), encoding="utf-8") as f:
            return json.load(f) or {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_index(idx):
    os.makedirs(ARCHIVE_ROOT, exist_ok=True)
    tmp = index_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)
    os.replace(tmp, index_path())


def classify(out_dir):
    """把 out_dir 顶层内容分成 交付/中间/其它，返回 (buckets, total_bytes)。"""
    buckets = {"deliverable": [], "intermediate": [], "other": []}
    total = 0
    for name in sorted(os.listdir(out_dir)):
        p = os.path.join(out_dir, name)
        size = dir_size(p) if os.path.isdir(p) else (os.path.getsize(p) if os.path.isfile(p) else 0)
        total += size
        if name in DELIVERABLE_NAMES:
            kind = "deliverable"
        elif name in INTERMEDIATE_NAMES:
            kind = "intermediate"
        elif name in ("draft", "drafts", "review"):
            kind = "intermediate"
        else:
            kind = "other"
        buckets[kind].append((name, size, os.path.isdir(p)))
    return buckets, total


def target_for(out_dir):
    """归档目标：<归档根>/<内容线>/<目录名>。内容线 = out_dir 的父目录名。"""
    line = os.path.basename(os.path.dirname(out_dir)) or "misc"
    return os.path.join(ARCHIVE_ROOT, line, os.path.basename(out_dir))


def is_archivable(out_dir):
    """返回 (ok, reason)。跳过不存在、非目录、临时目录、以及已在归档根里的。"""
    if not out_dir:
        return False, "out_dir 为空"
    d = out_dir.rstrip("/") + "/"
    if any(d.startswith(p) or out_dir.startswith(p.rstrip("/")) for p in TEMP_PREFIXES):
        return False, "临时/测试目录（smoke 残留），不动"
    if not os.path.isdir(out_dir):
        return False, "目录不存在"
    if os.path.abspath(out_dir).startswith(ARCHIVE_ROOT + os.sep):
        return False, "已在归档根目录内"
    return True, ""


def preview(out_dir, video=None):
    """打印一条任务的归档计划（只读）。"""
    ok, reason = is_archivable(out_dir)
    tag = (video or {}).get("video_id") or (video or {}).get("id") or os.path.basename(out_dir)
    if not ok:
        print(f"  ⏭️  跳过 {tag}: {reason}  ({out_dir})")
        return None
    size = dir_size(out_dir)
    buckets, _ = classify(out_dir)
    dst = target_for(out_dir)
    verb = "移动" if APPLY else "将移动"
    print(f"  {'📦' if APPLY else '🔍'} {tag}  ({human(size)})")
    print(f"      源:   {out_dir}")
    print(f"      目标: {dst}")
    if os.path.exists(dst) and not FORCE:
        print(f"      ⚠️  目标已存在——拒绝覆盖（--force 强制）")
        return None
    # 分类摘要
    for kind, label in (("deliverable", "成片/交付"), ("intermediate", "中间产物"), ("other", "其它")):
        items = buckets[kind]
        if not items:
            continue
        s = sum(x[1] for x in items)
        print(f"      {label}: {len(items)} 项 / {human(s)}  ← {', '.join(x[0] for x in items[:6])}"
              + (" …" if len(items) > 6 else ""))
    if buckets["intermediate"]:
        print("      ℹ️  含逐镜图/配音等中间产物：可能已被 Eagle 收录或被重跑复用；"
              "整目录搬走 + --restore 可原样还原，不会丢。")
    if video:
        fp = str(video.get("final_path") or "").strip()
        if fp and not fp.startswith(out_dir.rstrip("/") + os.sep):
            print(f"      ℹ️  人工成片在 out_dir 之外（本脚本不碰）: {fp}")
    return dst


def apply_one(out_dir, dst, video):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(out_dir, dst)
    idx = load_index()
    idx[os.path.abspath(out_dir)] = {
        "dst": dst,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "video_id": (video or {}).get("video_id") or "",
        "id": (video or {}).get("id") or "",
    }
    save_index(idx)
    print(f"      ✅ 已移动到 {dst}")


def do_restore():
    idx = load_index()
    if not idx:
        print("归档索引为空，没有可还原的条目。")
        return 0
    print(f"=== {'还原' if APPLY else 'DRY-RUN 还原预览'}（共 {len(idx)} 条）===")
    moved = 0
    remaining = dict(idx)
    for src, meta in idx.items():
        dst = meta.get("dst") or ""
        if not os.path.isdir(dst):
            print(f"  ⏭️  {src}: 归档位置不存在，跳过（可能已手动移走）")
            continue
        if os.path.exists(src) and not FORCE:
            print(f"  ⚠️  原路径已存在，拒绝覆盖（--force 强制）: {src}")
            continue
        print(f"  {'↩️' if APPLY else '🔍'} {dst}  →  {src}")
        if APPLY:
            os.makedirs(os.path.dirname(src), exist_ok=True)
            shutil.move(dst, src)
            remaining.pop(src, None)
            print(f"      ✅ 已还原")
        moved += 1
    if APPLY and moved:
        save_index(remaining)
        print(f"\n已还原 {moved} 条，索引剩 {len(remaining)} 条。")
    elif not APPLY:
        print(f"\ndry-run 结束：将还原 {moved} 条。加 --apply 执行。")
    return moved


def main():
    print(f"归档根: {ARCHIVE_ROOT}")
    if LIST_INDEX:
        idx = load_index()
        if not idx:
            print("（索引为空）")
            return
        print(json.dumps(idx, ensure_ascii=False, indent=2))
        return

    if RESTORE:
        sys.exit(0 if do_restore() >= 0 else 1)

    # 收集待处理：--dir 显式模式 优先，否则按 status 扫 API。
    jobs = []  # (out_dir, video|None)
    if MANUAL_DIR:
        jobs.append((os.path.abspath(os.path.expanduser(MANUAL_DIR)), None))
    else:
        wanted = {s.strip() for s in STATUS_CSV.split(",") if s.strip()}
        vids = fetch_videos()
        if vids is None:
            sys.exit(2)
        for v in vids:
            if str(v.get("status")) in wanted and v.get("out_dir"):
                jobs.append((v["out_dir"], v))

    mode = "APPLY（真实搬移）" if APPLY else "DRY-RUN（只预览，不移动任何文件）"
    print(f"模式: {mode}")
    if not jobs:
        print(f"没有匹配的任务（status ∈ {sorted(set(STATUS_CSV.split(',')))}）。")
        print("提示：--dir <out_dir> 显式处理某目录；--status <csv> 改筛选桶。")
        return

    moved = 0
    for out_dir, video in jobs:
        dst = preview(out_dir, video)
        if dst and APPLY:
            apply_one(out_dir, dst, video)
            moved += 1

    if APPLY:
        print(f"\n完成：移动 {moved} 个目录到归档根。--restore 可原路还原。")
    else:
        n = sum(1 for od, v in jobs if is_archivable(od)[0])
        print(f"\ndry-run 结束：可归档 {n} 个目录。确认无误后加 --apply 执行。")


if __name__ == "__main__":
    main()
