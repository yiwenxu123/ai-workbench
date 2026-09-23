#!/usr/bin/env python3
"""
SRT 字幕生成器 v2（分镜直出版 · 零 ASR 主线）

设计依据（2026-09-19 实测）：
- MiniMax T2A 的 subtitle_enable 不支持句内切分（每次请求只返回 1 个 segment），
  故「字幕由 TTS 原生句级时间戳直出」不成立；
- 但逐镜 TTS 的 extra_info.audio_length 给出毫秒级精确时长，
  每镜时长 + 台词直接累加即得逐句 SRT —— 对齐是确定性的，不需 ASR。

三种模式：
  1) 主线：--storyboard <分镜JSON>        逐镜累加（每镜一条字幕）
  2) 兜底：<audio> --script <文本>         整段按字符比例分配（旧版兼容）
  3) 镜内词级：--split-timed              读 TTS 侧车 *.words.json（edge WordBoundary
     本来就逐词流过来，A1 起落盘），按真实词边界在镜内断句；无侧车的镜退回 1)。

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


# ── 镜内词级对齐（A1）────────────────────────────────────────────────

STRONG_PUNCT = "。！？；!?;"
WEAK_PUNCT = "，,、：:"


def _norm(s: str) -> str:
    """只留实义字符（TTS 不播报标点与空白，比对/计数都要先归一化）"""
    return re.sub(r"[\s\W_]+", "", s or "", flags=re.UNICODE)


def load_shot_words(shot: dict) -> list:
    """读该镜的词级侧车（generate_voiceover 由 edge WordBoundary 落的 *.words.json）。

    路径优先取 audio.timing_path，退回 audio_path 同名侧车。
    侧车词表与本镜台词归一化后不一致（音频是旧版 / 台词改过）一律判为不可信，
    返回 []，该镜退回「整镜一条字幕」—— 宁可粗，不可错轴。
    """
    au = shot.get("audio") or {}
    p = au.get("timing_path")
    if not p and au.get("audio_path"):
        p = os.path.splitext(au["audio_path"])[0] + ".words.json"
    if not p:
        return []
    p = os.path.expanduser(p)
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    words = [w for w in (data.get("words") or [])
             if isinstance(w, dict) and w.get("w") and w.get("e") is not None]
    if not words:
        return []
    if _norm("".join(w["w"] for w in words)) != _norm(shot_text(shot)):
        return []
    return words


def char_times(text: str, words: list):
    """把词表时间摊到台词每个字符，返回 (ct, starts)。

    ct：与 text 等长的 [(start,end)|None]，标点/空白不占时间（沿用前一实义字符），
        一个词内按字符数线性摊分。对不上（词表字符数少于台词实义字符数）返回
        (None, None) 让调用方退回粗路径。
    starts：各词「第一个实义字符」在 text 中的下标集合——切分时的合法落点，
        用来避免把「五铢钱」这类多字词从中间劈开。
    """
    ct = [None] * len(text)
    starts = set()
    ti = wi = 0
    cur = None
    last = None
    for i, ch in enumerate(text):
        if not _norm(ch):
            ct[i] = last
            continue
        while ti < len(words):
            token = words[ti]["w"]
            while wi < len(token) and not _norm(token[wi]):
                wi += 1
            if wi < len(token):
                break
            ti += 1
            wi = 0
        if ti >= len(words):
            return None, None
        if ti != cur:
            starts.add(i)
            cur = ti
        w = words[ti]
        n = max(1, len(w["w"]))
        s, e = float(w["s"]), float(w["e"])
        step = (e - s) / n
        ct[i] = (s + step * wi, s + step * (wi + 1))
        last = ct[i]
        wi += 1
    return ct, starts


MIN_PIECE = 4          # 弱标点前至少攒够这么多实义字才肯断，避免 1~2 字孤条


def _snap(cut: int, b: int, start: int, starts: set) -> int:
    """硬切点吸附到最近的词首边界（找不到边界时原样返回）。"""
    if not starts or cut >= b or cut in starts:
        return cut
    back = max([s for s in starts if start < s < cut], default=None)
    fwd = min([s for s in starts if cut < s < b], default=None)
    if back is None:
        return fwd if fwd is not None else cut
    if fwd is None:
        return back
    return back if (cut - back) <= (fwd - cut) else fwd


def _chunk(a: int, b: int, text: str, max_chars: int, starts: set = None) -> list:
    """[a,b) 按「实义字数 ≤ max_chars」切小段，优先落在弱标点（逗号/顿号）之后。

    没有标点可落时的硬切点会吸附到词边界（starts），否则「一枚中国五 / 铢钱。」
    这种把词劈开的断句会直接印在屏幕上。
    """
    res, start, last_weak, i = [], a, -1, a
    while i < b:
        n = len(_norm(text[start:i + 1]))
        if text[i] in WEAK_PUNCT and i > start and n >= MIN_PIECE:
            last_weak = i + 1
        if n >= max_chars:
            cut = last_weak if last_weak > start else _snap(i + 1, b, start, starts)
            if cut <= start or cut >= b:
                cut = i + 1
            res.append((start, cut))
            start, last_weak = cut, -1
        i += 1
    if start < b and _norm(text[start:b]):
        res.append((start, b))
    return res


def timed_entries(text: str, ct: list, cursor: float, dur: float,
                  max_chars: int, starts: set = None) -> list:
    """一镜 → 多条字幕：镜内按真实词边界分配，镜轴锁死在 [cursor, cursor+dur]。

    段间边界取「下一段首字的真实起始」，首段起点仍从 cursor 起、末段终点仍到
    cursor+dur —— 与整段累加逐镜对齐，字幕不重叠也不留空洞。
    """
    ranges = []
    cur = 0
    for i, ch in enumerate(text):
        if ch in STRONG_PUNCT:
            if i + 1 > cur:
                ranges.extend(_chunk(cur, i + 1, text, max_chars, starts))
            cur = i + 1
    if cur < len(text):
        ranges.extend(_chunk(cur, len(text), text, max_chars, starts))
    if not ranges:
        ranges = [(0, len(text))]

    marks = []
    for a, b in ranges:
        s = next((ct[i][0] for i in range(a, b) if ct[i]), None)
        if s is None:
            return []                      # 词表覆盖不全，退回整镜一条
        # 词表时间是**本镜音频内**的相对秒（edge 每次合成从 0 计），换成全片轴
        st = cursor + max(0.0, min(s, dur))
        if st > cursor + dur - 0.05:
            return []                      # 词表跨度超出镜时长：侧车不可信
        piece = text[a:b].strip()
        if marks and st - marks[-1][0] < 0.05:
            marks[-1] = (marks[-1][0], marks[-1][1] + piece)
        else:
            marks.append((st, piece))
    if not marks:
        return []
    return [{"start": (cursor if k == 0 else st),
             "end": (cursor + dur if k == len(marks) - 1 else marks[k + 1][0]),
             "text": txt}
            for k, (st, txt) in enumerate(marks) if txt]


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
                          max_chars: int, split_timed: bool = False) -> tuple:
    """分镜 → SRT 条目列表 + 诊断信息"""
    shots = sb.get("shots") or []
    entries, cursor, missing = [], 0.0, []
    timed_shots = 0

    for i, shot in enumerate(shots, 1):
        text = shot_text(shot)
        dur, src = shot_duration(shot, probe)
        if dur <= 0:
            missing.append(shot.get("shot_id", i))
            continue

        timed = []
        if split_timed:
            words = load_shot_words(shot)
            ct, starts = char_times(text, words) if words else (None, None)
            if ct:
                timed = timed_entries(text, ct, cursor, dur, max_chars, starts)
        if timed:
            entries.extend(timed)
            timed_shots += 1
        elif split_long and len(text) > max_chars:
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
                     "missing_duration": missing, "timed_shots": timed_shots}


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
    ap.add_argument("--split-timed", action="store_true",
                    help="镜内按 TTS 词级侧车（*.words.json）的真实词边界切分；"
                         "无侧车或台词已变的镜自动退回整镜一条（不猜）")
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
            sb, args.probe_audio, args.split_long, args.max_chars,
            args.split_timed)
        out = args.output or os.path.splitext(sb_path)[0] + ".srt"
        write_srt(entries, out)
        print(f"📋 分镜 {diag['shot_count']} 镜 → {len(entries)} 条字幕，"
              f"总时长 {diag['total_sec']:.2f}s"
              + (f"（其中 {diag['timed_shots']} 镜按词边界对齐）"
                 if diag.get("timed_shots") else ""))
        if args.split_timed and diag["shot_count"] and not diag["timed_shots"]:
            print("⚠️  --split-timed 未命中任何镜：配音侧车缺失或台词与音频已不一致",
                  file=sys.stderr)
        if diag["missing_duration"]:
            print(f"⚠️  缺时长的镜（已跳过）: {diag['missing_duration']}",
                  file=sys.stderr)
        print(json.dumps({"srt_path": out, "entry_count": len(entries),
                          "timed_shots": diag["timed_shots"],
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
