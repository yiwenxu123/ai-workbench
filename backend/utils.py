"""
工具函数：payload 构建、端点检测、尺寸校验、结果提取

重构说明：
- 用策略函数替代 build_payload 中的 if-else 重复链
- 统一端点类型解析逻辑（模型名 + URL 双重检测）
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


# ── 端点类型检测 ──────────────────────────────────────────────────

# URL 关键字 → 端点类型的映射表（按优先级排列）
_URL_TYPE_MAP: list[tuple[str, str]] = [
    ("multimodal-generation", "qwen-v2"),
    ("compatible-mode", "openai"),
    ("volces.com", "doubao"),
    ("bigmodel.cn", "zhipu"),
    ("aliyuncs.com", "aliyun"),
    ("openai.com", "openai"),
]

# 模型名前缀 → 端点类型的映射表
_MODEL_TYPE_MAP: list[tuple[str, str]] = [
    ("qwen-image-2.0", "qwen-v2"),
    ("qwen-image-plus", "openai"),
    ("qwen-image", "openai"),
    ("wanx", "aliyun"),
]


def detect_endpoint_type(endpoint: str) -> str:
    """根据 URL 域名/路径检测端点类型"""
    for keyword, etype in _URL_TYPE_MAP:
        if keyword in endpoint:
            return etype
    return "generic"


def _model_based_endpoint_type(model: str) -> Optional[str]:
    """根据模型名推断端点类型"""
    if not model:
        return None
    for prefix, etype in _MODEL_TYPE_MAP:
        if model.startswith(prefix):
            return etype
    return None


def _resolve_endpoint_type(model: str, endpoint: str) -> str:
    """统一解析端点类型：模型名优先，URL 兜底"""
    return _model_based_endpoint_type(model) or detect_endpoint_type(endpoint)


# ── 各供应商的 Payload 构建策略 ────────────────────────────────────

def _build_doubao_payload(req: GenerateRequest) -> dict:
    """豆包 / volces.com 格式"""
    normalized = normalize_size(req.size, "doubao")
    payload = {
        "prompt": req.prompt,
        "model": req.model,
        "size": normalized,
        "response_format": req.response_format,
        "watermark": req.watermark,
        "stream": req.stream,
        "sequential_image_generation": "disabled",
    }
    if req.n > 1:
        payload["n"] = req.n
    return payload


def _build_zhipu_payload(req: GenerateRequest) -> dict:
    """智谱 / bigmodel.cn 格式"""
    return {
        "prompt": req.prompt,
        "model": req.model,
        "size": req.size,
    }


def _build_aliyun_payload(req: GenerateRequest) -> dict:
    """阿里云 DashScope text2image 格式"""
    return {
        "model": req.model or "wanx-v1",
        "input": {"prompt": req.prompt},
        "parameters": {"size": req.size, "n": req.n},
    }


def _build_openai_payload(req: GenerateRequest) -> dict:
    """OpenAI / 兼容模式格式"""
    return {
        "prompt": req.prompt,
        "model": req.model,
        "size": req.size,
        "n": req.n,
    }


def _build_qwen_v2_payload(req: GenerateRequest) -> dict:
    """通义千问 2.0 multimodal-generation messages 格式"""
    size = req.size.replace("x", "*") if req.size else "1024*1024"
    return {
        "model": req.model or "qwen-image-2.0-pro",
        "input": {
            "messages": [
                {"role": "user", "content": [{"text": req.prompt}]}
            ]
        },
        "parameters": {"size": size, "n": req.n or 1},
    }


# 端点类型 → 构建函数的映射
_PAYLOAD_BUILDERS: dict[str, callable] = {
    "doubao": _build_doubao_payload,
    "zhipu": _build_zhipu_payload,
    "aliyun": _build_aliyun_payload,
    "openai": _build_openai_payload,
    "qwen-v2": _build_qwen_v2_payload,
}


def build_payload(request: GenerateRequest, endpoint_type: str) -> dict:
    """根据端点类型构建 API 请求 payload

    优先使用传入的 endpoint_type，为 generic 时通过模型名+URL 重新解析。
    """
    effective_type = endpoint_type if endpoint_type != "generic" else _resolve_endpoint_type(
        request.model or "", request.api_endpoint or ""
    )

    builder = _PAYLOAD_BUILDERS.get(effective_type, _build_openai_payload)
    payload = builder(request)

    # 合并 extra_params（安全过滤）
    if request.extra_params:
        safe_params = {
            k: v for k, v in request.extra_params.items()
            if isinstance(k, str) and not k.startswith('_')
        }
        payload.update(safe_params)

    return payload


# ── 尺寸校验 ──────────────────────────────────────────────────────

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


# ── 结果提取 ──────────────────────────────────────────────────────

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


# ── 模型信息推断 ──────────────────────────────────────────────────

_PROVIDER_MAP: list[tuple[str, str]] = [
    ("doubao", "doubao"),
    ("wanx", "aliyun"),
    ("qwen", "aliyun"),
    ("cogview", "zhipu"),
    ("dall-e", "openai"),
]

_SCENARIO_MAP: dict[str, list[str]] = {
    "doubao": ["电商主图", "社媒海报", "PPT配图"],
    "wanx": ["国风插画", "商业海报", "图片编辑"],
    "qwen": ["电商主图", "产品设计", "写实照片"],
    "cogview": ["低成本试用", "知识学习", "草图验证"],
    "dall-e": ["英文提示词", "概念图", "创意探索"],
}


def infer_model_provider(model_id: str) -> str:
    for prefix, provider in _PROVIDER_MAP:
        if model_id.startswith(prefix):
            return provider
    return "custom"


def infer_model_scenarios(model_id: str) -> list[str]:
    for prefix, scenarios in _SCENARIO_MAP.items():
        if model_id.startswith(prefix):
            return scenarios
    return ["通用创作"]


def humanize_api_error(status_code: int, provider: str = "") -> str:
    """将 HTTP 错误码转为用户友好的错误提示"""
    suffix = f"（{provider}）" if provider else ""
    friendly = {
        400: "请求参数有误，请检查提示词或尺寸设置",
        401: f"API 密钥无效或已过期，请检查密钥是否正确{suffix}",
        402: "账户余额不足，请充值后再试",
        403: f"无权限访问，请检查 API 密钥权限{suffix}",
        404: f"API 端点地址错误，请检查配置{suffix}",
        429: "请求过于频繁，请稍后再试",
        500: f"API 服务暂时异常{suffix}，请稍后重试",
        502: "API 网关超时，请稍后重试",
        503: "API 服务维护中，请稍后重试",
    }
    return friendly.get(status_code, f"API 请求失败（错误码 {status_code}），请稍后重试")


def humanize_provider_error(status_code: int, body: str = "", provider: str = "") -> str:
    """优先解析上游返回的业务错误码，给出准确提示；无法解析时退回状态码映射"""
    business_hints = (
        ("arrearage", "账户欠费或状态异常，请检查账户余额"),
        ("overdue", "账户欠费或状态异常，请检查账户余额"),
        ("insufficient balance", "账户余额不足，请充值后再试"),
        ("model not exist", "模型不存在或已下线，请在模型清单中选择可用模型"),
        ("invalidapikey", "API 密钥无效或已过期，请检查密钥是否正确"),
        ("throttling", "请求过于频繁，请稍后再试"),
        ("flowcontrol", "请求过于频繁，请稍后再试"),
        ("invalidparameter", "请求参数有误，请检查提示词或尺寸设置"),
        ("request throttled", "请求过于频繁，请稍后再试"),
    )
    lowered = body.lower()
    for keyword, hint in business_hints:
        if keyword in lowered:
            return hint
    return humanize_api_error(status_code, provider)


def detect_default_model(endpoint: str) -> str:
    """为 'default' 模型名称返回供应商的默认模型"""
    for keyword, model in [
        ("volces.com", "doubao-seedream-4-5-251128"),
        ("bigmodel.cn", "cogview-3-flash"),
        ("openai.com", "dall-e-3"),
    ]:
        if keyword in endpoint:
            return model
    if "aliyuncs.com" in endpoint:
        if "multimodal-generation" in endpoint:
            return "qwen-image-2.0-pro"
        return "qwen-image-plus" if "compatible-mode" in endpoint else "wanx-v1"
    return ""
