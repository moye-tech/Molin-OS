"""Trading Worker — 量化分析与交易执行（TradingAgents-CN），挂载到墨算财务和墨情报局"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class TradingWorker(WorkerAgent):
    worker_id = "trading_worker"
    description = "量化分析 Worker（TradingAgents-CN）：行情分析、投资建议、交易执行"
    available_tools = ["trading_tool", "memory_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["行情分析","策略设计","交易信号","风险控制","回测结果"],"quality_criteria":["策略逻辑清晰","风险控制完善","回测数据可靠","信号可执行"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)