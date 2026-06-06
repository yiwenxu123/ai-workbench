"""
工具函数：payload 构建、端点检测、尺寸校验、结果提取
"""

from typing import Optional
from models import GenerateRequest
from config import MODEL_SIZE_CONFIG


def normalize_size(size: str, endpoint_type: str) -> str:
    size_map = {
        "2K": "2048x2048",
        "4K": "4096x4096",
    }
    if endpoint_type == "doubao":
        if size in size_map:
            return size_map[size]
        if size == "1024x1024":
            return "2048x2048"
    return size


def detect_endpoint_type(endpoint: str) -> str:
    if "volces.com" in endpoint:
        return "doubao"
    elif "bigmodel.cn" in endpoint:
        return "zhipu"
    elif "aliyuncs.com" in endpoint:
        if "multimodal-generation" in endpoint:
            return "qwen-v2"  # 通义千问 2.0 multimodal-generation 格式
        if "compatible-mode" in endpoint:
            return "openai"  # 兼容模式 = OpenAI 兼容格式
        return "aliyun"  # 标准 DashScope text2image 格式
    elif "openai.com" in endpoint:
        return "openai"
    else:
        return "generic"


def _model_based_endpoint_type(model: str) -> Optional[str]:
    if not model:
        return None
    if model.startswith("qwen-image-2.0"):
        return "qwen-v2"
    if model in ("qwen-image-plus", "qwen-image"):
        return "openai"
    if model.startswith("wanx"):
        return "aliyun"
    return None

def build_payload(request: GenerateRequest, endpoint_type: str) -> dict:
    # 模型名作为安全网：即使 endpoint_type 不匹配，模型名也能路由到正确格式
    model_type = _model_based_endpoint_type(request.model or "")
    effective_type = model_type or endpoint_type

    base_payload = {
        "prompt": request.prompt,
        "model": request.model,
    }

    # endpoint_type 优先，仅 generic 时回退到域名匹配
    if effective_type == "doubao":
        normalized_size = normalize_size(request.size, "doubao")
        base_payload.update({
            "size": normalized_size,
            "response_format": request.response_format,
            "watermark": request.watermark,
            "stream": request.stream,
            "sequential_image_generation": "disabled",
        })
        if request.n > 1:
            base_payload["n"] = request.n
    elif effective_type == "zhipu":
        base_payload.update({
            "size": request.size,
        })
    elif effective_type == "aliyun":
        base_payload.update({
            "model": request.model or "wanx-v1",
            "input": {
                "prompt": request.prompt
            },
            "parameters": {
                "size": request.size,
                "n": request.n
            }
        })
        del base_payload["prompt"]
    elif effective_type == "openai":
        base_payload.update({
            "size": request.size,
            "n": request.n,
        })
    elif effective_type == "qwen-v2":
        # 通义千问 2.0 multimodal-generation messages 格式
        size = request.size.replace("x", "*") if request.size else "1024*1024"
        base_payload = {
            "model": request.model or "qwen-image-2.0-pro",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": request.prompt}]
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": request.n or 1,
            }
        }
    else:
        api_endpoint = request.api_endpoint or ""
        if "volces.com" in api_endpoint:
            normalized_size = normalize_size(request.size, "doubao")
            base_payload.update({
                "size": normalized_size,
                "response_format": request.response_format,
                "watermark": request.watermark,
                "stream": request.stream,
                "sequential_image_generation": "disabled",
            })
            if request.n > 1:
                base_payload["n"] = request.n
        elif "bigmodel.cn" in api_endpoint:
            base_payload.update({
                "size": request.size,
            })
        elif "aliyuncs.com" in api_endpoint and "compatible-mode" not in api_endpoint:
            base_payload.update({
                "model": request.model or "wanx-v1",
                "input": {
                    "prompt": request.prompt
                },
                "parameters": {
                    "size": request.size,
                    "n": request.n
                }
            })
            del base_payload["prompt"]
        else:
            base_payload.update({
                "size": request.size,
                "n": request.n,
            })

    if request.extra_params:
        safe_params = {
            k: v for k, v in request.extra_params.items()
            if isinstance(k, str) and not k.startswith('_')
        }
        base_payload.update(safe_params)

    return base_payload


def validate_size_for_model(model: str, size: str) -> tuple[bool, Optional[str]]:
    config = MODEL_SIZE_CONFIG.get(model)
    if not config:
        return True, None

    try:
        width, height = map(int, size.split('x'))
        pixels = width * height

        if pixels < config['min_pixels']:
            min_w = int(config['min_pixels'] ** 0.5)
            return False, f"该模型要求最小 {config['min_pixels']:,} 像素，当前 {pixels:,} 像素不足。建议使用 {min_w}x{min_w} 或更大的尺寸"

        if pixels > config['max_pixels']:
            return False, f"该模型最大支持 {config['max_pixels']:,} 像素，当前尺寸超出限制"

        return True, None
    except ValueError:
        return False, "尺寸格式无效"


def extract_result_url(data: dict) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    for key in ("result_url", "video_url", "url"):
        if data.get(key):
            return data[key]
    # 通义千问 2.0 multimodal-generation 格式
    output = data.get("output") or {}
    choices = output.get("choices") if isinstance(output, dict) else None
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            msg = first_choice.get("message") or {}
            content = msg.get("content") if isinstance(msg, dict) else None
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("image"):
                        return item["image"]
    # 旧版 DashScope text2image 格式
    results = output.get("results") if isinstance(output, dict) else None
    if isinstance(results, list) and results:
        first = results[0]
        if isinstance(first, dict):
            return first.get("url")
    task_result = data.get("task_result") or {}
    videos = task_result.get("videos") if isinstance(task_result, dict) else None
    if isinstance(videos, list) and videos:
        first = videos[0]
        if isinstance(first, dict):
            return first.get("url") or first.get("video_url")
    return None


def infer_model_provider(model_id: str) -> str:
    if model_id.startswith("doubao"):
        return "doubao"
    if model_id.startswith("wanx") or model_id.startswith("qwen"):
        return "aliyun"
    if model_id.startswith("cogview"):
        return "zhipu"
    if model_id.startswith("dall-e"):
        return "openai"
    return "custom"


def infer_model_scenarios(model_id: str) -> list[str]:
    if model_id.startswith("doubao"):
        return ["电商主图", "社媒海报", "PPT配图"]
    if model_id.startswith("wanx"):
        return ["国风插画", "商业海报", "图片编辑"]
    if model_id.startswith("qwen"):
        return ["电商主图", "产品设计", "写实照片"]
    if model_id.startswith("cogview"):
        return ["低成本试用", "知识学习", "草图验证"]
    if model_id.startswith("dall-e"):
        return ["英文提示词", "概念图", "创意探索"]
    return ["通用创作"]


def humanize_api_error(status_code: int, provider: str = "") -> str:
    """将 HTTP 错误码转为用户友好的错误提示"""
    friendly = {
        400: f"请求参数有误，请检查提示词或尺寸设置",
        401: f"API 密钥无效或已过期，请检查密钥是否正确{f'（{provider}）' if provider else ''}",
        402: f"账户余额不足，请充值后再试",
        403: f"无权限访问，请检查 API 密钥权限{f'（{provider}）' if provider else ''}",
        404: f"API 端点地址错误，请检查配置{f'（{provider}）' if provider else ''}",
        429: "请求过于频繁，请稍后再试",
        500: f"API 服务暂时异常{f'（{provider}）' if provider else ''}，请稍后重试",
        502: "API 网关超时，请稍后重试",
        503: "API 服务维护中，请稍后重试",
    }
    return friendly.get(status_code, f"API 请求失败（错误码 {status_code}），请稍后重试")


def detect_default_model(endpoint: str) -> str:
    """为 'default' 模型名称返回供应商的默认模型"""
    if "volces.com" in endpoint:
        return "doubao-seedream-4-5-251128"
    if "bigmodel.cn" in endpoint:
        return "cogview-3-flash"
    if "aliyuncs.com" in endpoint:
        if "compatible-mode" in endpoint:
            return "qwen-image-plus"
        return "wanx-v1"
    if "openai.com" in endpoint:
        return "dall-e-3"
    return ""
