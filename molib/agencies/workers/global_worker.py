"""出海 Worker — 负责内容本地化、市场策略、跨境合规、平台适配"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class GlobalWorker(WorkerAgent):
    worker_id = "global_worker"
    description = "出海 Worker：内容本地化、市场策略、跨境合规、平台适配"
    available_tools = ["file_tool", "memory_tool", "web_tool", "browser_tools"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["目标市场分析","本地化策略","合规要求","竞品分析","进入路径"],"quality_criteria":["本地化到位","市场分析有深度","合规建议准确","策略可落地"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)