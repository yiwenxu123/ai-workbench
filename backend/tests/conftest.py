"""测试配置：使用临时 SQLite 数据库"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# 确保 backend 目录在 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """每个测试使用独立的临时数据库"""
    db_path = tmp_path / "test_knowledge.db"
    import knowledge_db
    monkeypatch.setattr(knowledge_db, "DB_PATH", db_path)
    knowledge_db.init_db()
    yield db_path


@pytest.fixture
def sample_knowledge():
    return [
        {
            "id": "term-cyberpunk",
            "type": "term",
            "title": "赛博朋克 Cyberpunk",
            "content": "科幻风格，以高科技与低生活为特征，常见霓虹灯、机械改造、未来城市。",
            "category": "style",
            "tags": ["赛博朋克", "科幻", "霓虹灯"],
            "sceneRelevance": {"ecommerce": 0.3, "social": 0.7, "general": 0.8},
            "quality": 0.9,
            "examples": ["cyberpunk city street, neon lights, rain"],
            "tips": "搭配霓虹光效和雨天氛围更佳",
            "relatedTerms": ["霓虹光效", "未来城市"],
            "lastVerified": "2026-05-01",
        },
        {
            "id": "term-neon",
            "type": "term",
            "title": "霓虹光效 Neon Lighting",
            "content": "霓虹灯管发出的彩色光线效果，适合赛博朋克、夜店、城市夜景。",
            "category": "lighting",
            "tags": ["霓虹灯", "光效", "夜景"],
            "sceneRelevance": {"ecommerce": 0.2, "social": 0.8, "general": 0.7},
            "quality": 0.85,
            "examples": ["neon glow, vibrant colors, night scene"],
            "tips": "色彩饱和度要高",
            "relatedTerms": ["赛博朋克"],
            "lastVerified": "2026-05-01",
        },
        {
            "id": "formula-product",
            "type": "formula",
            "title": "产品展示公式",
            "content": "[产品名称] + [背景] + [光线] + [画质词]",
            "category": "ecommerce",
            "tags": ["产品", "公式", "电商"],
            "sceneRelevance": {"ecommerce": 0.95, "general": 0.5},
            "quality": 0.9,
            "examples": ["smart watch, white background, studio lighting, 4K"],
            "tips": ["背景简洁", "光线均匀"],
            "lastVerified": "2026-05-01",
        },
    ]


@pytest.fixture
def sample_template():
    return {
        "id": "tpl-ecommerce-main",
        "title": "电商主图模板",
        "category": "电商",
        "description": "适合电商产品主图",
        "prompt": "{产品名称}，白底，产品摄影，专业打光",
        "negativePrompt": "blurry, low quality",
        "tags": ["电商", "产品"],
        "taskType": "image",
    }


@pytest.fixture
def sample_case():
    return {
        "id": "case-smart-watch",
        "name": "智能手表电商图",
        "category": "ecommerce",
        "description": "智能手表白底产品图",
        "prompt": "smart watch, white background, studio lighting, 4K",
        "negativePrompt": "blurry, low quality",
        "model": "doubao-seedream-4-5-251128",
        "size": "1024x1024",
        "tips": ["光线均匀", "背景纯净"],
        "tags": ["电商", "手表", "产品"],
    }
