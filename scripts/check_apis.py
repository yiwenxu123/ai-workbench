#!/usr/bin/env python3
"""
API 兼容性巡检脚本
对 backend/.env 中配置的每家平台发最小冒烟请求（不耗额度），输出可用性表格。

用法:
    python scripts/check_apis.py                # 输出表格
    python scripts/check_apis.py --json         # JSON 输出 (CI/定时任务友好)
    python scripts/check_apis.py --exit-code    # 任一检查失败时退出码为 1

判定规则 (与后端 /validate-api 一致):
    2xx / 400 / 422 → ✅ 端点可达 + 认证通过 (400 为参数校验, 不产生真实生成)
    401 → ❌ API 密钥无效或已过期
    403 → ❌ 无权限 (密钥权限不足或账户余额不足)
    404 → ❌ API 端点地址错误
    其他 4xx/5xx → ⚠️ 接口可能已变更, 需人工确认
    超时/连接错误  → ❌ 网络或端点不可达

巡检记录写入 docs/api-watch.md (见 --watch 选项)。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

TIMEOUT = 12.0


@dataclass
class CheckResult:
    provider: str
    capability: str
    status: str  # ok | fail | skip
    status_code: int
    detail: str


def _classify(response: httpx.Response) -> tuple[str, str]:
    code = response.status_code
    if code in (200, 201, 400, 422):
        return "ok", "端点可达 + 认证通过"
    if code == 401:
        return "fail", "API密钥无效或已过期"
    if code == 403:
        return "fail", "无权限（密钥权限/账户余额）"
    if code == 404:
        return "fail", "API端点地址错误"
    return "fail", f"接口可能已变更，HTTP {code}: {response.text[:120]}"


def _smoke(label: str, capability: str, endpoint: str, api_key: str,
           payload: dict, results: list[CheckResult]) -> None:
    if not endpoint or not api_key:
        results.append(CheckResult(label, capability, "skip", 0, "未配置 (backend/.env 缺少密钥或端点)"))
        return
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(endpoint, json=payload, headers=headers)
        status, detail = _classify(resp)
        results.append(CheckResult(label, capability, status, resp.status_code, detail))
    except httpx.TimeoutException:
        results.append(CheckResult(label, capability, "fail", 0, "连接超时"))
    except httpx.ConnectError:
        results.append(CheckResult(label, capability, "fail", 0, "无法连接到端点（网络/DNS）"))
    except Exception as e:  # noqa: BLE001
        results.append(CheckResult(label, capability, "fail", 0, f"异常: {e}"))


def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = []

    image_endpoint = os.getenv("API_ENDPOINT", "")
    image_key = os.getenv("API_KEY", "")
    if image_endpoint and "multimodal-generation" in image_endpoint:
        image_payload = {
            "model": "qwen-image-2.0-pro",
            "input": {"messages": [{"role": "user", "content": [{"text": "test"}]}]},
            "parameters": {"size": "1024*1024", "n": 1},
        }
    else:
        image_payload = {"prompt": "test", "model": "default", "size": "256x256", "n": 1}
    _smoke("豆包/通义图像", "image", image_endpoint, image_key, image_payload, results)

    _smoke("可灵", "video",
           os.getenv("KLING_API_ENDPOINT", ""),
           os.getenv("KLING_API_KEY", ""),
           {"prompt": "test", "model": "kling-v1", "duration": 3, "resolution": "720p"},
           results)

    _smoke("即梦", "video",
           os.getenv("JIMENG_API_ENDPOINT", ""),
           os.getenv("JIMENG_API_KEY", ""),
           {"prompt": "test", "model": "jimeng-v1", "duration": 3, "resolution": "720p"},
           results)

    _smoke("Runway", "video",
           os.getenv("RUNWAY_API_ENDPOINT", ""),
           os.getenv("RUNWAY_API_KEY", ""),
           {"prompt": "test", "model": "runway-gen3", "duration": 3, "resolution": "720p"},
           results)

    edit_endpoint = os.getenv("ALIYUN_EDIT_API_ENDPOINT", "")
    edit_key = os.getenv("ALIYUN_API_KEY", "")
    if edit_endpoint:
        edit_payload = {
            "model": "wanx2.1-imageedit",
            "input": {
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "instruction": "test",
            },
        }
    else:
        edit_payload = {}
    _smoke("阿里万相编辑", "edit", edit_endpoint, edit_key, edit_payload, results)

    embed_endpoint = os.getenv("DASHSCOPE_EMBEDDING_ENDPOINT", "")
    embed_key = os.getenv("DASHSCOPE_API_KEY", "")
    if embed_endpoint and "dashscope" in embed_endpoint:
        embed_payload = {"model": os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4"),
                         "input": {"texts": ["test"]}}
    else:
        embed_payload = {"model": "text-embedding-v4", "input": {"texts": ["test"]}}
    _smoke("DashScope向量", "embedding", embed_endpoint, embed_key, embed_payload, results)

    return results


def _render_table(results: list[CheckResult]) -> str:
    lines = [f"# AI 绘图工作台 API 巡检报告 — {date.today().isoformat()}",
             "",
             "| 供应商 | 能力 | 状态 | HTTP | 详情 |",
             "|--------|------|------|------|------|"]
    for r in results:
        icon = {"ok": "✅", "fail": "❌", "skip": "⚠️"}[r.status]
        code = str(r.status_code) if r.status_code else "-"
        lines.append(f"| {r.provider} | {r.capability} | {icon} | {code} | {r.detail} |")
    lines.append("")
    active = [r for r in results if r.status != "skip"]
    passed = sum(1 for r in active if r.status == "ok")
    lines.append(f"**结果**: {passed}/{len(active)} 通过，跳过 {len(results) - len(active)} 项未配置")
    return "\n".join(lines)


def append_to_watch(results: list[CheckResult]) -> None:
    watch = ROOT / "docs" / "api-watch.md"
    section = ["", f"## {date.today().isoformat()}", ""]
    for r in results:
        icon = {"ok": "✅", "fail": "❌", "skip": "⚠️"}[r.status]
        section.append(f"- **{r.provider}** ({r.capability}): {icon} HTTP {r.status_code or '-'} — {r.detail}")
    if watch.exists():
        content = watch.read_text(encoding="utf-8")
        header, sep, rest = content.partition("---")
        if sep:
            content = f"{header}{sep}{rest}"
            insert_at = content.find("## ")
            content = content[:insert_at] + "\n".join(section).strip() + "\n" + content[insert_at:]
        else:
            content += "\n".join(section) + "\n"
    else:
        content = f"# API 变更巡检记录\n\n自动巡检追加在此。手动记录平台接口变更请按日期追加。\n" + "\n".join(section) + "\n"
    watch.parent.mkdir(parents=True, exist_ok=True)
    watch.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="API 兼容性巡检")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--exit-code", action="store_true", help="任一失败时退出码 1")
    parser.add_argument("--watch", action="store_true", help="追加巡检记录到 docs/api-watch.md")
    args = parser.parse_args()

    start = time.monotonic()
    results = run_checks()
    elapsed = time.monotonic() - start

    if args.json:
        print(json.dumps({
            "date": date.today().isoformat(),
            "elapsed_s": round(elapsed, 2),
            "checks": [asdict(r) for r in results],
            "passed": sum(1 for r in results if r.status == "ok"),
            "failed": sum(1 for r in results if r.status == "fail"),
            "skipped": sum(1 for r in results if r.status == "skip"),
            "total": len(results),
        }, ensure_ascii=False, indent=2))
    else:
        print(_render_table(results))
        print(f"耗时 {elapsed:.1f}s")

    if args.watch:
        append_to_watch(results)
        print(f"已追加记录: docs/api-watch.md")

    if args.exit_code:
        return 1 if any(r.status == "fail" for r in results) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
