"""
后端配置：速率限制、模型能力注册表、常量
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"

PROMPT_MAX_LENGTH = 4000
PROMPT_MIN_LENGTH = 1
RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW = 60

RATE_LIMITED_PATHS = frozenset({
    "/generate",
    "/generate-video",
    "/edit-image",
    "/api/ingest/fetch-url",
    "/api/ingest/extract",
    "/api/ingest/save",
})

# ── Provider API Keys (backend-configured, frontend can opt out) ──────
DEFAULT_API_KEY = os.getenv("API_KEY")
DEFAULT_API_ENDPOINT = os.getenv("API_ENDPOINT")
KLING_API_KEY = os.getenv("KLING_API_KEY")
KLING_API_ENDPOINT = os.getenv("KLING_API_ENDPOINT", "https://api.klingai.com/v1/videos/generations")
JIMENG_API_KEY = os.getenv("JIMENG_API_KEY")
JIMENG_API_ENDPOINT = os.getenv("JIMENG_API_ENDPOINT", "https://jimeng.bytedance.com/api/v1/videos/generations")
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
RUNWAY_API_ENDPOINT = os.getenv("RUNWAY_API_ENDPOINT", "https://api.runwayml.com/v1/videos/generations")
ALIYUN_EDIT_API_KEY = os.getenv("ALIYUN_API_KEY")
ALIYUN_EDIT_API_ENDPOINT = os.getenv("ALIYUN_API_ENDPOINT", "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-edit")

# Which capabilities have backend-configured keys (for frontend to decide UI)
BACKEND_CONFIGURED_CAPABILITIES = {
    "image": bool(DEFAULT_API_KEY and DEFAULT_API_ENDPOINT),
    "video": bool(KLING_API_KEY or JIMENG_API_KEY or RUNWAY_API_KEY),
    "edit": bool(ALIYUN_EDIT_API_KEY),
}

MODEL_DISPLAY_NAMES = {
    'default': '默认模型',
    'doubao-seedream-4-5-251128': '豆包 Seedream 4.5',
    'doubao-seedream-4-0-250828': '豆包 Seedream 4.0',
    'cogview-3-flash': '智谱 CogView-3-Flash (免费)',
    'cogview-3-plus': '智谱 CogView-3-Plus',
    'wanx-v1': '通义万相 V1',
    'wanx-xl': '通义万相 XL',
    'dall-e-3': 'DALL-E 3',
    'dall-e-2': 'DALL-E 2',
    'qwen-image-plus': '通义千问 Qwen-Image-Plus',
    'qwen-image': '通义千问 Qwen-Image',
    'qwen-image-2.0-pro': '通义千问 Qwen-Image-2.0-Pro',
    'qwen-image-2.0': '通义千问 Qwen-Image-2.0',
    'cogview-4': '智谱 CogView-4',
    'cogview-4-plus': '智谱 CogView-4-Plus',
    'stable-diffusion': 'Stable Diffusion',
}

DEFAULT_IMAGE_SIZES = [
    '1024x1024', '1024x1792', '1792x1024', '2048x2048',
    '1440x2560', '1920x2560', '2560x1440', '512x512',
]

VIDEO_MODEL_MANIFEST = [
    {
        'id': 'kling-v1',
        'name': '可灵 V1',
        'provider': 'kling',
        'description': '性价比高，适合日常使用',
        'durations': [3, 5, 10, 15],
        'resolutions': ['720p', '1080p'],
        'recommended_scenarios': ['图生视频', '短视频开场', '产品动态展示'],
        'limitations': '视频生成通常为异步任务，需要轮询任务状态',
    },
    {
        'id': 'kling-v1-5',
        'name': '可灵 V1.5',
        'provider': 'kling',
        'description': '画质提升，适合高质量需求',
        'durations': [3, 5, 10, 15],
        'resolutions': ['720p', '1080p'],
        'recommended_scenarios': ['高质量短视频', '产品展示'],
        'limitations': '视频生成通常为异步任务，需要轮询任务状态',
    },
    {
        'id': 'jimeng-v1',
        'name': '即梦 V1',
        'provider': 'jimeng',
        'description': '字节跳动，中文理解好',
        'durations': [3, 5, 10, 15],
        'resolutions': ['720p', '1080p'],
        'recommended_scenarios': ['中文提示词视频', '社媒短视频'],
        'limitations': '异步任务，需轮询状态',
    },
    {
        'id': 'runway-gen3',
        'name': 'Runway Gen-3',
        'provider': 'runway',
        'description': '专业级，运镜丰富',
        'durations': [3, 5, 10, 15],
        'resolutions': ['720p', '1080p', '4k'],
        'recommended_scenarios': ['电影感镜头', '创意广告'],
        'limitations': '异步任务，需轮询状态',
    },
]

EDIT_MODEL_MANIFEST = {
    'id': 'wanx2.1-imageedit',
    'name': '阿里云万相编辑',
    'provider': 'aliyun',
    'recommended_scenarios': ['局部重绘', '指令编辑', '扩图'],
    'limitations': '编辑能力依赖源图质量与蒙版质量',
}

MODEL_SIZE_CONFIG = {
    'doubao-seedream-4-5-251128': {
        'min_pixels': 1024 * 1024,
        'max_pixels': 4096 * 4096,
        'supported_sizes': ['2048x2048', '1440x2560', '1920x2560', '2560x1440', '1024x1024', '1024x1792', '1792x1024'],
        'auto_scale': True,
        'note': '豆包模型会自动将小于 2048 的尺寸放大'
    },
    'doubao-seedream-4-0-250828': {
        'min_pixels': 1024 * 1024,
        'max_pixels': 4096 * 4096,
        'supported_sizes': ['2048x2048', '1440x2560', '1920x2560', '2560x1440', '1024x1024', '1024x1792', '1792x1024'],
        'auto_scale': True,
        'note': '豆包模型会自动将小于 2048 的尺寸放大'
    },
    'wanx-v1': {
        'min_pixels': 3686400,
        'max_pixels': 4096 * 4096,
        'supported_sizes': ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
        'auto_scale': False,
        'note': '图片尺寸至少需要 1920x1920 像素'
    },
    'wanx-xl': {
        'min_pixels': 3686400,
        'max_pixels': 4096 * 4096,
        'supported_sizes': ['2048x2048', '1440x2560', '1920x2560', '2560x1440'],
        'auto_scale': False,
        'note': '图片尺寸至少需要 1920x1920 像素'
    },
    'cogview-3-flash': {
        'min_pixels': 512 * 512,
        'max_pixels': 2048 * 2048,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
        'auto_scale': False,
        'note': None
    },
    'cogview-3-plus': {
        'min_pixels': 512 * 512,
        'max_pixels': 2048 * 2048,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
        'auto_scale': False,
        'note': None
    },
    'dall-e-3': {
        'min_pixels': 1024 * 1024,
        'max_pixels': 1792 * 1024,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024'],
        'auto_scale': False,
        'note': None
    },
    'dall-e-2': {
        'min_pixels': 256 * 256,
        'max_pixels': 1024 * 1024,
        'supported_sizes': ['1024x1024', '512x512', '256x256'],
        'auto_scale': False,
        'note': None
    },
    'qwen-image-plus': {
        'min_pixels': 512 * 512,
        'max_pixels': 4096 * 4096,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '2048x2048', '1440x2560', '1920x2560', '2560x1440'],
        'auto_scale': False,
        'note': '阿里云通义千问图像模型，支持中英文提示词'
    },
    'qwen-image': {
        'min_pixels': 512 * 512,
        'max_pixels': 4096 * 4096,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '2048x2048', '1440x2560', '1920x2560', '2560x1440'],
        'auto_scale': False,
        'note': '阿里云通义千问标准图像模型，性价比高'
    },
    'qwen-image-2.0-pro': {
        'min_pixels': 512 * 512,
        'max_pixels': 2048 * 2048,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '2048x2048'],
        'auto_scale': False,
        'note': '通义千问 2.0 Pro 图像生成与编辑融合模型，文字渲染、真实质感强'
    },
    'qwen-image-2.0': {
        'min_pixels': 512 * 512,
        'max_pixels': 2048 * 2048,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '2048x2048'],
        'auto_scale': False,
        'note': '通义千问 2.0 标准版，轻量化，兼顾效果与速度'
    },
    'cogview-4': {
        'min_pixels': 512 * 512,
        'max_pixels': 2048 * 2048,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
        'auto_scale': False,
        'note': '智谱 CogView-4 最新版，支持中文提示词'
    },
    'cogview-4-plus': {
        'min_pixels': 512 * 512,
        'max_pixels': 2048 * 2048,
        'supported_sizes': ['1024x1024', '1024x1792', '1792x1024', '768x1024', '1024x768'],
        'auto_scale': False,
        'note': '智谱 CogView-4-Plus 增强版，细节更丰富'
    }
}
