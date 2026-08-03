"""
导入镜头语言知识库
将 shot_language.json 中的运镜数据导入 SQLite 知识库
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from knowledge_db import knowledge_upsert, knowledge_list_all

DATA_FILE = Path(__file__).parent / "data" / "shot_language.json"


def import_shot_language():
    """导入镜头语言数据"""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        shot_data = json.load(f)

    print(f"准备导入 {len(shot_data)} 条镜头语言数据...")

    count = 0
    for item in shot_data:
        # 转换字段名，从下划线/驼峰统一
        kb_item = {
            "id": item.get("id", ""),
            "type": item.get("type", "shot_language"),
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "category": item.get("category", "shot_language"),
            "quality": item.get("quality", 1.0),
            "tags": item.get("tags", []),
            "tips": item.get("tips", []),
            "sceneRelevance": item.get("sceneRelevance", {}),
            "lastVerified": item.get("lastVerified", "2026-07-04"),
        }
        knowledge_upsert(kb_item)
        count += 1

    print(f"✅ 成功导入 {count} 条镜头语言数据")

    # 验证
    all_data = knowledge_list_all()
    shot_items = [e for e in all_data if e.get("type") == "shot_language"]
    print(f"📊 知识库中镜头语言条目: {len(shot_items)}")


if __name__ == "__main__":
    import_shot_language()
