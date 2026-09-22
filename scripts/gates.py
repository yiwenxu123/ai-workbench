#!/usr/bin/env python3
"""
人工确认闸（gates）——把「一口气跑完的流水线」变成「人能掌控每个决策点的工具」。

为什么需要（审计报告 P0-1）：
  原本从分镜到成片一口气跑完，用户只能在最后看结果。
  生图占单条成本约 94%，若在**脚本/分镜阶段**就能改，可避免整批白烧。

三道闸（按花钱顺序）：
  1. script     —— 台词确认（花钱之前；可编辑，回写分镜）
  2. storyboard —— 画面描述/镜头语言确认（**生图之前**，最省钱的一道；可编辑）
  3. images     —— 素材确认（可勾选「重跑」哪几镜）

用法（非交互式，脚本化可复现）：
  # 跑到闸就停下
  run_pipeline.py ... --gate script,storyboard,images
  # 在 review/xxx.md 里改，改完批准（同时把修改回写进分镜）
  run_pipeline.py ... --approve script
  run_pipeline.py ... --approve storyboard
  run_pipeline.py ... --approve images      # 会把勾选「重跑」的镜重新生图

批准状态 = review/<gate>.approved 文件存在。
"""
import json
import os
import sys

GATES = ["script", "storyboard", "images"]


# ── 成本可见性（v4.0 成本纪律：花钱发生在批准那一刻，数字必须在场）────────

def _image_unit_price(sb):
    """从项目配置取生图单价（元/张）；取不到按 wanx-v1 0.16 兜底"""
    try:
        from providers import load_project_config, _PRICE, unit_price
        pcfg = load_project_config(sb.get("project_id")) or {}
        icfg = pcfg.get("image") or {}
        provider = icfg.get("provider") or "dashscope"
        model = icfg.get("model") or "wanx-v1"
        price, est = unit_price("image", provider, model)
        return float(price), provider, model, bool(est)
    except Exception:
        return 0.16, "dashscope", "wanx-v1", False


def _spent_so_far(out_dir):
    """读本次已花成本（cost.jsonl 由 run_pipeline 设 VIDEO_COST_LOG 落盘）"""
    try:
        from providers import load_cost_log, cost_report
        path = os.environ.get("VIDEO_COST_LOG") or os.path.join(out_dir, ".cost.jsonl")
        entries = load_cost_log(path)
        if not entries:
            return None
        rep = cost_report(entries)
        return rep.get("total", 0.0)
    except Exception:
        return None


def _cost_footer(out_dir, gate, sb):
    """闸文件尾部的成本行：storyboard=预估生图成本；images=实际已花"""
    if gate == "storyboard":
        n = len(sb.get("shots") or [])
        price, provider, model, est = _image_unit_price(sb)
        est_flag = "（单价为估算）" if est else ""
        reuse_note = "（reuse 命中可省，实际以未命中数为准）"
        return (f"\n---\n💰 **预估生图成本**: {n} 镜 × ¥{price:.2f}/张 ≈ **¥{n * price:.2f}**"
                f"  \nprovider=`{provider}/{model}`{est_flag}{reuse_note}\n")
    if gate == "images":
        spent = _spent_so_far(out_dir)
        if spent is None:
            return ("\n---\n💰 本次暂无计费调用记录（全部复用或免费档）\n")
        return (f"\n---\n💰 **本次已花**: ¥{spent:.4f}"
                f"  \n（重新生图会追加成本；未勾「重跑」的镜保持免费复用）\n")
    return ""


def review_path(out_dir, gate):
    return os.path.join(out_dir, "review", f"{gate}.md")


def approved_path(out_dir, gate):
    return os.path.join(out_dir, "review", f"{gate}.approved")


def ensure_review_dir(out_dir):
    d = os.path.join(out_dir, "review")
    os.makedirs(d, exist_ok=True)
    return d


def is_approved(out_dir, gate):
    return os.path.exists(approved_path(out_dir, gate))


def mark_approved(out_dir, gate):
    ensure_review_dir(out_dir)
    p = approved_path(out_dir, gate)
    open(p, "w", encoding="utf-8").write("approved\n")
    return p


# ── 段落级意见（P1-b D4/D5）──────────────────────────────────────────
# 真相源在内容中心 metadata.gate_feedback（Web/面板直接提交）；本地
# review/feedback.json 是引擎侧镜像：regen 消费后写 consumed，闸文件
# 「意见:」行收集结果也追加到这里，保证两条入口在 --approve 时统一消费。

def feedback_mirror_path(out_dir):
    return os.path.join(out_dir, "review", "feedback.json")


def read_mirror_feedback(out_dir, gate):
    """本地镜像里的 pending 意见（无则 []）"""
    p = feedback_mirror_path(out_dir)
    if not os.path.exists(p):
        return []
    try:
        fb = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    if fb.get("gate") != gate or fb.get("status") != "pending":
        return []
    return [i for i in (fb.get("items") or []) if i.get("text")]


def append_mirror_feedback(out_dir, gate, items):
    """把闸文件收集到的意见并入镜像（同闸才合并；已 consumed 则重开 pending）"""
    p = feedback_mirror_path(out_dir)
    cur = []
    try:
        if os.path.exists(p):
            fb = json.load(open(p, encoding="utf-8"))
            if fb.get("gate") == gate:
                cur = [i for i in (fb.get("items") or []) if i.get("text")]
    except Exception:
        cur = []
    seen = {(i.get("target"), i.get("text")) for i in cur}
    added = [i for i in items if (i["target"], i["text"]) not in seen]
    json.dump({"gate": gate, "status": "pending", "items": cur + added},
              open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return added


def fetch_pending_feedback(video_id, gate, out_dir):
    """pending 意见 = 服务端记录 ∪ 本地镜像（按 target+text 去重）。
    网络失败只剩镜像；两路都没有 → []。"""
    items, seen = [], set()

    def add(lst):
        for i in (lst or []):
            k = (str(i.get("target")), str(i.get("text")))
            if k not in seen:
                seen.add(k)
                items.append(i)

    source = "none"
    api_ok = False
    if video_id:
        try:
            import urllib.request
            base = os.environ.get("CONTENT_OPS_API_BASE",
                                  "http://localhost:3002/api/v1").rstrip("/")
            req = urllib.request.Request(f"{base}/videos/{video_id}")
            tok = os.environ.get("CONTENT_OPS_API_TOKEN") or os.environ.get("AGENT_API_KEY")
            if tok:
                req.add_header("Authorization", f"Bearer {tok}")
            with urllib.request.urlopen(req, timeout=8) as r:
                d = (json.loads(r.read().decode("utf-8")) or {}).get("data") or {}
            gf = (d.get("metadata") or {}).get("gate_feedback") or {}
            if gf.get("gate") == gate and gf.get("status") == "pending":
                add([i for i in (gf.get("items") or []) if i.get("text")])
            api_ok = True
        except Exception as e:
            print(f"⚠️  意见拉取失败（内容中心不可达，只用本地镜像）: "
                  f"{type(e).__name__}: {str(e)[:100]}", file=sys.stderr)
    add(read_mirror_feedback(out_dir, gate))
    if api_ok:
        source = "api"
    elif items:
        source = "local"
    return items, source


# ── 写出待审阅文件 ─────────────────────────────────────────────────────

def write_review(out_dir, gate, sb, images_dir=None, feedback=None):
    ensure_review_dir(out_dir)
    shots = sb.get("shots") or []
    # 该闸 pending 意见 → 渲染成 `意见:` 行（regen 消费后随下次 write_review 消失）
    if feedback is None:
        feedback, _src = fetch_pending_feedback(
            (sb or {}).get("video_id") or os.environ.get("VIDEO_RECORD_ID"),
            gate, out_dir)
    fb_by_sid = {}
    for i in (feedback or []):
        t = str(i.get("target") or "")
        if t.startswith("shot-"):
            try:
                fb_by_sid.setdefault(int(t.split("-", 1)[1]), []).append(str(i.get("text")))
            except ValueError:
                pass
    L = []
    if gate == "script":
        L.append("# 台词确认闸（script）\n")
        L.append("> 直接修改每镜下方的台词，保存后执行 `--approve script` 即可应用。")
        L.append("> 界面提交的 `意见:` 行会被自动重生成消费（regen），不必手改正文。")
        L.append("> 不要改动 `## 镜 N` 标题行。\n")
        for s in shots:
            L.append(f"## 镜 {s.get('shot_id')}")
            L.append((s.get("script_line") or (s.get("audio") or {}).get("text") or "").strip())
            for t in fb_by_sid.get(s.get("shot_id"), []):
                L.append(f"意见: {t}")
            L.append("")
    elif gate == "storyboard":
        L.append("# 分镜确认闸（storyboard）\n")
        L.append("> 可修改每镜的「画面」描述（会直接影响生图）与「镜头」语言。")
        L.append("> 保存后执行 `--approve storyboard` 应用。**这是生图前的最后一道闸。**\n")
        for s in shots:
            vis = s.get("visual") or {}
            sl = vis.get("shot_language") or {}
            L.append(f"## 镜 {s.get('shot_id')}")
            L.append((s.get("script_line") or "").strip())
            L.append("")
            L.append(f"画面: {vis.get('prompt') or ''}")
            L.append(f"镜头: {sl.get('shot_size','')}/{sl.get('focal_length','')}/"
                     f"{sl.get('depth_of_field','')}/{sl.get('lighting','')}/"
                     f"{sl.get('color_temperature','')}/{sl.get('camera_movement','')}")
            for t in fb_by_sid.get(s.get("shot_id"), []):
                L.append(f"意见: {t}")
            L.append("")
    elif gate == "images":
        L.append("# 素材确认闸（images）\n")
        L.append("> 每镜在「结论」处填 `通过` 或 `重跑`。填 `重跑` 的会在 "
                 "`--approve images` 时重新生图（其余镜复用，不花钱）。\n")
        for s in shots:
            vis = s.get("visual") or {}
            L.append(f"## 镜 {s.get('shot_id')}")
            L.append((s.get("script_line") or "").strip())
            L.append("")
            L.append(f"文件: {(vis.get('source_ref') or {}).get('path') or vis.get('image_path') or '(未生成)'}")
            L.append(f"画面: {vis.get('prompt') or ''}")
            L.append("结论: 通过")
            for t in fb_by_sid.get(s.get("shot_id"), []):
                L.append(f"意见: {t}")
            L.append("")
    p = review_path(out_dir, gate)
    open(p, "w", encoding="utf-8").write("\n".join(L) + _cost_footer(out_dir, gate, sb))
    return p


# ── 回读编辑 → 应用回分镜 ──────────────────────────────────────────────

def _parse_sections(text):
    """把 review md 按 `## 镜 N` 切成 {shot_id: 正文}"""
    out, cur, buf = {}, None, []
    for line in text.split("\n"):
        if line.startswith("## 镜"):
            if cur is not None:
                out[cur] = "\n".join(buf).strip()
            try:
                cur = int(line.replace("## 镜", "").strip())
            except ValueError:
                cur = None
            buf = []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf).strip()
    return out


def apply_review(out_dir, gate, sb):
    """把 review 文件里的修改回写进分镜；
    返回 (storyboard, 变更说明, 需重跑的镜列表, 闸文件新增意见 items)"""
    p = review_path(out_dir, gate)
    if not os.path.exists(p):
        return sb, [], [], []
    secs = _parse_sections(open(p, encoding="utf-8").read())
    changes, regen, fb_items = [], [], []
    for s in sb.get("shots") or []:
        sid = s.get("shot_id")
        if sid not in secs:
            continue
        body = secs[sid]
        # 「意见:」行 = 人在闸文件里提的段落级反馈 → 收进镜像交给 regen 消费
        fb_lines = [ln[3:].strip() for ln in body.split("\n")
                    if ln.startswith("意见:") and ln[3:].strip()]
        if fb_lines:
            fb_items.extend({"target": f"shot-{sid}", "text": t} for t in fb_lines)
        if gate == "script":
            new = "\n".join(ln for ln in body.split("\n")
                            if not ln.startswith("意见:")).strip()
            old = (s.get("script_line") or "").strip()
            if new and new != old:
                s["script_line"] = new
                s.setdefault("audio", {})["text"] = new
                changes.append(f"镜{sid} 台词已更新")
        elif gate == "storyboard":
            for ln in body.split("\n"):
                if ln.startswith("画面:"):
                    new = ln.split(":", 1)[1].strip()
                    old = (s.get("visual") or {}).get("prompt") or ""
                    if new and new != old:
                        s.setdefault("visual", {})["prompt"] = new
                        changes.append(f"镜{sid} 画面描述已更新")
                elif ln.startswith("镜头:"):
                    parts = [x.strip() for x in ln.split(":", 1)[1].split("/")]
                    if len(parts) == 6:
                        s.setdefault("visual", {}).setdefault("shot_language", {})
                        sl = s["visual"]["shot_language"]
                        for k, v in zip(("shot_size", "focal_length", "depth_of_field",
                                         "lighting", "color_temperature", "camera_movement"), parts):
                            if v:
                                sl[k] = v
        elif gate == "images":
            for ln in body.split("\n"):
                if ln.startswith("结论:") and "重跑" in ln:
                    regen.append(sid)
                    # 清掉 hash，让 --only-missing 认定它"已变化"
                    s.get("visual", {}).pop("source_hash", None)
    return sb, changes, regen, fb_items


def gate_banner(out_dir, gate, sb):
    """停在闸口时给用户看的提示"""
    p = review_path(out_dir, gate)
    n = len(sb.get("shots") or [])
    tip = {
        "script": "台词确认（还没花钱，改台词最便宜）",
        "storyboard": "画面确认（**生图前**最后一道闸，改这里最省钱）",
        "images": "素材确认（勾选「重跑」的镜会重新生图，其余复用）",
    }.get(gate, "")
    return (f"\n⏸  已停在【{gate}】确认闸（{tip}）\n"
            f"    审阅文件: {p}\n"
            f"    共 {n} 镜。编辑该文件后执行:\n"
            f"      run_pipeline.py --storyboard <分镜> --out-dir <产物> --approve {gate}\n"
            f"    若无需修改，直接批准即可继续。\n")
