"""测试多厂商任务状态适配器"""

import pytest
from providers import get_adapter, list_providers
from providers.config_adapter import (
    ConfigDrivenAdapter,
    get_provider_config,
    load_registry,
    reload_registry,
)
from providers.kling_adapter import KlingStatusAdapter
from providers.jimeng_adapter import JimengStatusAdapter
from providers.runway_adapter import RunwayStatusAdapter


class TestAdapterRegistration:
    def test_list_providers(self):
        providers = list_providers()
        assert "kling" in providers
        assert "jimeng" in providers
        assert "runway" in providers

    def test_get_adapter_by_name(self):
        adapter = get_adapter("kling")
        assert isinstance(adapter, KlingStatusAdapter)

        adapter = get_adapter("jimeng")
        assert isinstance(adapter, JimengStatusAdapter)

        adapter = get_adapter("runway")
        assert isinstance(adapter, RunwayStatusAdapter)

    def test_get_adapter_default(self):
        adapter = get_adapter()
        assert isinstance(adapter, KlingStatusAdapter)

    def test_get_adapter_unknown_fallback(self):
        adapter = get_adapter("nonexistent_provider")
        assert isinstance(adapter, KlingStatusAdapter)


class TestKlingAdapter:
    @pytest.fixture
    def adapter(self):
        return KlingStatusAdapter()

    def test_build_url(self, adapter):
        url = adapter.build_status_url("https://api.klingai.com/v1/videos/generations", "task-123")
        assert url == "https://api.klingai.com/v1/videos/generations/task-123"

    def test_build_headers(self, adapter):
        headers = adapter.build_headers("sk-test-key")
        assert headers["Authorization"] == "Bearer sk-test-key"
        assert headers["Content-Type"] == "application/json"

    def test_parse_succeed(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "succeed",
                "result_url": "https://example.com/video.mp4",
                "progress": 100,
            }
        })
        assert result["status"] == "succeed"
        assert result["result_url"] == "https://example.com/video.mp4"
        assert result["progress"] == 100

    def test_parse_processing(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "processing",
                "progress": 50,
            }
        })
        assert result["status"] == "processing"
        assert result["progress"] == 50
        assert result["result_url"] is None

    def test_parse_pending(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "submitted",
            }
        })
        assert result["status"] == "pending"

    def test_parse_failed(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "failed",
            }
        })
        assert result["status"] == "failed"

    def test_parse_unknown_status(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "unknown_status",
            }
        })
        assert result["status"] == "pending"

    def test_parse_no_data_wrapper(self, adapter):
        result = adapter.parse_response({
            "task_status": "succeed",
            "video_url": "https://example.com/video.mp4",
        })
        assert result["status"] == "succeed"
        assert result["result_url"] == "https://example.com/video.mp4"

    def test_parse_progress_not_int(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "processing",
                "progress": "50",
            }
        })
        assert result["progress"] is None


class TestJimengAdapter:
    @pytest.fixture
    def adapter(self):
        return JimengStatusAdapter()

    def test_build_url(self, adapter):
        url = adapter.build_status_url("https://api.jimeng.com/v1/tasks", "task-456")
        assert url == "https://api.jimeng.com/v1/tasks/task-456"

    def test_parse_succeed(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "succeed",
                "video_url": "https://example.com/jimeng.mp4",
            }
        })
        assert result["status"] == "succeed"
        assert result["result_url"] == "https://example.com/jimeng.mp4"

    def test_parse_output_nested(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "succeed",
                "output": {"video_url": "https://example.com/nested.mp4"},
            }
        })
        assert result["result_url"] == "https://example.com/nested.mp4"

    def test_parse_running_status(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "running",
            }
        })
        assert result["status"] == "processing"

    def test_parse_suc_alias(self, adapter):
        result = adapter.parse_response({
            "data": {
                "task_status": "suc",
            }
        })
        assert result["status"] == "succeed"


class TestRunwayAdapter:
    @pytest.fixture
    def adapter(self):
        return RunwayStatusAdapter()

    def test_build_url(self, adapter):
        url = adapter.build_status_url("https://api.runway.com/v1/tasks", "task-789")
        assert url == "https://api.runway.com/v1/tasks/task-789"

    def test_parse_succeeded(self, adapter):
        result = adapter.parse_response({
            "data": {
                "status": "succeeded",
                "url": "https://example.com/runway.mp4",
            }
        })
        assert result["status"] == "succeed"
        assert result["result_url"] == "https://example.com/runway.mp4"

    def test_parse_queued(self, adapter):
        result = adapter.parse_response({
            "data": {
                "status": "queued",
            }
        })
        assert result["status"] == "pending"

    def test_parse_artifacts_array(self, adapter):
        result = adapter.parse_response({
            "data": {
                "status": "succeeded",
                "artifacts": [{"url": "https://example.com/artifact.mp4"}],
            }
        })
        assert result["result_url"] == "https://example.com/artifact.mp4"

    def test_parse_output_artifacts(self, adapter):
        result = adapter.parse_response({
            "data": {
                "status": "succeeded",
                "output": {
                    "artifacts": [{"video_url": "https://example.com/output.mp4"}],
                },
            }
        })
        assert result["result_url"] == "https://example.com/output.mp4"


class TestConfigDrivenAdapter:
    """验证配置驱动特性：行为来自 registry.json，改配置即改行为"""

    def test_registry_contains_all_providers(self):
        registry = load_registry()
        for provider in list_providers():
            assert provider in registry, f"{provider} 缺少 registry 配置"

    def test_all_adapters_are_config_driven(self):
        for provider in list_providers():
            assert isinstance(get_adapter(provider), ConfigDrivenAdapter)

    def test_get_provider_config_unknown(self):
        with pytest.raises(KeyError):
            get_provider_config("nonexistent")

    def test_status_mapping_from_config(self):
        """状态映射完全来自 JSON 配置"""
        cfg = get_provider_config("kling")
        assert cfg["status_map"]["succeed"] == "succeed"
        assert cfg["status_map"]["submitted"] == "pending"

    def test_url_template_from_config(self):
        cfg = get_provider_config("runway")
        assert cfg["status_endpoint_template"] == "{endpoint}/{task_id}"

    def test_reload_registry_keeps_working(self):
        """热重载后适配器仍正常"""
        reload_registry()
        adapter = get_adapter("kling")
        assert adapter.parse_response({"data": {"task_status": "succeed"}})["status"] == "succeed"

    def test_custom_provider_from_registry(self):
        """注册一个自定义 provider 配置，适配器无需代码即可支持"""
        reload_registry()
        registry = load_registry()
        original = dict(registry)
        try:
            registry["fakevendor"] = {
                "status_endpoint_template": "{endpoint}/tasks/{task_id}/status",
                "status_fields": ["state"],
                "status_map": {"done": "succeed"},
                "default_status": "pending",
                "result_url_fields": ["video"],
                "nested_output_fields": [],
                "artifact_fields": [],
                "artifact_url_keys": [],
                "require_http_prefix": True,
            }
            from providers import _adapters
            _adapters["fakevendor"] = ConfigDrivenAdapter()
            _adapters["fakevendor"].provider = "fakevendor"

            adapter = _adapters["fakevendor"]
            assert adapter.build_status_url("https://api.fake.com/v1", "t-1") == \
                "https://api.fake.com/v1/tasks/t-1/status"
            result = adapter.parse_response({"state": "done", "video": "https://x.com/v.mp4"})
            assert result["status"] == "succeed"
            assert result["result_url"] == "https://x.com/v.mp4"
        finally:
            reload_registry()
            registry = load_registry()
            registry.update(original)
            from providers import _adapters
            _adapters.pop("fakevendor", None)
            reload_registry()
