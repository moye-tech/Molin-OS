"""广告 Worker — 负责广告数据拉取、CAC/ROI 计算、投放策略执行、素材分析"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class AdsWorker(WorkerAgent):
    worker_id = "ads_worker"
    description = "广告 Worker：广告数据拉取、CAC/ROI 计算、投放策略执行、素材分析"
    available_tools = ["file_tool", "memory_tool", "bash_executor", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["投放策略","受众分析","预算分配","创意建议","ROI预期"],"quality_criteria":["投放策略可执行","受众定位精准","预算分配合理","预期效果有数据支撑"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)