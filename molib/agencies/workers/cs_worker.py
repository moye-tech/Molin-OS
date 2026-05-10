"""客服 Worker — 负责 FAQ 向量检索、工单状态更新、自动回复、投诉处理"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class CSWorker(WorkerAgent):
    worker_id = "cs_worker"
    description = "客服 Worker：FAQ 向量检索、工单状态更新、自动回复、投诉处理"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"markdown","sections":["问题分析","解决方案","回复话术","跟进建议","FAQ更新"],"quality_criteria":["回复专业得体","问题定位准确","方案有操作性","维护品牌形象"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)