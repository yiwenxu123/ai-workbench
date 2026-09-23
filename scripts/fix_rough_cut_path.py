#!/usr/bin/env python3
"""
一次性数据修复（P0-S2）：把存量任务里被管线误写进 final_path 的粗剪路径挪到
rough_cut_path，并清空 final_path——此后 final_path 只由用户「终剪完成」动作登记。

判据（全部满足才动）：
  - status == draft_ready（final_ready/published 的 final_path 视为真成片，绝不碰）
  - final_path 非空，且基名是粗剪产物约定（{video_id}.mp4 / storyboard.mp4）

用法：
  python3 fix_rough_cut_path.py            # dry-run，只打印将要改什么
  python3 fix_rough_cut_path.py --apply    # 真正 PATCH
"""
import json
import os
import sys
import urllib.request

BASE = os.environ.get("CONTENT_OPS_API_BASE", "http://localhost:3002/api/v1").rstrip("/")
APPLY = "--apply" in sys.argv


def req(method, url, body=None):
    r = urllib.request.Request(
        url, method=method,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None,
        headers={"Content-Type": "application/json"})
    tok = os.environ.get("VIDEO_CALLBACK_TOKEN")
    if tok:
        r.add_header("x-callback-token", tok)
    with urllib.request.urlopen(r, timeout=10) as f:
        return json.load(f)


def looks_like_rough_cut(v):
    fp = str(v.get("final_path") or "").strip()
    if not fp:
        return None
    # 基名白名单即判据：storyboard.mp4 / {video_id}.mp4 都是管线粗剪的固定产物名。
    # 不用 out_dir 前缀做硬条件——存量记录里 out_dir 本身可能是测试残留（/tmp/...）。
    name = os.path.basename(fp)
    if name not in (f"{v.get('video_id')}.mp4", "storyboard.mp4"):
        return None
    return fp


def main():
    videos = req("GET", f"{BASE}/videos")["data"]
    touched = 0
    for v in videos:
        if str(v.get("status")) != "draft_ready":
            continue
        fp = looks_like_rough_cut(v)
        if not fp:
            continue
        touched += 1
        print(f"[{'APPLY' if APPLY else 'DRY-RUN'}] {v['video_id']} ({v['id']})")
        print(f"    final_path: {fp}")
        print(f"    → rough_cut_path: {fp}")
        print(f"    → final_path:   (清空)")
        if APPLY:
            req("PATCH", f"{BASE}/videos/{v['id']}",
                {"rough_cut_path": fp, "final_path": ""})
            print("    ✅ 已回写")
    skipped_final = [v["video_id"] for v in videos
                     if v.get("final_path") and str(v.get("status")) != "draft_ready"]
    if skipped_final:
        print(f"ℹ️  跳过（非 draft_ready，final_path 按真成片处理）: {', '.join(skipped_final)}")
    if not touched:
        print("没有需要修复的记录。")
    elif not APPLY:
        print(f"\ndry-run 结束：将修复 {touched} 条。加 --apply 执行。")


if __name__ == "__main__":
    main()
