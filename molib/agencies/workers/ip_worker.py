"""小红书/IP Worker — 负责内容创作、标题生成、文案撰写"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class IPWorker(WorkerAgent):
    worker_id = "ip_worker"
    description = "小红书/IP Worker：内容创作、标题生成、文案撰写"
    available_tools = ["web_tool", "browser_tools", "file_tool", "memory_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"markdown","sections":["标题候选","正文内容","标签推荐","配图建议","发布策略"],"quality_criteria":["标题有吸引力","内容可直接发布","符合平台调性","包含互动引导"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        # LLM 驱动的执行计划（基类默认实现），替代关键词 if-else
        return await super().build_plan(subtask)
