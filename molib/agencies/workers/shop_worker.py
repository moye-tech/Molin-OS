"""销售 Worker — 负责报价生成、合同草拟、交付物打包、销售话术"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class ShopWorker(WorkerAgent):
    worker_id = "shop_worker"
    description = "销售 Worker：报价生成、合同草拟、交付物打包、销售话术"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["转化漏斗分析","话术优化","定价建议","客户价值评估","提升方案"],"quality_criteria":["话术有说服力","转化路径可优化","定价策略合理","客户价值清晰"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)