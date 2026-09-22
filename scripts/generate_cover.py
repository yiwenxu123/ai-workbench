#!/usr/bin/env python3
"""
封面/标题包生成器（v5.1 P2-2）

为什么需要：
  成片、字幕都有了，离「发出去」还差封面图 + 标题。此前这两样靠人工在剪映/平台里现挑现想，
  属高频且重复的收尾动作，故收进管线做成一阶段（可 --skip cover）。

两件事（都是确定性、零成本、不调任何模型）：
  1) 钩子帧优选 —— 按 cover_templates.json 的信号表给每镜台词打「钩子分」，取最高分镜的画面
     做封面；有视频片段优先抽帧，否则用该镜图片；按分镜 aspect_ratio 居中裁切。
  2) 母版文案 + 标题候选 —— 产出一份「平台中立文案母版」（标题候选 + 简介 + 话题标签 + 封面大字），
     打包层再按各平台 copyProfile 渲染成平台成品（引擎不做分平台裁剪）。
     真相源优先级：out_dir/copy_master.json（agent 用 LLM 写好的母版，含简介/话题）
       > out_dir/cover_titles.json（旧：仅标题候选，向后兼容）
       > cover_templates.json 模板兜底（只保证标题有候选）。
     简介缺省时从 out_dir/script.md 确定性抽取「首段 hook + 末段互动」兜底；话题**不臆造**，
     agent 没给就留空（对外露出内容，宁缺毋滥）。
     **引擎不调 LLM**（引擎不解释业务、不绑模型）；模板只保证「永远有候选可用」，不假装是创意。

产物：
  out/cover.jpg    封面图（裁切到目标比例；ffmpeg 不可用时退化为原图拷贝）
  out/cover.json   封面指针 + 母版文案（videos 表 cover 字段只存指针，这里是真相源）

用法：
  generate_cover.py --storyboard sb.json --out-dir out/ \
      [--copy-file out/copy_master.json] [--titles-file out/cover_titles.json] [--hook-shot 3] \
      [--max-titles 5] [--aspect-ratio 9:16] [--update-storyboard]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_PATH = os.path.join(HERE, "cover_templates.json")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv")


# ── 模板加载 ──────────────────────────────────────────────────────────

def load_templates(path: str = TEMPLATES_PATH) -> dict:
    """读模板表；缺失/损坏时用内置最小兜底（保证阶段永不因模板挂掉）。"""
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict):
            raise ValueError("模板根节点不是对象")
        return cfg
    except Exception as e:
        print(f"⚠️  模板表读取失败（{path}）: {e}，改用内置兜底", file=sys.stderr)
        return {
            "hook": {"signals": [
                {"id": "digit", "weight": 2, "label": "含数字", "pattern": "\\d"},
                {"id": "contrast", "weight": 3, "label": "含反差/悬念",
                 "pattern": "其实|竟然|真相|秘密|误区"},
            ]},
            "templates": {"max_chars": 20, "items": [{"style": "悬念式", "pattern": "{hook_short}"}]},
            "stopwords": [],
        }


# ── 钩子打分 ──────────────────────────────────────────────────────────

def score_hook(text: str, signals: list) -> tuple:
    """按信号表给一段台词打分 → (总分, 命中说明列表)"""
    score, reasons = 0, []
    for sig in signals or []:
        if not isinstance(sig, dict):
            continue
        label = sig.get("label") or sig.get("id") or "信号"
        weight = int(sig.get("weight") or 0)
        pat = sig.get("pattern")
        hit = False
        if pat:
            try:
                hit = re.search(pat, text) is not None
            except re.error:
                hit = False
        else:  # length_ok 之类：按字数区间
            lo = int(sig.get("min_chars") or 0)
            hi = int(sig.get("max_chars") or 10 ** 9)
            hit = lo <= len(text) <= hi
        if hit and weight:
            score += weight
            reasons.append(label)
    return score, reasons


def resolve_media(shot: dict, idx: int, img_dir: str) -> tuple:
    """定位某镜可用于封面的媒体 → (绝对路径, 'video'|'image'|'')。视频优先（更接近成片观感）。"""
    vis = shot.get("visual") or {}
    ref = vis.get("source_ref") or {}
    sid = shot.get("shot_id", idx)
    candidates = []
    for key in ("video_path", "clip_path"):
        if vis.get(key):
            candidates.append((str(vis[key]), "video"))
    if ref.get("video_path"):
        candidates.append((str(ref["video_path"]), "video"))
    for key in ("image_path",):
        if vis.get(key):
            candidates.append((str(vis[key]), "image"))
    if ref.get("path"):
        candidates.append((str(ref["path"]), "image"))
    candidates.append((os.path.join(img_dir, f"shot_{sid:03d}.jpg"), "image"))
    for p, kind in candidates:
        p = os.path.expanduser(p.strip())
        if os.path.exists(p) and p.lower().endswith(IMAGE_EXT + VIDEO_EXT):
            return p, kind
    return "", ""


def is_placeholder(shot: dict) -> bool:
    vis = shot.get("visual") or {}
    ref = vis.get("source_ref") or {}
    return bool(vis.get("placeholder") or ref.get("placeholder"))


def pick_hook_shot(shots: list, img_dir: str, signals: list, forced_id=None) -> dict:
    """
    优选封面帧：优先取「有可用媒体」且钩子分最高的镜。
    forced_id 给定时直接采用该镜（人/agent 指定）。
    返回 {idx, shot, shot_id, score, reasons, media, kind, placeholder}
    """
    best = None
    for i, shot in enumerate(shots, 1):
        sid = shot.get("shot_id", i)
        if forced_id is not None and int(sid) != int(forced_id):
            continue
        text = str(shot.get("script_line") or (shot.get("audio") or {}).get("text") or "")
        score, reasons = score_hook(text, signals)
        media, kind = resolve_media(shot, i, img_dir)
        cand = {
            "idx": i, "shot": shot, "shot_id": int(sid),
            "score": score, "reasons": reasons,
            "media": media, "kind": kind,
            "placeholder": is_placeholder(shot),
            "script_line": text,
        }
        # 排序键：有媒体 > 非占位 > 钩子分 > 镜序靠前
        key = (1 if media else 0, 0 if cand["placeholder"] else 1, score, -i)
        if best is None or key > best["_key"]:
            cand["_key"] = key
            best = cand
    if best:
        best.pop("_key", None)
    return best


# ── 封面图裁切 ────────────────────────────────────────────────────────

def _probe_size(path: str) -> tuple:
    """ffprobe 取宽高 → (w, h)；失败返回 (0, 0)"""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", path],
            capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            w, h = r.stdout.strip().split("x")[:2]
            return int(w), int(h)
    except Exception:
        pass
    return 0, 0


def make_cover(src: str, dst: str, kind: str, aspect_ratio: str, out_w: int = 1080) -> dict:
    """
    生成封面图：按 aspect_ratio 居中裁切 + 缩放到 out_w 宽（高度取偶数）。
    ffmpeg 不可用/失败时退化为原图拷贝，并在返回值里如实标注，不假装裁切成功。
    """
    info = {"ok": False, "method": "", "note": ""}
    try:
        a, b = (aspect_ratio or "").split(":")
        a, b = float(a), float(b)
        if a <= 0 or b <= 0:
            raise ValueError("比例非法")
    except Exception:
        a, b = 9.0, 16.0
        info["note"] = f"aspect_ratio「{aspect_ratio}」不可解析，按 9:16 处理"

    w, h = _probe_size(src)
    vf = ""
    if w > 0 and h > 0:
        # 居中裁切到目标比例（宽高都取 min，避免超出源图）
        crop_w = int(min(w, h * a / b))
        crop_h = int(min(h, w * b / a))
        vf = f"crop={crop_w}:{crop_h},scale={out_w}:-2"
    else:
        vf = f"scale={out_w}:-2"

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if kind == "video":
        # 抽中间帧（避开转场首帧的黑场）
        dur = 0.0
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=nw=1:nk=1", src],
                               capture_output=True, text=True, timeout=20)
            dur = float(r.stdout.strip() or 0)
        except Exception:
            dur = 0.0
        cmd += ["-ss", f"{max(0.0, dur / 2):.2f}"]
    cmd += ["-i", src]
    if kind == "video":
        cmd += ["-frames:v", "1"]
    cmd += ["-vf", vf, "-q:v", "3", dst]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0:
            info.update(ok=True, method="ffmpeg-frame" if kind == "video" else "ffmpeg-crop")
            return info
        info["note"] = (info["note"] + " | " if info["note"] else "") + \
            f"ffmpeg 失败: {(r.stderr or '')[-200:]}"
    except FileNotFoundError:
        info["note"] = (info["note"] + " | " if info["note"] else "") + "未安装 ffmpeg"
    except Exception as e:
        info["note"] = (info["note"] + " | " if info["note"] else "") + f"{type(e).__name__}: {e}"

    # 退化：原图拷贝（比例可能不符，但至少有封面可用）
    try:
        shutil.copyfile(src, dst)
        info.update(ok=os.path.exists(dst), method="copy-fallback")
    except Exception as e:
        info["note"] = (info["note"] + " | " if info["note"] else "") + f"拷贝也失败: {e}"
    return info


# ── 标题候选 ──────────────────────────────────────────────────────────

def extract_number(texts: list, fallback: int) -> int:
    for t in texts:
        m = re.search(r"\d+", t or "")
        if m:
            return int(m.group(0))
    return fallback


def extract_keyword(title: str, stopwords: list, max_len: int = 8) -> str:
    """
    从标题抽核心词：按标点切块 → 去停用词 → 取「2~max_len 字」里最长的一块。
    限长很关键：不限长时整句口播会整段当选，拼出来的标题必然是废话。
    没有标题（或抽不出）时返回空串，调用方据此跳过依赖 {keyword} 的模板。
    """
    parts = [p for p in re.split(r"[，。！？；、,.\s:：/|（）()《》\"'“”‘’\-—…]+", title or "") if p]
    cleaned = []
    for p in parts:
        for sw in sorted(stopwords or [], key=len, reverse=True):
            p = p.replace(sw, "")
        p = p.strip()
        if 2 <= len(p) <= max_len:
            cleaned.append(p)
    return max(cleaned, key=len) if cleaned else ""


def clip(text: str, n: int) -> str:
    text = (text or "").strip().rstrip("，。！？；、,.!?;")
    return text if len(text) <= n else text[:n].rstrip("，。！？；、,.!?;") + "…"


def normalize_titles(raw) -> list:
    """把候选标题的三种形态统一成 [{text,style,angle?}]：
       ["标题1", ...] / [{"text","style"}, ...] / 已从 {titles:[...]} 取出的列表。"""
    if isinstance(raw, dict):
        raw = raw.get("titles") or raw.get("items") or []
    if not isinstance(raw, list):
        return []
    out = []
    for it in raw:
        if isinstance(it, str) and it.strip():
            out.append({"text": it.strip(), "style": "自定义"})
        elif isinstance(it, dict) and str(it.get("text") or "").strip():
            out.append({"text": str(it["text"]).strip(),
                        "style": str(it.get("style") or "自定义"),
                        "angle": str(it.get("angle") or "")})
    return out


def load_agent_titles(path: str) -> list:
    """读旧版纯标题真相源 cover_titles.json（向后兼容）。"""
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"⚠️  候选标题文件解析失败（{path}）: {e}", file=sys.stderr)
        return []
    return normalize_titles(raw)


def load_agent_copy(path: str) -> dict:
    """
    读 agent 写好的母版文案 copy_master.json（最高优先级真相源）。
    兼容：{"titles":[...], "recommended":"", "description":"", "hashtags":["#x"], "cover_text":""}
    hashtags 里的裸词（不带 #）自动补 #。文件缺失/损坏返回**完整结构的空母版**，调用方逐级退化。
    """
    base = {"titles": [], "recommended": "", "description": "", "hashtags": [], "cover_text": ""}
    if not path or not os.path.exists(path):
        return base
    try:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"⚠️  母版文案文件解析失败（{path}）: {e}", file=sys.stderr)
        return base
    if not isinstance(raw, dict):
        return base
    tags = []
    hs = raw.get("hashtags") or raw.get("tags") or []
    if isinstance(hs, list):
        for t in hs:
            s = str(t or "").strip().lstrip("#").strip()
            if s:
                tags.append("#" + s)
    base.update({
        "titles": normalize_titles(raw),
        "recommended": str(raw.get("recommended") or "").strip(),
        "description": str(raw.get("description") or raw.get("desc") or "").strip(),
        "hashtags": tags,
        "cover_text": str(raw.get("cover_text") or raw.get("coverText") or "").strip(),
    })
    return base


def extract_description_from_script(out_dir: str, recommended: str, max_chars: int = 400) -> tuple:
    """
    简介兜底：从 out_dir/script.md 确定性抽取「开场 hook（首段）+ 结尾互动钩子（末段）」，
    拼在推荐标题下。**不臆造、不调模型**；script.md 缺失/读失败返回 ("", 原因) 让调用方跳过。
    """
    p = os.path.join(out_dir, "script.md")
    if not os.path.exists(p):
        return "", ""
    try:
        with open(p, encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"⚠️  script.md 读取失败（简介兜底跳过）: {e}", file=sys.stderr)
        return "", ""
    paras = []
    for block in re.split(r"\n\s*\n", text):
        keep = [ln for ln in block.split("\n")
                if not re.match(r"^\s*【画面", ln) and not re.match(r"^\s*#", ln)]
        cleaned = "\n".join(keep).replace("**", "").strip()
        if cleaned:
            paras.append(cleaned)
    parts = []
    if recommended:
        parts.append(recommended)
    if paras:
        parts.append(paras[0])
        if len(paras) > 1 and paras[-1] != paras[0]:
            parts.append(paras[-1])
    desc = "\n\n".join(parts).strip()
    truncated = False
    if len(desc) > max_chars:
        desc = desc[:max_chars].rstrip() + "…（已截断，请人工精简）"
        truncated = True
    return desc, ("script.md" + ("（已截断）" if truncated else ""))


def build_titles_template(sb: dict, hook_line: str, cfg: dict, max_titles: int,
                          title_override: str = "") -> list:
    """
    模板兜底生成候选：占位符替换 → **跳过变量为空的模板** → 去重 → 截断到 max_chars。
    「跳过」是必要的：没有标题就没有 keyword，硬拼出来的是整句口播当标题的废话。
    """
    tpl = cfg.get("templates") or {}
    items = tpl.get("items") or []
    max_chars = int(tpl.get("max_chars") or 20)
    stopwords = cfg.get("stopwords") or []
    shots = sb.get("shots") or []
    title = (title_override or str(sb.get("title") or "")).strip()
    keyword = extract_keyword(title, stopwords)
    number = extract_number([hook_line, title], len(shots) or 0)
    # 末镜通常是「落点/结论」，比中间镜更适合做标题（无标题可抽时的第二来源）
    payoff_line = ""
    if shots:
        last = shots[-1] or {}
        payoff_line = str(last.get("script_line") or (last.get("audio") or {}).get("text") or "")
    variables = {
        "hook_short": clip(hook_line, max_chars),
        "hook": clip(hook_line, 40),
        "payoff_short": clip(payoff_line, max_chars),
        "title": title,
        "keyword": keyword,
        "number": number,
        "shot_count": len(shots),
    }
    out, seen = [], set()
    for it in items:
        if not isinstance(it, dict) or not it.get("pattern"):
            continue
        text = str(it["pattern"])
        used = re.findall(r"\{(\w+)\}", text)
        if any(not str(variables.get(k, "")).strip() for k in used):
            continue  # 占位符取值为空 → 该模板本轮不可用
        for k in used:
            text = text.replace("{" + k + "}", str(variables[k]))
        text = clip(text, max_chars)
        if len(text) < 4 or text in seen:
            continue
        seen.add(text)
        out.append({"text": text, "style": str(it.get("style") or "候选")})
        if len(out) >= max_titles:
            break
    return out


# ── 主流程 ────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="封面/标题包生成器（钩子帧优选 + 标题候选）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--titles-file", default=None,
                    help="agent 写好的候选标题 JSON（缺省自动找 <out-dir>/cover_titles.json）")
    ap.add_argument("--copy-file", default=None,
                    help="agent 写好的母版文案 JSON（缺省自动找 <out-dir>/copy_master.json；优先级高于 --titles-file）")
    ap.add_argument("--hook-shot", type=int, default=None,
                    help="强制指定封面取自哪一镜（缺省按钩子分优选）")
    ap.add_argument("--max-titles", type=int, default=5)
    ap.add_argument("--aspect-ratio", default=None,
                    help="封面比例（缺省取分镜 aspect_ratio，再缺省 9:16）")
    ap.add_argument("--title", default="",
                    help="选题/视频标题（模板兜底抽核心词用；缺省取分镜 title 字段）")
    ap.add_argument("--update-storyboard", action="store_true",
                    help="把封面指针回写进分镜 JSON（与其它阶段一致）")
    ap.add_argument("--cover-name", default="cover.jpg", help="封面文件名（默认 cover.jpg）")
    args = ap.parse_args()

    sb_path = os.path.abspath(os.path.expanduser(args.storyboard))
    out = os.path.abspath(os.path.expanduser(args.out_dir))
    if not os.path.exists(sb_path):
        print(f"❌ 分镜文件不存在: {sb_path}", file=sys.stderr)
        sys.exit(1)
    with open(sb_path, encoding="utf-8") as f:
        sb = json.load(f)
    os.makedirs(out, exist_ok=True)
    img_dir = os.path.join(out, "shots")
    cfg = load_templates()
    signals = ((cfg.get("hook") or {}).get("signals")) or []

    shots = sb.get("shots") or []
    if not shots:
        print("❌ 分镜没有 shots，无法优选封面帧", file=sys.stderr)
        sys.exit(1)

    # ① 钩子帧优选
    picked = pick_hook_shot(shots, img_dir, signals, args.hook_shot)
    if not picked:
        print(f"❌ 指定镜 {args.hook_shot} 不存在", file=sys.stderr)
        sys.exit(1)
    aspect = args.aspect_ratio or sb.get("aspect_ratio") or (sb.get("project") or {}).get("aspect_ratio") or "9:16"
    cover_path = os.path.join(out, args.cover_name)
    if picked["media"]:
        conv = make_cover(picked["media"], cover_path, picked["kind"], aspect)
        origin = ("placeholder" if picked["placeholder"] else picked["kind"])
    else:
        conv = {"ok": False, "method": "", "note": "该镜无可用媒体（图片/视频都缺失）"}
        origin = "missing"

    print(f"🖼  封面帧优选: 第 {picked['shot_id']} 镜（钩子分 {picked['score']}"
          f"{'，' + '/'.join(picked['reasons']) if picked['reasons'] else ''}）"
          f" ← {os.path.basename(picked['media']) if picked['media'] else '无媒体'}"
          f" [{conv['method'] or '失败'}]")
    if conv.get("note"):
        print(f"   ⚠️  {conv['note']}", file=sys.stderr)

    # ② 母版文案 + 标题候选：copy_master.json（agent 母版）> cover_titles.json（仅标题）> 模板兜底
    copy_file = args.copy_file or os.path.join(out, "copy_master.json")
    titles_file = args.titles_file or os.path.join(out, "cover_titles.json")
    copy = load_agent_copy(copy_file)
    titles = copy["titles"]
    source = "copy_master" if titles else ""
    recommended = copy["recommended"]
    if not titles:
        legacy = load_agent_titles(titles_file)
        if legacy:
            titles = legacy
            source = "agent"
    if not titles:
        titles = build_titles_template(sb, picked["script_line"], cfg, args.max_titles, args.title)
        source = "template"
    else:
        titles = titles[:args.max_titles]
    if not recommended and titles:
        recommended = titles[0]["text"]
    if not titles:
        print("⚠️  未能生成任何标题候选（模板表为空？）", file=sys.stderr)

    # 简介：母版给定 > script.md 确定性兜底；话题**不臆造**（agent 没给即空）
    description = copy["description"]
    desc_source = "copy_master" if description else ""
    if not description:
        description, desc_source = extract_description_from_script(out, recommended)
    hashtags = copy["hashtags"]
    cover_text = copy["cover_text"]

    result = {
        "video_id": sb.get("video_id") or os.path.splitext(os.path.basename(sb_path))[0],
        "generated_at": int(time.time() * 1000),
        "aspect_ratio": aspect,
        "cover": {
            "shot_id": picked["shot_id"],
            "image": cover_path if conv.get("ok") else "",
            "source_media": picked["media"],
            "origin": origin,
            "hook_score": picked["score"],
            "hook_reasons": picked["reasons"],
            "script_line": picked["script_line"][:200],
            "convert": conv,
        },
        "titles": titles,
        "recommended": recommended,
        "source": source,
        "titles_file": titles_file if source == "agent" else "",
        "copy": {
            "description": description,
            "description_source": desc_source,
            "hashtags": hashtags,
            "cover_text": cover_text,
            "copy_file": copy_file if os.path.exists(copy_file) else "",
        },
    }
    cover_json = os.path.join(out, "cover.json")
    with open(cover_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"🏷  标题候选（{len(titles)} 条，来源={source}）:")
    for i, t in enumerate(titles, 1):
        print(f"   {i}. [{t['style']}] {t['text']}")
    print(f"📝 母版：简介 {len(description)} 字（来源={desc_source or '无'}）· "
          f"话题 {len(hashtags)} 个 · 封面大字 {'有' if cover_text else '无'}")
    print(f"✅ 封面/标题包已生成: {cover_json}")

    if args.update_storyboard:
        sb["cover"] = {
            "shot_id": picked["shot_id"],
            "image": result["cover"]["image"],
            "aspect_ratio": aspect,
            "titles": [t["text"] for t in titles],
            "recommended": recommended,
            "copy": result["copy"],
        }
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
        print(f"   已回写分镜 cover 字段: {sb_path}")

    # 供编排层解析（run_pipeline 读 cover.json 即可，这里也给一份 stdout JSON）
    print(json.dumps({
        "cover_json": cover_json,
        "cover_image": result["cover"]["image"],
        "shot_id": picked["shot_id"],
        "title_count": len(titles),
        "source": source,
        "copy": result["copy"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
