#!/usr/bin/env python3
"""
Whisper SRT 字幕生成器
输入：mp3/wav 音频文件 + 可选的参考文本
输出：SRT 字幕文件（句子级时间戳）

用法：
  python3 whisper_srt.py audio.mp3                    # 自动转录
  python3 whisper_srt.py audio.mp3 --text "参考文本"  # 用参考文本对齐
  python3 whisper_srt.py audio.mp3 --output out.srt
"""
import argparse
import os
import re
import sys


def format_timestamp(seconds: float) -> str:
    """秒转 SRT 时间格式：HH:MM:SS,mmm"""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


def transcribe_with_words(audio_path: str, model_size: str = "base"):
    """用 faster-whisper 转录，返回 word-level timestamps"""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        language="zh",
        vad_filter=True,
    )

    words = []
    for segment in segments:
        if segment.words:
            for word in segment.words:
                words.append({
                    "word": word.word.strip(),
                    "start": word.start,
                    "end": word.end,
                })
    return words, info


def group_words_to_srt(words: list, max_chars_per_line: int = 20) -> list:
    """把 word-level 时间戳按句子/短语合并成 SRT 条目"""
    srt_entries = []
    current_text = ""
    current_start = None
    current_end = None

    for i, w in enumerate(words):
        if current_start is None:
            current_start = w["start"]

        current_text += w["word"]
        current_end = w["end"]

        # 遇到标点符号或达到最大字符数，就断句
        is_punct = bool(re.search(r'[。！？，；：、.!?;:,]', w["word"]))
        is_max_len = len(current_text) >= max_chars_per_line
        is_last = i == len(words) - 1

        if is_punct or is_max_len or is_last:
            srt_entries.append({
                "start": current_start,
                "end": current_end,
                "text": current_text.strip(),
            })
            current_text = ""
            current_start = None
            current_end = None

    return srt_entries


def write_srt(entries: list, output_path: str):
    """写入 SRT 文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, entry in enumerate(entries, 1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(entry['start'])} --> {format_timestamp(entry['end'])}\n")
            f.write(f"{entry['text']}\n")
            f.write("\n")
    print(f"✅ SRT 已生成: {output_path}（{len(entries)} 条字幕）")


def main():
    parser = argparse.ArgumentParser(description="Whisper SRT 字幕生成器")
    parser.add_argument("audio", help="音频文件路径（mp3/wav）")
    parser.add_argument("--text", help="参考文本（可选，用于对齐）")
    parser.add_argument("--output", help="输出 SRT 路径（默认同名 .srt）")
    parser.add_argument("--model", default="base", help="whisper 模型大小（tiny/base/small/medium）")
    parser.add_argument("--max-chars", type=int, default=20, help="每行最大字符数")
    args = parser.parse_args()

    audio_path = args.audio
    if not os.path.exists(audio_path):
        print(f"❌ 文件不存在: {audio_path}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or os.path.splitext(audio_path)[0] + ".srt"

    print(f"🎙️  转录音频: {audio_path}")
    words, info = transcribe_with_words(audio_path, model_size=args.model)
    print(f"   检测到语言: {info.language}，共 {len(words)} 个词")

    if not words:
        print("❌ 未识别到语音内容", file=sys.stderr)
        sys.exit(1)

    entries = group_words_to_srt(words, max_chars_per_line=args.max_chars)
    write_srt(entries, output_path)


if __name__ == "__main__":
    main()
