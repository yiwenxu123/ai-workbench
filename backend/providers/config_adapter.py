"""配置驱动任务状态适配器

厂商差异全部收敛到 registry.json：
  - 状态查询 URL 模板
  - 状态字段名与状态映射
  - 结果 URL 提取规则（顶层字段 / output 嵌套 / artifacts 数组）

接口变更时只改 registry.json，不动代码。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .base import TaskStatusAdapter

_REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"

_registry: Optional[dict] = None


def load_registry() -> dict:
    """加载 registry.json（进程内缓存）"""
    global _registry
    if _registry is None:
        with open(_REGISTRY_PATH, encoding="utf-8") as f:
            _registry = json.load(f)
    return _registry or {}


def get_provider_config(provider: str) -> dict:
    cfg = load_registry().get(provider)
    if cfg is None:
        raise KeyError(f"provider '{provider}' 未在 registry.json 中注册")
    return cfg


def reload_registry() -> None:
    """强制重新加载 registry（测试/热更新用）"""
    global _registry
    _registry = None


class ConfigDrivenAdapter(TaskStatusAdapter):
    """根据 registry.json 配置驱动行为的通用适配器"""

    provider: str = ""

    @property
    def _config(self) -> dict:
        return get_provider_config(self.provider)

    def build_status_url(self, base_endpoint: str, task_id: str) -> str:
        template = self._config.get("status_endpoint_template", "{endpoint}/{task_id}")
        endpoint = base_endpoint.rstrip("/")
        return template.format(endpoint=endpoint, task_id=task_id)

    def build_headers(self, api_key: str) -> dict:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def parse_response(self, data: dict) -> dict:
        cfg = self._config
        result_data = data.get("data") or data

        mapped_status = self._map_status(result_data, cfg)
        result_url = self._extract_result_url(result_data, cfg)

        progress = result_data.get("progress")
        if not isinstance(progress, int):
            progress = None

        return {
            "status": mapped_status,
            "progress": progress,
            "result_url": result_url,
            "raw_data": data,
        }

    def _map_status(self, result_data: dict, cfg: dict) -> str:
        status_fields = cfg.get("status_fields", ["task_status", "status"])
        task_status = ""
        for field in status_fields:
            val = result_data.get(field)
            if val:
                task_status = str(val).lower()
                break
        status_map = cfg.get("status_map", {})
        return status_map.get(task_status, cfg.get("default_status", "pending"))

    def _extract_result_url(self, result_data: dict, cfg: dict) -> Optional[str]:
        require_http = cfg.get("require_http_prefix", False)

        for key in cfg.get("result_url_fields", []):
            val = result_data.get(key)
            if isinstance(val, str) and self._acceptable_url(val, require_http):
                return val

        output = result_data.get("output")
        if isinstance(output, dict):
            for key in cfg.get("nested_output_fields", []):
                val = output.get(key)
                if isinstance(val, str) and self._acceptable_url(val, require_http):
                    return val
            url = self._from_artifacts(output, cfg, require_http)
            if url:
                return url

        return self._from_artifacts(result_data, cfg, require_http)

    def _from_artifacts(self, container: dict, cfg: dict, require_http: bool) -> Optional[str]:
        for key in cfg.get("artifact_fields", []):
            val = container.get(key)
            if isinstance(val, list) and val and isinstance(val[0], dict):
                for k in cfg.get("artifact_url_keys", ["url", "video_url", "src"]):
                    item = val[0].get(k)
                    if isinstance(item, str) and self._acceptable_url(item, require_http):
                        return item
        return None

    @staticmethod
    def _acceptable_url(url: str, require_http: bool) -> bool:
        if require_http:
            return url.startswith(("http://", "https://"))
        return True
