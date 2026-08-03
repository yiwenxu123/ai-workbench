#!/usr/bin/env python3
"""
知识入库流水线：抓取 → LLM 提取 → 去重对比 → 待审清单 → 入库

用法:
  # 1) 从 URL 提取（只输出待审清单，不写入）
  python3 scripts/knowledge_pipeline.py --url https://example.com/article \
      --target knowledge --llm-endpoint https://api.deepseek.com/v1/chat/completions \
      --llm-api-key sk-xxx --llm-model deepseek-chat

  # 2) 从文本文件提取
  python3 scripts/knowledge_pipeline.py --file article.txt --target cases ...

  # 3) 提取并直接入库（跳过人工确认）
  python3 scripts/knowledge_pipeline.py --url ... --save

  # 4) 从上次待审清单入库（review 文件由前面命令生成）
  python3 scripts/knowledge_pipeline.py --review-review review-xxx.json --save

输出:
  - 待审清单: scripts/review-<目标类型>-<时间戳>.json
  - 入库结果: 打印新增/替换/重复统计
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from ingest import call_llm, compare_with_existing, fetch_url_content, save_items  # noqa: E402


def _llm_args(args: argparse.Namespace) -> dict:
    return {
        "llm_endpoint": args.llm_endpoint,
        "llm_api_key": args.llm_api_key,
        "llm_model": args.llm_model,
    }


def _verify_llm(args: argparse.Namespace) -> None:
    if not args.llm_endpoint or not args.llm_api_key:
        print("错误: 需要 --llm-endpoint 与 --llm-api-key（可用 --env-file 读取 .env）")
        sys.exit(2)


def _load_env(args: argparse.Namespace) -> None:
    """可选: 从 backend/.env 读取 DASHSCOPE_API_KEY 等配置。"""
    env_file = args.env_file or (BACKEND / ".env")
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os_environ_setdefault(key.strip(), value.strip())


def os_environ_setdefault(key: str, value: str) -> None:
    import os

    if key not in os.environ:
        os.environ[key] = value


def _write_review(items: list[dict], target_type: str) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    out = ROOT / "scripts" / f"review-{target_type}-{ts}.json"
    payload = {
        "generatedAt": ts,
        "targetType": target_type,
        "items": items,
        "stats": {},
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return out


def _load_review(path: Path) -> list[dict]:
    data = json.loads(path.read_text())
    items = data.get("items", [])
    # 剔除 LLM 对比附加字段，仅保留可入库字段
    clean = []
    for item in items:
        item = {k: v for k, v in item.items() if not k.startswith("_")}
        item.pop("_comparison", None)
        clean.append(item)
    return clean


async def _run(args: argparse.Namespace) -> None:
    _load_env(args)

    if args.review:
        # 模式 B: 从待审清单直接入库
        items = _load_review(Path(args.review))
        if not items:
            print("待审清单为空，退出。")
            return
        result = save_items(args.target, items, replace_ids=None)
        total = result.get("added", 0) + result.get("replaced", 0)
        print(f"入库完成: 新增 {result.get('added', 0)}，替换 {result.get('replaced', 0)}，重复跳过 {result.get('duplicates', 0)}")
        print(f"共 {total} 条入库。")
        return

    _verify_llm(args)

    # 模式 A: 抓取 → 提取 → 对比
    if args.url:
        print(f"[1/4] 抓取: {args.url}")
        content = await fetch_url_content(args.url)
        source_url = args.url
    elif args.file:
        print(f"[1/4] 读取文件: {args.file}")
        content = Path(args.file).read_text(encoding="utf-8")
        source_url = None
    else:
        print("错误: 需要 --url 或 --file")
        sys.exit(2)

    print(f"[2/4] LLM 提取（内容 {len(content)} 字，目标 {args.target}）...")
    llm = _llm_args(args)
    items = await call_llm(
        content=content,
        target_type=args.target,
        source_url=source_url,
        **llm,
    )
    now = time.strftime("%Y-%m-%d")
    for item in items:
        item.setdefault("sourceUrl", source_url)
        item.setdefault("updatedAt", now)
        item.setdefault("lastVerifiedAt", now)
        item.setdefault("reviewStatus", "pending")

    print(f"[3/4] 与知识库去重对比（{len(items)} 条）...")
    compared = await compare_with_existing(
        items=items, target_type=args.target, **llm
    )
    stats = {"new": 0, "replace": 0, "duplicate": 0, "keep_both": 0}
    for item in compared:
        verdict = item.get("_comparison", {}).get("verdict", "new")
        stats[verdict] = stats.get(verdict, 0) + 1
    print(f"      对比结果: {stats}")

    review_path = _write_review(compared, args.target)
    print(f"[4/4] 待审清单已生成: {review_path}")

    if args.save:
        clean = _load_review(review_path)
        result = save_items(args.target, clean, replace_ids=None)
        print(f"入库完成: 新增 {result.get('added', 0)}，替换 {result.get('replaced', 0)}，重复跳过 {result.get('duplicates', 0)}")
    else:
        print(f"提示: 人工确认后执行以下命令入库:")
        print(f"  python3 scripts/knowledge_pipeline.py --review {review_path} --target {args.target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="知识入库流水线（抓取→提取→去重→入库）")
    parser.add_argument("--url", help="文章 URL（抓取并提取）")
    parser.add_argument("--file", help="本地文本文件（提取）")
    parser.add_argument("--target", choices=["cases", "knowledge", "templates"], default="knowledge", help="入库目标类型")
    parser.add_argument("--llm-endpoint", help="LLM API 端点")
    parser.add_argument("--llm-api-key", help="LLM API 密钥")
    parser.add_argument("--llm-model", default="deepseek-chat", help="LLM 模型名")
    parser.add_argument("--env-file", help="读取 .env 补充 LLM 配置（默认 backend/.env）")
    parser.add_argument("--review", help="从待审清单 JSON 入库（跳过抓取/提取）")
    parser.add_argument("--save", action="store_true", help="提取后直接入库（跳过人工确认）")
    args = parser.parse_args()

    if args.review and args.url:
        parser.error("--review 与 --url/--file 不能同时使用")
    if not args.review and not args.url and not args.file:
        parser.error("请提供 --url、--file 或 --review 之一")

    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
