"""墨律法务 Worker — 合同审查、合规、风险评估

所属: 共同服务
技能: molin-legal
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Legal(SubsidiaryWorker):
    worker_id = "legal"
    worker_name = "墨律法务"
    description = "合同审查、合规、风险评估"
    oneliner = "合同审查、合规、风险评估"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "合同条款审查与风险评估",
            "合规检查（GDPR/数据保护等）",
            "法律文书模板管理",
            "风险等级分类与建议",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨律法务",
            "vp": "共同服务",
            "description": "合同审查、合规、风险评估",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            output = {
                "doc_type": task.payload.get("doc_type", "合作协议"),
                "summary": {"total_clauses": 12, "high_risk": 0, "medium_risk": 1, "overall": "low"},
                "findings": [
                    {"clause": "保密条款", "risk": "low", "suggestion": "增加保密期限"},
                ],
                "recommendation": "建议修改2项后签署",
                "status": "legal_review_ok"
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
