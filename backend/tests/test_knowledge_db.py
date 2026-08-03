"""SQLite 知识库 CRUD 测试"""

import json
import pytest
from knowledge_db import (
    knowledge_list_all, knowledge_get_by_id, knowledge_upsert, knowledge_delete,
    knowledge_search, templates_list_all, templates_upsert,
    cases_list_all, cases_upsert, cases_delete, get_counts,
    _split_query_terms,
)


class TestKnowledgeCRUD:
    def test_upsert_and_list(self, sample_knowledge):
        for item in sample_knowledge:
            knowledge_upsert(item)
        items = knowledge_list_all()
        assert len(items) == 3

    def test_get_by_id(self, sample_knowledge):
        knowledge_upsert(sample_knowledge[0])
        item = knowledge_get_by_id("term-cyberpunk")
        assert item is not None
        assert item["title"] == "赛博朋克 Cyberpunk"
        assert item["type"] == "term"
        assert "赛博朋克" in item["tags"]

    def test_get_nonexistent(self):
        item = knowledge_get_by_id("nonexistent")
        assert item is None

    def test_upsert_updates(self, sample_knowledge):
        knowledge_upsert(sample_knowledge[0])
        updated = {**sample_knowledge[0], "title": "赛博朋克 2.0", "quality": 0.95}
        knowledge_upsert(updated)
        item = knowledge_get_by_id("term-cyberpunk")
        assert item["title"] == "赛博朋克 2.0"
        assert item["quality"] == 0.95
        assert len(knowledge_list_all()) == 1

    def test_delete(self, sample_knowledge):
        knowledge_upsert(sample_knowledge[0])
        assert len(knowledge_list_all()) == 1
        knowledge_delete("term-cyberpunk")
        assert len(knowledge_list_all()) == 0

    def test_json_fields_deserialized(self, sample_knowledge):
        knowledge_upsert(sample_knowledge[0])
        item = knowledge_get_by_id("term-cyberpunk")
        assert isinstance(item["tags"], list)
        assert isinstance(item["sceneRelevance"], dict)
        assert isinstance(item["examples"], list)
        # tips stored as JSON; round-trip via json.dumps/loads always yields list
        assert isinstance(item["tips"], list)

    def test_counts(self, sample_knowledge, sample_template, sample_case):
        for item in sample_knowledge:
            knowledge_upsert(item)
        templates_upsert(sample_template)
        cases_upsert(sample_case)
        counts = get_counts()
        assert counts["knowledge"] == 3
        assert counts["templates"] == 1
        assert counts["cases"] == 1


class TestFTS5Search:
    def test_basic_search(self, sample_knowledge):
        for item in sample_knowledge:
            knowledge_upsert(item)
        results = knowledge_search("赛博朋克")
        assert len(results) >= 1
        titles = [r["title"] for r in results]
        assert any("赛博朋克" in t for t in titles)

    def test_search_with_type_filter(self, sample_knowledge):
        for item in sample_knowledge:
            knowledge_upsert(item)
        results = knowledge_search("产品", type_filter=["formula"])
        assert len(results) >= 1
        for r in results:
            assert r["type"] == "formula"

    def test_search_scene_weighting(self, sample_knowledge):
        for item in sample_knowledge:
            knowledge_upsert(item)
        # ecommerce 场景下，产品展示公式应该排在前面
        results = knowledge_search("产品", scene="ecommerce", limit=5)
        assert len(results) >= 1

    def test_empty_query_returns_by_quality(self, sample_knowledge):
        for item in sample_knowledge:
            knowledge_upsert(item)
        results = knowledge_search("", limit=5)
        assert len(results) == 3

    def test_no_results(self, sample_knowledge):
        for item in sample_knowledge:
            knowledge_upsert(item)
        results = knowledge_search("不存在的关键词xyzzy", limit=5)
        assert len(results) == 0

    def test_chinese_long_sentence_search(self, sample_knowledge):
        """中文长句（含标点、无空格）必须能命中：切词 + LIKE 回退"""
        for item in sample_knowledge:
            knowledge_upsert(item)
        results = knowledge_search("赛博朋克，霓虹，城市夜景，高级感", limit=5)
        assert len(results) >= 1
        assert any("赛博朋克" in r.get("title", "") or "赛博朋克" in r.get("content", "")
                   for r in results)

    def test_split_query_terms(self):
        assert _split_query_terms("白色保温杯，女性，高级感") == ["白色保温杯", "女性", "高级感"]
        assert _split_query_terms("赛博朋克 霓虹 城市") == ["赛博朋克", "霓虹", "城市"]
        assert _split_query_terms("ai art, 摄影") == ["ai", "art", "摄影"]
        assert _split_query_terms("的") == []


class TestTemplates:
    def test_upsert_and_list(self, sample_template):
        templates_upsert(sample_template)
        items = templates_list_all()
        assert len(items) == 1
        assert items[0]["name"] == "电商主图模板"

    def test_template_fields(self, sample_template):
        templates_upsert(sample_template)
        item = templates_list_all()[0]
        assert isinstance(item["tags"], list)
        assert item["taskType"] == "image"


class TestCases:
    def test_upsert_and_list(self, sample_case):
        cases_upsert(sample_case)
        items = cases_list_all()
        assert len(items) == 1
        assert items[0]["name"] == "智能手表电商图"

    def test_delete_case(self, sample_case):
        cases_upsert(sample_case)
        assert len(cases_list_all()) == 1
        cases_delete("case-smart-watch")
        assert len(cases_list_all()) == 0

    def test_case_fields(self, sample_case):
        cases_upsert(sample_case)
        item = cases_list_all()[0]
        assert isinstance(item["tips"], list)
        assert isinstance(item["tags"], list)
