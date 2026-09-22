#!/usr/bin/env python3
"""
段落级意见重生成（P1-b D5）——把「人对某一镜提的意见」变成「分镜里该镜的新内容」。

数据流（单向）：
  Web/面板/闸文件「意见:」行 → 内容中心 metadata.gate_feedback（服务端） 
  → 本脚本拉取 pending → LLM 按意见改写目标镜的字段 → 回写分镜 JSON → 服务端清空（consumed）。

- 改写范围按闸收敛：script 只动台词；storyboard/images 只动画面描述
  （镜头语言六字段太结构化，LLM 易写飞，仍走人直接改 review md）。
- 意见里写 `改成「…」` 视为**精确替换**，不过 LLM（离线兜底、意图零失真）。
- LLM 走内容中心 /agent/llm/chat（与 MCP generate_storyboard 同一家）；
  不可达时该条意见保留在本地镜像 feedback.json，人工照 md 手改，不静默吞。
- 无 pending 意见 → exit 0 空操作（run_pipeline --approve 每次都可以先调它）。

用法：
  regen_shots.py --storyboard sb.json --out-dir DIR --gate script \
      [--video-id <videos记录id>] [--shots 3,5] [--dry-run]
"""
import argparse
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API_BASE_DEFAULT = "http://localhost:3002/api/v1"
# 精确替换语法：意见中含 改成「X」/改为「X」/换成「X」 → 字段整体替换为 X，不调 LLM
PRECISE_RE = re.compile(r"(?:改成|改为|换成)\s*[「\"](.+?)[」\"]", re.S)


def _base():
    return os.environ.get("CONTENT_OPS_API_BASE", API_BASE_DEFAULT).rstrip("/")


def _headers():
    h = {"Content-Type": "application/json"}
    tok = os.environ.get("CONTENT_OPS_API_TOKEN") or os.environ.get("AGENT_API_KEY")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def http_json(url, body=None, method=None, timeout=15):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(),
                                 method=method or ("POST" if data else "GET"))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def rewrite_by_llm(field_label, shot_view, feedback_text, gate):
    """让 LLM 按意见重写目标字段；返回新文本，失败返回 None。"""
    system = (
        "你是短视频分镜修订助手。按人工意见改写口播文案中的指定字段。"
        "只输出 JSON 对象（形如 {\"new_text\": \"...\"}），不要输出解释或代码块标记。"
        "要求：保持与原字段相同的语言与人设口吻；改动只服务于意见本身；"
        "台词要口语化、可直接朗读；画面描述要具体可拍（主体/动作/环境/光线），"
        f"总长不超过原文的 1.3 倍。{gate_hint(gate)}"
    )
    user = (
        f"字段：{field_label}\n当前内容：{shot_view.get('cur')}\n"
        f"人工意见：{shot_view.get('feedback')}\n"
        f"该镜上下文：台词=「{shot_view.get('script_line', '')[:120]}」 "
        f"画面=「{shot_view.get('prompt', '')[:160]}」"
    )
    try:
        d = http_json(f"{_base()}/agent/llm/chat",
                      {"system": system, "user": user,
                       "temperature": 0.5, "max_tokens": 1200, "role": "generate"},
                      timeout=90)
        content = ((d.get("data") or {}).get("content") or "").strip()
        if not content:
            return None
        m = re.search(r"\{.*\}", content, re.S)
        new = json.loads(m.group(0)).get("new_text") if m else None
        new = str(new or "").strip()
        return new or None
    except Exception as e:
        print(f"    ⚠️  LLM 改写失败: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
        return None


def gate_hint(gate):
    return {
        "script": "这是配音台词：不要加入无法朗读的符号（括号注释、星号）。",
        "storyboard": "这是文生图画面描述：输出单段中文描述，不要分点、不要镜头术语堆砌。",
        "images": "这是文生图画面描述：输出单段中文描述，针对意见指出的画面问题定向修正。",
    }.get(gate, "")


def apply_feedback(sb, gate, items):
    """按意见逐条改写分镜（就地修改 sb）。返回 (affected 镜号列表, 未消费意见列表)。"""
    shots = {s.get("shot_id"): s for s in (sb.get("shots") or [])}
    field = "script_line" if gate == "script" else "prompt"
    label = "口播台词" if field == "script_line" else "画面描述(visual.prompt)"
    affected, leftover = [], []
    for it in items:
        m = re.fullmatch(r"shot-(\d+)", str(it.get("target") or ""))
        sid = int(m.group(1)) if m else None
        shot = shots.get(sid) or shots.get(str(sid))
        if not shot:
            print(f"    ⚠️  {it.get('target')}: 分镜里不存在，意见丢弃", file=sys.stderr)
            continue
        text = str(it.get("text") or "").strip()
        vis = shot.get("visual") or {}
        cur = (shot.get("script_line") if field == "script_line" else vis.get("prompt")) or ""
        precise = PRECISE_RE.search(text)
        if precise:
            new = precise.group(1).strip()
            how = "精确替换"
        else:
            new = rewrite_by_llm(label, {
                "cur": cur, "feedback": text,
                "script_line": shot.get("script_line") or "",
                "prompt": vis.get("prompt") or "",
            }, text, gate)
            how = "LLM 改写"
        if not new:
            leftover.append(it)
            print(f"    ❌ 镜{sid}: 改写失败（{how}），意见保留待人工处理")
            continue
        if field == "script_line":
            shot["script_line"] = new
            shot.setdefault("audio", {})["text"] = new
        else:
            # 素材闸：prompt 变了 → 旧图作废（清 hash 让增量重生成认账为「已变化」）
            vis["prompt"] = new
            shot.setdefault("visual", {}).pop("source_hash", None)
        affected.append(sid)
        print(f"    ✅ 镜{sid}: {label} 已重写（{how}）")
        print(f"       旧: {cur[:40]}{'…' if len(cur) > 40 else ''}")
        print(f"       新: {new[:40]}{'…' if len(new) > 40 else ''}")
    return sorted(set(affected)), leftover


def main():
    ap = argparse.ArgumentParser(description="段落级意见 → 分镜重生成（P1-b）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--gate", required=True, choices=["script", "storyboard", "images"])
    ap.add_argument("--video-id", default=None, help="内容中心 videos 记录 id（有则与服务端同步）")
    ap.add_argument("--shots", default=None,
                    help="只消费这些镜号的意见（缺省消费该闸全部 pending）")
    ap.add_argument("--dry-run", action="store_true", help="只打印将做什么，不改分镜不清意见")
    args = ap.parse_args()

    sb_path = os.path.expanduser(args.storyboard)
    sb = json.load(open(sb_path, encoding="utf-8"))
    import gates
    items, src = gates.fetch_pending_feedback(args.video_id, args.gate,
                                              os.path.expanduser(args.out_dir))
    if args.shots:
        want = {f"shot-{x.strip()}" for x in args.shots.replace("，", ",").split(",") if x.strip()}
        items = [i for i in items if str(i.get("target")) in want]
    if not items:
        print(f"ℹ️  【{args.gate}】闸无 pending 意见（来源: {src}），空操作")
        print(json.dumps({"affected": [], "leftover": 0}, ensure_ascii=False))
        return

    print(f"🔁 【{args.gate}】闸收到 {len(items)} 条意见（{src}），开始按意见重生成…")
    if args.dry_run:
        for i in items:
            print(f"    （dry-run）{i.get('target')}: {str(i.get('text'))[:60]}")
        return

    affected, leftover = apply_feedback(sb, args.gate, items)
    out_dir_pre = os.path.expanduser(args.out_dir)

    if affected:
        try:
            from storyboard_schema import validate
            errs = [x for x in validate(sb) if x["level"] == "error"]
            if errs:
                for e in errs[:5]:
                    print(f"❌ 契约 {e['path']}: {e['msg']}", file=sys.stderr)
                print("❌ 改写后分镜不再符合契约，**未写回**（意见保留）", file=sys.stderr)
                sys.exit(1)
        except ImportError:
            pass
        with open(sb_path, "w", encoding="utf-8") as f:
            json.dump(sb, f, ensure_ascii=False, indent=2)
        print(f"📝 分镜已更新: {sb_path}（重写镜 {affected}）")
        # 记下被重写的镜：下次 --approve 时只重跑这些阶段（增量，不整批重烧）
        os.makedirs(os.path.join(out_dir_pre, "review"), exist_ok=True)
        json.dump(affected, open(os.path.join(out_dir_pre, "review",
                                              "affected_shots.json"), "w",
                                 encoding="utf-8"), ensure_ascii=False)

    # 消费记录：本地镜像 +（可达时）服务端清空；失败的意见留在 pending 里
    out_dir = os.path.expanduser(args.out_dir)
    mirror = os.path.join(out_dir, "review", "feedback.json")
    os.makedirs(os.path.dirname(mirror), exist_ok=True)
    json.dump({"gate": args.gate, "status": "pending" if leftover else "consumed",
               "items": leftover},
              open(mirror, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if args.video_id and not leftover:
        try:
            http_json(f"{_base()}/videos/{args.video_id}/feedback",
                      {"gate": args.gate, "items": []}, method="POST", timeout=8)
            print("📡 服务端意见已标记消费")
        except Exception as e:
            print(f"⚠️  服务端清空失败（镜像已消费，重跑本脚本会幂等空操作）: "
                  f"{type(e).__name__}: {str(e)[:100]}", file=sys.stderr)

    print(json.dumps({"affected": affected, "leftover": len(leftover)}, ensure_ascii=False))
    if leftover:
        print(f"⚠️  {len(leftover)} 条意见未能自动改写，保留在 pending —— "
              f"可直接编辑闸文件（画面/台词字段，或写 `改成「…」` 精确替换后重跑本脚本）",
              file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
