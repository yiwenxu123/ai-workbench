"""视频/图片任务状态查询适配器基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class TaskStatusAdapter(ABC):
    """任务状态查询适配器抽象基类"""

    # 厂商标识，用于注册和路由
    provider: str = ""

    @abstractmethod
    def build_status_url(self, base_endpoint: str, task_id: str) -> str:
        """构建查询任务状态的完整 URL"""
        ...

    @abstractmethod
    def build_headers(self, api_key: str) -> dict:
        """构建 HTTP 请求头"""
        ...

    @abstractmethod
    def parse_response(self, data: dict) -> dict:
        """解析厂商返回结果为标准格式

        返回:
            {
                "status": "pending" | "processing" | "succeed" | "failed",
                "progress": Optional[int],   # 0-100
                "result_url": Optional[str],
                "raw_data": Optional[dict],  # 保留原始数据
            }
        """
        ...
