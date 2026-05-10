"""数据 Worker — 负责多数据源聚合、图表生成、数据清洗、归因分析"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class DataWorker(WorkerAgent):
    worker_id = "data_worker"
    description = "数据 Worker：多数据源聚合、图表生成、数据清洗、归因分析"
    available_tools = ["file_tool", "memory_tool", "bash_executor", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["数据来源","分析方法","核心发现","可视化说明","归因结论","行动建议"],"quality_criteria":["数据来源可追溯","计算方法明确","结论有数据支撑","建议可执行"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)