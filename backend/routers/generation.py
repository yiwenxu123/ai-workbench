"""
图像/视频生成、图片编辑路由
"""
from datetime import date, datetime
from typing import Union

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import (
    ALIYUN_EDIT_API_ENDPOINT, ALIYUN_EDIT_API_KEY,
    BACKEND_CONFIGURED_CAPABILITIES,
    DEFAULT_API_ENDPOINT, DEFAULT_API_KEY,
    DEFAULT_IMAGE_SIZES,
    EDIT_MODEL_MANIFEST,
    KLING_API_ENDPOINT, KLING_API_KEY,
    MODEL_DISPLAY_NAMES,
    MODEL_LAST_VERIFIED,
    MODEL_SIZE_CONFIG,
    VERIFICATION_MAX_AGE_DAYS,
    VIDEO_MODEL_MANIFEST,
)
from models import (
    ConfigResponse, GenerateRequest, GenerateResponse,
    ImageEditRequest, ImageEditResponse,
    TaskStatusResponse, ValidateRequest, ValidateResponse,
    VideoGenerateRequest, VideoGenerateResponse,
)
from providers import get_adapter
from utils import (
    build_payload, detect_default_model, detect_endpoint_type,
    extract_result_url, humanize_api_error, infer_model_provider,
    infer_model_scenarios, validate_size_for_model,
)

router = APIRouter()


# ── Helper functions ────────────────────────────────────────────────────

async def _call_api(
    api_key: str, api_endpoint: str, payload: dict,
    timeout: float = 180.0,
) -> tuple[int, Union[str, dict]]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(api_endpoint, json=payload, headers=headers)
        if response.status_code != 200:
            return response.status_code, response.text[:500]
        return response.status_code, response.json()


def _is_aliyun_response(result: Union[str, dict]) -> bool:
    return isinstance(result, dict) and "output" in result and "results" in result["output"]


def _extract_aliyun_urls(result: dict) -> dict:
    urls = [item.get("url") for item in result["output"]["results"]]
    return {"data": [{"url": url} for url in urls if url]}


def _is_multimodal_response(result: Union[str, dict]) -> bool:
    """检测是否为 通义千问 2.0 multimodal-generation 响应格式"""
    if not isinstance(result, dict):
        return False
    output = result.get("output")
    if not isinstance(output, dict):
        return False
    choices = output.get("choices")
    return isinstance(choices, list) and len(choices) > 0


def _extract_multimodal_urls(result: dict) -> dict:
    """从 multimodal-generation 响应中提取图片 URL → 标准 {data: [{url: ...}]} 格式"""
    output = result.get("output") or {}
    choices = output.get("choices") or []
    urls = []
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        msg = choice.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("image"):
                    urls.append(item["image"])
    return {"data": [{"url": url} for url in urls if url]}


# ── Config & Models ────────────────────────────────────────────────────


def _build_config_models() -> list[dict]:
    models = [{"id": "default", "name": MODEL_DISPLAY_NAMES.get("default", "默认模型")}]
    for model_id in MODEL_SIZE_CONFIG:
        models.append({
            "id": model_id,
            "name": MODEL_DISPLAY_NAMES.get(model_id, model_id),
        })
    return models


@router.get("/config", response_model=ConfigResponse)
async def get_config():
    has_backend_config = bool(DEFAULT_API_KEY and DEFAULT_API_ENDPOINT)
    return ConfigResponse(
        has_backend_config=has_backend_config,
        frontend_config_required=not has_backend_config,
        models=_build_config_models(),
        sizes=DEFAULT_IMAGE_SIZES,
        backend_configured_capabilities=BACKEND_CONFIGURED_CAPABILITIES,
    )


@router.get("/models/video")
async def get_video_models():
    return {
        "models": [
            {
                "id": m["id"],
                "name": m["name"],
                "description": m.get("description", ""),
                "durations": m.get("durations", [5]),
                "resolutions": m.get("resolutions", ["720p"]),
                "provider": m.get("provider", ""),
            }
            for m in VIDEO_MODEL_MANIFEST
        ],
        "resolutions": sorted(set(
            r for m in VIDEO_MODEL_MANIFEST for r in m.get("resolutions", [])
        )),
        "durations": sorted(set(
            d for m in VIDEO_MODEL_MANIFEST for d in m.get("durations", [])
        )),
    }


@router.get("/models/edit")
async def get_edit_models():
    return {
        "models": [
            {"id": "wanx2.1-imageedit", "name": "阿里云万相编辑", "description": "支持指令编辑、局部重绘、扩图"},
        ],
        "edit_types": [
            {"id": "instruction", "name": "指令编辑", "description": "用文字描述修改图片"},
            {"id": "inpaint", "name": "局部重绘", "description": "涂抹区域+文字描述修改"},
            {"id": "outpaint", "name": "扩图", "description": "扩展画布并自动补全"},
        ],
    }


# ── Image Generation ───────────────────────────────────────────────────


@router.post("/generate", response_model=GenerateResponse, summary="生成AI图片 (Skill)", tags=["Skills"], operation_id="generateImage")
async def generate_image(request: GenerateRequest):
    api_key = request.api_key or DEFAULT_API_KEY
    api_endpoint = request.api_endpoint or DEFAULT_API_ENDPOINT

    if not api_key or not api_endpoint:
        return GenerateResponse(success=False, error="请配置API密钥和端点地址")

    if request.model == 'default':
        resolved_model = detect_default_model(api_endpoint)
        if not resolved_model:
            return GenerateResponse(success=False, error="请选择具体的模型（当前为 default），或在 API 配置中设置默认模型")
        request.model = resolved_model

    is_valid, size_error = validate_size_for_model(request.model, request.size)
    if not is_valid:
        return GenerateResponse(success=False, error=size_error)

    endpoint_type = detect_endpoint_type(api_endpoint)
    payload = build_payload(request, endpoint_type)

    try:
        status_code, result = await _call_api(api_key, api_endpoint, payload)

        if status_code != 200:
            provider = detect_endpoint_type(api_endpoint)
            return GenerateResponse(success=False, error=humanize_api_error(status_code, provider))

        if status_code == 200:
            if _is_aliyun_response(result):
                result = _extract_aliyun_urls(result)
            elif _is_multimodal_response(result):
                result = _extract_multimodal_urls(result)

        return GenerateResponse(success=True, data=result)
    except httpx.TimeoutException:
        return GenerateResponse(success=False, error="请求超时，请稍后重试")
    except httpx.ConnectError:
        return GenerateResponse(success=False, error="无法连接到API端点，请检查地址")
    except Exception as e:
        return GenerateResponse(success=False, error=f"请求失败: {str(e)}")


# ── Video Generation ───────────────────────────────────────────────────


@router.post("/generate-video", response_model=VideoGenerateResponse, summary="生成AI视频任务 (Skill)", tags=["Skills"], operation_id="generateVideo")
async def generate_video(request: VideoGenerateRequest):
    api_key = request.api_key or KLING_API_KEY
    api_endpoint = request.api_endpoint or KLING_API_ENDPOINT

    if not api_key or not api_endpoint:
        return VideoGenerateResponse(success=False, error="请配置视频生成API密钥和端点地址")

    payload = {
        "prompt": request.prompt,
        "model": request.model,
        "duration": request.duration,
        "resolution": request.resolution,
    }
    if request.source_image:
        payload["source_image"] = request.source_image
    if request.negative_prompt:
        payload["negative_prompt"] = request.negative_prompt

    try:
        status_code, result = await _call_api(api_key, api_endpoint, payload, timeout=300.0)

        if status_code not in [200, 201]:
            return VideoGenerateResponse(success=False, error=humanize_api_error(status_code, request.model))

        task_id = (result.get("task_id") or result.get("id") or
                   (result.get("data") or {}).get("task_id"))
        return VideoGenerateResponse(success=True, data=result, task_id=task_id)
    except httpx.TimeoutException:
        return VideoGenerateResponse(success=False, error="请求超时，视频生成可能需要较长时间")
    except httpx.ConnectError:
        return VideoGenerateResponse(success=False, error="无法连接到视频API端点")
    except Exception as e:
        return VideoGenerateResponse(success=False, error=f"请求失败: {str(e)}")


# ── Task Status ────────────────────────────────────────────────────────


@router.get("/task-status/{task_id}", response_model=TaskStatusResponse, summary="查询生成任务状态 (Skill)", tags=["Skills"], operation_id="checkTaskStatus")
async def get_task_status(
    task_id: str,
    api_key: str = None,
    api_endpoint: str = None,
    provider: str = None,
):
    key = api_key or KLING_API_KEY
    endpoint = api_endpoint or "https://api.klingai.com/v1/videos/generations"

    if not key:
        return TaskStatusResponse(success=False, status="failed", error="未配置API密钥")

    adapter = get_adapter(provider)
    headers = adapter.build_headers(key)
    status_url = adapter.build_status_url(endpoint, task_id)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(status_url, headers=headers)

            if response.status_code != 200:
                return TaskStatusResponse(success=False, status="failed", error=f"API错误: {response.text}")

            parsed = adapter.parse_response(response.json())

            return TaskStatusResponse(
                success=True,
                status=parsed["status"],
                progress=parsed["progress"],
                result_url=parsed["result_url"],
                data=parsed["raw_data"],
            )
    except Exception as e:
        return TaskStatusResponse(success=False, status="failed", error=f"查询失败: {str(e)}")


# ── Image Editing ──────────────────────────────────────────────────────


@router.post("/edit-image", response_model=ImageEditResponse, summary="AI图片编辑 (Skill)", tags=["Skills"], operation_id="editImage")
async def edit_image(request: ImageEditRequest):
    api_key = request.api_key or ALIYUN_EDIT_API_KEY
    api_endpoint = request.api_endpoint or ALIYUN_EDIT_API_ENDPOINT

    if not api_key or not api_endpoint:
        return ImageEditResponse(success=False, error="请配置图片编辑API密钥和端点地址")

    payload = {
        "model": "wanx2.1-imageedit",
        "input": {"image": request.image, "instruction": request.instruction},
    }
    if request.edit_type == "inpaint" and request.mask:
        payload["input"]["mask"] = request.mask

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(api_endpoint, json=payload, headers=headers)

            if response.status_code not in [200, 201]:
                return ImageEditResponse(success=False, error=humanize_api_error(response.status_code, '阿里云万相编辑'))

            result = response.json()
            if "output" in result and "results" in result["output"]:
                urls = [item.get("url") for item in result["output"]["results"]]
                result = {"data": [{"url": url} for url in urls if url]}

            return ImageEditResponse(success=True, data=result)
    except httpx.TimeoutException:
        return ImageEditResponse(success=False, error="请求超时，请稍后重试")
    except httpx.ConnectError:
        return ImageEditResponse(success=False, error="无法连接到编辑API端点")
    except Exception as e:
        return ImageEditResponse(success=False, error=f"请求失败: {str(e)}")


# ── API Validation ─────────────────────────────────────────────────────


@router.post("/validate-api", response_model=ValidateResponse)
async def validate_api(request: ValidateRequest):
    provider_type = request.provider_type.lower()

    if provider_type in ["image", "doubao", "zhipu", "aliyun", "openai"]:
        # 根据 endpoint 判断格式
        if request.api_endpoint and "multimodal-generation" in request.api_endpoint:
            test_payload = {
                "model": "qwen-image-2.0-pro",
                "input": {
                    "messages": [
                        {"role": "user", "content": [{"text": "test"}]}
                    ]
                },
                "parameters": {"size": "1024*1024", "n": 1}
            }
        else:
            test_payload = {"prompt": "test", "model": "default", "size": "256x256", "n": 1}
    elif provider_type in ["video", "kling", "jimeng", "runway"]:
        test_payload = {"prompt": "test video", "model": "kling-v1", "duration": 3, "resolution": "720p"}
    elif provider_type in ["edit", "wanx"]:
        test_payload = {
            "model": "wanx2.1-imageedit",
            "input": {
                "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "instruction": "test",
            },
        }
    elif provider_type in ["llm", "deepseek", "chatglm", "qwen"]:
        # LLM 类型：发送最小化 chat completion 请求验证连通性
        llm_model = request.model or "deepseek-chat"
        test_payload = {
            "model": llm_model,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 1,
        }
    else:
        return ValidateResponse(success=True, valid=False, message=f"不支持的供应商类型: {provider_type}")

    headers = {
        "Authorization": f"Bearer {request.api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(request.api_endpoint, json=test_payload, headers=headers)

            if response.status_code == 401:
                return ValidateResponse(success=True, valid=False, message="API密钥无效或已过期", details="请检查API密钥是否正确")
            elif response.status_code == 403:
                return ValidateResponse(success=True, valid=False, message="无权限访问此API", details="请检查API密钥权限或账户余额")
            elif response.status_code == 404:
                return ValidateResponse(success=True, valid=False, message="API端点地址错误", details="请检查API端点URL是否正确")
            elif response.status_code in [200, 201, 400, 422]:
                return ValidateResponse(success=True, valid=True, message="API配置有效", details="验证成功，可以正常使用")
            else:
                return ValidateResponse(success=True, valid=False, message=f"API返回异常状态码: {response.status_code}", details=response.text[:200])
    except httpx.TimeoutException:
        return ValidateResponse(success=True, valid=False, message="API连接超时", details="请检查网络连接或API端点是否可访问")
    except httpx.ConnectError:
        return ValidateResponse(success=True, valid=False, message="无法连接到API端点", details="请检查API端点URL是否正确，或网络是否通畅")
    except Exception as e:
        return ValidateResponse(success=True, valid=False, message=f"验证失败: {str(e)}")


# ── Model Manifest ─────────────────────────────────────────────────────


@router.get("/api/model-manifest", summary="获取模型能力注册表")
async def get_model_manifest():
    updated_at = "2026-06-12"

    def _recommended_sizes(model_cfg: dict) -> list[str]:
        supported = model_cfg.get("supported_sizes", [])
        return supported[:4] if isinstance(supported, list) else []

    def _verification(model: dict) -> dict:
        """根据 last_verified 计算 verified 状态"""
        last = model.get("last_verified") or MODEL_LAST_VERIFIED.get(model.get("id", ""))
        verified = False
        if last:
            try:
                last_date = datetime.strptime(last, "%Y-%m-%d").date()
                verified = (date.today() - last_date).days <= VERIFICATION_MAX_AGE_DAYS
            except ValueError:
                verified = False
        return {"last_verified": last, "verified": verified}

    image_models = [
        {
            "id": model_id,
            "name": MODEL_DISPLAY_NAMES.get(model_id, model_id),
            "provider": infer_model_provider(model_id),
            "capabilities": ["image"] + (["advanced_params"] if model_id in ("dall-e-3", "dall-e-2", "stable-diffusion") else []),
            "supported_sizes": model_cfg.get("supported_sizes", []),
            "recommended_sizes": _recommended_sizes(model_cfg),
            "min_pixels": model_cfg.get("min_pixels"),
            "max_pixels": model_cfg.get("max_pixels"),
            "auto_scale": model_cfg.get("auto_scale", False),
            "async": False,
            "recommended_scenarios": infer_model_scenarios(model_id),
            "limitations": model_cfg.get("note"),
            "pricing": "paid",
            "updated_at": updated_at,
            **_verification({"id": model_id}),
        }
        for model_id, model_cfg in MODEL_SIZE_CONFIG.items()
    ]

    video_models = [
        {
            "id": m["id"],
            "name": m["name"],
            "description": m.get("description", ""),
            "provider": m["provider"],
            "capabilities": ["video", "image-to-video"],
            "supported_sizes": [],
            "durations": m.get("durations", [3, 5, 10, 15]),
            "max_duration": max(m.get("durations", [15])),
            "resolutions": m.get("resolutions", ["720p", "1080p"]),
            "supports_image_input": True,
            "async": True,
            "pricing": "paid",
            "recommended_scenarios": m.get("recommended_scenarios", []),
            "limitations": m.get("limitations"),
            "updated_at": updated_at,
            **_verification(m),
        }
        for m in VIDEO_MODEL_MANIFEST
    ]

    edit_model = {
        "id": EDIT_MODEL_MANIFEST["id"],
        "name": EDIT_MODEL_MANIFEST["name"],
        "provider": EDIT_MODEL_MANIFEST["provider"],
        "capabilities": ["edit"],
        "supported_sizes": [],
        "async": True,
        "pricing": "paid",
        "recommended_scenarios": EDIT_MODEL_MANIFEST.get("recommended_scenarios", []),
        "limitations": EDIT_MODEL_MANIFEST.get("limitations"),
        "updated_at": updated_at,
        **_verification(EDIT_MODEL_MANIFEST),
    }

    return {
        "updated_at": updated_at,
        "models": image_models + video_models + [edit_model],
    }
