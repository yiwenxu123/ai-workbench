#!/usr/bin/env python3
"""
QC 粗剪自检门禁（v5.0 补缺环：业界共识「a gate, not a reminder」）

定位：
  run_pipeline 的最后一道机器门禁。降级直出 mp4 产出后、状态推进到
  「待终剪(draft_ready)」之前运行；有 error 级问题即阻断（退出码 2），
  任务停在 qc_failed，由内容中心 workbench-actions 下发修复动作。
  剪映草稿通道（人工终剪导出）无粗剪可检时只做中间产物软检。

检查级别：
  error   阻断 —— 粗剪不可交付（无音轨/比例错/时长对不上/素材缺失…）
  warning 不阻断 —— 建议人工关注（黑场/响度偏低/字幕条数对不齐…）

用法：
  qc_checks.py --storyboard sb.json --out-dir out/ [--video out/x.mp4] \
               [--report out/qc_report.json] [--json] \
               [--no-voiceover] [--no-subtitles]
退出码：0=通过（可能含 warning）；2=有 error；1=自检本身异常（缺 ffprobe 等）

类型口径（v5.1 P3-2）：`--no-voiceover` / `--no-subtitles` 供无配音类型线（混剪）、
无字幕类型线（品牌/混剪）使用，由 run_pipeline 按内容中心类型目录下传；
默认（都不传）= 口播口径，行为与历史一致。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

# ── 阈值（集中管理，随验收口径调整只改这里）──────────────────────────
THRESHOLDS = {
    "audio_duration_tolerance": 0.6,   # 回填时长 vs mp3 实测（秒）
    "srt_start_tolerance": 0.6,        # 首条字幕起点（秒）
    "srt_end_vs_audio": 2.0,           # 末条字幕 vs 整段配音（秒，软检）
    "video_end_vs_srt": 3.0,           # 粗剪时长 vs 末条字幕（秒，硬检：尾部黑场/音画错位）
    "black_min_duration": 0.5,         # 连续黑场 ≥ 此值记 warning（秒）
    "black_edge_ignore": 0.5,          # 片头/片尾此范围内的黑场视为正常转场（秒）
    "mean_volume_min": -35.0,          # 平均响度下限（dBFS，过低听不清）
    "mean_volume_max": -5.0,           # 平均响度上限（过高易削波）
    "ffprobe_timeout": 20,
    "ffmpeg_timeout": 90,
}

ASPECT_TO_WH = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
    "3:4": (1080, 1440),
}


def _fid(level: str, check: str, message: str, **detail: Any) -> Dict[str, Any]:
    """构造一条检查结果：{level, check, message[, detail]}。"""
    d: Dict[str, Any] = {"level": level, "check": check, "message": message}
    if detail:
        d["detail"] = detail
    return d


# ── ffprobe / ffmpeg 封装（超时与缺失都显式建模，不静默吞）─────────────

def _run(cmd: List[str], timeout: int) -> Tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return 127, "", f"命令不存在: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"超时（{timeout}s）: {' '.join(cmd[:2])}"


def ffprobe_media(path: str) -> Optional[Dict[str, Any]]:
    """返回 {duration, width, height, has_video, has_audio}；ffprobe 不可用返回 None。"""
    code, out, err = _run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,width,height", "-of", "json", path],
        THRESHOLDS["ffprobe_timeout"],
    )
    if code != 0:
        return None
    data = json.loads(out)
    streams = data.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {
        "duration": float((data.get("format") or {}).get("duration") or 0.0),
        "width": int((v or {}).get("width") or 0),
        "height": int((v or {}).get("height") or 0),
        "has_video": v is not None,
        "has_audio": a is not None,
    }


def probe_duration(path: str) -> Optional[float]:
    """音频/图片视频通用的时长探测（配音 mp3 时长核对用）。"""
    code, out, _ = _run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        THRESHOLDS["ffprobe_timeout"],
    )
    if code != 0:
        return None
    try:
        return float(out.strip())
    except ValueError:
        return None


def detect_black_segments(path: str) -> List[Tuple[float, float]]:
    """黑场段（秒）。解析 ffmpeg blackdetect 的 stderr。"""
    code, _, err = _run(
        ["ffmpeg", "-hide_banner", "-i", path,
         "-vf", f"blackdetect=d={THRESHOLDS['black_min_duration']}:pix_th=0.10",
         "-an", "-f", "null", "-"],
        THRESHOLDS["ffmpeg_timeout"],
    )
    if code != 0 and "blackdetect" not in err:
        return []
    segs: List[Tuple[float, float]] = []
    for m in re.finditer(r"black_start:([\d.]+)\S*\s+black_end:([\d.]+)", err):
        segs.append((float(m.group(1)), float(m.group(2))))
    return segs


def detect_mean_volume(path: str) -> Optional[float]:
    """平均响度 dBFS（volumedetect）。"""
    code, _, err = _run(
        ["ffmpeg", "-hide_banner", "-i", path, "-af", "volumedetect",
         "-f", "null", "-"],
        THRESHOLDS["ffmpeg_timeout"],
    )
    if code != 0 and "mean_volume" not in err:
        return None
    m = re.search(r"mean_volume:\s*(-?[\d.]+)\s*dB", err)
    return float(m.group(1)) if m else None


# ── SRT 最小解析（不引第三方依赖）────────────────────────────────────

_SRT_TIME = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")


def _srt_ts(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0


def parse_srt(path: str) -> List[Tuple[float, float, str]]:
    """返回 [(start, end, text), ...]，按文件顺序。"""
    if not os.path.exists(path):
        return []
    entries: List[Tuple[float, float, str]] = []
    # utf-8-sig 兼容带 BOM 的 SRT（部分 TTS 工具会写 BOM）
    with open(path, encoding="utf-8-sig") as f:
        content = f.read()
    blocks = re.split(r"\n\s*\n", content.strip())
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        time_line = next((ln for ln in lines if "-->" in ln), None)
        if not time_line:
            continue
        m = _SRT_TIME.search(time_line)
        if not m:
            continue
        g = m.groups()
        entries.append((_srt_ts(*g[:4]), _srt_ts(*g[4:]), ""))
    return entries


# ── 检查实现 ──────────────────────────────────────────────────────────

def check_intermediates(sb: Dict[str, Any], out: str, vo_dir: str, img_dir: str,
                        srt_path: str, expect_voiceover: bool = True,
                        expect_subtitles: bool = True) -> List[Dict[str, Any]]:
    """A 类：中间产物完整性（任何通道都跑；缺素材=阻断）。

    expect_voiceover / expect_subtitles（v5.1 P3-2 类型线）：
      品牌片不要全片字幕、混剪不要配音也不要字幕 —— 这些类型线缺 mp3/SRT 是**正常**的。
      仍照口播口径检查会让它们永远过不了 QC（每次都被判 error），故由 run_pipeline 按
      类型目录下传；两个参数默认 True = 历史行为不变（口播不受影响）。
    """
    findings: List[Dict[str, Any]] = []
    shots = sb.get("shots") or []

    # 1) 每镜配音文件 + 回填时长与实测一致
    missing_vo: List[int] = []
    dur_mismatch: List[str] = []
    if not expect_voiceover:
        # 无配音类型线：mp3 与时长回填都不检查（时长来自分镜的 duration_sec）
        pass
    else:
        for i, shot in enumerate(shots, 1):
            sid = int(shot.get("shot_id", i))
            p = os.path.join(vo_dir, f"shot_{sid:03d}.mp3")
            if not os.path.exists(p):
                missing_vo.append(sid)
                continue
            actual = (shot.get("audio") or {}).get("duration_sec_actual")
            measured = probe_duration(p)
            if actual and measured is not None:
                if abs(float(actual) - measured) > THRESHOLDS["audio_duration_tolerance"]:
                    dur_mismatch.append(f"镜{sid}:回填{float(actual):.2f}s/实测{measured:.2f}s")
        if missing_vo:
            findings.append(_fid("error", "voiceover", f"缺 {len(missing_vo)} 镜配音文件", shots=missing_vo))
        if dur_mismatch:
            findings.append(_fid("warning", "voiceover-duration",
                                 f"{len(dur_mismatch)} 镜回填时长与 mp3 实测不符（字幕可能错位）",
                                 samples=dur_mismatch[:5]))

    # 2) 每镜图片（优先信分镜 source_ref/image_path，回退 shots/shot_XXX.jpg）
    missing_img: List[int] = []
    placeholder_shots: List[int] = []
    for i, shot in enumerate(shots, 1):
        sid = int(shot.get("shot_id", i))
        visual = shot.get("visual") or {}
        sr = visual.get("source_ref") or {}
        is_placeholder = bool(visual.get("placeholder") or (isinstance(sr, dict) and sr.get("placeholder")))
        ref = (sr.get("path") if isinstance(sr, dict) else None) or visual.get("image_path")
        candidates = [ref] if ref else []
        for ext in (".jpg", ".png", ".webp", ".mp4"):
            candidates.append(os.path.join(img_dir, f"shot_{sid:03d}{ext}"))
        if not any(c and os.path.exists(c) for c in candidates):
            missing_img.append(sid)
        elif is_placeholder:
            placeholder_shots.append(sid)
    if missing_img:
        findings.append(_fid("error", "shots", f"缺 {len(missing_img)} 镜画面素材", shots=missing_img))
    # v5.1：占位图守卫。test 档允许（流程验证用，warning 提醒不可交付）；
    # prod 档出现占位图=生产事故风险，error 阻断，防止占位画面流到终剪/发布。
    if placeholder_shots:
        is_test = os.environ.get("VIDEO_PROFILE") == "test"
        if is_test:
            findings.append(_fid("warning", "placeholder-shots",
                                 f"{len(placeholder_shots)} 镜为本地占位图（¥0 开发档产物，不可交付；"
                                 f"生产前需用真实生图重跑这些镜）", shots=placeholder_shots))
        else:
            findings.append(_fid("error", "placeholder-shots",
                                 f"{len(placeholder_shots)} 镜仍是占位图，禁止进入终剪/发布"
                                 f"（用 --profile prod 对这些镜重跑生图：--shots {','.join(map(str, placeholder_shots))}）",
                                 shots=placeholder_shots))

    # 2b) 实拍镜（混剪 M2 / 审计 A3 盲区补齐）：素材必须真能解析、剪辑点必须落带内。
    # 此前"视频素材只查存在性"——文件在但带长/入出点错，装配阶段才炸（或静默出废片）。
    try:
        from real_clip import real_clip_of, resolve_clip, probe_duration, clip_span
        _has_rc = True
    except ImportError:
        _has_rc = False
    if _has_rc:
        rc_bad: List[str] = []
        for i, shot in enumerate(shots, 1):
            sid = int(shot.get("shot_id", i))
            rcl = real_clip_of(shot)
            if not rcl:
                continue
            media, why = resolve_clip(rcl)
            if not media:
                rc_bad.append(f"镜{sid}: {why}")
                findings.append(_fid("error", "real-clip",
                                     f"实拍镜 {sid} 素材无法定位：{why}", shots=[sid]))
                continue
            native = probe_duration(media)
            if not native:
                findings.append(_fid("error", "real-clip",
                                     f"实拍镜 {sid} 素材探针失败（非视频文件？）", shots=[sid]))
                continue
            sv = float(rcl.get("start") or 0)
            ev = rcl.get("end")
            out_of_range = sv >= native or (ev is not None and float(ev) > native + 0.5)
            if out_of_range:
                findings.append(_fid("error", "real-clip-cut",
                                     f"镜{sid} 剪辑点越界：入点{sv:.1f}s/出点{ev}"
                                     f" vs 素材带长 {native:.1f}s", shots=[sid]))
            else:
                _, du = clip_span(rcl, native)
                declared = (shot.get("audio") or {}).get("duration_sec") or shot.get("duration_sec")
                if declared and abs(float(declared) - du) > max(1.5, 0.5 * du):
                    findings.append(_fid("warning", "real-clip-duration",
                                         f"镜{sid} 申报时长 {declared}s 与画面原生 {du:.1f}s 偏差大"
                                         f"（装配以画面为时间源，字幕/节奏请按原生核对）",
                                         shots=[sid]))
        if rc_bad:
            print("   实拍镜定位失败: " + "; ".join(rc_bad), file=sys.stderr)

    # 3) SRT 存在、条数、时间轴（无字幕类型线整段跳过）
    if not expect_subtitles:
        return findings
    subs = parse_srt(srt_path)
    if not subs:
        findings.append(_fid("error", "srt", "字幕文件缺失或解析不出条目", path=srt_path))
        return findings  # 后续字幕相关检查无意义

    if len(subs) < len(shots):
        findings.append(_fid("warning", "srt-count",
                             f"字幕 {len(subs)} 条 < 分镜 {len(shots)} 镜（有镜没出字幕）"))
    # 条数**多于**镜数是正常的：A1 起长镜会按词边界拆成逐句字幕（一句一条）。
    non_monotonic = [i + 1 for i, (a, b) in enumerate(zip(subs, subs[1:])) if b[0] < a[1] - 0.01]
    if non_monotonic:
        findings.append(_fid("error", "srt-timeline",
                             f"{len(non_monotonic)} 处字幕时间轴倒挂/重叠", positions=non_monotonic[:8]))
    if abs(subs[0][0]) > THRESHOLDS["srt_start_tolerance"]:
        findings.append(_fid("warning", "srt-start",
                             f"首条字幕 {subs[0][0]:.2f}s 才开始（> {THRESHOLDS['srt_start_tolerance']}s 片头静默）"))

    # 4) 字幕覆盖 vs 整段配音
    voice_all = os.path.join(out, "voice_all.mp3")
    if os.path.exists(voice_all):
        va = probe_duration(voice_all)
        if va is not None and abs(va - subs[-1][1]) > THRESHOLDS["srt_end_vs_audio"]:
            findings.append(_fid("warning", "srt-vs-audio",
                                 f"末条字幕结束 {subs[-1][1]:.2f}s 与配音总长 {va:.2f}s 差 > "
                                 f"{THRESHOLDS['srt_end_vs_audio']}s（尾部可能漏字幕）"))
    return findings


def check_final_video(sb: Dict[str, Any], video_path: str, srt_path: str,
                      expect_voiceover: bool = True,
                      expect_subtitles: bool = True) -> List[Dict[str, Any]]:
    """B 类：粗剪硬门禁（降级直出 mp4；任一 error 阻断待终剪）。

    expect_voiceover / expect_subtitles：无配音类型线（混剪）本就没有音轨，
      不再判「无音频轨=配音丢失」的 error，降级为提醒；无字幕类型线不做出片 vs 字幕的时长对齐。
    """
    findings: List[Dict[str, Any]] = []
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        findings.append(_fid("error", "video-exists", "粗剪 mp4 缺失或为 0 字节", path=video_path))
        return findings

    media = ffprobe_media(video_path)
    if media is None:
        findings.append(_fid("error", "ffprobe", "ffprobe 无法读取粗剪（文件可能损坏）"))
        return findings

    if not media["has_video"]:
        findings.append(_fid("error", "video-stream", "粗剪无视频流"))
    if not media["has_audio"]:
        if expect_voiceover:
            findings.append(_fid("error", "audio-stream", "粗剪无音频轨（配音丢失，口播视频不可交付）"))
        else:
            findings.append(_fid("warning", "audio-stream",
                                 "粗剪无音频轨（该类型线不配音；若要 BGM 请在项目配置 video.bgm 挂上）"))

    # 比例/分辨率（对照分镜显式声明的 aspect_ratio）
    aspect = sb.get("aspect_ratio")
    expect = ASPECT_TO_WH.get(str(aspect or ""))
    if media["has_video"] and expect:
        ew, eh = expect
        if (media["width"], media["height"]) != (ew, eh):
            findings.append(_fid("error", "aspect-ratio",
                                 f"分辨率 {media['width']}x{media['height']} 与声明 {aspect}（{ew}x{eh}）不符"))

    # 粗剪时长 vs 末条字幕（尾部黑场/音画错位的硬指标；无字幕类型线跳过）
    subs = parse_srt(srt_path) if expect_subtitles else []
    if subs and media["duration"] > 0:
        gap = media["duration"] - subs[-1][1]
        if abs(gap) > THRESHOLDS["video_end_vs_srt"]:
            findings.append(_fid("error", "video-vs-srt",
                                 f"粗剪 {media['duration']:.2f}s 与末条字幕 {subs[-1][1]:.2f}s 差 {gap:+.2f}s"
                                 f"（> {THRESHOLDS['video_end_vs_srt']}s，疑似尾部黑场或音画错位）",
                                 videoDuration=round(media["duration"], 2),
                                 srtEnd=round(subs[-1][1], 2)))

    # 黑场（忽略片头片尾正常转场）
    blacks = detect_black_segments(video_path)
    edge = THRESHOLDS["black_edge_ignore"]
    inner = [(s, e) for s, e in blacks if s > edge and e < media["duration"] - edge]
    if inner:
        findings.append(_fid("warning", "blackframes",
                             f"{len(inner)} 段片内黑场（≥{THRESHOLDS['black_min_duration']}s）",
                             segments=[[round(s, 2), round(e, 2)] for s, e in inner[:6]]))

    # 响度
    mean_vol = detect_mean_volume(video_path)
    if mean_vol is not None:
        if mean_vol < THRESHOLDS["mean_volume_min"]:
            findings.append(_fid("warning", "volume-low",
                                 f"平均响度 {mean_vol:.1f}dBFS 偏低（< {THRESHOLDS['mean_volume_min']}），手机外放可能听不清"))
        elif mean_vol > THRESHOLDS["mean_volume_max"]:
            findings.append(_fid("warning", "volume-high",
                                 f"平均响度 {mean_vol:.1f}dBFS 偏高（> {THRESHOLDS['mean_volume_max']}），注意削波"))
    return findings


def run_qc(sb: Dict[str, Any], out: str, video_path: Optional[str],
           expect_voiceover: bool = True,
           expect_subtitles: bool = True) -> Dict[str, Any]:
    vo_dir = os.path.join(out, "voiceover")
    img_dir = os.path.join(out, "shots")
    srt_path = os.path.join(out, "subtitles.srt")

    findings = check_intermediates(sb, out, vo_dir, img_dir, srt_path,
                                   expect_voiceover, expect_subtitles)
    final_checked = False
    if video_path:
        findings += check_final_video(sb, video_path, srt_path,
                                      expect_voiceover, expect_subtitles)
        final_checked = True

    errors = [f for f in findings if f["level"] == "error"]
    warnings = [f for f in findings if f["level"] == "warning"]
    return {
        "schema_version": 1,
        "passed": len(errors) == 0,
        "final_checked": final_checked,
        # 本次按哪套口径检查的（无配音/无字幕类型线的报告可自解释，避免误读成漏检）
        "expect": {"voiceover": expect_voiceover, "subtitles": expect_subtitles},
        "counts": {"error": len(errors), "warning": len(warnings), "total": len(findings)},
        "thresholds": THRESHOLDS,
        "findings": findings,
    }


def print_summary(report: Dict[str, Any]) -> None:
    c = report["counts"]
    mode = "粗剪门禁" if report["final_checked"] else "中间产物软检（无粗剪）"
    print(f"\n{'='*60}\n🔍 QC 自检（{mode}）：{c['total']} 项异常"
          f"（❌ {c['error']} 阻断 / ⚠️ {c['warning']} 提醒）\n{'='*60}")
    for f in report["findings"]:
        icon = "❌" if f["level"] == "error" else "⚠️ "
        print(f"  {icon} [{f['check']}] {f['message']}")
    if report["passed"]:
        print("  ✅ QC 通过" + ("（有 warning，建议终剪时扫一眼报告）" if c["warning"] else ""))
    else:
        print("  🛑 QC 未通过：任务停在 qc_failed，修复后重跑："
              "run_pipeline.py … --only qc")


def main() -> int:
    ap = argparse.ArgumentParser(description="QC 粗剪自检门禁")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--video", default=None, help="粗剪 mp4；不给定则只做中间产物软检")
    ap.add_argument("--report", default=None, help="报告输出路径（默认 <out-dir>/qc_report.json）")
    ap.add_argument("--json", action="store_true", help="只输出机器可读结果（无装饰）")
    # 类型口径（v5.1 P3-2）：由 run_pipeline 按内容中心类型目录下传。
    # 默认都是「期望有」= 口播口径，行为与历史一致。
    ap.add_argument("--no-voiceover", action="store_true",
                    help="该类型线不配音（如混剪）：不检查逐镜 mp3，粗剪无音轨降级为提醒")
    ap.add_argument("--no-subtitles", action="store_true",
                    help="该类型线不打字幕（如品牌/混剪）：不检查 SRT 与其时间轴")
    args = ap.parse_args()

    sb_path = os.path.abspath(os.path.expanduser(args.storyboard))
    out = os.path.abspath(os.path.expanduser(args.out_dir))
    video_path = os.path.abspath(os.path.expanduser(args.video)) if args.video else None
    report_path = args.report or os.path.join(out, "qc_report.json")

    try:
        with open(sb_path, encoding="utf-8") as f:
            sb = json.load(f)
    except Exception as e:
        print(f"QC 自检异常：读不到分镜 {sb_path}: {e}", file=sys.stderr)
        return 1

    report = run_qc(sb, out, video_path,
                    expect_voiceover=not args.no_voiceover,
                    expect_subtitles=not args.no_subtitles)
    report["storyboard"] = sb_path
    report["out_dir"] = out
    report["video"] = video_path

    try:
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ QC 报告写入失败（不影响判定）: {e}", file=sys.stderr)

    if not args.json:
        print_summary(report)
        print(f"  报告: {report_path}")
    else:
        print(json.dumps({"passed": report["passed"], "counts": report["counts"],
                          "report": report_path}, ensure_ascii=False))

    return 0 if report["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
