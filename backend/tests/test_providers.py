"""测试多厂商任务状态适配器"""

import pytest
from providers import get_adapter, list_providers
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
