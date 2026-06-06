"""
异步 Embedding 生成队列
知识入库时标记 pending，后台批量生成向量
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
from typing import Optional

import embedding_service as es
from knowledge_db import DB_PATH, get_connection


MAX_RETRIES = 3
BATCH_SIZE = 10  # DashScope compatible-mode 批量上限
POLL_INTERVAL = 10  # seconds


def _get_pending_items(limit: int = BATCH_SIZE) -> list[dict]:
    """获取待处理的知识条目"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, title, content, tags, tips FROM knowledge WHERE embedding_status = 'pending' LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _mark_computed(kid: str) -> None:
    """标记为已生成向量"""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE knowledge SET embedding_status = 'computed' WHERE id = ?",
            (kid,),
        )
        conn.commit()
    finally:
        conn.close()


def _mark_failed(kid: str) -> None:
    """标记为生成失败"""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE knowledge SET embedding_status = 'failed' WHERE id = ?",
            (kid,),
        )
        conn.commit()
    finally:
        conn.close()


def _build_embedding_text(item: dict) -> str:
    """构建用于 embedding 的文本（拼接 title + content + tags）"""
    parts = [item.get("title", ""), item.get("content", "")]
    tags = item.get("tags", "")
    if isinstance(tags, str) and tags:
        parts.append(tags)
    elif isinstance(tags, list):
        parts.extend(tags)
    tips = item.get("tips", "")
    if isinstance(tips, str) and tips:
        parts.append(tips)
    return " ".join(parts)[:2000]


async def process_pending() -> int:
    """处理一批 pending 条目，返回成功数"""
    if not es.is_available():
        return 0

    items = _get_pending_items()
    if not items:
        return 0

    texts = [_build_embedding_text(item) for item in items]
    embeddings = await es.get_embeddings_batch(texts)

    success_count = 0
    for item, embedding in zip(items, embeddings):
        kid = item["id"]
        if embedding:
            conn = get_connection()
            try:
                es.store_embedding(conn, kid, embedding, _build_embedding_text(item))
                conn.commit()
            finally:
                conn.close()
            _mark_computed(kid)
            success_count += 1
        else:
            _mark_failed(kid)

    return success_count


async def run_worker(poll_interval: int = POLL_INTERVAL) -> None:
    """持续运行的 worker 循环"""
    print(f"[EmbeddingWorker] Started (interval={poll_interval}s, batch={BATCH_SIZE})")
    while True:
        try:
            count = await process_pending()
            if count > 0:
                print(f"[EmbeddingWorker] Processed {count} items")
        except Exception as e:
            print(f"[EmbeddingWorker] Error: {e}")
        await asyncio.sleep(poll_interval)


async def process_all_pending() -> dict:
    """一次性处理所有 pending 条目（用于启动时或手动触发）"""
    if not es.is_available():
        return {"processed": 0, "reason": "embedding service unavailable"}

    total = 0
    while True:
        count = await process_pending()
        if count == 0:
            break
        total += count
    return {"processed": total}


def get_embedding_stats() -> dict:
    """获取 embedding 状态统计"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT embedding_status, COUNT(*) as cnt FROM knowledge GROUP BY embedding_status"
        ).fetchall()
        stats = {r["embedding_status"]: r["cnt"] for r in rows}
        vector_count = conn.execute("SELECT COUNT(*) FROM knowledge_vectors").fetchone()[0]
        return {
            "pending": stats.get("pending", 0),
            "computed": stats.get("computed", 0),
            "failed": stats.get("failed", 0),
            "vectors_stored": vector_count,
            "service_available": es.is_available(),
        }
    finally:
        conn.close()
