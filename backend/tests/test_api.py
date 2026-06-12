"""API 端点集成测试"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


class TestHealthEndpoints:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestKnowledgeAPI:
    def test_get_knowledge(self, client, sample_knowledge):
        from knowledge_db import knowledge_upsert
        for item in sample_knowledge:
            knowledge_upsert(item)
        resp = client.get("/api/knowledge")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_get_knowledge_terms(self, client, sample_knowledge):
        from knowledge_db import knowledge_upsert
        for item in sample_knowledge:
            knowledge_upsert(item)
        resp = client.get("/api/knowledge/terms")
        assert resp.status_code == 200
        data = resp.json()
        assert all(e["type"] == "term" for e in data)
        assert len(data) == 2

    def test_get_knowledge_formulas(self, client, sample_knowledge):
        from knowledge_db import knowledge_upsert
        for item in sample_knowledge:
            knowledge_upsert(item)
        resp = client.get("/api/knowledge/formulas")
        assert resp.status_code == 200
        data = resp.json()
        assert all(e["type"] == "formula" for e in data)
        assert len(data) == 1

    def test_search_knowledge(self, client, sample_knowledge):
        from knowledge_db import knowledge_upsert
        for item in sample_knowledge:
            knowledge_upsert(item)
        resp = client.post("/api/knowledge/search", json={"query": "赛博朋克", "scene": "general"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["total"] >= 1

    def test_search_knowledge_with_type_filter(self, client, sample_knowledge):
        from knowledge_db import knowledge_upsert
        for item in sample_knowledge:
            knowledge_upsert(item)
        resp = client.post("/api/knowledge/search", json={"query": "产品", "types": ["formula"]})
        assert resp.status_code == 200
        data = resp.json()
        for item in data["items"]:
            assert item["type"] == "formula"


class TestTemplatesAPI:
    def test_get_templates(self, client, sample_template):
        from knowledge_db import templates_upsert
        templates_upsert(sample_template)
        resp = client.get("/api/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    def test_get_unified_templates(self, client, sample_template):
        from knowledge_db import templates_upsert
        templates_upsert(sample_template)
        resp = client.get("/api/unified-templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    def test_get_video_templates(self, client):
        resp = client.get("/api/video-templates")
        assert resp.status_code == 200


class TestCasesAPI:
    def test_get_cases(self, client, sample_case):
        from knowledge_db import cases_upsert
        cases_upsert(sample_case)
        resp = client.get("/api/cases")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    def test_create_case(self, client):
        resp = client.post("/api/cases", json={
            "title": "测试案例",
            "prompt": "test prompt, white background",
            "negativePrompt": "blurry",
            "model": "doubao-seedream-4-5-251128",
            "size": "1024x1024",
            "tips": ["tip1"],
            "tags": ["test"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "案例已收录" in data["message"]


class TestConfigAPI:
    def test_get_config(self, client):
        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert any(m["id"] == "default" for m in data["models"])
        assert any(m["id"] == "doubao-seedream-4-5-251128" for m in data["models"])

    def test_backend_configured_capabilities(self, client):
        resp = client.get("/config")
        caps = resp.json().get("backend_configured_capabilities", {})
        assert isinstance(caps, dict)
        for key in ("image", "video", "edit"):
            assert key in caps
            assert isinstance(caps[key], bool)


class TestModelManifestAPI:
    def test_model_manifest_schema(self, client):
        resp = client.get("/api/model-manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert "models" in data
        assert len(data["models"]) > 0
        for model in data["models"]:
            assert "id" in model
            assert "name" in model
            assert "capabilities" in model
            assert "provider" in model

    def test_config_models_subset_of_manifest(self, client):
        config_resp = client.get("/config")
        manifest_resp = client.get("/api/model-manifest")
        config_ids = {m["id"] for m in config_resp.json()["models"]}
        manifest_ids = {m["id"] for m in manifest_resp.json()["models"]}
        assert config_ids.issubset(manifest_ids | {"default"})

    def test_video_models_in_manifest(self, client):
        resp = client.get("/api/model-manifest")
        video_ids = {
            m["id"] for m in resp.json()["models"]
            if "video" in m.get("capabilities", [])
        }
        assert "kling-v1" in video_ids
        assert "jimeng-v1" in video_ids
