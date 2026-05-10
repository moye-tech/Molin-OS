"""开发 Worker — 负责代码开发、脚本编写、测试执行"""

from __future__ import annotations

from typing import Any, Dict
from molib.agencies.worker import ExecutionPlan, ExecutionStep, WorkerAgent


class DevWorker(WorkerAgent):
    worker_id = "dev_worker"
    description = "开发 Worker：代码开发、脚本编写、测试执行"
    available_tools = ["bash_executor", "code_tool", "file_tool", "memory_tool"]

    deliverable_spec: Dict[str, Any] = {"format":"markdown","sections":["需求分析","技术方案","代码实现","测试用例","部署说明"],"quality_criteria":["代码可运行","错误处理完善","文档清晰","符合最佳实践"]}

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        # LLM 驱动的执行计划（基类默认实现），替代关键词 if-else
        return await super().build_plan(subtask)
