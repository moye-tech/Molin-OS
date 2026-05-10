"""知识 Worker — 负责知识提取、SOP 更新、知识图谱构建、文档编写"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class KnowledgeWorker(WorkerAgent):
    worker_id = "knowledge_worker"
    description = "知识 Worker：知识提取、SOP 更新、知识图谱构建、文档编写"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"markdown","sections":["知识提取","结构化整理","关键概念","应用场景","检索索引"],"quality_criteria":["知识提取准确","结构清晰合理","便于检索复用","有实用价值"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)