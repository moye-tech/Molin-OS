"""运维 Worker — 负责系统监控、故障响应、性能调优、容器管理"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class DevopsWorker(WorkerAgent):
    worker_id = "devops_worker"
    description = "运维 Worker：系统监控、故障响应、性能调优、容器管理"
    available_tools = ["bash_executor", "file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["系统状态","性能指标","风险识别","优化方案","监控建议"],"quality_criteria":["监控指标完整","性能分析有数据","优化方案可落地","风险识别准确"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)