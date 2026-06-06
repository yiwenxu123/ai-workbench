"""
SQLite + FTS5 知识库存储
替代 JSON 文件，支持全文搜索
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).parent / "data" / "knowledge.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """初始化数据库 schema（幂等）"""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT '',
                quality REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                tips TEXT DEFAULT '[]',
                prompt TEXT DEFAULT '',
                negative_prompt TEXT DEFAULT '',
                model TEXT DEFAULT '',
                scene_relevance TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]',
                related_terms TEXT DEFAULT '[]',
                examples TEXT DEFAULT '[]',
                last_verified TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT '',
                embedding_status TEXT DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS templates (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT DEFAULT '',
                description TEXT DEFAULT '',
                prompt TEXT NOT NULL,
                negative_prompt TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                task_type TEXT DEFAULT 'image',
                audience TEXT DEFAULT '',
                required_fields TEXT DEFAULT '[]',
                recommended_model TEXT DEFAULT '',
                recommended_size TEXT DEFAULT '',
                source TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT DEFAULT '',
                description TEXT DEFAULT '',
                prompt TEXT NOT NULL,
                negative_prompt TEXT DEFAULT '',
                model TEXT DEFAULT '',
                size TEXT DEFAULT '',
                tips TEXT DEFAULT '[]',
                tags TEXT DEFAULT '[]',
                author TEXT DEFAULT '',
                source_url TEXT DEFAULT '',
                created_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS knowledge_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_id TEXT NOT NULL,
                chunk_index INTEGER DEFAULT 0,
                chunk_text TEXT,
                embedding BLOB,
                FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
            );
        """)

        # FTS5 虚拟表 — 使用 unicode61 tokenizer
        # 注意：FTS5 不支持 IF NOT EXISTS，用 try 包裹
        for table_name, columns in [
            ("knowledge_fts", "title, content, tags, tips"),
            ("templates_fts", "title, description, prompt, tags"),
            ("cases_fts", "name, description, prompt, tags, tips"),
        ]:
            try:
                conn.execute(
                    f"CREATE VIRTUAL TABLE {table_name} USING fts5({columns}, tokenize='unicode61')"
                )
            except sqlite3.OperationalError:
                pass  # 已存在则跳过

        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def _json_load(val: Any, default: Any = None) -> Any:
    if val is None:
        return default if default is not None else []
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


# ── Knowledge CRUD ────────────────────────────────────────────────────

def knowledge_list_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM knowledge ORDER BY quality DESC").fetchall()
        return [_deserialize_knowledge(r) for r in rows]
    finally:
        conn.close()


def knowledge_get_by_id(kid: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM knowledge WHERE id = ?", (kid,)).fetchone()
        return _deserialize_knowledge(row) if row else None
    finally:
        conn.close()


def knowledge_upsert(item: dict) -> None:
    conn = get_connection()
    try:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        conn.execute("""
            INSERT INTO knowledge (id, type, title, content, category, quality, usage_count,
                tips, prompt, negative_prompt, model, scene_relevance, tags, related_terms,
                examples, last_verified, created_at, updated_at, embedding_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ON CONFLICT(id) DO UPDATE SET
                type=excluded.type, title=excluded.title, content=excluded.content,
                category=excluded.category, quality=excluded.quality,
                usage_count=excluded.usage_count, tips=excluded.tips,
                prompt=excluded.prompt, negative_prompt=excluded.negative_prompt,
                model=excluded.model, scene_relevance=excluded.scene_relevance,
                tags=excluded.tags, related_terms=excluded.related_terms,
                examples=excluded.examples, last_verified=excluded.last_verified,
                updated_at=excluded.updated_at, embedding_status='pending'
        """, (
            item.get("id", ""),
            item.get("type", "term"),
            item.get("title", ""),
            item.get("content", ""),
            item.get("category", ""),
            item.get("quality", 0.0),
            item.get("usageCount", 0),
            json.dumps(_json_load(item.get("tips"), []), ensure_ascii=False),
            item.get("prompt", ""),
            item.get("negativePrompt", ""),
            item.get("model", ""),
            json.dumps(_json_load(item.get("sceneRelevance"), {}), ensure_ascii=False),
            json.dumps(_json_load(item.get("tags"), []), ensure_ascii=False),
            json.dumps(_json_load(item.get("relatedTerms"), []), ensure_ascii=False),
            json.dumps(_json_load(item.get("examples"), []), ensure_ascii=False),
            item.get("lastVerified", ""),
            item.get("createdAt", now),
            now,
        ))
        # 更新 FTS 索引
        conn.execute("DELETE FROM knowledge_fts WHERE rowid = (SELECT rowid FROM knowledge WHERE id = ?)", (item.get("id", ""),))
        conn.execute("""
            INSERT INTO knowledge_fts(rowid, title, content, tags, tips)
            SELECT rowid, title, content, tags, tips FROM knowledge WHERE id = ?
        """, (item.get("id", ""),))
        conn.commit()
    finally:
        conn.close()


def knowledge_delete(kid: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM knowledge_fts WHERE rowid = (SELECT rowid FROM knowledge WHERE id = ?)", (kid,))
        conn.execute("DELETE FROM knowledge WHERE id = ?", (kid,))
        conn.commit()
    finally:
        conn.close()


def knowledge_search(query: str, scene: str = "general", type_filter: list[str] | None = None, limit: int = 10) -> list[dict]:
    """FTS5 全文搜索 + sceneRelevance 评分加权"""
    conn = get_connection()
    try:
        # 构建 FTS5 查询：对中文使用 2-gram + 3-gram 匹配
        fts_query = _build_fts_query(query)
        if not fts_query:
            # 无有效查询词时，按 quality 排序返回
            sql = "SELECT * FROM knowledge"
            params: list = []
            if type_filter:
                placeholders = ",".join("?" for _ in type_filter)
                sql += f" WHERE type IN ({placeholders})"
                params.extend(type_filter)
            sql += " ORDER BY quality DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [_deserialize_knowledge(r) for r in rows]

        # FTS5 搜索
        sql = """
            SELECT k.*, bm25(knowledge_fts) AS rank
            FROM knowledge_fts
            JOIN knowledge k ON k.rowid = knowledge_fts.rowid
            WHERE knowledge_fts MATCH ?
        """
        params = [fts_query]
        if type_filter:
            placeholders = ",".join("?" for _ in type_filter)
            sql += f" AND k.type IN ({placeholders})"
            params.extend(type_filter)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit * 3)  # 多取一些，后续加权重排序

        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            # FTS 查询语法错误时回退到 LIKE
            return _knowledge_like_search(conn, query, scene, type_filter, limit)

        # 综合排序：FTS rank + sceneRelevance + quality
        results = []
        for row in rows:
            entry = _deserialize_knowledge(row)
            fts_rank = abs(row["rank"]) if row["rank"] else 0
            scene_score = 0.0
            sr = entry.get("sceneRelevance", {})
            if isinstance(sr, dict):
                scene_score = sr.get(scene, 0) * 5.0
                if scene != "general" and sr.get(scene, 0) > 0.5:
                    scene_score += 2.0
            quality_score = (entry.get("quality", 1.0) - 0.5) * 1.0
            entry["_score"] = fts_rank + scene_score + quality_score
            results.append(entry)

        results.sort(key=lambda x: -x["_score"])
        return results[:limit]
    finally:
        conn.close()


def _build_fts_query(query: str) -> str:
    """将用户查询转为 FTS5 查询表达式

    FTS5 unicode61 tokenizer 将中文字符逐字拆分，
    因此中文短语需要用前缀匹配（赛*）或完整短语匹配。
    """
    query = query.strip().lower()
    if not query:
        return ""
    # 按空格拆分为多个查询词
    parts = [p for p in query.split() if p]
    if not parts:
        return ""
    tokens = []
    for part in parts:
        if any("一" <= c <= "鿿" for c in part):
            # 中文：用完整短语匹配（FTS5 会逐字索引，短语查询可匹配连续字符）
            tokens.append(f'"{part}"')
        else:
            tokens.append(f'"{part}"')
    return " OR ".join(tokens)


def _knowledge_like_search(conn: sqlite3.Connection, query: str, scene: str, type_filter: list[str] | None, limit: int) -> list[dict]:
    """LIKE 回退搜索"""
    like_pattern = f"%{query}%"
    sql = "SELECT * FROM knowledge WHERE (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
    params: list = [like_pattern, like_pattern, like_pattern]
    if type_filter:
        placeholders = ",".join("?" for _ in type_filter)
        sql += f" AND type IN ({placeholders})"
        params.extend(type_filter)
    sql += " ORDER BY quality DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_deserialize_knowledge(r) for r in rows]


def _deserialize_knowledge(row: sqlite3.Row) -> dict:
    d = _row_to_dict(row)
    d["tips"] = _json_load(d.get("tips"), [])
    d["tags"] = _json_load(d.get("tags"), [])
    d["relatedTerms"] = _json_load(d.get("related_terms"), [])
    d["examples"] = _json_load(d.get("examples"), [])
    d["sceneRelevance"] = _json_load(d.get("scene_relevance"), {})
    d["usageCount"] = d.pop("usage_count", 0)
    d["negativePrompt"] = d.pop("negative_prompt", "")
    d["lastVerified"] = d.pop("last_verified", "")
    d["createdAt"] = d.pop("created_at", "")
    d["updatedAt"] = d.pop("updated_at", "")
    d["embeddingStatus"] = d.pop("embedding_status", "pending")
    d.pop("rank", None)
    d.pop("_score", None)
    return d


# ── Templates CRUD ────────────────────────────────────────────────────

def templates_list_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM templates ORDER BY category").fetchall()
        return [_deserialize_template(r) for r in rows]
    finally:
        conn.close()


def templates_list_by_task(task_type: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM templates WHERE task_type = ? ORDER BY category", (task_type,)).fetchall()
        return [_deserialize_template(r) for r in rows]
    finally:
        conn.close()


def templates_upsert(item: dict) -> None:
    conn = get_connection()
    try:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        conn.execute("""
            INSERT INTO templates (id, title, category, description, prompt, negative_prompt,
                tags, task_type, audience, required_fields, recommended_model, recommended_size,
                source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title, category=excluded.category, description=excluded.description,
                prompt=excluded.prompt, negative_prompt=excluded.negative_prompt,
                tags=excluded.tags, task_type=excluded.task_type, audience=excluded.audience,
                required_fields=excluded.required_fields, recommended_model=excluded.recommended_model,
                recommended_size=excluded.recommended_size, source=excluded.source,
                updated_at=excluded.updated_at
        """, (
            item.get("id", ""),
            item.get("title", ""),
            item.get("category", ""),
            item.get("description", ""),
            item.get("prompt", ""),
            item.get("negativePrompt", ""),
            json.dumps(_json_load(item.get("tags"), []), ensure_ascii=False),
            item.get("taskType", "image"),
            item.get("audience", ""),
            json.dumps(_json_load(item.get("requiredFields"), []), ensure_ascii=False),
            item.get("recommendedModel", ""),
            item.get("recommendedSize", ""),
            item.get("source", ""),
            item.get("createdAt", now),
            now,
        ))
        conn.execute("DELETE FROM templates_fts WHERE rowid = (SELECT rowid FROM templates WHERE id = ?)", (item.get("id", ""),))
        conn.execute("""
            INSERT INTO templates_fts(rowid, title, description, prompt, tags)
            SELECT rowid, title, description, prompt, tags FROM templates WHERE id = ?
        """, (item.get("id", ""),))
        conn.commit()
    finally:
        conn.close()


def _deserialize_template(row: sqlite3.Row) -> dict:
    d = _row_to_dict(row)
    d["tags"] = _json_load(d.get("tags"), [])
    d["requiredFields"] = _json_load(d.get("required_fields"), [])
    d["negativePrompt"] = d.pop("negative_prompt", "")
    d["taskType"] = d.pop("task_type", "image")
    d["recommendedModel"] = d.pop("recommended_model", "")
    d["recommendedSize"] = d.pop("recommended_size", "")
    d["createdAt"] = d.pop("created_at", "")
    d["updatedAt"] = d.pop("updated_at", "")
    return d


# ── Cases CRUD ────────────────────────────────────────────────────────

def cases_list_all() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        return [_deserialize_case(r) for r in rows]
    finally:
        conn.close()


def cases_upsert(item: dict) -> None:
    conn = get_connection()
    try:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        conn.execute("""
            INSERT INTO cases (id, name, category, description, prompt, negative_prompt,
                model, size, tips, tags, author, source_url, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, category=excluded.category, description=excluded.description,
                prompt=excluded.prompt, negative_prompt=excluded.negative_prompt,
                model=excluded.model, size=excluded.size, tips=excluded.tips,
                tags=excluded.tags, author=excluded.author, source_url=excluded.source_url,
                updated_at=excluded.updated_at
        """, (
            item.get("id", ""),
            item.get("name", ""),
            item.get("category", ""),
            item.get("description", ""),
            item.get("prompt", ""),
            item.get("negativePrompt", ""),
            item.get("model", ""),
            item.get("size", "") or (item.get("parameters", {}) or {}).get("size", ""),
            json.dumps(_json_load(item.get("tips"), []), ensure_ascii=False),
            json.dumps(_json_load(item.get("tags"), []), ensure_ascii=False),
            item.get("author", ""),
            item.get("sourceUrl", ""),
            item.get("createdAt", now),
            now,
        ))
        conn.execute("DELETE FROM cases_fts WHERE rowid = (SELECT rowid FROM cases WHERE id = ?)", (item.get("id", ""),))
        conn.execute("""
            INSERT INTO cases_fts(rowid, name, description, prompt, tags, tips)
            SELECT rowid, name, description, prompt, tags, tips FROM cases WHERE id = ?
        """, (item.get("id", ""),))
        conn.commit()
    finally:
        conn.close()


def cases_delete(cid: str) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM cases_fts WHERE rowid = (SELECT rowid FROM cases WHERE id = ?)", (cid,))
        conn.execute("DELETE FROM cases WHERE id = ?", (cid,))
        conn.commit()
    finally:
        conn.close()


def _deserialize_case(row: sqlite3.Row) -> dict:
    d = _row_to_dict(row)
    d["tips"] = _json_load(d.get("tips"), [])
    d["tags"] = _json_load(d.get("tags"), [])
    d["negativePrompt"] = d.pop("negative_prompt", "")
    d["sourceUrl"] = d.pop("source_url", "")
    d["createdAt"] = d.pop("created_at", "")
    d["updatedAt"] = d.pop("updated_at", "")
    # 保持与旧格式兼容
    if d.get("size"):
        d["parameters"] = {"size": d["size"]}
    return d


# ── 批量操作 ──────────────────────────────────────────────────────────

def bulk_insert_knowledge(items: list[dict]) -> int:
    count = 0
    for item in items:
        knowledge_upsert(item)
        count += 1
    return count


def bulk_insert_templates(items: list[dict]) -> int:
    count = 0
    for item in items:
        templates_upsert(item)
        count += 1
    return count


def bulk_insert_cases(items: list[dict]) -> int:
    count = 0
    for item in items:
        cases_upsert(item)
        count += 1
    return count


def get_counts() -> dict[str, int]:
    conn = get_connection()
    try:
        k = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        t = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
        c = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        return {"knowledge": k, "templates": t, "cases": c}
    finally:
        conn.close()
