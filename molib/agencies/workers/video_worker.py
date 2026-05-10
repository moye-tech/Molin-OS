"""Video Worker — 短视频自动生成（MoneyPrinterTurbo），挂载到墨迹内容和墨增引擎"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, WorkerAgent


class VideoWorker(WorkerAgent):
    worker_id = "video_worker"
    description = "短视频自动生成 Worker（MoneyPrinterTurbo）：输入主题 → 生成脚本 → 配音 → 合成视频"
    available_tools = ["video_tool", "memory_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"markdown","sections":["选题方向","视频脚本","分镜建议","配音文案","发布策略"],"quality_criteria":["选题有流量潜力","脚本可拍摄","内容有记忆点","发布时机合理"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)