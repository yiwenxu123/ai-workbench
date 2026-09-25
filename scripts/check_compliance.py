#!/usr/bin/env python3
"""
合规闸（先审后播）—— 台词/字幕/标题的敏感词检查

为什么放在引擎侧而不是直接写死在 Python 里：
  敏感词表是**内容运营的资产**，会持续增补，且已在内容中心沉淀
  （`rule-engine` 内置 sensitive_words + `audit_rules` 集合的自定义规则，
   见 `POST /api/v1/audit-rules`）。本脚本只做「取文本 → 调内容中心 → 落结论」，
   **一个敏感词都不硬编码** —— 加词只需在内容中心建一条规则，引擎侧零改动。

位置：紧跟在 srt 之后（`run_pipeline` 里排在生图之前），
  这样台词有问题时能在**花钱之前**拦下（与 P2-1「决策权前移到免费阶段」同思路）。

检查哪些文本（按可定位性优先）：
  1) 台词    逐镜（script_line / audio.text），label 形如「镜3」——最便于人工定位；
  2) 字幕    out/subtitles.srt。字幕是台词的确定性派生，内容相同时**不重复送检**；
             仅当 SRT 被手工改过（与台词拼合结果不一致）才额外送检，避免同一处命中报两遍；
  3) 标题    out/cover.json 里的标题候选（若已生成）——封面标题也会对外露出。
     ⚠️ 合规闸排在 cover 之前（刻意：台词有问题要在花钱前拦下），首次送检时标题还没生成；
     cover 跑完后 run_pipeline 会用 `--titles-only` **补检一次**（结论合并进同一份
     compliance.json，不覆盖台词/字幕的既有结论），把「标题未判敏感词」这个口补上。

降级策略（重要，与「先审后播」的分工）：
  内容中心不可达 / 返回异常时**不阻断管线**（避免中心抖动导致整条视频白跑），
  但 compliance.json 记 `degraded: true` 且 `passed: false`；
  内容中心的「先审后播」门禁只认 `status == 'passed'`，degraded 不等于通过，
  因此**发布仍会被拦**，只是不浪费已完成的制作。

产物：out/compliance.json（真相源：逐条命中明细 + 结论 + 覆盖到的来源）

退出码：0=通过或降级（都不阻断管线）；5=**确有**命中阻断级词（供 run_pipeline 判定并停 compliance_failed）
  ⚠️ 判据是「blockedCount > 0」，不是「passed == False」—— 后者会把降级也判成阻断。

用法：
  check_compliance.py --storyboard sb.json --out-dir out/ \
      [--srt out/subtitles.srt] [--api-base http://localhost:3002/api/v1] \
      [--block-severities critical,high] [--timeout 20] [--titles-only]
"""
import argparse
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request

EXIT_BLOCKED = 5

# 命中这些级别即判「不可播」——与内容中心 ComplianceChecker 的默认口径一致
DEFAULT_BLOCK_SEVERITIES = ["critical", "high"]


def norm_text(s: str) -> str:
    """归一化：去掉所有空白与标点，只留实义字符（用于判断字幕是否被改过）。"""
    return re.sub(r"[\s\W_]+", "", s or "", flags=re.UNICODE)


def shot_script(shot: dict) -> str:
    audio = shot.get("audio") or {}
    return (audio.get("text") or shot.get("script_line") or "").strip()


def srt_plain_text(path: str) -> str:
    """SRT → 纯文本（去掉序号行与时间轴行）。文件不存在返回 ''。"""
    if not path or not os.path.exists(path):
        return ""
    try:
        raw = open(path, encoding="utf-8").read()
    except Exception as e:
        print(f"⚠️  读取字幕失败 {path}: {type(e).__name__}: {e}", file=sys.stderr)
        return ""
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.isdigit() or "-->" in s:
            continue
        lines.append(s)
    return "\n".join(lines)


def cover_titles(out_dir: str) -> list:
    """读 out/cover.json 的标题候选（可能不存在——cover 阶段排在合规之后）。"""
    p = os.path.join(out_dir, "cover.json")
    if not os.path.exists(p):
        return []
    try:
        cj = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    out = []
    for t in cj.get("titles") or []:
        if isinstance(t, dict) and t.get("text"):
            out.append({"style": t.get("style") or "", "text": str(t["text"])})
        elif isinstance(t, str) and t.strip():
            out.append({"style": "", "text": t.strip()})
    return out


def build_texts(sb: dict, out_dir: str, srt_path: str, titles_only: bool = False) -> tuple:
    """组装待检文本 + 覆盖说明。返回 (texts, sources_note)

    titles_only（v5.1 P3-2 补口）：只检标题候选。为补历史缺口 —— 合规闸排在 cover 之前
    （刻意如此：台词有问题要在花钱前拦下），于是**标题候选在首次送检时还不存在**，
    而标题恰恰是对外露出的内容。cover 跑完后再补一次，见 run_pipeline 的 titles 复核。
    """
    texts, sources = [], []

    if titles_only:
        titles = cover_titles(out_dir)
        for t in titles:
            texts.append({"source": "title", "label": t["style"] or "标题候选", "text": t["text"]})
        sources.append(f"标题候选({len(titles)}条)" if titles else "标题候选(尚未生成)")
        return texts, sources

    shots = sb.get("shots") or []
    shot_lines = []
    for i, shot in enumerate(shots, 1):
        t = shot_script(shot)
        if not t:
            continue
        shot_lines.append(t)
        texts.append({"source": "script", "label": f"镜{i}", "text": t})
    if shot_lines:
        sources.append(f"台词({len(shot_lines)}镜)")

    srt_text = srt_plain_text(srt_path)
    if srt_text:
        if norm_text(srt_text) == norm_text("".join(shot_lines)):
            # 字幕由台词确定性派生，内容一致 —— 送检只会把同一处命中报两遍
            sources.append("字幕(与台词一致，已跳过重复送检)")
        else:
            texts.append({
                "source": "subtitle",
                "label": os.path.basename(srt_path),
                "text": srt_text,
            })
            sources.append("字幕(与台词不一致，已单独送检)")
    else:
        sources.append("字幕(未找到)")

    titles = cover_titles(out_dir)
    for t in titles:
        texts.append({"source": "title", "label": t["style"] or "标题候选", "text": t["text"]})
    if titles:
        sources.append(f"标题候选({len(titles)}条)")
    else:
        sources.append("标题候选(尚未生成)")

    return texts, sources


def call_api(api_base: str, texts: list, block_severities: list, timeout: int) -> dict:
    """调内容中心合规端点。返回 result dict；失败抛异常。"""
    url = api_base.rstrip("/") + "/audit/compliance"
    body = json.dumps({"texts": texts, "blockSeverities": block_severities}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not payload.get("success"):
        raise RuntimeError(payload.get("error") or "内容中心返回 success=false")
    return payload.get("result") or {}


def main():
    ap = argparse.ArgumentParser(description="合规闸（先审后播）")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--srt", default=None, help="字幕路径；默认 <out-dir>/subtitles.srt")
    ap.add_argument("--api-base", default=None,
                    help="内容中心 API 基址；默认取环境变量 CONTENT_OPS_API_BASE，再缺省 localhost:3002")
    ap.add_argument("--block-severities", default=",".join(DEFAULT_BLOCK_SEVERITIES),
                    help="命中即阻断的严重度（逗号分隔），默认 critical,high")
    ap.add_argument("--timeout", type=int, default=20, help="HTTP 超时秒数，默认 20")
    ap.add_argument("--titles-only", action="store_true",
                    help="只检标题候选（cover 跑完后的补检；结论**合并**进已有 compliance.json，"
                         "不覆盖台词/字幕的既有结论）")
    args = ap.parse_args()

    sb_path = os.path.abspath(os.path.expanduser(args.storyboard))
    out = os.path.abspath(os.path.expanduser(args.out_dir))
    srt_path = os.path.abspath(os.path.expanduser(args.srt or os.path.join(out, "subtitles.srt")))
    api_base = (args.api_base or os.environ.get("CONTENT_OPS_API_BASE")
                or "http://localhost:3002/api/v1")
    block_severities = [s.strip() for s in args.block_severities.split(",") if s.strip()]

    sb = json.load(open(sb_path, encoding="utf-8"))
    texts, sources = build_texts(sb, out, srt_path, titles_only=args.titles_only)

    print(f"🔍 合规检查: {len(texts)} 段文本  ←  {'；'.join(sources)}")
    if not texts:
        print("ℹ️  没有可检文本，跳过（视为通过）")

    result, degraded, err_msg = {}, False, ""
    if texts:
        try:
            result = call_api(api_base, texts, block_severities, args.timeout)
        except urllib.error.HTTPError as e:
            degraded, err_msg = True, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            degraded, err_msg = True, f"无法连接（{e.reason}）"
        except Exception as e:
            degraded, err_msg = True, f"{type(e).__name__}: {e}"

    report = {
        "checked_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "api_base": api_base,
        "sources": sources,
        "block_severities": block_severities,
        "degraded": degraded,
        "error": err_msg,
        # 降级时 passed 一律为 false —— 「没查过」不等于「查过了没问题」，
        # 否则先审后播的发布门禁会被中心抖动绕过。
        "passed": bool(result.get("passed")) if not degraded else False,
        "severity": result.get("severity") or ("unknown" if degraded else "none"),
        "counts": result.get("counts") or {},
        "hits": result.get("hits") or [],
        "hitCount": result.get("hitCount", 0),
        "blockedCount": result.get("blockedCount", 0),
        "rulesApplied": result.get("rulesApplied") or [],
    }

    os.makedirs(out, exist_ok=True)
    out_path = os.path.join(out, "compliance.json")

    # titles 补检合并（v5.1 P3-2）：不能整份覆盖 —— 否则「只检标题」的补检会把此前
    # 台词/字幕的结论与命中明细冲掉，等于用一次局部检查抹掉整条合规历史。
    # 合并口径：命中并集 + passed = 本次通过 **且** 既有通过（任一侧没过就是没过）；
    # degraded 同理取或（任一侧没查成 → 整体不算查过，发布门禁仍拦）。
    if args.titles_only:
        prev = {}
        if os.path.exists(out_path):
            try:
                prev = json.load(open(out_path, encoding="utf-8"))
            except Exception as e:
                print(f"⚠️  既有 compliance.json 读取失败（按首次送检处理）: {type(e).__name__}: {e}",
                      file=sys.stderr)
        if prev:
            merged_hits = list(prev.get("hits") or []) + list(report.get("hits") or [])
            prev_sources = [s for s in (prev.get("sources") or []) if "标题候选" not in str(s)]
            report["hits"] = merged_hits
            report["sources"] = prev_sources + sources
            report["passed"] = bool(report.get("passed")) and bool(prev.get("passed"))
            report["degraded"] = bool(report.get("degraded")) or bool(prev.get("degraded"))
            if prev.get("checked_at"):
                report["checked_at"] = prev["checked_at"]      # 首次送检时间（覆盖口径）
            report["titlesCheckedAt"] = datetime.datetime.now().isoformat(timespec="seconds")
            # 计数按合并后的命中重算，避免保留旧 counts 与明细对不上
            report["hitCount"] = len(merged_hits)
            report["blockedCount"] = sum(
                1 for h in merged_hits if h.get("severity") in block_severities)
            if report["blockedCount"]:
                report["severity"] = "blocked"
            elif not prev.get("severity") or prev.get("severity") == "none":
                report["severity"] = report.get("severity") or "none"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 阻断判据（v5.1 P3-2 修正）：**真的命中了阻断级词**才算未过。
    # 此前用「passed == False 就 exit 5」，而降级时 passed 恒为 False → 内容中心一抖动
    # 就把「不阻断管线」的设计变成「整条视频白跑」，与本文件头「降级策略」自相矛盾。
    # 降级 / 未完成检查一律 exit 0（发布门禁仍会拦，因为只认 status=='passed'）。
    blocked = bool(report.get("blockedCount")) or report.get("severity") == "blocked"

    if blocked:
        print(f"❌ 合规未过：命中 {report['blockedCount']} 处（{report['severity']} 级）", file=sys.stderr)
        for h in report["hits"][:10]:
            if h.get("severity") in block_severities:
                print(f"    [{h.get('severity')}] {h.get('source')}/{h.get('label')}: "
                      f"「{h.get('word')}」… {h.get('snippet')}", file=sys.stderr)
        print(f"    明细: {out_path}", file=sys.stderr)
    elif report.get("degraded"):
        # 可能是本次降级，也可能是 titles 补检合并进来的历史降级 —— 口径一致：不算通过
        print(f"⚠️降级  合规检查降级（{err_msg or '历史降级（见 compliance.json）'}）："
              f"**未完成检查**，不阻断管线，但任务不会被标记为「已过合规」，发布仍会被拦",
              file=sys.stderr)
    else:
        print(f"✅ 合规通过（未命中 {','.join(block_severities)} 级词）"
              f"{'，另有 ' + str(report['hitCount']) + ' 处低级别提示' if report['hitCount'] else ''}")
    print(f"📄 结论: {out_path}")

    sys.exit(EXIT_BLOCKED if blocked else 0)


if __name__ == "__main__":
    main()
