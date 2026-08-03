"""
SQLite + FTS5 知识库存储
替代 JSON 文件，支持全文搜索

重构说明：
- 使用线程本地连接池，避免每次操作新建/关闭连接
- 统一反序列化函数，消除三个 _deserialize_* 的重复代码
- 批量操作使用单事务包裹
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

DB_PATH = Path(__file__).parent / "data" / "knowledge.db"

# ── 线程本地连接池 ─────────────────────────────────────────────────

_local = threading.local()


def _get_pooled_connection() -> sqlite3.Connection:
    """获取当前线程的数据库连接（懒创建，自动复用）"""
    conn = getattr(_local, "connection", None)
    try:
        if conn is not None:
            conn.execute("SELECT 1")
            return conn
    except (sqlite3.ProgrammingError, sqlite3.OperationalError):
        _local.connection = None

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _local.connection = conn
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """数据库连接上下文管理器，自动 commit/rollback"""
    conn = _get_pooled_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def get_connection() -> sqlite3.Connection:
    """获取原始连接（兼容 embedding_worker 等外部调用方）"""
    return _get_pooled_connection()


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """增量 schema 迁移：为已有表添加缺失的列"""
    migrations = [
        ("templates", "tips", "TEXT DEFAULT '[]'"),
    ]
    for table, column, col_type in migrations:
        try:
            conn.execute(f"SELECT {column} FROM {table} LIMIT 1")
        except sqlite3.OperationalError:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


def init_db() -> None:
    """初始化数据库 schema（幂等）。同时清除当前线程的缓存连接，确保使用最新的 DB_PATH。"""
    old_conn = getattr(_local, "connection", None)
    if old_conn is not None:
        try:
            old_conn.close()
        except Exception:
            pass
        _local.connection = None
    with get_db() as conn:
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
                tips TEXT DEFAULT '[]',
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

        # Schema 迁移：为已有表添加缺失的列
        _migrate_schema(conn)


# ── 通用工具 ──────────────────────────────────────────────────────

def _json_load(val: Any, default: Any = None) -> Any:
    if val is None:
        return default if default is not None else []
    if isinstance(val, (list, dict)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def _deserialize_row(row: sqlite3.Row, json_fields: list[str], rename_map: dict[str, str]) -> dict:
    """统一反序列化：JSON 字段解析 + 字段重命名

    Args:
        row: SQLite Row 对象
        json_fields: 需要 JSON 解析的字段名列表
        rename_map: snake_case → camelCase 的字段映射
    """
    d = dict(row)
    for field in json_fields:
        if field in d:
            d[field] = _json_load(d.get(field), [] if field != "scene_relevance" else {})
    for old, new in rename_map.items():
        if old in d:
            d[new] = d.pop(old)
    # 移除内部字段
    d.pop("rank", None)
    d.pop("_score", None)
    return d


# 各表的反序列化配置
_KNOWLEDGE_JSON = ["tips", "tags", "related_terms", "examples", "scene_relevance"]
_KNOWLEDGE_RENAME = {
    "usage_count": "usageCount",
    "negative_prompt": "negativePrompt",
    "related_terms": "relatedTerms",
    "last_verified": "lastVerified",
    "scene_relevance": "sceneRelevance",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
    "embedding_status": "embeddingStatus",
}

_TEMPLATE_JSON = ["tags", "required_fields", "tips"]
_TEMPLATE_RENAME = {
    "title": "name",
    "negative_prompt": "negativePrompt",
    "task_type": "taskType",
    "required_fields": "fields",
    "recommended_model": "recommendedModel",
    "recommended_size": "recommendedSize",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
}

_CASE_JSON = ["tips", "tags"]
_CASE_RENAME = {
    "negative_prompt": "negativePrompt",
    "source_url": "sourceUrl",
    "created_at": "createdAt",
    "updated_at": "updatedAt",
}


def _deserialize_knowledge(row: sqlite3.Row) -> dict:
    return _deserialize_row(row, _KNOWLEDGE_JSON, _KNOWLEDGE_RENAME)


def _deserialize_template(row: sqlite3.Row) -> dict:
    return _deserialize_row(row, _TEMPLATE_JSON, _TEMPLATE_RENAME)


def _deserialize_case(row: sqlite3.Row) -> dict:
    d = _deserialize_row(row, _CASE_JSON, _CASE_RENAME)
    if d.get("size"):
        d["parameters"] = {"size": d["size"]}
    return d


# ── Knowledge CRUD ────────────────────────────────────────────────

def knowledge_list_all() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM knowledge ORDER BY quality DESC").fetchall()
        return [_deserialize_knowledge(r) for r in rows]


def knowledge_get_by_id(kid: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM knowledge WHERE id = ?", (kid,)).fetchone()
        return _deserialize_knowledge(row) if row else None


def knowledge_upsert(item: dict) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with get_db() as conn:
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
        conn.execute("DELETE FROM knowledge_fts WHERE rowid = (SELECT rowid FROM knowledge WHERE id = ?)", (item.get("id", ""),))
        conn.execute("""
            INSERT INTO knowledge_fts(rowid, title, content, tags, tips)
            SELECT rowid, title, content, tags, tips FROM knowledge WHERE id = ?
        """, (item.get("id", ""),))


def knowledge_delete(kid: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM knowledge_fts WHERE rowid = (SELECT rowid FROM knowledge WHERE id = ?)", (kid,))
        conn.execute("DELETE FROM knowledge WHERE id = ?", (kid,))


def knowledge_search(query: str, scene: str = "general", type_filter: list[str] | None = None, limit: int = 10) -> list[dict]:
    """FTS5 全文搜索 + sceneRelevance 评分加权"""
    with get_db() as conn:
        fts_query = _build_fts_query(query)
        if not fts_query:
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
        params.append(limit * 3)

        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.OperationalError:
            return _knowledge_like_search(conn, query, scene, type_filter, limit)

        # macOS 上 FTS5 unicode61 对中文分词行为不可预测（如"赛博朋克"可能整体为
        # 一个 token，"电商"可能独立），导致某些中文短语 FTS5 返回空结果。
        # 自动回退 LIKE 搜索保证中文查询有结果。
        if not rows and any("\u4e00" <= c <= "\u9fff" for c in query):
            return _knowledge_like_search(conn, query, scene, type_filter, limit)

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


def _split_query_terms(query: str) -> list[str]:
    """将用户查询切分为检索词：按空格与中英文标点切分，过滤单字停用词"""
    parts = re.split(r"[\s，。、；：！？,.;:!?()（）·]+", query.strip().lower())
    terms = [p for p in parts if len(p) >= 2]
    if not terms and len(query.strip()) >= 2:
        terms = [query.strip().lower()]
    return terms


def _build_fts_query(query: str) -> str:
    """将用户查询转为 FTS5 查询表达式

    中文无空格分词，先按标点切分为多词，再以 OR 组合，
    避免整句作为一个 token 导致 FTS5 无命中。
    """
    query = query.strip().lower()
    if not query:
        return ""
    terms = _split_query_terms(query)
    if not terms:
        return ""
    tokens = [f'"{term}"' for term in terms]
    return " OR ".join(tokens)


def _knowledge_like_search(conn: sqlite3.Connection, query: str, scene: str, type_filter: list[str] | None, limit: int) -> list[dict]:
    """LIKE 回退搜索：先全词 AND，无结果时降级为 OR（取前 3 词防噪音）"""
    terms = _split_query_terms(query)
    if not terms:
        return []

    def _build(mode: str, term_slice: list[str]) -> tuple[str, list]:
        conditions = []
        params: list = []
        for term in term_slice:
            like_pattern = f"%{term}%"
            conditions.append("(title LIKE ? OR content LIKE ? OR tags LIKE ?)")
            params.extend([like_pattern, like_pattern, like_pattern])
        sql = f"SELECT * FROM knowledge WHERE {' AND '.join(conditions) if mode == 'and' else ' OR '.join(conditions)}"
        if type_filter:
            placeholders = ",".join("?" for _ in type_filter)
            sql += f" AND type IN ({placeholders})"
            params.extend(type_filter)
        sql += " ORDER BY quality DESC LIMIT ?"
        params.append(limit)
        return sql, params

    rows = conn.execute(*_build("and", terms)).fetchall()
    if not rows and len(terms) > 1:
        rows = conn.execute(*_build("or", terms[:3])).fetchall()
    return [_deserialize_knowledge(r) for r in rows]


# ── Templates CRUD ────────────────────────────────────────────────

def templates_list_all() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM templates ORDER BY category").fetchall()
        return [_deserialize_template(r) for r in rows]


def templates_list_by_task(task_type: str) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM templates WHERE task_type = ? ORDER BY category", (task_type,)).fetchall()
        return [_deserialize_template(r) for r in rows]


def _normalize_template_fields(item: dict) -> dict:
    """统一模板字段名：兼容 JSON 原始格式和 camelCase 格式"""
    return {
        "id": item.get("id", ""),
        "title": item.get("title") or item.get("name") or "",
        "category": item.get("category", ""),
        "description": item.get("description", ""),
        "prompt": item.get("prompt", ""),
        "negativePrompt": item.get("negativePrompt", ""),
        "tags": item.get("tags", []),
        "taskType": item.get("taskType") or item.get("task_type") or "image",
        "audience": item.get("audience", ""),
        "requiredFields": item.get("requiredFields") or item.get("required_fields") or item.get("fields") or [],
        "tips": item.get("tips", []),
        "recommendedModel": item.get("recommendedModel") or item.get("model") or "",
        "recommendedSize": item.get("recommendedSize") or item.get("size") or "",
        "source": item.get("source") or item.get("_source") or "",
        "createdAt": item.get("createdAt") or item.get("created_at") or "",
    }


def _template_row_values(item: dict, now: str) -> tuple:
    """从规范化的模板 dict 提取 INSERT 参数"""
    n = _normalize_template_fields(item)
    return (
        n["id"], n["title"], n["category"], n["description"], n["prompt"],
        n["negativePrompt"],
        json.dumps(_json_load(n["tags"], []), ensure_ascii=False),
        n["taskType"], n["audience"],
        json.dumps(_json_load(n["requiredFields"], []), ensure_ascii=False),
        json.dumps(_json_load(n["tips"], []), ensure_ascii=False),
        n["recommendedModel"], n["recommendedSize"],
        n["source"], n["createdAt"] or now, now,
    )


_INSERT_TPL_COLS = """INSERT INTO templates (id, title, category, description, prompt, negative_prompt,
    tags, task_type, audience, required_fields, tips, recommended_model, recommended_size,
    source, created_at, updated_at)"""
_INSERT_TPL_PLACEHOLDERS = "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
_UPSERT_TPL_ON_CONFLICT = """ON CONFLICT(id) DO UPDATE SET
    title=excluded.title, category=excluded.category, description=excluded.description,
    prompt=excluded.prompt, negative_prompt=excluded.negative_prompt,
    tags=excluded.tags, task_type=excluded.task_type, audience=excluded.audience,
    required_fields=excluded.required_fields, tips=excluded.tips,
    recommended_model=excluded.recommended_model, recommended_size=excluded.recommended_size,
    source=excluded.source, updated_at=excluded.updated_at"""


def templates_upsert(item: dict) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with get_db() as conn:
        conn.execute(
            f"{_INSERT_TPL_COLS} {_INSERT_TPL_PLACEHOLDERS} {_UPSERT_TPL_ON_CONFLICT}",
            _template_row_values(item, now),
        )
        conn.execute("DELETE FROM templates_fts WHERE rowid = (SELECT rowid FROM templates WHERE id = ?)", (item.get("id", ""),))
        conn.execute("""
            INSERT INTO templates_fts(rowid, title, description, prompt, tags)
            SELECT rowid, title, description, prompt, tags FROM templates WHERE id = ?
        """, (item.get("id", ""),))


# ── Cases CRUD ────────────────────────────────────────────────────

def cases_list_all() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
        return [_deserialize_case(r) for r in rows]


def cases_upsert(item: dict) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with get_db() as conn:
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


def cases_delete(cid: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM cases_fts WHERE rowid = (SELECT rowid FROM cases WHERE id = ?)", (cid,))
        conn.execute("DELETE FROM cases WHERE id = ?", (cid,))


# ── 批量操作 ──────────────────────────────────────────────────────

def bulk_insert_knowledge(items: list[dict]) -> int:
    """批量插入知识条目（单事务）"""
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with get_db() as conn:
        for item in items:
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
            conn.execute("DELETE FROM knowledge_fts WHERE rowid = (SELECT rowid FROM knowledge WHERE id = ?)", (item.get("id", ""),))
            conn.execute("""
                INSERT INTO knowledge_fts(rowid, title, content, tags, tips)
                SELECT rowid, title, content, tags, tips FROM knowledge WHERE id = ?
            """, (item.get("id", ""),))
    return len(items)


def bulk_insert_templates(items: list[dict]) -> int:
    """批量插入模板（单事务）"""
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with get_db() as conn:
        for item in items:
            conn.execute(
                f"{_INSERT_TPL_COLS} {_INSERT_TPL_PLACEHOLDERS} {_UPSERT_TPL_ON_CONFLICT}",
                _template_row_values(item, now),
            )
            conn.execute("DELETE FROM templates_fts WHERE rowid = (SELECT rowid FROM templates WHERE id = ?)", (item.get("id", ""),))
            conn.execute("""
                INSERT INTO templates_fts(rowid, title, description, prompt, tags)
                SELECT rowid, title, description, prompt, tags FROM templates WHERE id = ?
            """, (item.get("id", ""),))
    return len(items)


def bulk_insert_cases(items: list[dict]) -> int:
    """批量插入案例（单事务）"""
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    with get_db() as conn:
        for item in items:
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
    return len(items)


def get_counts() -> dict[str, int]:
    with get_db() as conn:
        k = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        t = conn.execute("SELECT COUNT(*) FROM templates").fetchone()[0]
        c = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        return {"knowledge": k, "templates": t, "cases": c}
