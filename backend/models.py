"""
数据模型：请求/响应的 Pydantic 模型
"""

import re
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from config import PROMPT_MAX_LENGTH, PROMPT_MIN_LENGTH


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=PROMPT_MIN_LENGTH, max_length=PROMPT_MAX_LENGTH, description="图像生成的文本提示词，详细描述画面内容")
    model: str = Field(default="default", max_length=100, description="使用的绘图模型，如 wanx-v1, doubao-seedream-4-5-251128，若不确定可用 default")
    size: str = Field(default="1024x1024", max_length=50, description="生成图片的尺寸分辨率，如 1024x1024, 16:9, 1080p")
    n: int = Field(default=1, ge=1, le=4, description="生成的图片数量")
    extra_params: Optional[dict] = Field(default=None, description="额外的特定模型参数")
    api_key: Optional[str] = Field(default=None, max_length=200, description="可选的覆盖系统配置的API密钥")
    api_endpoint: Optional[str] = Field(default=None, max_length=500, description="可选的API端点URL")
    response_format: Optional[str] = Field(default="url", max_length=20, description="响应格式，通常为 url")
    watermark: Optional[bool] = Field(default=True, description="是否添加水印")
    stream: Optional[bool] = Field(default=False, description="是否流式返回")

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('提示词不能为空')
        if len(v) > PROMPT_MAX_LENGTH:
            raise ValueError(f'提示词长度不能超过 {PROMPT_MAX_LENGTH} 字符')
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('提示词包含不允许的内容')
        return v

    @field_validator('api_endpoint')
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('API端点必须以 http:// 或 https:// 开头')
        return v

    @field_validator('size')
    @classmethod
    def validate_size(cls, v: str) -> str:
        if not re.match(r'^\d+x\d+$', v):
            raise ValueError('尺寸格式应为 宽x高，如 1024x1024')
        return v


class GenerateResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class ConfigResponse(BaseModel):
    has_backend_config: bool
    frontend_config_required: bool
    models: list
    sizes: list
    backend_configured_capabilities: dict[str, bool] = {}


class VideoGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=PROMPT_MIN_LENGTH, max_length=PROMPT_MAX_LENGTH, description="视频生成的画面和运镜描述")
    model: str = Field(default="kling-v1", max_length=100, description="视频模型名称，如 kling-v1, jimeng-v1")
    duration: int = Field(default=5, ge=3, le=15, description="生成的视频时长（秒），支持 3, 5, 10, 15")
    resolution: str = Field(default="1080p", max_length=20, description="视频分辨率，如 720p, 1080p, 4k")
    source_image: Optional[str] = Field(default=None, max_length=100000, description="图生视频所需的源图片URL")
    negative_prompt: Optional[str] = Field(default=None, max_length=PROMPT_MAX_LENGTH, description="不希望在视频中出现的内容描述")
    api_key: Optional[str] = Field(default=None, max_length=200, description="可选的覆盖API密钥")
    api_endpoint: Optional[str] = Field(default=None, max_length=500, description="可选的API端点")

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('提示词不能为空')
        if len(v) > PROMPT_MAX_LENGTH:
            raise ValueError(f'提示词长度不能超过 {PROMPT_MAX_LENGTH} 字符')
        return v


class VideoGenerateResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None
    task_id: Optional[str] = None


class ImageEditRequest(BaseModel):
    image: str = Field(..., max_length=500000, description="需要编辑的原始图片URL或Base64")
    instruction: str = Field(..., min_length=1, max_length=PROMPT_MAX_LENGTH, description="编辑指令描述，例如'把图里的猫换成狗'")
    edit_type: Literal["instruction", "inpaint", "outpaint"] = Field(default="instruction", description="编辑类型: 指令编辑、局部重绘、扩图")
    mask: Optional[str] = Field(default=None, max_length=500000, description="局部重绘所需的蒙版图片URL")
    api_key: Optional[str] = Field(default=None, max_length=200)
    api_endpoint: Optional[str] = Field(default=None, max_length=500)

    @field_validator('instruction')
    @classmethod
    def validate_instruction(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('编辑指令不能为空')
        return v


class ImageEditResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class TaskStatusResponse(BaseModel):
    success: bool
    status: str
    progress: Optional[int] = None
    result_url: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None


class ValidateRequest(BaseModel):
    api_key: str = Field(..., min_length=1, max_length=200)
    api_endpoint: str = Field(..., min_length=1, max_length=500)
    provider_type: str = Field(default="image", max_length=50)
    model: Optional[str] = Field(default=None, max_length=100)


class ValidateResponse(BaseModel):
    success: bool
    valid: bool
    message: str
    details: Optional[str] = None


class IngestExtractRequest(BaseModel):
    content: str = Field(..., max_length=50000, description="待提取的文章文本内容")
    source_url: Optional[str] = Field(default=None, description="来源网址（可选）")
    target_type: str = Field(default="cases", description="提取目标类型: cases / knowledge / templates")
    llm_endpoint: str = Field(..., description="LLM API端点，如 https://api.deepseek.com/v1/chat/completions")
    llm_api_key: str = Field(..., description="LLM API密钥")
    llm_model: str = Field(default="deepseek-chat", description="LLM 模型名称")


class IngestSaveRequest(BaseModel):
    target_type: str = Field(..., description="保存目标: cases / knowledge / templates")
    items: list = Field(..., description="经确认的条目列表（JSON 数组）")
    replace_ids: Optional[list[str]] = Field(default=None, description="需要替换的已有条目 ID 列表")


class FetchUrlRequest(BaseModel):
    url: str = Field(..., max_length=2000, description="需要抓取的网页URL")


class CreateCaseRequest(BaseModel):
    title: str = Field(..., max_length=200, description="案例标题")
    prompt: str = Field(..., max_length=PROMPT_MAX_LENGTH, description="完整提示词")
    negativePrompt: str = Field(default="", max_length=PROMPT_MAX_LENGTH, description="负面提示词")
    model: str = Field(default="", max_length=100, description="使用的模型")
    size: str = Field(default="", max_length=50, description="图片尺寸")
    tips: list[str] = Field(default=[], description="使用技巧")
    tags: list[str] = Field(default=[], description="标签")


class OptimizePromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=PROMPT_MAX_LENGTH, description="需要优化的提示词")
    scene: str = Field(default="general", max_length=50, description="场景: product/marketing/presentation/portrait/illustration/general")
    style: str = Field(default="general", max_length=50, description="风格: general/professional/minimalist/creative/corporate/casual")
    modelType: str = Field(default="", max_length=100, description="目标图像模型ID")
    llm_endpoint: str = Field(default="", description="LLM API端点（可选，默认读 LLM_API_ENDPOINT 环境变量；未配置时降级为知识库规则增强）")
    llm_api_key: str = Field(default="", description="LLM API密钥（可选，默认读 LLM_API_KEY 环境变量；未配置时降级为知识库规则增强）")
    llm_model: str = Field(default="deepseek-chat", description="LLM模型名称")


# ── 知识库相关模型 ─────────────────────────────────────────────────────

class KnowledgeEntry(BaseModel):
    id: str = ""
    type: Literal["term", "formula", "case", "industry", "negative_pack", "template", "shot_language"] = "term"
    title: str = ""
    content: str = ""
    tags: list[str] = []
    category: str = ""
    sceneRelevance: dict[str, float] = {}
    quality: float = 1.0
    usageCount: int = 0
    lastVerified: str = ""
    examples: list[str] = []
    tips: list[str] = []
    relatedTerms: list[str] = []
    prompt: str = ""
    negativePrompt: str = ""
    model: str = ""


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(default="", max_length=1000, description="用户输入的原始提示词")
    scene: str = Field(default="general", max_length=50, description="场景: ecommerce/social/presentation/portrait/illustration/general/...")
    types: list[str] = Field(default=[], description="过滤知识类型，为空则返回全部")
    limit: int = Field(default=10, ge=1, le=30, description="返回条数上限")
    modelType: str = Field(default="", max_length=100, description="目标图像模型ID")


class KnowledgeSearchResponse(BaseModel):
    success: bool = True
    items: list[KnowledgeEntry] = []
    total: int = 0
    query: str = ""
    scene: str = ""


class EvaluateKnowledgeRequest(BaseModel):
    content: str = Field(..., max_length=10000, description="知识条目内容")
    type: str = Field(default="term", description="知识类型: term/formula/case/industry/negative_pack")
    scene: str = Field(default="general", max_length=50, description="目标场景（可选）")
    llm_endpoint: str = Field(..., description="LLM API端点")
    llm_api_key: str = Field(..., description="LLM API密钥")
    llm_model: str = Field(default="deepseek-chat", description="LLM模型名称")


class DeduplicateKnowledgeRequest(BaseModel):
    item: dict = Field(..., description="待检查的知识条目")
    target_type: str = Field(default="knowledge", description="目标知识类型")
    llm_endpoint: str = Field(default="", description="LLM API端点（可选，不提供则仅做本地匹配）")
    llm_api_key: str = Field(default="", description="LLM API密钥（可选）")
    llm_model: str = Field(default="deepseek-chat", description="LLM模型名称")
