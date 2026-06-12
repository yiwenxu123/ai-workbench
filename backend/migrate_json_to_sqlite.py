#!/usr/bin/env python3
"""
JSON → SQLite 迁移脚本（强制 UPSERT）
日常开发无需手动执行：后端启动时会自动 seed_from_json_if_empty()。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge_db import init_db, get_counts
from seed_data import DATA_DIR, migrate_all_from_json


def main():
    print("=== JSON → SQLite 迁移（强制同步）===\n")

    print("[1/3] 初始化数据库...")
    init_db()

    print("[2/3] 迁移数据...")
    counts = migrate_all_from_json()
    for name, n in counts.items():
        print(f"  {name}: 处理 {n} 条")

    print("\n[3/3] 验证...")
    final = get_counts()
    ok = all(final[k] >= counts[k] or counts[k] == 0 for k in counts)
    for name, actual in final.items():
        mark = "✓" if ok else "?"
        print(f"  {mark} {name}: {actual} 条")

    print(f"\n完成。数据库: {DATA_DIR / 'knowledge.db'}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
