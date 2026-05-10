"""CRM Worker — 负责客户画像更新、跟进任务创建、用户分层、流失预警执行"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class CRMWorker(WorkerAgent):
    worker_id = "crm_worker"
    description = "CRM Worker：客户画像更新、跟进任务创建、用户分层、流失预警执行"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["用户分层","运营策略","自动化流程","触达计划","效果预估"],"quality_criteria":["分层逻辑清晰","策略有针对性","流程可自动化","指标可衡量"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)