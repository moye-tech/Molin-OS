"""法务 Worker — 负责合同审查、合规分析、文档起草、知识产权检查"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class LegalWorker(WorkerAgent):
    worker_id = "legal_worker"
    description = "法务 Worker：合同审查、合规分析、文档起草、知识产权检查"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["法律依据","风险评估","合规建议","整改方案","注意事项"],"quality_criteria":["法律依据准确","风险识别全面","建议合规专业","用语严谨"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)