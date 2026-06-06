#!/usr/bin/env python3
"""
JSON → SQLite 迁移脚本
将 backend/data/*.json 迁移到 backend/data/knowledge.db
"""

import json
import sys
from pathlib import Path

# 确保 import 能找到 backend 目录
sys.path.insert(0, str(Path(__file__).parent))

from knowledge_db import (
    init_db, get_counts,
    bulk_insert_knowledge, bulk_insert_templates, bulk_insert_cases,
)
from json_store import load_json_list

DATA_DIR = Path(__file__).parent / "data"


def migrate_knowledge():
    items = load_json_list(DATA_DIR / "knowledge.json")
    if not items:
        print("  knowledge.json 为空或不存在，跳过")
        return 0
    count = bulk_insert_knowledge(items)
    print(f"  knowledge: 迁移 {count} 条")
    return count


def migrate_templates():
    """合并 4 个模板文件到统一 templates 表"""
    all_templates = []

    # templates.json
    for item in load_json_list(DATA_DIR / "templates.json"):
        item["_source"] = "templates"
        item["taskType"] = "image"
        all_templates.append(item)

    # work_templates.json
    for item in load_json_list(DATA_DIR / "work_templates.json"):
        item["_source"] = "work_templates"
        item["taskType"] = "image"
        all_templates.append(item)

    # festival_templates.json
    for item in load_json_list(DATA_DIR / "festival_templates.json"):
        item["_source"] = "festival_templates"
        item["taskType"] = "image"
        all_templates.append(item)

    # video_templates.json
    for item in load_json_list(DATA_DIR / "video_templates.json"):
        item["_source"] = "video_templates"
        item["taskType"] = "video"
        all_templates.append(item)

    if not all_templates:
        print("  模板文件为空，跳过")
        return 0

    count = bulk_insert_templates(all_templates)
    print(f"  templates: 迁移 {count} 条（合并 4 个文件）")
    return count


def migrate_cases():
    items = load_json_list(DATA_DIR / "cases.json")
    if not items:
        print("  cases.json 为空或不存在，跳过")
        return 0
    count = bulk_insert_cases(items)
    print(f"  cases: 迁移 {count} 条")
    return count


def verify(expected_knowledge: int, expected_templates: int, expected_cases: int):
    counts = get_counts()
    ok = True
    for name, expected, actual in [
        ("knowledge", expected_knowledge, counts["knowledge"]),
        ("templates", expected_templates, counts["templates"]),
        ("cases", expected_cases, counts["cases"]),
    ]:
        if actual >= expected:
            print(f"  ✓ {name}: {actual} 条 (预期 >= {expected})")
        else:
            print(f"  ✗ {name}: {actual} 条 (预期 >= {expected})")
            ok = False
    return ok


def main():
    print("=== JSON → SQLite 迁移 ===\n")

    print("[1/4] 初始化数据库...")
    init_db()

    print("[2/4] 迁移数据...")
    k_count = migrate_knowledge()
    t_count = migrate_templates()
    c_count = migrate_cases()

    print("\n[3/4] 验证迁移完整性...")
    ok = verify(k_count, t_count, c_count)

    print(f"\n[4/4] 完成！数据库路径: {DATA_DIR / 'knowledge.db'}")
    if ok:
        print("✓ 迁移成功")
    else:
        print("✗ 迁移验证失败，请检查数据")
        sys.exit(1)


if __name__ == "__main__":
    main()
