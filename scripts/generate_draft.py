#!/usr/bin/env python3
"""
剪映草稿生成器 - 从分镜 JSON + SRT + 音频生成剪映草稿
输入：分镜 JSON、音频文件、SRT 字幕、图片素材目录
输出：剪映草稿（放在剪映草稿目录里）
"""
import argparse
import json
import os
import shutil
import sys

import pyJianYingDraft as draft


# ── A2 草稿观感：运镜 / 镜间转场 / 字幕入场 ──────────────────────────

def _resolve_enum(cls, name, what):
    """按中文名取剪映动效枚举；名字不对就退回「不加」并提示（不猜同名近似的）。"""
    name = str(name or "").strip()
    if not name:
        return None
    hit = next((m for m in cls if m.name == name), None)
    if hit is None:
        print(f"⚠️  未知{what}「{name}」，该项不加"
              f"（可选如：{'、'.join(m.name for m in list(cls)[:6])}…）", file=sys.stderr)
    return hit


def apply_ken_burns(seg, duration_us, pos, style):
    """给**图片静帧镜**加缩放+横漂关键帧（实拍视频镜本身在动，不加）。

    推拉方向逐镜交替；关键点是「缩回到 1.0 的那一刻横移也归 0」，
    否则原尺寸下横移会露出黑边。
    """
    scale = max(1.0, float(style.get("kb_scale") or 1.0))
    pan = abs(float(style.get("kb_pan") or 0.0))
    if not style.get("ken_burns", True):
        return False
    if scale <= 1.001 and pan <= 0.001:
        return False
    zoom_in = pos % 2 == 0
    lo, hi = 1.0, scale
    seg.add_keyframe(draft.KeyframeProperty.uniform_scale, 0, lo if zoom_in else hi)
    seg.add_keyframe(draft.KeyframeProperty.uniform_scale, duration_us,
                     hi if zoom_in else lo)
    if pan > 0.001:
        drift = pan * (1 if pos % 4 < 2 else -1)
        seg.add_keyframe(draft.KeyframeProperty.position_x, 0, 0.0 if zoom_in else drift)
        seg.add_keyframe(draft.KeyframeProperty.position_x,
                         duration_us, drift if zoom_in else 0.0)
    return True


def apply_transition(seg, duration_us, style):
    """镜间叠化：转场挂在**后一个镜**上（剪映语义＝该段的入点转场）。"""
    tr = _resolve_enum(draft.TransitionType, style.get("transition"), "转场")
    if tr is None:
        return False
    want = int(float(style.get("transition_sec") or 0.3) * 1_000_000)
    # 不超过该镜时长的 1/3，且至少 0.1s，否则短镜会被转场吃掉大半
    span = min(want, int(duration_us / 3))
    if span < 100_000:
        return False
    seg.add_transition(tr, duration=span)
    return True


def apply_subtitle_intro(script, style):
    """给 import_srt 生成的字幕段加入场动画。

    坑（实测）：pyJD 只在 `add_segment()` 时把段上的动画登记进 materials，
    而 `import_srt` 是直接把段塞进轨道的 —— 之后补的动画不会自动出现在
    `material_animations` 里，必须照 add_segment 的做法自己登记一次。
    """
    intro = _resolve_enum(draft.TextIntro, style.get("subtitle_intro"), "字幕入场动画")
    if intro is None:
        return 0
    sec = float(style.get("subtitle_intro_sec") or 0.25)
    done = 0
    for track in script.tracks.values():
        for seg in getattr(track, "segments", []):
            if not isinstance(seg, draft.TextSegment):
                continue
            seg.add_animation(intro, int(sec * 1_000_000))
            inst = seg.animations_instance
            if inst is not None and inst not in script.materials.animations:
                script.materials.animations.append(inst)
                done += 1
    return done


def build_native_bed(shots, vo_dir, work_dir):
    """
    A4 草稿通道：real_clip 镜素材含音轨时，产出与整片逐镜对齐的**原声垫轨**。
    与 assemble_video 共享 real_clip.build_aligned_track（bed 模式）：
    有配音的镜只出"被配音 key duck 过的原声"（配音本身留在 voice_all 轨，避免双份），
    无配音的实拍镜原声顶上，其余镜静音占位保对齐。

    返回 real_segs：{shot_id -> (media, start, cdur)}。real_clip 镜的画面轨直接挂
    **视频片段**（入出点用 source_timerange），否则画面停在抽帧静帧、原声却在动，
    观感/时间源都割裂。无任何 real_clip 时返回 {}，草稿保持原样（零变化）。
    """
    from real_clip import (real_clip_of, resolve_clip, probe_duration,
                           clip_span, probe_has_audio, build_aligned_track)
    shot_audio, real_segs = [], {}
    for pos, shot in enumerate(shots, 1):
        sid = shot.get("shot_id", pos)
        au = shot.get("audio") or {}
        vis = shot.get("visual") or {}
        dur = (au.get("duration_sec_actual") or au.get("duration_sec")
               or vis.get("duration_sec_estimate") or shot.get("duration_sec") or 3.0)
        native = None
        rc = real_clip_of(shot)
        if rc:
            media, why = resolve_clip(rc)
            nd = probe_duration(media) if media else 0
            if media and nd:
                start, cdur = clip_span(rc, nd)
                dur = cdur  # 实拍镜时长=画面原生（D3，与装配轨同一时间源）
                real_segs[sid] = (media, start, cdur)
                if probe_has_audio(media):
                    native = (media, start)
            else:
                print(f"⚠️  镜{sid}: 实拍素材未定位（{why or '探针失败'}），草稿回退静帧"
                      f"（real_clip 不循环，缺素材即无画面）", file=sys.stderr)
        vo = None
        if vo_dir:
            for cand in (f"shot_{sid:03d}.mp3", f"shot_{pos:03d}.mp3",
                         f"shot_{sid:03d}.wav"):
                p = os.path.join(vo_dir, cand)
                if os.path.exists(p):
                    vo = p
                    break
        shot_audio.append({"dur": float(dur), "native": native, "vo": vo})
    if not any(s["native"] for s in shot_audio):
        return None, real_segs   # 无原声可用：不产垫轨，但画面段仍要挂实拍
    n_native = sum(1 for s in shot_audio if s["native"])
    n_duck = sum(1 for s in shot_audio if s["native"] and s["vo"])
    print(f"🔊 A4 草稿原声垫轨：{n_native} 镜原声入线（其中 {n_duck} 镜按配音 ducking）")
    return build_aligned_track(shot_audio, work_dir, "bed", "native_mix.m4a"), real_segs



def create_draft(
    draft_name: str,
    draft_root: str,
    audio_path: str,
    srt_path: str,
    shots: list,
    images_dir: str,
    aspect_ratio: str = "9:16",
    native_mix: str = None,
    real_segs: dict = None,
    motion: dict = None,
):
    """
    创建剪映草稿（画布比例随项目走，不再写死 9:16）

    motion=None 时按账号观感契约取默认（storyboard_schema.motion_style）；
    传 `{"ken_burns": False, "transition": "", "subtitle_intro": ""}` 即完全不加动效。
    """
    try:
        from storyboard_schema import motion_style as _motion_style
        mo = motion if motion is not None else _motion_style({})
    except ImportError:
        mo = {"ken_burns": False, "transition": "", "subtitle_intro": ""}

    # 1. 创建草稿文件夹
    draft_folder = draft.DraftFolder(draft_root)
    if draft_folder.has_draft(draft_name):
        print(f"⚠️  草稿已存在: {draft_name}，将覆盖")
        draft_folder.remove(draft_name)

    # 画布比例（审计报告 P0-4：原写死 1080x1920，导致 3:4/16:9 项目无法出草稿）
    AR_CANVAS = {"9:16": (1080, 1920), "3:4": (1080, 1440),
                 "16:9": (1920, 1080), "1:1": (1080, 1080),
                 "4:3": (1440, 1080)}
    W, H = AR_CANVAS.get(aspect_ratio, (1080, 1920))
    if aspect_ratio not in AR_CANVAS:
        print(f"⚠️  未内置比例 {aspect_ratio}，回退 9:16（已内置：{list(AR_CANVAS)}）")
    script = draft_folder.create_draft(draft_name, width=W, height=H)
    print(f"✅ 草稿已创建: {draft_name}  画布 {W}x{H}（{aspect_ratio}）")

    # 2. 添加音频
    if os.path.exists(audio_path):
        audio_material = draft.AudioMaterial(audio_path)
        script.add_material(audio_material)
        duration_us = audio_material.duration  # 已经是微秒
        audio_segment = draft.AudioSegment(audio_material, draft.Timerange(0, duration_us))
        audio_track_ref = script.append_track(draft.TrackSpec(draft.TrackType.audio))
        script.add_segment(audio_segment, track=audio_track_ref)
        print(f"✅ 音频已添加: {audio_path}（{duration_us/1_000_000:.1f}s）")

    # 2.5 A4 原声垫轨：逐镜对齐的混音带（ducking 已在带内烘焙），独立音频轨、
    # 音量略降留剪映手动余量；无实拍原声时 native_mix=None，本段整体跳过。
    if native_mix and os.path.exists(native_mix):
        bed_material = draft.AudioMaterial(native_mix)
        script.add_material(bed_material)
        bed_dur_us = bed_material.duration
        bed_segment = draft.AudioSegment(bed_material, draft.Timerange(0, bed_dur_us),
                                         volume=0.8)
        bed_track_ref = script.append_track(draft.TrackSpec(draft.TrackType.audio,
                                                            name="原声垫轨"))
        script.add_segment(bed_segment, track=bed_track_ref)
        print(f"✅ 原声垫轨已添加（{bed_dur_us/1_000_000:.1f}s，volume=0.8）")

    # 3. 添加视频轨（图片素材作为视频片段）
    n_kb = n_tr = n_seg = 0
    if shots and os.path.exists(images_dir):
        video_track_ref = script.append_track(draft.TrackSpec(draft.TrackType.video))

        current_time_us = 0
        for pos, shot in enumerate(shots, 1):
            # 对齐 §2.1 分镜契约：镜号优先 shot_id，时长优先 audio.duration_sec_actual
            shot_index = shot.get("shot_id", shot.get("index", pos))
            au = shot.get("audio") or {}
            vis = shot.get("visual") or {}
            duration_sec = (au.get("duration_sec_actual")
                            or au.get("duration_sec")
                            or vis.get("duration_sec_estimate")
                            or shot.get("duration_sec") or 3.0)
            duration_sec = float(duration_sec)
            duration_us = int(duration_sec * 1_000_000)
            image_path = os.path.join(images_dir, f"shot_{shot_index:03d}.jpg")

            # A4/M2：real_clip 镜画面轨挂**真视频段**（入出点 source_timerange）。
            # 素材静音（volume=0）：原声由垫轨轨统一承担，避免双份。
            seg = (real_segs or {}).get(shot_index)
            if seg:
                media, src_start, cdur = seg
                duration_us = int(cdur * 1_000_000)
                v_material = draft.VideoMaterial(media)
                script.add_material(v_material)
                v_segment = draft.VideoSegment(
                    v_material,
                    draft.Timerange(current_time_us, duration_us),
                    source_timerange=draft.Timerange(int(src_start * 1_000_000), duration_us),
                    volume=0.0,
                    clip_settings=draft.ClipSettings(alpha=1.0),
                )
                # A2：实拍镜画面本身在动，只补镜间转场、不加运镜关键帧
                # （转场只加在"前面已有画面段"之后 —— 首段加转场等于凭空叠黑）
                if n_seg and apply_transition(v_segment, duration_us, mo):
                    n_tr += 1
                script.add_segment(v_segment, track=video_track_ref)
                n_seg += 1
                print(f"  镜头 {shot_index}: 实拍 {os.path.basename(media)}"
                      f"（{src_start:.1f}s–{src_start+cdur:.1f}s，静音由垫轨承担）")
                current_time_us += duration_us
                continue

            if os.path.exists(image_path):
                video_material = draft.VideoMaterial(image_path)
                script.add_material(video_material)
                # 图片时长设为镜头时长
                # 关键：start 必须用累计时间，否则所有片段堆在 0 点 → SegmentOverlap
                video_segment = draft.VideoSegment(
                    video_material,
                    draft.Timerange(current_time_us, duration_us),
                    clip_settings=draft.ClipSettings(alpha=1.0),
                )
                # A2：静帧镜加运镜（Ken Burns）+ 镜间转场 —— 必须在 add_segment 之前，
                # pyJD 是在 add_segment 时才把关键帧/转场登记进素材表。
                if apply_ken_burns(video_segment, duration_us, pos, mo):
                    n_kb += 1
                if n_seg and apply_transition(video_segment, duration_us, mo):
                    n_tr += 1
                script.add_segment(video_segment, track=video_track_ref)
                n_seg += 1
                print(f"  镜头 {shot_index}: {image_path}（{duration_sec}s）")
            else:
                print(f"  ⚠️  图片不存在: {image_path}")

            current_time_us += duration_us

    # 4. 导入 SRT 字幕
    n_intro = 0
    if os.path.exists(srt_path):
        try:
            script.import_srt(srt_path, track_name="字幕轨")
            n_intro = apply_subtitle_intro(script, mo)
            print(f"✅ 字幕已导入: {srt_path}"
                  + (f"（{n_intro} 条带「{mo.get('subtitle_intro')}」入场）" if n_intro else ""))
        except Exception as e:
            print(f"⚠️  字幕导入失败: {e}")

    if n_kb or n_tr:
        print(f"🎬 A2 观感: {n_kb} 镜运镜（Ken Burns 缩放 {mo.get('kb_scale')} / "
              f"横漂 {mo.get('kb_pan')}），{n_tr} 处镜间转场"
              f"「{mo.get('transition')}」{mo.get('transition_sec')}s")

    # 5. 保存草稿
    script.save()
    print(f"✅ 草稿已保存")

    # 6. Mac 版剪映修补（11.4.2）
    draft_dir = os.path.join(draft_root, draft_name)
    content_json = os.path.join(draft_dir, "draft_content.json")
    info_json = os.path.join(draft_dir, "draft_info.json")

    # 6.1 重命名 draft_content.json → draft_info.json
    if os.path.exists(content_json):
        os.rename(content_json, info_json)
        print("✅ 已重命名 draft_content.json → draft_info.json")

    # 6.2 修改 version 号
    if os.path.exists(info_json):
        import json
        with open(info_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["version"] = "400000.10.100"
        with open(info_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("✅ 已修改 version 号")

    print(f"✅ 草稿已保存到剪映草稿目录")
    return script


def apply_subtitle_style(draft_dir: str, storyboard: dict) -> int:
    """
    把账号字幕样式注入草稿（后处理）。

    为什么需要：pyJD 的 TextStyle **不支持描边（strokes）**，导入 SRT 后
    剪映里就是「无描边白字」。但草稿在被剪映打开前是**明文 JSON**，
    因此可由本函数直接改写文本素材的 content，注入 size / 描边 / 行距 / 垂直位置。
    样式契约见 storyboard_schema.DEFAULT_SUBTITLE_STYLE（数值取自用户真实草稿）。

    返回：改写成功的文本条数（0 表示无字幕或跳过）。
    """
    import json as _json
    info_json = os.path.join(draft_dir, "draft_info.json")
    if not os.path.exists(info_json):
        return 0
    try:
        from storyboard_schema import subtitle_style as _sts, shot_scale as _scale
        st = _sts(storyboard or {})
    except ImportError:
        print("⚠️  未找到 storyboard_schema，跳过字幕样式注入", file=sys.stderr)
        return 0

    with open(info_json, "r", encoding="utf-8") as f:
        data = _json.load(f)

    shots = (storyboard or {}).get("shots") or []
    # A1 之后一镜可能对应多条字幕（镜内按词边界断句），**不能再按序号 1:1 对镜**。
    # 字幕文本必是所在镜台词的子串，且顺序单调 → 用游标往前找即可确定归属。
    import re as _re

    def _norm(s):
        return _re.sub(r"[\s\W_]+", "", s or "", flags=_re.UNICODE)

    def _shot_text(sh):
        au = sh.get("audio") or {}
        return au.get("text") or sh.get("script_line") or ""

    shot_norm = [_norm(_shot_text(sh)) for sh in shots]
    cur = 0
    patched = 0
    for t in (data.get("materials") or {}).get("texts", []):
        raw = t.get("content")
        if not raw:
            continue
        try:
            c = _json.loads(raw)
        except Exception:
            continue
        seg = _norm(c.get("text") or "")
        j = cur
        while j < len(shot_norm) and (not seg or seg not in shot_norm[j]):
            j += 1
        if j >= len(shot_norm):
            j = min(cur, len(shots) - 1)   # 对不上就沿用当前镜，不猜
        else:
            cur = j
        # 逐镜字幕倍率（AI 可主动调整）：按字幕所属镜取
        sc = _scale(shots[j]) if shots else 1.0
        size = round(float(st["size"]) * sc, 2)
        for s in c.get("styles", []):
            s["size"] = size
            s["fill"] = {"alpha": 1.0, "content": {
                "render_type": "solid",
                "solid": {"alpha": 1.0, "color": st["color"]}}}
            s["strokes"] = ([{
                "width": st["stroke_width"], "alpha": 1.0,
                "content": {"render_type": "solid",
                            "solid": {"alpha": 1.0, "color": st["stroke_color"]}}}]
                if st.get("stroke_width") else [])
        t["content"] = _json.dumps(c, ensure_ascii=False)
        t["line_spacing"] = st["line_spacing"]
        t["line_max_width"] = st["line_max_width"]

        # ★ 关键：剪映实际生效的描边/字号在素材**顶层**字段，
        #   content.styles[].strokes 剪映不认（实测：只设 strokes 时描边不显示）。
        #   以下字段名与取值均取自用户真实草稿中「剪映自己生成的描边文本」。
        def _hex(rgb):
            return "#" + "".join(f"{max(0, min(255, int(round(float(x) * 255)))):02x}"
                                 for x in rgb)
        t["font_size"] = size
        t["text_color"] = _hex(st["color"])
        t["border_width"] = float(st["stroke_width"] or 0)
        t["border_color"] = _hex(st["stroke_color"])
        t["border_alpha"] = 1
        # 剪映自身"白字+描边"文本的 check_flag 为 63（pyJD 默认给 7）
        t["check_flag"] = 63
        patched += 1

    for tr in data.get("tracks", []):
        if tr.get("type") != "text":
            continue
        for seg in tr.get("segments", []):
            clip = seg.setdefault("clip", {})
            tf = clip.setdefault("transform", {"x": 0.0, "y": 0.0})
            tf["y"] = st["transform_y"]
            tf.setdefault("x", 0.0)

    if patched:
        with open(info_json, "w", encoding="utf-8") as f:
            _json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 已注入字幕样式: size={st['size']} "
              f"描边={st['stroke_width']} 行距={st['line_spacing']} "
              f"→ {patched} 条字幕")
    return patched


def main():
    parser = argparse.ArgumentParser(description="剪映草稿生成器")
    parser.add_argument("--draft-name", required=True, help="草稿名称")
    parser.add_argument("--draft-root",
                        default="~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft",
                        help="剪映草稿根目录")
    parser.add_argument("--audio", required=True, help="音频文件路径")
    parser.add_argument("--srt", required=True, help="SRT 字幕文件路径")
    parser.add_argument("--storyboard", help="分镜 JSON 文件路径")
    parser.add_argument("--images-dir", help="图片素材目录")
    parser.add_argument("--aspect-ratio",
                        help="画布比例：9:16 / 3:4 / 16:9 / 1:1 / 4:3；"
                             "默认取分镜，再取项目配置")
    parser.add_argument("--no-subtitle-style", action="store_true",
                        help="不注入账号字幕样式（保留剪映默认无描边样式）")
    parser.add_argument("--vo-dir",
                        help="逐镜配音目录（含 shot_NNN.mp3），A4 原声 ducking 的 key 来源")
    parser.add_argument("--no-native-audio", action="store_true",
                        help="A4 关闭实拍原声垫轨")
    parser.add_argument("--out-dir",
                        help="把原声垫轨另存一份到该目录（产物留档，便于复查）")
    parser.add_argument("--no-polish", action="store_true",
                        help="A2 关闭观感动效（运镜/镜间转场/字幕入场），回到裸草稿")
    args = parser.parse_args()

    draft_root = os.path.expanduser(args.draft_root)
    audio_path = os.path.expanduser(args.audio)
    srt_path = os.path.expanduser(args.srt)

    # 读取分镜
    shots = []
    storyboard = {}
    if args.storyboard:
        storyboard_path = os.path.expanduser(args.storyboard)
        with open(storyboard_path, "r", encoding="utf-8") as f:
            storyboard = json.load(f)
            shots = storyboard.get("shots", [])
        print(f"📋 分镜: {len(shots)} 个镜头")

    images_dir = os.path.expanduser(args.images_dir) if args.images_dir else None

    # A4 原声垫轨（含实拍镜才产出；纯口播/无 real_clip → (None, {}) 草稿零变化）
    native_mix, real_segs = None, {}
    if shots and not args.no_native_audio:
        import tempfile
        work = tempfile.mkdtemp(prefix="draft_a4_")
        try:
            native_mix, real_segs = build_native_bed(
                shots, os.path.expanduser(args.vo_dir) if args.vo_dir else None, work)
            # 临时目录随后即删：草稿引用**留档件**，非临时件
            if native_mix and args.out_dir:
                os.makedirs(os.path.expanduser(args.out_dir), exist_ok=True)
                keep = os.path.join(os.path.expanduser(args.out_dir), "native_mix.m4a")
                shutil.copyfile(native_mix, keep)
                native_mix = keep
                print(f"📀 原声垫轨留档: {keep}")
        except RuntimeError as e:
            print(f"❌ A4 原声垫轨生成失败: {e}", file=sys.stderr)
            raise SystemExit(1)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    # 画布比例：命令行 > 分镜 > 项目配置 > 默认 9:16
    ar = args.aspect_ratio or (storyboard or {}).get("aspect_ratio")
    if not ar:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from providers import load_project_config
            ar = (load_project_config((storyboard or {}).get("project_id"))
                  .get("video") or {}).get("aspect_ratio")
        except Exception:
            ar = None
    ar = ar or "9:16"

    # A2 观感：分镜 style.motion / 项目配置 motion > 账号默认；--no-polish 一键全关
    OFF = {"ken_burns": False, "transition": "", "subtitle_intro": ""}
    motion = OFF
    if not args.no_polish:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from storyboard_schema import motion_style
            motion = motion_style(storyboard)
        except ImportError:
            print("⚠️  未找到 storyboard_schema，跳过动效", file=sys.stderr)

    # 创建草稿
    create_draft(
        aspect_ratio=ar,
        draft_name=args.draft_name,
        draft_root=draft_root,
        audio_path=audio_path,
        srt_path=srt_path,
        shots=shots,
        images_dir=images_dir,
        native_mix=native_mix,
        real_segs=real_segs,
        motion=motion,
    )

    # 后处理：注入账号字幕样式（pyJD 不支持描边，故在明文 JSON 上改写）
    if not args.no_subtitle_style:
        apply_subtitle_style(os.path.join(draft_root, args.draft_name),
                             storyboard)


if __name__ == "__main__":
    main()
