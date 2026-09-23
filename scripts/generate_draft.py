#!/usr/bin/env python3
"""
剪映草稿生成器 - 从分镜 JSON + SRT + 音频生成剪映草稿
输入：分镜 JSON、音频文件、SRT 字幕、图片素材目录
输出：剪映草稿（放在剪映草稿目录里）
"""
import argparse
import json
import os
import sys

import pyJianYingDraft as draft


def create_draft(
    draft_name: str,
    draft_root: str,
    audio_path: str,
    srt_path: str,
    shots: list,
    images_dir: str,
    aspect_ratio: str = "9:16",
):
    """
    创建剪映草稿（画布比例随项目走，不再写死 9:16）
    """
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

    # 3. 添加视频轨（图片素材作为视频片段）
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
                script.add_segment(video_segment, track=video_track_ref)
                print(f"  镜头 {shot_index}: {image_path}（{duration_sec}s）")
            else:
                print(f"  ⚠️  图片不存在: {image_path}")

            current_time_us += duration_us

    # 4. 导入 SRT 字幕
    if os.path.exists(srt_path):
        try:
            script.import_srt(srt_path, track_name="字幕轨")
            print(f"✅ 字幕已导入: {srt_path}")
        except Exception as e:
            print(f"⚠️  字幕导入失败: {e}")

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
    patched = 0
    for idx, t in enumerate((data.get("materials") or {}).get("texts", [])):
        raw = t.get("content")
        if not raw:
            continue
        try:
            c = _json.loads(raw)
        except Exception:
            continue
        # 逐镜字幕倍率（AI 可主动调整）：SRT 条目顺序 ↔ 分镜顺序
        sc = _scale(shots[idx]) if idx < len(shots) else 1.0
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

    # 创建草稿
    create_draft(
        aspect_ratio=ar,
        draft_name=args.draft_name,
        draft_root=draft_root,
        audio_path=audio_path,
        srt_path=srt_path,
        shots=shots,
        images_dir=images_dir,
    )

    # 后处理：注入账号字幕样式（pyJD 不支持描边，故在明文 JSON 上改写）
    if not args.no_subtitle_style:
        apply_subtitle_style(os.path.join(draft_root, args.draft_name),
                             storyboard)


if __name__ == "__main__":
    main()
