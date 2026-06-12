"""
从 backend/data/*.json 灌入 SQLite 知识库。

- seed_from_json_if_empty(): 各表为空时自动导入（启动时调用，幂等）
- migrate_all_from_json(): 强制从 JSON 同步（CLI 迁移脚本用）
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from json_store import load_json_list
from knowledge_db import (
    bulk_insert_cases,
    bulk_insert_knowledge,
    bulk_insert_templates,
    get_counts,
)

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent / "data"


def collect_templates_from_json() -> list[dict]:
    """合并 4 个模板 JSON 为统一列表"""
    all_templates: list[dict] = []
    sources = [
        ("templates.json", "templates", "image"),
        ("work_templates.json", "work_templates", "image"),
        ("festival_templates.json", "festival_templates", "image"),
        ("video_templates.json", "video_templates", "video"),
    ]
    for filename, source, task_type in sources:
        for item in load_json_list(DATA_DIR / filename):
            row = dict(item)
            row["_source"] = source
            row["taskType"] = task_type
            all_templates.append(row)
    return all_templates


def _seed_table_if_empty(
    count_before: int,
    loader: Callable[[], list],
    inserter: Callable[[list], int],
) -> int:
    if count_before > 0:
        return 0
    items = loader()
    if not items:
        return 0
    return inserter(items)


def seed_from_json_if_empty() -> dict[str, Any]:
    """
    若 knowledge / templates / cases 任一张表为空，则从对应 JSON 导入。
    返回导入统计；已有人工/入库数据时不会覆盖。
    """
    before = get_counts()
    knowledge_added = _seed_table_if_empty(
        before["knowledge"],
        lambda: load_json_list(DATA_DIR / "knowledge.json"),
        bulk_insert_knowledge,
    )
    templates_added = _seed_table_if_empty(
        before["templates"],
        collect_templates_from_json,
        bulk_insert_templates,
    )
    cases_added = _seed_table_if_empty(
        before["cases"],
        lambda: load_json_list(DATA_DIR / "cases.json"),
        bulk_insert_cases,
    )
    after = get_counts()
    seeded = any((knowledge_added, templates_added, cases_added))

    if seeded:
        logger.info(
            "知识库已从 JSON 自动灌入: knowledge +%d, templates +%d, cases +%d (总计 %s)",
            knowledge_added,
            templates_added,
            cases_added,
            after,
        )

    return {
        "seeded": seeded,
        "knowledge": knowledge_added,
        "templates": templates_added,
        "cases": cases_added,
        "before": before,
        "after": after,
    }


def migrate_all_from_json() -> dict[str, int]:
    """强制从 JSON 同步（UPSERT），供 migrate_json_to_sqlite.py 使用"""
    knowledge_items = load_json_list(DATA_DIR / "knowledge.json")
    template_items = collect_templates_from_json()
    case_items = load_json_list(DATA_DIR / "cases.json")

    return {
        "knowledge": bulk_insert_knowledge(knowledge_items) if knowledge_items else 0,
        "templates": bulk_insert_templates(template_items) if template_items else 0,
        "cases": bulk_insert_cases(case_items) if case_items else 0,
    }
