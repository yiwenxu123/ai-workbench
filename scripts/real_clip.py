#!/usr/bin/env python3
"""
实拍片段（visual.real_clip）解析与探针助手（混剪 M2 瘦核心）

契约（计划 D2/D5）：一镜一段。`shot.visual.real_clip = {path|eagle_id, start?, end?}`
  - path     本地绝对路径（兜底通道，永远可用）
  - eagle_id Eagle 库条目 id（素材主通道：视频统一存 Eagle）
  - start/end 入出点（秒，选填）；缺省=整段素材

分工铁律：LLM/agent 只**标注** real_clip；解析、ffprobe、剪辑点全部确定性代码，
引擎从不调模型。Eagle 解析为**只读**（item/get、thumbnail），绝不入库/改库。
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.request

FFPROBE = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
EAGLE_BASE = "http://localhost:41595"

_EW_SRC = os.path.expanduser("~/Projects/tools/eagle-watcher/src")


def real_clip_of(shot):
    """安全读取 shot.visual.real_clip —— 仅当是非空 dict 才算实拍镜。"""
    rc = ((shot or {}).get("visual") or {}).get("real_clip")
    return rc if isinstance(rc, dict) and (rc.get("path") or rc.get("eagle_id")) else None


def _eagle_token():
    tok = os.environ.get("EAGLE_TOKEN", "")
    if tok:
        return tok
    cfgp = os.path.expanduser("~/.eagle-watcher/config.yaml")
    if os.path.exists(cfgp):
        import re
        m = re.search(r"^\s*token:\s*[\"']?([^\s\"']+)", open(cfgp, encoding="utf-8").read(), re.M)
        if m:
            tok = m.group(1)
    if not tok:
        sp = os.path.expanduser("~/.dsh/secrets/eagle.env")
        if os.path.exists(sp):
            for line in open(sp):
                if line.startswith("export EAGLE_TOKEN="):
                    tok = line.split("=", 1)[1].strip().strip('"').strip("'")
    return tok


def _eagle_get(path, token, version="v2"):
    ver = f"api/{version}/" if version else "api/"
    url = f"{EAGLE_BASE}/{ver}{path}"
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(
        url + (sep + "token=" + token if token else ""),
        headers={"Authorization": f"Bearer {token}"} if token else {})
    with urllib.request.urlopen(req, timeout=6) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_eagle_file(eagle_id):
    """
    eagle_id → 本地媒体绝对路径（只读尽力解析，失败返回 None）。
    Eagle 未启动/无 token 时静默失败——上层按"素材无法定位"处理并告警。
    实测 Eagle v4：item/get **不返回** file/thumbnail 字段，且 v2 的
    item/thumbnail 端点已下线（404）；缩略图只走 legacy `/api/item/thumbnail`。
    解析次序：
      1) item.file 本身是绝对路径（旧版/外链条目）
      2) 缩略图路径推导库根：join(library_root, item.file)
      3) legacy 缩略图同目录 + name.ext（v4 库内条目的唯一可行通道）
    """
    token = _eagle_token()
    try:
        d = _eagle_get(f"item/get?id={eagle_id}", token)
        arr = (d.get("data") or {}).get("data") or []
        item = arr[0] if arr else None
        if not item:
            return None
        rel = item.get("file") or ""
        if rel and os.path.isabs(rel) and os.path.exists(os.path.expanduser(rel)):
            return os.path.expanduser(rel)
        t = _eagle_get(f"item/thumbnail?id={eagle_id}", token, version="")
        thumb = (t.get("data") or "").replace("\\", "/")
        if thumb:
            from urllib.parse import unquote
            thumb = unquote(thumb)
        if rel and thumb:
            # thumb: <Library>.library/images/x.info/y_thumbnail.png → 库根上溯三级
            lib_root = os.path.dirname(os.path.dirname(os.path.dirname(thumb)))
            p = os.path.join(lib_root, rel)
            if os.path.exists(p):
                return p
        if thumb and item.get("name") and item.get("ext"):
            p = os.path.join(os.path.dirname(thumb), f"{item['name']}.{item['ext']}")
            if os.path.exists(p):
                return p
        return None
    except Exception:
        return None


def resolve_clip(rc, verbose=False):
    """real_clip → (绝对路径 | None, 失败原因)。"""
    p = rc.get("path")
    if p:
        p = os.path.expanduser(str(p))
        if os.path.exists(p):
            return p, ""
        return None, f"path 不存在: {p}"
    eid = str(rc.get("eagle_id") or "")
    if eid:
        got = resolve_eagle_file(eid)
        if got:
            if verbose:
                print(f"   🔗 eagle {eid[:8]}… → {os.path.basename(got)}")
            return got, ""
        return None, (f"eagle_id 无法解析（Eagle 未启动或条目不存在）: {eid}")
    return None, "real_clip 缺少 path/eagle_id"


def probe_duration(path):
    """ffprobe 实测媒体时长（秒）；失败 None。"""
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "json", path],
            capture_output=True, text=True, timeout=15).stdout
        d = float(json.loads(out)["format"]["duration"])
        return d if d > 0 else None
    except Exception:
        return None


def clip_span(rc, native_dur):
    """
    入出点 → (start, dur)，钳制进素材原生时长（D3：画面为时间源）。
    非法/缺省 start、end 越界钳而不报错——QC 侧另有硬校验（A3）。
    """
    start = max(0.0, float(rc.get("start") or 0))
    if start >= native_dur:
        start = 0.0
    end = float(rc.get("end") or 0) if rc.get("end") else native_dur
    end = min(end, native_dur)
    if end <= start:
        end = native_dur
    return start, max(0.1, end - start)


def extract_frame(path, t, out_jpg):
    """提取第 t 秒附近的一帧为 jpg（¥0，供 draft/封面/QC 等一切认图的消费方复用）。"""
    os.makedirs(os.path.dirname(out_jpg) or ".", exist_ok=True)
    r = subprocess.run(
        [FFMPEG, "-y", "-ss", f"{max(0.0, t):.3f}", "-i", path,
         "-frames:v", "1", "-q:v", "2", out_jpg],
        capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out_jpg)


if __name__ == "__main__":
    # 手工自检：python3 real_clip.py '{"path":"/x.mp4"}'
    if len(sys.argv) > 1:
        rcx = json.loads(sys.argv[1])
        p, why = resolve_clip(rcx, verbose=True)
        print(f"resolved={p} reason={why}")
        if p:
            print(f"duration={probe_duration(p)}")


def probe_has_audio(path):
    """素材是否含音频流（A4：无声实拍镜按静音镜处理，不炸混音）。"""
    try:
        out = subprocess.run(
            [FFPROBE, "-v", "quiet", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=15).stdout
        return "audio" in out
    except Exception:
        return False


def build_aligned_track(shot_audio, work, mode, out_name):
    """
    A4 共享底座（assemble_video 与 generate_draft 同一条混音带）：
    每镜产出一段**严格等于该镜时长**的音频再 concat，保证与视频轨逐镜对齐。
      mode="assemble"：配音+原声 → amix(配音为主, 原声 sidechain ducking)；
                       只有原声 → 原声顶上；只有配音 → 配音钳到镜时长；都无 → 静音。
      mode="bed"：    配音+原声 → 只出**被配音 key  duck 过的原声**（剪映里配音轨在
                       独立音轨上，垫轨只担原声职责，避免配音双份叠音）；其余同上。
    返回拼接后的音频路径；全片无任何可发声来源时返回 None。
    """
    if not any(s["native"] or s["vo"] for s in shot_audio):
        return None
    enc = ["-ar", "44100", "-ac", "2", "-c:a", "aac", "-b:a", "160k"]
    seg_paths = []
    for idx, s in enumerate(shot_audio, 1):
        dur = float(s["dur"])
        seg = os.path.join(work, f"a4_{mode}_{idx:03d}.m4a")
        native, vo = s["native"], s["vo"]
        if native and vo:
            media, start = native
            if mode == "bed":
                # 垫轨只担原声职责：vo 整个作 sidechain key，无需 asplit 分流
                fc = (f"[0:a]volume=0.9[nat];"
                      f"[nat][1:a]sidechaincompress=threshold=0.03:ratio=8:"
                      f"attack=20:release=350[natd];"
                      f"[natd]apad,atrim=0:{dur:.3f}[a]")
            else:
                fc = (f"[1:a]asplit=2[vom][vok];"
                      f"[0:a]volume=0.9[nat];"
                      f"[nat][vok]sidechaincompress=threshold=0.03:ratio=8:"
                      f"attack=20:release=350[natd];"
                      f"[vom][natd]amix=inputs=2:normalize=0[amix];"
                      f"[amix]apad,atrim=0:{dur:.3f}[a]")
            _run_ff(["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", media,
                     "-i", vo, "-filter_complex", fc, "-map", "[a]"], enc, seg)
        elif native:
            media, start = native
            _run_ff(["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", media,
                     "-vn", "-af", f"apad,atrim=0:{dur:.3f}"], enc, seg)
        elif vo:
            _run_ff(["-i", vo, "-af", f"apad,atrim=0:{dur:.3f}"], enc, seg)
        else:
            _run_ff(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                     "-t", f"{dur:.3f}"], enc, seg)
        seg_paths.append(seg)
    lst = os.path.join(work, f"a4list_{mode}.txt")
    with open(lst, "w") as f:
        for pth in seg_paths:
            f.write(f"file '{pth}'\n")
    out = os.path.join(work, out_name)
    _run_ff(["-f", "concat", "-safe", "0", "-i", lst],
            ["-c:a", "aac", "-ar", "44100", "-ac", "2"], out)
    return out


def _run_ff(in_args, enc, out):
    r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", *in_args, *enc, out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败: {r.stderr[-300:]}")
    return out
