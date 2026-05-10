"""调研 Worker — 负责市场调研、竞品分析、行业情报"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, ExecutionStep, WorkerAgent


class ResearchWorker(WorkerAgent):
    worker_id = "research_worker"
    description = "调研 Worker：市场调研、竞品分析、行业情报收集"
    available_tools = ["web_tool", "browser_tools", "file_tool", "memory_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["调研方法","信息来源","核心发现","竞品对比","趋势判断","行动建议"],"quality_criteria":["数据来源可追溯","结论有依据","覆盖主要维度","建议可落地"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        # LLM 驱动的执行计划（基类默认实现），替代关键词 if-else
        return await super().build_plan(subtask)
