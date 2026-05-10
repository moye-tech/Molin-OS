"""财务 Worker — 负责流水记录、月报 Excel 生成、成本核算、预算监控"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class FinanceWorker(WorkerAgent):
    worker_id = "finance_worker"
    description = "财务 Worker：流水记录、月报 Excel 生成、成本核算、预算监控"
    available_tools = ["file_tool", "memory_tool", "bash_executor", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["数据概览","收入分析","成本分析","利润归因","风险提示","优化建议"],"quality_criteria":["数据准确","计算正确","分析深入","建议有财务逻辑"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)