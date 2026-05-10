"""增长 Worker — 负责内容多平台分发、数据拉取聚合、增长实验执行"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class GrowthWorker(WorkerAgent):
    worker_id = "growth_worker"
    description = "增长 Worker：内容多平台分发、数据拉取聚合、增长实验执行"
    available_tools = ["web_tool", "browser_tools", "file_tool", "memory_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["实验假设","实验设计","数据指标","结果分析","放量建议"],"quality_criteria":["假设清晰可验证","指标定义明确","结果分析有数据","放量建议审慎"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)