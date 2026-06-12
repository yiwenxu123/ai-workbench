"""即梦 (Jimeng) 任务状态查询适配器

即梦 API 模式（推测，基于通用任务式接口）：
  - 提交时返回 task_id
  - 状态查询: GET /{endpoint}/{task_id}
  - 认证: Bearer Token
"""

from typing import Optional

from .base import TaskStatusAdapter


class JimengStatusAdapter(TaskStatusAdapter):
    provider = "jimeng"

    def build_status_url(self, base_endpoint: str, task_id: str) -> str:
        endpoint = base_endpoint.rstrip("/")
        return f"{endpoint}/{task_id}"

    def build_headers(self, api_key: str) -> dict:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def parse_response(self, data: dict) -> dict:
        result_data = data.get("data") or data

        task_status = str(result_data.get("task_status", "") or
                          result_data.get("status", "") or "unknown").lower()

        status_map = {
            "submitted": "pending",
            "running": "processing",
            "processing": "processing",
            "succeed": "succeed",
            "suc": "succeed",
            "failed": "failed",
            "fail": "failed",
        }
        mapped_status = status_map.get(task_status, "pending")

        # 结果 URL —— 不同厂商字段名不同
        result_url: Optional[str] = None
        for key in ("result_url", "video_url", "url", "output_url", "resource_url"):
            if result_data.get(key):
                result_url = result_data[key]
                break
        # 尝试嵌套结构: output.video_url
        if not result_url:
            output = result_data.get("output") or {}
            if isinstance(output, dict):
                for key in ("video_url", "url", "result_url"):
                    if output.get(key):
                        result_url = output[key]
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
