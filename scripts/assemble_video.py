#!/usr/bin/env python3
"""
降级出片通道（ffmpeg 直出 · 不依赖剪映 · 不依赖 libass）

Phase 1.8：当剪映草稿通道失效（版本升级/草稿加密/机器绑定/pyJD 断更）时，
用同一份分镜 JSON 走「静帧 Ken Burns + TTS + 字幕 → 直出 mp4」兜底。

⚠️ 本机 ffmpeg 8.0.1（homebrew）**未编译 libass**，没有 ass/subtitles/drawtext 滤镜，
   故字幕改为「PIL 渲染透明字幕层 → ffmpeg overlay 合成」，全链路零额外依赖。
   （若将来装了带 libass 的 ffmpeg，可切回 subtitles= 滤镜方案。）

合成纪律（§十一.3）：
  1) BGM ducking（sidechaincompress，解说处压低音乐）
  2) 响度对齐（loudnorm I=-16 LUFS）
  3) 时间轴按实测配音排布（每镜时长来自 audio.duration_sec_actual）
  4) 实拍镜原生音轨（A4）：有配音→原声 ducking 垫底；无配音→原声顶上；
     --no-native-audio 关闭

用法：
  assemble_video.py --storyboard sb.json --srt subs.srt --output out.mp4 \
      [--images-dir DIR] [--audio-dir DIR] [--audio 整段配音] [--bgm bgm.mp3] \
      [--kenburns] [--font PATH] [--font-size 64]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"

FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
]


def resolve_font(explicit=None):
    if explicit and os.path.exists(explicit):
        return explicit
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def run(cmd, desc, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if r.returncode != 0:
        print(f"❌ {desc} 失败:\n{r.stderr[-700:]}", file=sys.stderr)
        raise SystemExit(1)
    return r


# ── SRT 解析 ──────────────────────────────────────────────────────────

def parse_srt(path):
    text = open(path, "r", encoding="utf-8-sig").read().replace("\r\n", "\n")
    out = []
    for b in re.split(r"\n\s*\n", text):
        if not b.strip():
            continue
        lines = b.strip().split("\n")
        ti = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if ti is None:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)",
                     lines[ti].strip())
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        s = g[0]*3600 + g[1]*60 + g[2] + g[3]/1000
        e = g[4]*3600 + g[5]*60 + g[6] + g[7]/1000
        body = " ".join(l.strip() for l in lines[ti+1:] if l.strip())
        if body:
            out.append({"start": s, "end": e, "text": body})
    return out


# ── 字幕层渲染（PIL，无 libass 依赖）──────────────────────────────────

def wrap_cjk(text, max_chars):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)] or [text]


def render_subtitle_png(text, W, H, font_path, size, margin_v, out_png):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, size)
    except Exception:
        font = ImageFont.load_default()
    max_chars = max(6, int(W * 0.86 / max(size, 1)))
    lines = wrap_cjk(text, max_chars)[:3]
    lh = int(size * 1.35)
    total_h = lh * len(lines)
    y = H - margin_v - total_h
    for ln in lines:
        w = d.textlength(ln, font=font)
        d.text(((W - w) / 2, y), ln, font=font, fill=(255, 255, 255, 255),
               stroke_width=max(2, size // 18), stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(out_png)


# ── 素材定位 ──────────────────────────────────────────────────────────

def img_for_shot(shot, i, images_dir):
    vis = shot.get("visual") or {}
    ref = vis.get("source_ref")
    if isinstance(ref, dict) and ref.get("path"):
        p = os.path.expanduser(ref["path"])
        if os.path.exists(p):
            return p
    if images_dir:
        for cand in (f"shot_{i:03d}.jpg", f"shot_{i:03d}.png",
                     f"shot_{shot.get('shot_id', i):03d}.jpg"):
            p = os.path.join(images_dir, cand)
            if os.path.exists(p):
                return p
    return None


def audio_for_shot(shot, i, audio_dir):
    au = shot.get("audio") or {}
    if au.get("audio_path"):
        p = os.path.expanduser(au["audio_path"])
        if os.path.exists(p):
            return p
    if audio_dir:
        for cand in (f"shot_{i:03d}.mp3", f"shot_{i:03d}.wav",
                     f"shot_{shot.get('shot_id', i):03d}.mp3"):
            p = os.path.join(audio_dir, cand)
            if os.path.exists(p):
                return p
    return None


def shot_duration(shot, default=3.0):
    au = shot.get("audio") or {}
    vis = shot.get("visual") or {}
    for v in (au.get("duration_sec_actual"), au.get("duration_sec"),
              vis.get("duration_sec_estimate"), shot.get("duration_sec")):
        if v:
            return float(v)
    return default


def real_clip_source(shot):
    """
    实拍镜（混剪 M2，D3/D4）→ (media_path, clip_start, clip_dur) 或 None。
    时间源反转：这类镜的时长=画面**原生**（ffprobe 实测入出点区间），
    不再贴配音时长；装配禁用 -stream_loop（实拍循环=口型/动作穿帮）。
    解析失败（素材缺失/Eagle 离线）返回 None → 落回原有静帧路径并告警。
    """
    try:
        from real_clip import real_clip_of, resolve_clip, probe_duration, clip_span
    except ImportError:
        return None
    rc = real_clip_of(shot)
    if not rc:
        return None
    media, why = resolve_clip(rc)
    if not media:
        print(f"⚠️  镜{shot.get('shot_id', '?')}: 实拍素材未定位（{why}），回退静帧",
              file=sys.stderr)
        return None
    native = probe_duration(media)
    if not native:
        print(f"⚠️  镜{shot.get('shot_id', '?')}: {os.path.basename(media)} 探针失败，回退静帧",
              file=sys.stderr)
        return None
    start, dur = clip_span(rc, native)
    return media, start, dur


def probe_has_audio(path):
    """素材是否含音频流（A4：无声实拍镜按静音镜处理，不炸混音）。"""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=15).stdout
        return "audio" in out
    except Exception:
        return False


def build_aligned_voice(shot_audio, work):
    """
    A4：分镜级时间轴对齐音频轨。混音底座在 real_clip.build_aligned_track
    （与 generate_draft 的剪映垫轨共享，保证两条通道同一套 ducking 参数）。
    """
    from real_clip import build_aligned_track
    try:
        return build_aligned_track(shot_audio, work, "assemble", "voice.m4a")
    except RuntimeError as e:
        print(f"❌ A4 逐镜混音失败: {e}", file=sys.stderr)
        raise SystemExit(1)


def plan_intervals(shot_start, shot_end, entries, tol=0.02):
    """把 [shot_start, shot_end) 按字幕条目切成若干 (s, e, text) 区间，空隙补 None"""
    segs, cur = [], shot_start
    for e in entries:
        if e["end"] <= shot_start + tol or e["start"] >= shot_end - tol:
            continue
        s, en = max(e["start"], shot_start), min(e["end"], shot_end)
        if s > cur + tol:
            segs.append((cur, s, None))
        segs.append((s, en, e["text"]))
        cur = en
    if cur < shot_end - tol:
        segs.append((cur, shot_end, None))
    return segs or [(shot_start, shot_end, None)]


def main():
    ap = argparse.ArgumentParser(description="降级出片通道（ffmpeg 直出，无 libass 依赖）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--srt")
    ap.add_argument("--output", required=True)
    ap.add_argument("--images-dir")
    ap.add_argument("--audio-dir")
    ap.add_argument("--audio", help="单个整段配音")
    ap.add_argument("--bgm")
    ap.add_argument("--kenburns", action="store_true")
    ap.add_argument("--intro", help="片头视频文件（v4.0；项目配置 video.intro 也可）")
    ap.add_argument("--outro", help="片尾视频文件（v4.0；项目配置 video.outro 也可）")
    ap.add_argument("--font", help="字体路径（默认自动探测）")
    ap.add_argument("--font-size", type=int,
                    help="字幕像素字号；默认取分镜 style.subtitle.font_size_px")
    ap.add_argument("--margin-v", type=int,
                    help="距底部像素；默认由 style.subtitle.transform_y 推导")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--no-subtitles", action="store_true")
    ap.add_argument("--no-native-audio", action="store_true",
                    help="实拍镜不保留原生音轨（默认保留：无配音时原声顶上，"
                         "有配音时原声 sidechain 自动 ducking 垫底）")
    args = ap.parse_args()

    with open(os.path.expanduser(args.storyboard), "r", encoding="utf-8") as f:
        sb = json.load(f)
    shots = sb.get("shots") or []
    if not shots:
        print("❌ 分镜为空", file=sys.stderr); sys.exit(1)

    # ── 字幕样式：与剪映通道共用同一份契约（storyboard_schema）──
    # 使「字号/描边/位置」两通道同源，避免再次出现"两条通道字幕不一致"
    try:
        from storyboard_schema import subtitle_style as _sts, shot_scale as _scale
        _st = _sts(sb)
    except ImportError:
        _st = {"font_size_px": 64, "stroke_width": 0.06, "transform_y": -0.7}
        _scale = lambda _shot: 1.0
    if args.font_size is None:
        args.font_size = int(_st.get("font_size_px") or 64)

    ar = sb.get("aspect_ratio", "9:16")
    W, H = {"9:16": (1080, 1920), "3:4": (1080, 1440),
            "16:9": (1920, 1080), "1:1": (1080, 1080)}.get(ar, (1080, 1920))
    if args.margin_v is None:
        # transform_y ∈ (-1,0)：文字中心相对位置（0=居中，-1=贴底）
        ty = float(_st.get("transform_y", -0.7))
        args.margin_v = max(20, int(H / 2 * (1 - abs(ty))) - args.font_size // 2)
    images_dir = os.path.expanduser(args.images_dir) if args.images_dir else None
    audio_dir = os.path.expanduser(args.audio_dir) if args.audio_dir else None

    entries = []
    if args.srt and not args.no_subtitles and os.path.exists(os.path.expanduser(args.srt)):
        entries = parse_srt(os.path.expanduser(args.srt))
    font_path = resolve_font(args.font)
    if entries and not font_path:
        print("⚠️  未找到中文字体，字幕可能不显示", file=sys.stderr)

    work = tempfile.mkdtemp(prefix="assemble_")
    print(f"📐 {W}x{H} @{args.fps}fps，{len(shots)} 镜"
          f"{'，字幕 ' + str(len(entries)) + ' 条' if entries else ''}")

    # ── 逐镜（必要时按字幕切成子段）生成视频段 ──
    seg_files, audio_files, missing_img = [], [], []
    shot_audio = []  # A4：逐镜音频计划 {dur, native=(media,start)|None, vo=path|None}
    cursor = 0.0
    sub_png_cache = {}
    for i, shot in enumerate(shots, 1):
        # 实拍镜优先：时长=画面原生（D3），素材=real_clip（D4：不循环）
        rcs = real_clip_source(shot)
        dur = rcs[2] if rcs else shot_duration(shot)
        s0, s1 = cursor, cursor + dur
        cursor = s1
        img = img_for_shot(shot, i, images_dir)
        if not img and not rcs:
            missing_img.append(i); continue

        base = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}")
        # ── 动态 B-roll：该镜若有 AI 生成的视频片段，优先用它（循环补足时长）──
        #    没有则仍用静帧 + KenBurns（默认路径，零额外成本）
        vclip = (shot.get("visual") or {}).get("video_path")
        use_video = bool(vclip and os.path.exists(vclip))
        src = vclip if use_video else img
        in_args = ["-stream_loop", "-1"] if use_video else ["-loop", "1"]
        if use_video:
            print(f"   镜{i}: 使用动态 B-roll 片段")
        if rcs:
            src = rcs[0]
            in_args = []  # -ss 逐子段随偏移推进（见下），整镜只打一次日志
            use_video = True  # 视作"有运动"：不 zoompan、不 loop
            print(f"   镜{i}: 实拍片段 {os.path.basename(rcs[0])}"
                  f"（入点 {rcs[1]:.1f}s，时长 {rcs[2]:.2f}s，画面为时间源）")
        intervals = (plan_intervals(s0, s1, entries) if entries
                     else [(s0, s1, None)])

        for j, (a, b, text) in enumerate(intervals):
            d = b - a
            if d <= 0.05:
                continue
            seg = os.path.join(work, f"seg_{i:03d}_{j:02d}.mp4")
            seg_in = in_args
            if rcs:
                seg_in = ["-ss", f"{max(0.0, rcs[1] + (a - s0)):.3f}"]
            if use_video:
                # 视频本身有运动，不需要 zoompan
                vf = f"{base},fps={args.fps}"
            else:
                vf = (f"{base},zoompan=z='min(zoom+0.0006,1.12)':"
                      f"d={max(1,int(d*args.fps))}:s={W}x{H}:fps={args.fps}"
                      if args.kenburns else f"{base},fps={args.fps}")
            if text:
                # 逐镜字幕倍率（AI 可主动调整字号）
                fsize = max(12, int(round(args.font_size * _scale(shot))))
                key = (text[:60], W, H, fsize)
                png = sub_png_cache.get(key)
                if not png:
                    png = os.path.join(work, f"sub_{len(sub_png_cache):03d}.png")
                    render_subtitle_png(text, W, H, font_path,
                                        fsize, args.margin_v, png)
                    sub_png_cache[key] = png
                cmd = [FFMPEG, "-y"] + seg_in + ["-i", src, "-i", png,
                       "-filter_complex", f"[0:v]{vf}[bg];[bg][1:v]overlay=0:0[v]",
                       "-map", "[v]", "-t", f"{d:.3f}", "-r", str(args.fps),
                       "-c:v", "libx264", "-preset", "veryfast",
                       "-pix_fmt", "yuv420p", seg]
            else:
                cmd = [FFMPEG, "-y"] + seg_in + ["-i", src, "-t", f"{d:.3f}",
                       "-vf", vf, "-r", str(args.fps), "-c:v", "libx264",
                       "-preset", "veryfast", "-pix_fmt", "yuv420p", seg]
            try:
                run(cmd, f"镜头{i} 子段{j}")
            except SystemExit:
                if args.kenburns:
                    run([FFMPEG, "-y"] + seg_in + ["-i", src, "-t", f"{d:.3f}",
                         "-vf", f"{base},fps={args.fps}", "-r", str(args.fps),
                         "-c:v", "libx264", "-preset", "veryfast",
                         "-pix_fmt", "yuv420p", seg], f"镜头{i} 子段{j}(回退)")
                else:
                    raise
            seg_files.append(seg)

        a = audio_for_shot(shot, i, audio_dir)
        if a:
            audio_files.append(a)
        # A4 原声计划：实拍镜素材含音频流才入线；有配音的镜由混音段做 ducking
        native_a = None
        if rcs and not args.no_native_audio and probe_has_audio(rcs[0]):
            native_a = (rcs[0], rcs[1])
        shot_audio.append({"dur": dur, "native": native_a, "vo": a})

    if missing_img:
        print(f"⚠️  缺图片的镜（已跳过）: {missing_img}", file=sys.stderr)
    if not seg_files:
        print("❌ 没有任何可用图片素材", file=sys.stderr); sys.exit(1)

    # 1) 视频轨拼接
    vlist = os.path.join(work, "vlist.txt")
    with open(vlist, "w") as f:
        for s in seg_files:
            f.write(f"file '{s}'\n")
    silent = os.path.join(work, "silent.mp4")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", vlist,
         "-c", "copy", silent], "视频轨拼接")

    # 2) 音频轨
    #    A4：只要有任何带原声的实拍镜 → 走逐镜时间轴对齐混音（原声入线，配音侧压）；
    #    纯口播/无原声任务保持下方历史路径，逐字节零变化。
    voice = None
    has_native = any(s["native"] for s in shot_audio)
    if has_native:
        n_mix = sum(1 for s in shot_audio if s["native"] and s["vo"])
        n_nat = sum(1 for s in shot_audio if s["native"] and not s["vo"])
        print(f"🔊 A4 原声混音：{n_nat} 镜原声顶上 / {n_mix} 镜配音+原声 ducking"
              f"（--no-native-audio 可关闭）")
        voice = build_aligned_voice(shot_audio, work)
    elif audio_files and len(audio_files) == len(shots) - len(missing_img):
        alist = os.path.join(work, "alist.txt")
        with open(alist, "w") as f:
            for x in audio_files:
                f.write(f"file '{x}'\n")
        voice = os.path.join(work, "voice.m4a")
        run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", alist,
             "-c:a", "aac", "-ar", "44100", "-ac", "2", voice], "语音轨拼接")
    elif args.audio:
        voice = os.path.expanduser(args.audio)
    elif audio_files:
        print(f"⚠️  逐镜音频数({len(audio_files)})与镜数不匹配，"
              f"请用 --audio 指定整段配音", file=sys.stderr)

    # 3) 合成为粗剪（终剪成片由用户在剪映导出后登记）
    out = os.path.abspath(os.path.expanduser(args.output))
    if os.path.dirname(out):
        os.makedirs(os.path.dirname(out), exist_ok=True)
    inputs = ["-i", silent]
    if voice:
        inputs += ["-i", voice]
    if args.bgm:
        inputs += ["-i", os.path.expanduser(args.bgm)]
    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k"]

    if voice and args.bgm:
        fc = ("[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,asplit=2[vo][sc];"
              "[2:a]volume=0.18[bg];[bg][sc]sidechaincompress="
              "threshold=0.03:ratio=8:attack=20:release=400[bgd];"
              "[vo][bgd]amix=inputs=2:normalize=0[a]")
        run([FFMPEG, "-y", *inputs, "-filter_complex", fc, "-map", "0:v",
             "-map", "[a]", *enc, "-shortest", out], "最终合成(+BGM)", cwd=work)
    elif voice:
        fc = "[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]"
        run([FFMPEG, "-y", *inputs, "-filter_complex", fc, "-map", "0:v",
             "-map", "[a]", *enc, "-shortest", out], "最终合成(有配音)", cwd=work)
    else:
        run([FFMPEG, "-y", *inputs, "-c:v", "libx264", "-preset", "medium",
             "-crf", "19", "-pix_fmt", "yuv420p", out], "最终合成(无声)", cwd=work)

    # 4) 片头/片尾（v4.0 P2-8）：存在则归一化后拼接（全部重编码保证参数一致）
    intro = os.path.expanduser(args.intro) if args.intro else ""
    outro = os.path.expanduser(args.outro) if args.outro else ""
    parts = [p0 for p0 in (intro, out, outro) if p0 and os.path.exists(p0)]
    missing = [p0 for p0 in (intro, outro) if p0 and not os.path.exists(p0)]
    if missing:
        print(f"⚠️  片头/尾文件不存在，跳过拼接: {missing}", file=sys.stderr)
    if len(parts) > 1:
        norm = []
        for idx, p0 in enumerate(parts):
            np0 = os.path.join(work, f"part_{idx:02d}.mp4")
            run([FFMPEG, "-y", "-i", p0,
                 "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={args.fps}",
                 "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                 "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                 "-ar", "44100", "-ac", "2", np0],
                f"归一片头/尾 {os.path.basename(p0)}")
            norm.append(np0)
        plist = os.path.join(work, "plist.txt")
        with open(plist, "w") as f:
            for np0 in norm:
                f.write(f"file '{np0}'\n")
        merged = out + ".with_intro_outro.mp4"
        run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", plist,
             "-c", "copy", merged], "拼接片头片尾")
        os.replace(merged, out)
        print(f"🎬 已拼接片头/片尾（{len(parts)} 段）")

    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", out],
        capture_output=True, text=True).stdout)
    dur = float(info.get("format", {}).get("duration", 0))
    print(f"✅ 粗剪（待终剪）: {out}")
    print(f"   时长 {dur:.2f}s，{len(seg_files)} 段"
          f"{'，含字幕层' if entries else ''}{'，含配音' if voice else ''}"
          f"{'，含实拍原声' if has_native else ''}"
          f"{'，含BGM ducking' if (voice and args.bgm) else ''}"
          f"{'，含片头/尾' if len(parts) > 1 else ''}")
    print(json.dumps({"output": out, "duration_sec": round(dur, 2),
                      "segments": len(seg_files)}))


if __name__ == "__main__":
    main()
