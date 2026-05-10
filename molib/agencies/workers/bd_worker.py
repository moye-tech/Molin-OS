"""BD Worker — 负责客户分析、报价生成、谈判策略制定、跟进管理"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class BDWorker(WorkerAgent):
    worker_id = "bd_worker"
    description = "BD Worker：客户分析、报价生成、谈判策略制定、跟进管理"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["客户分析","合作方案","报价策略","谈判要点","跟进计划"],"quality_criteria":["客户分析深入","方案有说服力","风险可控","跟进计划具体"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)