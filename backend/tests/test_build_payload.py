"""测试 payload 构建、端点检测、响应解析"""

import pytest
from models import GenerateRequest
from utils import (
    build_payload, detect_endpoint_type, normalize_size,
    validate_size_for_model, extract_result_url,
)
from routers.generation import (
    _is_aliyun_response, _extract_aliyun_urls,
    _is_multimodal_response, _extract_multimodal_urls,
)


class TestDetectEndpointType:
    def test_doubao_by_url(self):
        assert detect_endpoint_type("https://ark.volces.com/api/v3") == "doubao"

    def test_aliyun_by_url(self):
        assert detect_endpoint_type("https://dashscope.aliyuncs.com/api/v1") == "aliyun"

    def test_zhipu_by_url(self):
        assert detect_endpoint_type("https://open.bigmodel.cn/api/paas/v4") == "zhipu"

    def test_openai_by_url(self):
        assert detect_endpoint_type("https://api.openai.com/v1/images/generations") == "openai"

    def test_qwen_v2_by_url(self):
        assert detect_endpoint_type("https://dashscope.aliyuncs.com/api/v1/multimodal-generation") == "qwen-v2"

    def test_compatible_mode_returns_openai(self):
        assert detect_endpoint_type("https://dashscope.aliyuncs.com/compatible-mode/v1") == "openai"

    def test_unknown_endpoint(self):
        assert detect_endpoint_type("https://custom.example.com/api") == "generic"


class TestNormalizeSize:
    def test_doubao_1024_to_2048(self):
        assert normalize_size("1024x1024", "doubao") == "2048x2048"

    def test_doubao_2k_expanded(self):
        assert normalize_size("2K", "doubao") == "2048x2048"

    def test_doubao_4k_expanded(self):
        assert normalize_size("4K", "doubao") == "4096x4096"

    def test_non_doubao_passthrough(self):
        assert normalize_size("1024x1024", "openai") == "1024x1024"

    def test_doubao_custom_size(self):
        assert normalize_size("1344x768", "doubao") == "1344x768"


class TestValidateSizeForModel:
    def test_valid_size(self):
        ok, err = validate_size_for_model("doubao-seedream-4-5-251128", "1024x1024")
        assert ok is True
        assert err is None

    def test_too_small(self):
        ok, err = validate_size_for_model("doubao-seedream-4-5-251128", "128x128")
        assert ok is False
        assert err is not None
        assert "像素" in err

    def test_unknown_model(self):
        ok, err = validate_size_for_model("unknown-model", "1024x1024")
        assert ok is True
        assert err is None

    def test_invalid_format(self):
        ok, err = validate_size_for_model("doubao-seedream-4-5-251128", "invalid")
        assert ok is False
        assert err is not None and "格式无效" in err


class TestBuildPayload:
    def test_openai_payload(self):
        req = GenerateRequest(prompt="test", model="dall-e-3", api_endpoint="https://api.openai.com/v1")
        payload = build_payload(req, "openai")
        assert payload["model"] == "dall-e-3"
        assert payload["prompt"] == "test"
        assert payload["n"] == 1
        assert "size" in payload

    def test_doubao_payload(self):
        req = GenerateRequest(prompt="test", model="doubao-seedream-4-5-251128", api_endpoint="https://ark.volces.com/api/v3")
        payload = build_payload(req, "doubao")
        assert payload["model"] == "doubao-seedream-4-5-251128"
        assert payload["prompt"] == "test"
        assert payload["sequential_image_generation"] == "disabled"
        # 1024x1024 应该被放大为 2048x2048
        assert payload["size"] == "2048x2048"

    def test_zhipu_payload(self):
        req = GenerateRequest(prompt="test", model="cogview-3", api_endpoint="https://open.bigmodel.cn")
        payload = build_payload(req, "zhipu")
        assert payload["model"] == "cogview-3"
        assert payload["prompt"] == "test"
        assert "input" not in payload

    def test_aliyun_payload(self):
        req = GenerateRequest(prompt="test", model="wanx-v1", api_endpoint="https://dashscope.aliyuncs.com")
        payload = build_payload(req, "aliyun")
        assert payload["model"] == "wanx-v1"
        assert payload["input"]["prompt"] == "test"
        assert payload["parameters"]["size"] == "1024x1024"

    def test_qwen_v2_payload(self):
        req = GenerateRequest(prompt="test", model="qwen-image-2.0-pro", size="1024x1024")
        payload = build_payload(req, "qwen-v2")
        assert payload["model"] == "qwen-image-2.0-pro"
        assert payload["input"]["messages"][0]["content"][0]["text"] == "test"
        assert payload["parameters"]["size"] == "1024*1024"

    def test_generic_endpoint_falls_to_openai(self):
        req = GenerateRequest(prompt="test", model="custom-model", api_endpoint="https://custom.com/v1")
        payload = build_payload(req, "generic")
        assert payload["model"] == "custom-model"
        # generic 无法通过 URL 识别，应 fallback 到 openai 格式
        assert "prompt" in payload

    def test_extra_params_merged(self):
        req = GenerateRequest(
            prompt="test", model="dall-e-3",
            api_endpoint="https://api.openai.com/v1",
            extra_params={"quality": "hd", "style": "vivid"},
        )
        payload = build_payload(req, "openai")
        assert payload["quality"] == "hd"
        assert payload["style"] == "vivid"

    def test_extra_params_private_keys_filtered(self):
        req = GenerateRequest(
            prompt="test", model="dall-e-3",
            extra_params={"_secret": "nope", "valid": "ok"},
        )
        payload = build_payload(req, "openai")
        assert "_secret" not in payload
        assert payload["valid"] == "ok"

    def test_request_n_gt_1_doubao(self):
        req = GenerateRequest(prompt="test", model="doubao", n=4, api_endpoint="https://ark.volces.com")
        payload = build_payload(req, "doubao")
        assert payload["n"] == 4


class TestAliyunResponseParsing:
    def test_is_aliyun_response(self):
        resp = {"output": {"results": [{"url": "https://example.com/img.jpg"}]}}
        assert _is_aliyun_response(resp) is True

    def test_is_not_aliyun_response(self):
        assert _is_aliyun_response({"data": [{"url": "x.jpg"}]}) is False
        assert _is_aliyun_response("not a dict") is False

    def test_extract_aliyun_urls(self):
        resp = {"output": {"results": [{"url": "https://img1.jpg"}, {"url": "https://img2.jpg"}]}}
        result = _extract_aliyun_urls(resp)
        assert len(result["data"]) == 2
        assert result["data"][0]["url"] == "https://img1.jpg"
        assert result["data"][1]["url"] == "https://img2.jpg"

    def test_extract_aliyun_empty(self):
        resp = {"output": {"results": []}}
        result = _extract_aliyun_urls(resp)
        assert result["data"] == []


class TestMultimodalResponseParsing:
    def test_is_multimodal_response(self):
        resp = {"output": {"choices": [{"message": {"content": []}}]}}
        assert _is_multimodal_response(resp) is True

    def test_is_not_multimodal(self):
        assert _is_multimodal_response({"data": []}) is False
        assert _is_multimodal_response("text") is False

    def test_extract_multimodal_urls(self):
        resp = {
            "output": {
                "choices": [{
                    "message": {
                        "content": [
                            {"image": "https://img1.jpg"},
                            {"text": "description"},
                            {"image": "https://img2.jpg"},
                        ]
                    }
                }]
            }
        }
        result = _extract_multimodal_urls(resp)
        assert len(result["data"]) == 2
        assert result["data"][0]["url"] == "https://img1.jpg"
        assert result["data"][1]["url"] == "https://img2.jpg"

    def test_extract_multimodal_empty_choices(self):
        resp = {"output": {"choices": []}}
        result = _extract_multimodal_urls(resp)
        assert result["data"] == []

    def test_extract_multimodal_missing_message(self):
        resp = {"output": {"choices": [{"no_message": True}]}}
        result = _extract_multimodal_urls(resp)
        assert result["data"] == []


class TestExtractResultUrl:
    def test_result_url_key(self):
        assert extract_result_url({"result_url": "https://ex.com/v.mp4"}) == "https://ex.com/v.mp4"

    def test_video_url_key(self):
        assert extract_result_url({"video_url": "https://ex.com/v.mp4"}) == "https://ex.com/v.mp4"

    def test_url_key(self):
        assert extract_result_url({"url": "https://ex.com/v.mp4"}) == "https://ex.com/v.mp4"

    def test_precedence_result_over_video(self):
        data = {"result_url": "https://ex.com/r.mp4", "video_url": "https://ex.com/v.mp4"}
        assert extract_result_url(data) == "https://ex.com/r.mp4"

    def test_aliyun_output_format(self):
        data = {"output": {"results": [{"url": "https://ex.com/img.jpg"}]}}
        assert extract_result_url(data) == "https://ex.com/img.jpg"

    def test_multimodal_output_format(self):
        data = {"output": {"choices": [{"message": {"content": [{"image": "https://ex.com/img.jpg"}]}}]}}
        assert extract_result_url(data) == "https://ex.com/img.jpg"

    def test_task_result_videos(self):
        data = {"task_result": {"videos": [{"url": "https://ex.com/v.mp4"}]}}
        assert extract_result_url(data) == "https://ex.com/v.mp4"

    def test_none_input(self):
        assert extract_result_url(None) is None  # type: ignore

    def test_empty_dict(self):
        assert extract_result_url({}) is None
