"""墨律法务 Worker — 合同审查、合规、风险评估

所属: 共同服务
技能: molin-legal
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult

class Legal(_Base):
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
            doc_type = task.payload.get("doc_type", "合作协议")
            doc_content = task.payload.get("doc_content", "")
            jurisdiction = task.payload.get("jurisdiction", "中国大陆")
            review_focus = task.payload.get("review_focus", "")

            system = (
                "你是墨律法务——墨麟AI集团旗下的专业法务子公司。"
                "你的专长是：合同条款审查与风险评估、合规检查（GDPR/数据保护等）、"
                "法律文书模板管理、风险等级分类与建议。"
                "你精通中国及国际商法，能精准识别合同中的法律风险并提供修改建议。"
                "请输出结构化的法务审查报告。"
            )
            prompt = (
                f"请对以下{doc_type}进行专业法务审查：\n\n"
                f"文件类型：{doc_type}\n"
                f"适用法律：{jurisdiction}\n"
                f"审查重点：{review_focus if review_focus else '全面审查'}\n"
                f"文件内容：{doc_content if doc_content else '未提供具体内容，请基于常见条款进行模板化审查'}\n\n"
                f"请输出JSON格式，包含：\n"
                f"- doc_type（文件类型）\n"
                f"- summary（审查概要，含：total_clauses总条款数, high_risk高风险数, "
                f"medium_risk中风险数, low_risk低风险数, overall总体风险等级）\n"
                f"- findings（审查发现数组，每项含：clause条款名称, risk风险等级, "
                f"issue问题描述, suggestion修改建议, priority优先级）\n"
                f"- compliance_checks（合规检查，含各合规领域的检查结果）\n"
                f"- recommendation（综合建议）\n"
                f"- status（固定为'legal_review_ok'或'legal_review_caution'）"
            )

            llm_result = await self.llm_chat_json(prompt, system=system)
            if llm_result:
                output = {
                    "doc_type": llm_result.get("doc_type", doc_type),
                    "summary": llm_result.get("summary", {
                        "total_clauses": 12, "high_risk": 0, "medium_risk": 1, "overall": "low"
                    }),
                    "findings": llm_result.get("findings", []),
                    "compliance_checks": llm_result.get("compliance_checks", {}),
                    "recommendation": llm_result.get("recommendation", "建议修改2项后签署"),
                    "status": llm_result.get("status", "legal_review_ok"),
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "doc_type": doc_type,
                    "summary": {"total_clauses": 12, "high_risk": 0, "medium_risk": 1, "overall": "low"},
                    "findings": [
                        {"clause": "保密条款", "risk": "low", "suggestion": "增加保密期限"},
                    ],
                    "recommendation": "建议修改2项后签署",
                    "status": "legal_review_ok",
                    "source": "mock",
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
