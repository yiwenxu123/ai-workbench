"""多厂商任务状态查询适配器工厂"""

from __future__ import annotations

from typing import Optional

from .base import TaskStatusAdapter
from .kling_adapter import KlingStatusAdapter
from .jimeng_adapter import JimengStatusAdapter
from .runway_adapter import RunwayStatusAdapter

# 内置适配器注册表
_BUILTIN_ADAPTERS: list[type[TaskStatusAdapter]] = [
    KlingStatusAdapter,
    JimengStatusAdapter,
    RunwayStatusAdapter,
]

# 运行时适配器实例缓存（provider → instance）
_adapters: dict[str, TaskStatusAdapter] = {}

# 返回默认 adapter 时的回退
_DEFAULT_PROVIDER = "kling"


def _init_adapters() -> None:
    if _adapters:
        return
    for adapter_cls in _BUILTIN_ADAPTERS:
        instance = adapter_cls()
        _adapters[instance.provider] = instance


def get_adapter(provider: Optional[str] = None) -> TaskStatusAdapter:
    """根据厂商标识获取适配器实例

    Args:
        provider: 厂商标识（kling/jimeng/runway），为 None 时默认返回 Kling 适配器

    Returns:
        TaskStatusAdapter 实例
    """
    _init_adapters()
    key = (provider or _DEFAULT_PROVIDER).strip().lower()
    adapter = _adapters.get(key)
    if adapter is None:
        adapter = _adapters[_DEFAULT_PROVIDER]
    return adapter


def list_providers() -> list[str]:
    """列出所有已注册的适配器厂商标识"""
    _init_adapters()
    return list(_adapters.keys())


__all__ = [
    "TaskStatusAdapter",
    "get_adapter",
    "list_providers",
]
