"""可灵 (KlingAI) 任务状态查询适配器"""

from typing import Optional

from .base import TaskStatusAdapter


class KlingStatusAdapter(TaskStatusAdapter):
    provider = "kling"

    def build_status_url(self, base_endpoint: str, task_id: str) -> str:
        # 默认端点: https://api.klingai.com/v1/videos/generations
        endpoint = base_endpoint.rstrip("/")
        return f"{endpoint}/{task_id}"

    def build_headers(self, api_key: str) -> dict:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def parse_response(self, data: dict) -> dict:
        result_data = data.get("data") or data

        # 可灵状态字段: task_status
        task_status = str(result_data.get("task_status", "") or
                          result_data.get("status", "") or "unknown").lower()

        status_map = {
            "submitted": "pending",
            "processing": "processing",
            "succeed": "succeed",
            "failed": "failed",
        }
        mapped_status = status_map.get(task_status, "pending")

        # 结果 URL 提取
        result_url: Optional[str] = None
        for key in ("result_url", "video_url", "url"):
            if result_data.get(key):
                result_url = result_data[key]
                break

        progress = result_data.get("progress")
        if not isinstance(progress, int):
            progress = None

        return {
            "status": mapped_status,
            "progress": progress,
            "result_url": result_url,
            "raw_data": data,
        }
