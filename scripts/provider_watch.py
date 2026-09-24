#!/usr/bin/env python3
"""模型巡检 → macOS 通知（P0⑦ 里"主动"的那一半）。

为什么不是"每天弹一次失败清单"：dashscope 欠费这类已知问题天天弹，会把人训练成
划掉通知，那比不提醒更糟。所以只在**故障集合发生变化**时通知 —— 新增故障弹一次，
故障恢复也弹一次（后者重要：它同时证明巡检还活着，不是"没消息=好消息"的错觉）。

巡检自身跑挂同样通知。静默死掉的监控等于没有监控。
状态落在 runs/provider_watch/（runs/ 已 gitignore，定时任务不会弄脏工作区）。

用法:
    python scripts/provider_watch.py            # 巡检 + 按需通知
    python scripts/provider_watch.py --always   # 无论如何都弹（测试通知是否可用）
    python scripts/provider_watch.py --quiet    # 只更新状态，不弹通知
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "check_apis.py"
STATE_DIR = ROOT / "runs" / "provider_watch"
STATE_FILE = STATE_DIR / "last.json"
LATEST_FILE = STATE_DIR / "latest.json"
HISTORY_FILE = STATE_DIR / "history.jsonl"

TITLE = "视频工作流·模型巡检"


def _safe(text: str, n: int = 140) -> str:
    """AppleScript 里嵌的是双引号字符串，且来自接口错误体 —— 先剥掉引号/反斜杠/控制符。"""
    cleaned = "".join(ch for ch in str(text) if ch.isprintable() and ch not in '"\\')
    return " ".join(cleaned.split())[:n]


def notify(body: str) -> None:
    script = (f'display notification "{_safe(body)}" '
              f'with title "{TITLE}" sound name "Glass"')
    subprocess.run(["osascript", "-e", script], check=False, timeout=30)


def run_check() -> dict:
    """用**当前解释器**跑巡检 —— 定时任务那边必须指 .venv-pyjd，
    否则 backend/.venv 里没有 edge-tts，降级链兜底会被记成 skip。"""
    r = subprocess.run([sys.executable, str(CHECK), "--json"],
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"check_apis 退出码 {r.returncode}: {_safe(r.stderr, 200)}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"巡检输出不是 JSON（{e}）: {_safe(r.stdout, 200)}") from e


def _provider_key(raw: str) -> str:
    return re.split(r"[//(（]", raw)[0].strip()


def failed_set(data: dict) -> list[str]:
    """按 provider/网关归并：百炼一次故障会同时报出 6 行，通知里合成 1 行更可读，
    具体模型名与原因留在 latest.json 的 failures 明细里查。"""
    return sorted({_provider_key(c.get("provider") or "")
                   for c in data.get("checks", []) if c.get("status") == "fail"})


def failure_detail(data: dict) -> list[dict]:
    """故障逐条明细（面板要看「为什么失败」，只看归并后的 provider 名不够用）。
    只带脱敏后的短字段：detail 截 180 字，绝不回传密钥/端点以外的凭据信息。"""
    out = []
    for c in data.get("checks", []):
        if c.get("status") != "fail":
            continue
        out.append({
            "provider": _provider_key(c.get("provider") or ""),
            "check": (c.get("provider") or "").strip(),
            "capability": c.get("capability") or "",
            "status_code": c.get("status_code"),
            "detail": _safe(c.get("detail") or "", 180),
        })
    return sorted(out, key=lambda x: (x["provider"], x["capability"]))


def read_prev() -> dict | None:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_state(payload: dict) -> None:
    """latest.json = 美观全量（含 failures 明细，供面板读）；
    last.json = 单行基线；history.jsonl 每轮一行，只留判定所需的字段。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LATEST_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    STATE_FILE.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    slim = {k: payload.get(k) for k in ("ran_at", "passed", "skipped", "failed")}
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(slim, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="模型巡检并按变化推送 macOS 通知")
    ap.add_argument("--always", action="store_true", help="无条件弹一条（验证通知通道）")
    ap.add_argument("--quiet", action="store_true", help="只更新状态，不发通知")
    args = ap.parse_args()

    stamp = datetime.now().astimezone().isoformat(timespec="seconds")

    try:
        data = run_check()
    except Exception as e:  # noqa: BLE001
        # 跑不成也要留痕并告警：解释器被换掉、脚本被移动都会走这里
        if not args.quiet:
            notify(f"巡检本身没跑起来：{_safe(e)}")
        print(f"❌ 巡检执行失败: {e}", file=sys.stderr)
        return 2

    now_failed = failed_set(data)
    prev = read_prev()
    was_failed = sorted(prev.get("failed", [])) if prev else []

    state = {"ran_at": stamp, "failed": now_failed, "prev_failed": was_failed,
             "passed": data.get("passed"), "skipped": data.get("skipped"),
             "failures": failure_detail(data), "interpreter": sys.executable}
    write_state(state)

    if args.always:
        notify(f"通知通道正常。当前失败 {len(now_failed)} 项："
               f"{'、'.join(now_failed) or '无'}")
        return 0
    if args.quiet:
        return 0

    first_run = prev is None
    if first_run:
        # 首次没有基线可比：全量报一遍，之后每次只报差集
        notify(f"首次巡检基线：{len(now_failed)} 项不可用 —— "
               f"{'、'.join(now_failed) or '无'}")
    elif not now_failed and was_failed:
        notify(f"已恢复 {len(was_failed)} 项：{'、'.join(was_failed)}")
    elif now_failed != was_failed:
        added = [x for x in now_failed if x not in was_failed]
        removed = [x for x in was_failed if x not in now_failed]
        msg = (f"新增不可用：{'、'.join(added)}" if added
               else f"{len(now_failed)} 项不可用")
        if removed:
            msg += f"；同时恢复：{'、'.join(removed)}"
        notify(msg + "（详见 runs/provider_watch/latest.json）")
    else:
        print("故障集合未变化，静默。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
