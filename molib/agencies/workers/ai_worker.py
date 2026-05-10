"""AI Worker — 负责 Prompt 工程、RAG 配置、Agent 工作流搭建、模型测试"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class AIWorker(WorkerAgent):
    worker_id = "ai_worker"
    description = "AI Worker：Prompt 工程、RAG 配置、Agent 工作流搭建、模型测试"
    available_tools = ["file_tool", "memory_tool", "code_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["需求分析","技术方案","架构设计","实施路径","风险评估"],"quality_criteria":["技术方案可行","架构可扩展","风险识别全面","建议可落地"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)