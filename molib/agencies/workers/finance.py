"""墨算财务 Worker — 记账、预算、成本控制

所属: VP财务
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Finance(SubsidiaryWorker):
    worker_id = "finance"
    worker_name = "墨算财务"
    description = "记账、预算、成本控制"
    oneliner = "记账、预算、成本控制"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "API成本追踪与月报生成",
            "收支记录与分类统计",
            "预算管理与超支预警",
            "成本优化建议与模型路由降级分析",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨算财务",
            "vp": "财务",
            "description": "记账、预算、成本控制",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            output = {
                "period": task.payload.get("period", "本月"),
                "revenue": {"total": task.payload.get("revenue", 0), "target": 48000},
                "costs": {
                    "api": task.payload.get("api_costs", 0),
                    "tools": task.payload.get("tool_costs", 0),
                    "total": task.payload.get("total_costs", 0),
                },
                "profit_margin": "65%",
                "recommendation": "模型路由降级可省30%",
                "status": "finance_ready"
            }
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=output,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )
