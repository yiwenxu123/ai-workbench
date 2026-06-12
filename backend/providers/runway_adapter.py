"""Runway 任务状态查询适配器

Runway API 模式（推测，基于 RESTful 任务接口）：
  - 提交时返回 task id
  - 状态查询: GET /{endpoint}/{task_id}
  - 认证: Bearer Token
"""

from typing import Optional

from .base import TaskStatusAdapter


class RunwayStatusAdapter(TaskStatusAdapter):
    provider = "runway"

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
            "queued": "pending",
            "running": "processing",
            "processing": "processing",
            "succeeded": "succeed",
            "succeed": "succeed",
            "completed": "succeed",
            "failed": "failed",
            "error": "failed",
        }
        mapped_status = status_map.get(task_status, "pending")

        result_url: Optional[str] = None
        for key in ("result_url", "video_url", "url", "output_url", "artifacts"):
            val = result_data.get(key)
            if isinstance(val, str) and val.startswith(("http://", "https://")):
                result_url = val
                break
            # artifacts 可能是 [{url: ...}]，取第一项
            if isinstance(val, list) and val:
                first = val[0]
                if isinstance(first, dict):
                    for k in ("url", "video_url", "src"):
                        if first.get(k):
                            result_url = first[k]
                            break
                if result_url:
                    break

        # 嵌套 output 结构
        if not result_url:
            output = result_data.get("output") or {}
            if isinstance(output, dict):
                for key in ("video_url", "url", "result_url", "artifacts"):
                    val = output.get(key)
                    if isinstance(val, str) and val.startswith(("http://", "https://")):
                        result_url = val
                        break
                    if isinstance(val, list) and val:
                        first = val[0]
                        if isinstance(first, dict):
                            for k in ("url", "video_url", "src"):
                                if first.get(k):
                                    result_url = first[k]
                                    break
                        if result_url:
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
