"""订单 Worker — 负责询盘处理、报价生成、交付跟踪、订单状态更新"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class OrderWorker(WorkerAgent):
    worker_id = "order_worker"
    description = "订单 Worker：询盘处理、报价生成、交付跟踪、订单状态更新"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["需求确认","报价方案","交付计划","风险评估","合同要点"],"quality_criteria":["报价合理透明","交付方案可行","风险识别清晰","时间线可执行"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)