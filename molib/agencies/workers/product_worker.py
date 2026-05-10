"""产品 Worker — 负责 MVP 设计、功能规划、需求分析、路线图制定"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class ProductWorker(WorkerAgent):
    worker_id = "product_worker"
    description = "产品 Worker：MVP 设计、功能规划、需求分析、路线图制定"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["用户需求","功能设计","优先级排序","实现路径","验收标准"],"quality_criteria":["需求明确可执行","功能设计合理","优先级清晰","考虑资源约束"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)