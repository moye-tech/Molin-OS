"""教育 Worker — 负责学员进度扫描、作业批改、课表生成、课程设计"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class EduWorker(WorkerAgent):
    worker_id = "edu_worker"
    description = "教育 Worker：学员进度扫描、作业批改、课表生成、课程设计"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["课程目标","内容大纲","教学方法","学员体验设计","转化路径"],"quality_criteria":["课程结构合理","内容深度适当","学员体验考虑周全","转化路径清晰"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)