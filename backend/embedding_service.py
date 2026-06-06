"""
Embedding 向量服务
调用阿里云 DashScope text-embedding-v4 生成 1024 维向量
使用 OpenAI 兼容模式 endpoint
带优雅降级：无 API key 时跳过向量搜索
"""

from __future__ import annotations

import json
import os
import sqlite3
import struct
from typing import Optional

import httpx

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_ENDPOINT = os.getenv(
    "DASHSCOPE_EMBEDDING_ENDPOINT",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
)
EMBEDDING_MODEL = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")
EMBEDDING_DIM = 1024


def is_available() -> bool:
    """检查 Embedding 服务是否可用"""
    return bool(DASHSCOPE_API_KEY)


async def get_embedding(text: str) -> Optional[list[float]]:
    """获取单条文本的 embedding 向量（OpenAI 兼容格式）"""
    if not DASHSCOPE_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                DASHSCOPE_ENDPOINT,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": text[:2000],
                    "dimensions": EMBEDDING_DIM,
                },
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            result = resp.json()
            data = result.get("data", [])
            if data:
                return data[0].get("embedding", [])
    except Exception as e:
        print(f"Embedding error: {e}")
    return None


_MAX_BATCH_SIZE = 10  # DashScope compatible-mode 单次上限


async def get_embeddings_batch(texts: list[str]) -> list[Optional[list[float]]]:
    """批量获取 embedding（OpenAI 兼容格式），自动分批"""
    if not DASHSCOPE_API_KEY or not texts:
        return [None] * len(texts)

    all_results: list[Optional[list[float]]] = []
    for i in range(0, len(texts), _MAX_BATCH_SIZE):
        chunk = texts[i : i + _MAX_BATCH_SIZE]
        chunk_results = await _get_embeddings_chunk(chunk)
        all_results.extend(chunk_results)
    return all_results


async def _get_embeddings_chunk(texts: list[str]) -> list[Optional[list[float]]]:
    """单批 embedding 请求（≤10 条）"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                DASHSCOPE_ENDPOINT,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": [t[:2000] for t in texts],
                    "dimensions": EMBEDDING_DIM,
                },
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            result = resp.json()
            data = result.get("data", [])
            sorted_emb = sorted(data, key=lambda e: e.get("index", 0))
            return [e.get("embedding", []) for e in sorted_emb]
    except Exception as e:
        print(f"Batch embedding error: {e}")
        return [None] * len(texts)


def embedding_to_bytes(vec: list[float]) -> bytes:
    """将 float 列表转为紧凑的 bytes (float32)"""
    return struct.pack(f"{len(vec)}f", *vec)


def bytes_to_embedding(data: bytes) -> list[float]:
    """将 bytes 还原为 float 列表"""
    count = len(data) // 4
    return list(struct.unpack(f"{count}f", data))


def store_embedding(conn: sqlite3.Connection, knowledge_id: str, embedding: list[float], chunk_text: str = "") -> None:
    """存储向量到 knowledge_vectors 表"""
    conn.execute("""
        INSERT OR REPLACE INTO knowledge_vectors (knowledge_id, chunk_index, chunk_text, embedding)
        VALUES (?, 0, ?, ?)
    """, (knowledge_id, chunk_text, embedding_to_bytes(embedding)))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def vector_search(conn: sqlite3.Connection, query_embedding: list[float], limit: int = 10) -> list[tuple[str, float]]:
    """向量搜索：遍历计算余弦相似度（小规模数据适用）"""
    rows = conn.execute("SELECT knowledge_id, embedding FROM knowledge_vectors").fetchall()
    scored = []
    for kid, emb_bytes in rows:
        if emb_bytes:
            vec = bytes_to_embedding(emb_bytes)
            sim = cosine_similarity(query_embedding, vec)
            scored.append((kid, sim))
    scored.sort(key=lambda x: -x[1])
    return scored[:limit]
