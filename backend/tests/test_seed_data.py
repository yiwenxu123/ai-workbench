"""知识库 JSON 自动灌入测试"""

from knowledge_db import get_counts, knowledge_upsert
from seed_data import seed_from_json_if_empty


class TestSeedFromJsonIfEmpty:
    def test_seeds_empty_database_from_repo_json(self, temp_db):
        assert get_counts() == {"knowledge": 0, "templates": 0, "cases": 0}

        result = seed_from_json_if_empty()

        assert result["seeded"] is True
        assert result["knowledge"] > 0
        assert result["templates"] > 0
        assert result["cases"] > 0
        assert get_counts()["knowledge"] == result["after"]["knowledge"]

    def test_does_not_overwrite_existing_knowledge(self, temp_db, sample_knowledge):
        for item in sample_knowledge:
            knowledge_upsert(item)
        before = get_counts()
        assert before["knowledge"] == 3

        result = seed_from_json_if_empty()

        assert result["knowledge"] == 0
        assert get_counts()["knowledge"] == 3

    def test_second_call_is_idempotent(self, temp_db):
        first = seed_from_json_if_empty()
        assert first["seeded"] is True

        second = seed_from_json_if_empty()
        assert second["seeded"] is False
        assert second["knowledge"] == 0
        assert second["templates"] == 0
        assert second["cases"] == 0
