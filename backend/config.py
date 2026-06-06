"""
后端配置：速率限制、模型能力注册表、常量
"""

import os
from pathlib import Path

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

DEFAULT_API_KEY = os.getenv("API_KEY")
DEFAULT_API_ENDPOINT = os.getenv("API_ENDPOINT")
KLING_API_KEY = os.getenv("KLING_API_KEY")
KLING_API_ENDPOINT = os.getenv("KLING_API_ENDPOINT", "https://api.klingai.com/v1/videos/generations")
ALIYUN_EDIT_API_KEY = os.getenv("ALIYUN_API_KEY")
ALIYUN_EDIT_API_ENDPOINT = os.getenv("ALIYUN_API_ENDPOINT", "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-edit")

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
