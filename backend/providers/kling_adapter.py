"""可灵 (KlingAI) 任务状态查询适配器（配置驱动）

行为配置见 registry.json 的 "kling" 条目。
"""

from .config_adapter import ConfigDrivenAdapter


class KlingStatusAdapter(ConfigDrivenAdapter):
    provider = "kling"
