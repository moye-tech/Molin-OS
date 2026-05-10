"""安全 Worker — 负责安全审计、漏洞扫描、合规检查、权限审查"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class SecureWorker(WorkerAgent):
    worker_id = "secure_worker"
    description = "安全 Worker：安全审计、漏洞扫描、合规检查、权限审查"
    available_tools = ["file_tool", "memory_tool", "bash_executor", "web_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"report","sections":["安全评估","漏洞分析","风险等级","修复方案","预防措施"],"quality_criteria":["安全评估全面","漏洞识别准确","修复方案具体","预防措施有效"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)