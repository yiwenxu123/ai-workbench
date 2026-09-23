#!/usr/bin/env python3
"""
SRT 字幕生成器 v2（分镜直出版 · 零 ASR 主线）

设计依据（2026-09-19 实测）：
- MiniMax T2A 的 subtitle_enable 不支持句内切分（每次请求只返回 1 个 segment），
  故「字幕由 TTS 原生句级时间戳直出」不成立；
- 但逐镜 TTS 的 extra_info.audio_length 给出毫秒级精确时长，
  每镜时长 + 台词直接累加即得逐句 SRT —— 对齐是确定性的，不需 ASR。

两种模式：
  1) 主线：--storyboard <分镜JSON>        逐镜累加（每镜一条字幕）
  2) 兜底：<audio> --script <文本>         整段按字符比例分配（旧版兼容）

时长来源优先级（每镜）：
  audio.duration_sec_actual  >  audio.duration_ms/1000  >  ffprobe(audio.audio_path)
"""
import argparse
import json
import os
import re
import subprocess
import sys


# ── 基础工具 ──────────────────────────────────────────────────────────

def ffprobe_duration(path: str) -> float:
    """用 ffprobe 获取音频时长（秒）"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return float(r.stdout.strip())
    except Exception as e:
        print(f"⚠️  ffprobe 失败 {path}: {e}", file=sys.stderr)
        return 0.0


def fmt_ts(seconds: float) -> str:
    """秒 → SRT 时间戳 HH:MM:SS,mmm"""
    seconds = max(0.0, seconds)
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis == 1000:  # 进位保护
        secs += 1
        millis = 0
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def split_sentences(text: str, break_on_comma: bool = False) -> list:
    """切分短句。break_on_comma=True 时在逗号/顿号处也断行（中文口播字幕常用）"""
    pat = r'(?<=[。！？；!?;，,、])' if break_on_comma else r'(?<=[。！？；!?;])'
    parts = re.split(pat, text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


# ── 主线：分镜直出 ────────────────────────────────────────────────────

def shot_text(shot: dict) -> str:
    audio = shot.get("audio") or {}
    return (audio.get("text") or shot.get("script_line") or "").strip()


def shot_duration(shot: dict, probe: bool) -> tuple:
    """返回 (duration_sec, source)；找不到返回 (0, None)"""
    audio = shot.get("audio") or {}
    if audio.get("duration_sec_actual"):
        return float(audio["duration_sec_actual"]), "duration_sec_actual"
    if audio.get("duration_ms"):
        return float(audio["duration_ms"]) / 1000.0, "duration_ms"
    p = audio.get("audio_path")
    if probe and p and os.path.exists(os.path.expanduser(p)):
        return ffprobe_duration(os.path.expanduser(p)), "ffprobe"
    return 0.0, None


def build_from_storyboard(sb: dict, probe: bool, split_long: bool,
                          max_chars: int) -> tuple:
    """分镜 → SRT 条目列表 + 诊断信息"""
    shots = sb.get("shots") or []
    entries, cursor, missing = [], 0.0, []

    for i, shot in enumerate(shots, 1):
        text = shot_text(shot)
        dur, src = shot_duration(shot, probe)
        if dur <= 0:
            missing.append(shot.get("shot_id", i))
            continue

        if split_long and len(text) > max_chars:
            # 该镜无句内时间戳：按字符比例在镜内二次分配（仅影响观感，不影响总轴）
            sents = split_sentences(text, break_on_comma=True)
            total = sum(len(s) for s in sents) or 1
            t = cursor
            for s in sents:
                d = dur * len(s) / total
                entries.append({"start": t, "end": t + d, "text": s})
                t += d
        else:
            entries.append({"start": cursor, "end": cursor + dur, "text": text})
        cursor += dur

    return entries, {"total_sec": cursor, "shot_count": len(shots),
                     "missing_duration": missing}


# ── 兜底：整段比例分配 ────────────────────────────────────────────────

def build_from_ratio(script: str, total: float) -> tuple:
    sents = split_sentences(script)
    if not sents or total <= 0:
        return [], {"total_sec": total, "shot_count": 0, "missing_duration": []}
    chars = sum(len(s) for s in sents) or 1
    entries, t = [], 0.0
    for s in sents:
        d = total * len(s) / chars
        entries.append({"start": t, "end": t + d, "text": s})
        t += d
    return entries, {"total_sec": total, "shot_count": len(sents),
                     "missing_duration": []}


# ── 输出 ──────────────────────────────────────────────────────────────

def write_srt(entries: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, e in enumerate(entries, 1):
            f.write(f"{i}\n{fmt_ts(e['start'])} --> {fmt_ts(e['end'])}\n{e['text']}\n\n")
    print(f"✅ SRT 已生成: {output_path}（{len(entries)} 条）")


def main():
    ap = argparse.ArgumentParser(description="SRT 字幕生成器 v2（分镜直出版）")
    ap.add_argument("audio", nargs="?", help="[兜底模式] 音频文件路径")
    ap.add_argument("--storyboard", help="分镜 JSON 路径（主线模式）")
    ap.add_argument("--script", help="脚本文本（兜底模式）")
    ap.add_argument("--script-file", help="脚本文件路径（兜底模式）")
    ap.add_argument("--output", help="输出 SRT 路径")
    ap.add_argument("--probe-audio", action="store_true",
                    help="分镜下探：无 duration 字段时对 audio_path 跑 ffprobe")
    ap.add_argument("--split-long", action="store_true",
                    help="镜内按标点+字符比例二次切分（无句内时间戳时的近似）")
    ap.add_argument("--max-chars", type=int, default=18,
                    help="触发镜内切分的字数阈值（默认 18）")
    args = ap.parse_args()

    # 主线：分镜直出
    if args.storyboard:
        sb_path = os.path.expanduser(args.storyboard)
        if not os.path.exists(sb_path):
            print(f"❌ 分镜文件不存在: {sb_path}", file=sys.stderr)
            sys.exit(1)
        with open(sb_path, "r", encoding="utf-8") as f:
            sb = json.load(f)
        entries, diag = build_from_storyboard(
            sb, args.probe_audio, args.split_long, args.max_chars)
        out = args.output or os.path.splitext(sb_path)[0] + ".srt"
        write_srt(entries, out)
        print(f"📋 分镜 {diag['shot_count']} 镜 → {len(entries)} 条字幕，"
              f"总时长 {diag['total_sec']:.2f}s")
        if diag["missing_duration"]:
            print(f"⚠️  缺时长的镜（已跳过）: {diag['missing_duration']}",
                  file=sys.stderr)
        print(json.dumps({"srt_path": out, "entry_count": len(entries),
                          "total_sec": round(diag["total_sec"], 3)}))
        return

    # 兜底：整段比例
    if not args.audio:
        print("❌ 需 --storyboard，或提供 <audio> + --script", file=sys.stderr)
        sys.exit(1)
    audio_path = os.path.expanduser(args.audio)
    if not os.path.exists(audio_path):
        print(f"❌ 文件不存在: {audio_path}", file=sys.stderr)
        sys.exit(1)
    if args.script:
        script = args.script
    elif args.script_file:
        with open(os.path.expanduser(args.script_file), "r", encoding="utf-8") as f:
            script = f.read()
    else:
        print("❌ 请提供 --script 或 --script-file", file=sys.stderr)
        sys.exit(1)
    total = ffprobe_duration(audio_path)
    if total <= 0:
        print("❌ 无法获取音频时长", file=sys.stderr)
        sys.exit(1)
    entries, _ = build_from_ratio(script, total)
    out = args.output or os.path.splitext(audio_path)[0] + ".srt"
    write_srt(entries, out)
    print(json.dumps({"srt_path": out, "entry_count": len(entries),
                      "total_sec": round(total, 3)}))


if __name__ == "__main__":
    main()
