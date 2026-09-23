#!/usr/bin/env python3
"""
分镜契约（storyboard schema）单一权威定义 + 校验器

为什么存在（§16.4 R3）：
  §2.1 的契约此前只存在于文档里，导致实现漂移——
  generate_draft.py 曾用 `index`/`duration_sec`，而契约是 `shot_id`/`audio.duration_sec_actual`，
  结果图片找不到、时长全默认 3s。把契约固化成代码，可让**所有消费方共用同一份判定**。

用法：
    from storyboard_schema import validate
    issues = validate(sb)            # 返回 [{"level","path","msg"}]

约定：level = "error"（阻断）/ "warn"（可继续）
"""
from typing import Any, Dict, List

VALID_PLATFORM = {"douyin", "xiaohongshu", "weixin", "web", "bilibili"}
VALID_ASPECT = {"9:16", "3:4", "16:9", "1:1"}
VALID_VISUAL_TYPE = {"ai_image", "ai_video", "broll", "static_image", "real_clip"}
SHOT_LANGUAGE_KEYS = ("shot_size", "focal_length", "depth_of_field",
                      "lighting", "color_temperature", "camera_movement")
# platform → 期望比例（§4.5 铁律：禁止默认 16:9）
PLATFORM_ASPECT = {"douyin": "9:16", "xiaohongshu": "3:4",
                   "weixin": "9:16", "web": "16:9"}

# ── 账号字幕样式契约（单一来源，两通道共用）──────────────────────────
# 数值由用户真实草稿「7月15日」的字幕样式实测提取（画布 1440x1920）：
#   size 8 / 白字 / 黑描边 width 0.06 / line_spacing 0.2 / line_max_width 0.82 / y -0.7
# 说明：pyJD 的 TextStyle 不支持 strokes，故草稿侧由 generate_draft.py
#      在生成后**直接改写明文 JSON** 注入描边（剪映打开前草稿是明文）。
DEFAULT_SUBTITLE_STYLE = {
    "size": 8,                      # 剪映文本字号（内部单位）
    "color": [1.0, 1.0, 1.0],       # 字色（RGB 0-1）
    "stroke_width": 0.06,           # 描边宽度；0 = 无描边
    "stroke_color": [0.0, 0.0, 0.0],
    "line_spacing": 0.2,
    "line_max_width": 0.82,
    "transform_y": -0.55,           # 垂直位置（越负越靠下；-0.7 偏下，用户反馈太靠下）
    "font_size_px": 48,             # ffmpeg/PIL 通道的像素字号（用户按标定图选定 48px）
}


def source_ref(shot):
    """
    安全读取 shot.visual.source_ref —— 恒返回 dict。
    ⚠️ LLM 生成的分镜常把 source_ref 写成字符串（如"良渚古城遗址航拍素材"），
    直接 `(vis.get("source_ref") or {}).get(...)` 会 AttributeError 崩掉整条管线。
    """
    vis = (shot or {}).get("visual") or {}
    ref = vis.get("source_ref")
    return ref if isinstance(ref, dict) else {}


def ensure_source_ref(shot):
    """返回（必要时创建并挂回）shot.visual.source_ref 的 dict（写回用）"""
    vis = shot.setdefault("visual", {})
    ref = vis.get("source_ref")
    if not isinstance(ref, dict):
        ref = {}
        vis["source_ref"] = ref
    return ref


def subtitle_style(sb):
    """
    取字幕样式，优先级：分镜 style.subtitle > 项目配置 subtitle > 默认值

    修复（审计报告 P0-3）：此前**只读分镜与默认值**，项目配置里的 subtitle 段
    写了却没人读 ——「配置了但不生效」比没配置更误导，故在此补上项目配置这一层。
    """
    s = dict(DEFAULT_SUBTITLE_STYLE)

    # 项目配置（project_configs/<project_id>.json 的 subtitle 段）
    try:
        import os
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from providers import load_project_config
        pc = (load_project_config(sb.get("project_id")).get("subtitle") or {})
        s.update({k: v for k, v in pc.items()
                  if not str(k).startswith("_") and v is not None})
    except Exception:
        pass

    # 分镜显式配置（最高优先级）
    user = ((sb.get("style") or {}).get("subtitle") or {})
    s.update({k: v for k, v in user.items() if v is not None})
    return s


# ── 逐镜字幕倍率（让 AI 主动调整字号）────────────────────────────────
# 设计：LLM 在生成分镜时为每镜输出 subtitle_scale（默认 1.0）：
#   钩子/金句/情绪高点 → 1.15~1.3（放大强调）
#   信息密集长句       → 0.85~0.9（缩小，少遮画面）
# 两通道各自乘上该倍率：剪映侧改写文本素材 size；ffmpeg 侧改 PIL 像素字号。
SUBTITLE_SCALE_MIN, SUBTITLE_SCALE_MAX = 0.7, 1.6

# 中文 TTS 语速经验值（字/秒）。实测：307 字 → 70.92s（MiniMax speech-2.8-hd, speed 1.0）
CHARS_PER_SEC = 4.3


def shot_scale(shot):
    """取某镜的字幕倍率（带上下限钳制）"""
    v = shot.get("subtitle_scale")
    try:
        v = float(v) if v is not None else 1.0
    except (TypeError, ValueError):
        return 1.0
    return max(SUBTITLE_SCALE_MIN, min(SUBTITLE_SCALE_MAX, v))


# ── 草稿观感契约（A2：运镜 / 转场 / 字幕入场）────────────────────────
# 只作用于**剪映草稿通道**：ffmpeg 直出通道的运镜早已在 assemble_video 里（KenBurns）。
# 数值保守：缩放 8%、漂移 3% 画布，观感"在动"但不晕；转场只在镜间 0.3s 叠化。
DEFAULT_MOTION_STYLE = {
    "ken_burns": True,          # 图片静镜的运镜（实拍视频镜本身在动，不加）
    "kb_scale": 1.08,           # 镜内缩放终值（1.0 = 不动）
    "kb_pan": 0.03,             # 横向漂移幅度（占画布宽比例，逐镜左右交替）
    "transition": "叠化",        # 镜间转场名（须匹配剪映转场名；"" = 不加）
    "transition_sec": 0.3,
    "subtitle_intro": "渐显",   # 字幕入场动画名（须匹配剪映文本入场名；"" = 不加）
    "subtitle_intro_sec": 0.25,
}


def motion_style(sb):
    """取草稿运观感配置，优先级同 subtitle_style：分镜 style.motion > 项目配置 motion > 默认"""
    s = dict(DEFAULT_MOTION_STYLE)
    try:
        import os
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from providers import load_project_config
        pc = (load_project_config((sb or {}).get("project_id")).get("motion") or {})
        s.update({k: v for k, v in pc.items()
                  if not str(k).startswith("_") and v is not None})
    except Exception:
        pass
    user = ((sb or {}).get("style") or {}).get("motion") or {}
    s.update({k: v for k, v in user.items() if v is not None})
    return s


def _real_clip_of(shot):
    """real_clip 助手不可导入时的纯 dict 兜底（校验器不能被解析层拖崩）"""
    rc = ((shot or {}).get("visual") or {}).get("real_clip")
    return rc if isinstance(rc, dict) and (rc.get("path") or rc.get("eagle_id")) else None


def validate(sb: Dict[str, Any], require_durations: bool = False) -> List[Dict[str, str]]:
    """
    校验分镜 JSON 是否符合 §2.1 契约。

    require_durations=True 时，要求每镜已有 audio.duration_sec_actual
    （用于配音之后、出片之前的阶段校验）。
    """
    issues: List[Dict[str, str]] = []

    def err(path, msg):
        issues.append({"level": "error", "path": path, "msg": msg})

    def warn(path, msg):
        issues.append({"level": "warn", "path": path, "msg": msg})

    if not isinstance(sb, dict):
        err("$", "分镜根节点必须是对象")
        return issues

    # 顶层
    for k in ("project_id", "shots"):
        if k not in sb:
            (err if k == "shots" else warn)(k, f"缺少字段 {k}")
    if not sb.get("project_id"):
        warn("project_id", "为空（影响项目级配置：音色/字幕样式/BGM）")

    platform = sb.get("platform")
    if platform and platform not in VALID_PLATFORM:
        warn("platform", f"未知平台 {platform!r}，合法值 {sorted(VALID_PLATFORM)}")

    # 视频类型（v4.0：口播/品牌/混剪；brand 提示横竖屏）
    content_type = sb.get("content_type")
    if content_type and content_type not in ("koubo", "brand", "mixcut"):
        warn("content_type", f"未知视频类型 {content_type!r}，合法值 koubo/brand/mixcut")
    elif content_type == "brand" and sb.get("aspect_ratio") == "9:16":
        warn("content_type", "brand 品牌片通常 16:9；当前 9:16，请确认是否竖屏投放")

    aspect = sb.get("aspect_ratio")
    if not aspect:
        err("aspect_ratio", "缺失——§4.5 铁律要求显式声明，禁止默认 16:9")
    else:
        if aspect not in VALID_ASPECT:
            err("aspect_ratio", f"非法比例 {aspect!r}，合法值 {sorted(VALID_ASPECT)}")
        expect = PLATFORM_ASPECT.get(platform)
        if expect and aspect != expect:
            err("aspect_ratio", f"与平台不符：{platform} 应为 {expect}，实际 {aspect}")

    # 音色
    voice = sb.get("voice") or {}
    if not voice.get("voice_id"):
        warn("voice.voice_id", "缺失（将回落到默认音色）")

    # 字幕样式（可选；缺省用 DEFAULT_SUBTITLE_STYLE）
    st = (sb.get("style") or {}).get("subtitle")
    if st is not None:
        if not isinstance(st, dict):
            err("style.subtitle", "必须是对象")
        else:
            if "size" in st and not (isinstance(st["size"], (int, float))
                                     and st["size"] > 0):
                err("style.subtitle.size", "必须为正数")
            for ck in ("color", "stroke_color"):
                if ck in st and not (isinstance(st[ck], list) and len(st[ck]) == 3):
                    err(f"style.subtitle.{ck}", "必须是长度 3 的 RGB 数组")
            if "font_size_px" in st and not (isinstance(st["font_size_px"], (int, float))
                                             and st["font_size_px"] > 0):
                err("style.subtitle.font_size_px", "必须为正数")

    # 分镜
    shots = sb.get("shots")
    if not isinstance(shots, list) or not shots:
        err("shots", "必须是非空数组")
        return issues

    seen_ids = set()
    for i, shot in enumerate(shots):
        p = f"shots[{i}]"
        if not isinstance(shot, dict):
            err(p, "必须是对象"); continue

        sid = shot.get("shot_id", shot.get("index"))
        if sid is None:
            err(f"{p}.shot_id", "缺失（契约字段为 shot_id）")
        elif sid in seen_ids:
            err(f"{p}.shot_id", f"重复：{sid}")
        else:
            seen_ids.add(sid)

        au = shot.get("audio") or {}
        vis = shot.get("visual") or {}
        rc_raw = vis.get("real_clip")
        rc = _real_clip_of(shot)
        text = au.get("text") or shot.get("script_line")
        if not text:
            # 实拍镜允许无台词（纯实拍段/原声段，混剪 M2）；其余镜维持硬约束
            (warn if rc else err)(f"{p}.audio.text",
                                  "缺失（且无 script_line 兜底）" if not rc
                                  else "缺失（实拍镜可为空台词，仅提醒）")

        if require_durations and not au.get("duration_sec_actual") and not rc:
            err(f"{p}.audio.duration_sec_actual",
                "缺失——出片前必须回填 TTS 实测时长（§4.2 唯一时间源）")
        if require_durations and rc and not au.get("duration_sec_actual"):
            # 实拍镜时间源=画面原生时长（D3），配音时长不适用
            pass

        sc = shot.get("subtitle_scale")
        if sc is not None:
            if not (isinstance(sc, (int, float))
                    and SUBTITLE_SCALE_MIN <= sc <= SUBTITLE_SCALE_MAX):
                warn(f"{p}.subtitle_scale",
                     f"建议在 {SUBTITLE_SCALE_MIN}~{SUBTITLE_SCALE_MAX} 之间，"
                     f"实际 {sc}（超界会被钳制）")

        vtype = vis.get("type")
        if vtype and vtype not in VALID_VISUAL_TYPE:
            warn(f"{p}.visual.type", f"未知类型 {vtype!r}，合法值 {sorted(VALID_VISUAL_TYPE)}")
        if not vis.get("prompt") and vtype in ("ai_image", "ai_video"):
            warn(f"{p}.visual.prompt", f"{vtype} 建议提供 prompt")

        # 实拍片段契约（混剪 M2，D2 一镜一段）：对象、path/eagle_id 至少其一、start<end
        if rc_raw is not None:
            if not isinstance(rc_raw, dict):
                err(f"{p}.visual.real_clip", "必须是对象 {path|eagle_id, start?, end?}")
            else:
                if not (rc_raw.get("path") or rc_raw.get("eagle_id")):
                    err(f"{p}.visual.real_clip", "必须有 path 或 eagle_id（素材定位）")
                sv, ev = rc_raw.get("start"), rc_raw.get("end")
                bad = False
                for tag, v in (("start", sv), ("end", ev)):
                    if v is None:
                        continue
                    try:
                        if float(v) < 0:
                            bad = True
                    except (TypeError, ValueError):
                        bad = True
                    if bad:
                        err(f"{p}.visual.real_clip.{tag}", f"必须为 ≥0 的秒数，实际 {v!r}")
                        break
                if not bad and sv is not None and ev is not None and float(ev) <= float(sv):
                    err(f"{p}.visual.real_clip.end", f"end({ev}) 必须大于 start({sv})")
                if not bad and (rc_raw.get("path") or rc_raw.get("eagle_id")):
                    try:
                        from real_clip import resolve_clip, probe_duration
                        media, why = resolve_clip(rc_raw)
                        if not media:
                            # Eagle 离线不等于数据错误 → warn 不阻断闸（装配/QC 侧硬失败）
                            warn(f"{p}.visual.real_clip", f"素材暂无法定位：{why}")
                        elif probe_duration(media) is None:
                            warn(f"{p}.visual.real_clip", f"{media} 探针失败（非视频文件？）")
                    except ImportError:
                        pass

        sl = vis.get("shot_language")
        if sl is None:
            warn(f"{p}.visual.shot_language", "缺失（六字段用于镜头语言一致性）")
        elif isinstance(sl, dict):
            missing = [k for k in SHOT_LANGUAGE_KEYS if not sl.get(k)]
            if missing:
                warn(f"{p}.visual.shot_language", f"缺字段 {missing}")

        # source_ref 双值（§2.1）
        ref = vis.get("source_ref")
        if ref is not None and not (isinstance(ref, dict)
                                    and ("eagle_id" in ref or "path" in ref)):
            warn(f"{p}.visual.source_ref",
                 "应为 {eagle_id, path} 双值对象（§2.1/§13）")

    # ── 时长前置估算（真实选题实测：中文 TTS 约 4.3 字/秒）──
    # 目的：在**配音之前**就发现"文案长度与目标时长不匹配"，
    #       而不是花完 TTS/生图额度才在成片阶段发现超标（v2.2 §21.5 问题1）。
    target = sb.get("duration_target_sec")
    if target:
        chars = sum(len((s.get("audio") or {}).get("text")
                        or s.get("script_line") or "") for s in shots
                    if isinstance(s, dict))
        est = chars / CHARS_PER_SEC
        dev = (est - float(target)) / float(target)
        if abs(dev) > 0.10:
            warn("duration_target_sec",
                 f"文案 {chars} 字 ≈ {est:.0f}s，与目标 {target}s 偏差 {dev*100:+.1f}%"
                 f"（超 ±10%）。建议调整文案长度或改 duration_target_sec")

    return issues


def summarize(issues: List[Dict[str, str]]) -> str:
    e = sum(1 for i in issues if i["level"] == "error")
    w = sum(1 for i in issues if i["level"] == "warn")
    return f"{e} error / {w} warn"


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print("用法: python storyboard_schema.py <storyboard.json> [--require-durations]")
        sys.exit(2)
    sb = json.load(open(sys.argv[1], encoding="utf-8"))
    issues = validate(sb, require_durations="--require-durations" in sys.argv)
    for it in issues:
        mark = "❌" if it["level"] == "error" else "⚠️"
        print(f"{mark} {it['path']}: {it['msg']}")
    print(f"\n{summarize(issues)}")
    sys.exit(1 if any(i["level"] == "error" for i in issues) else 0)
