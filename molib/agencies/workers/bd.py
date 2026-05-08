"""墨商BD Worker — 商务拓展、合作洽谈

所属: VP战略
技能: molin-bd-scanner, agent-sales-deal-strategist
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class Bd(SubsidiaryWorker):
    worker_id = "bd"
    worker_name = "墨商BD"
    description = "商务拓展、合作洽谈"
    oneliner = "商务拓展、合作洽谈"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "客户识别与线索评估",
            "合作方案自动生成",
            "报价与合同条款建议",
            "客户关系管理与跟进",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨商BD",
            "vp": "战略",
            "description": "商务拓展、合作洽谈",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            client = task.payload.get("client", "未指定客户")
            industry = task.payload.get("industry", "")
            needs = task.payload.get("needs", "")
            budget_range = task.payload.get("budget_range", "")

            system = (
                "你是墨商BD——墨麟AI集团旗下的专业商务拓展子公司。"
                "你的专长是：客户识别与线索评估、合作方案自动生成、"
                "报价与合同条款建议、客户关系管理与跟进。"
                "你擅长B2B商务谈判，能根据客户画像制定针对性的合作方案。"
                "请输出结构化的商务合作方案。"
            )
            prompt = (
                f"请为以下客户制定商务合作方案：\n\n"
                f"客户名称：{client}\n"
                f"所属行业：{industry if industry else '未指定'}\n"
                f"客户需求：{needs if needs else '未指定'}\n"
                f"预算范围：{budget_range if budget_range else '未指定'}\n\n"
                f"请输出JSON格式，包含：\n"
                f"- client（客户名称）\n"
                f"- proposal（合作方案对象，含：title方案标题, value核心价值主张, deliverables交付物数组, "
                f"pricing定价对象含setup一次性费用和monthly月费）\n"
                f"- engagement_strategy（接洽策略说明）\n"
                f"- key_talking_points（关键谈判要点列表）\n"
                f"- risk_notes（风险备注）\n"
                f"- next_steps（后续跟进步骤列表）\n"
                f"- status（固定为'proposal_draft_ready'）"
            )

            llm_result = await self.llm_chat_json(prompt, system=system)
            if llm_result:
                output = {
                    "client": llm_result.get("client", client),
                    "proposal": llm_result.get("proposal", {
                        "title": f"{client}合作方案",
                        "value": "提升3倍运营效率",
                        "deliverables": ["AI客服", "内容自动化", "数据看板"],
                        "pricing": {"setup": 5000, "monthly": 2000},
                    }),
                    "engagement_strategy": llm_result.get("engagement_strategy", ""),
                    "key_talking_points": llm_result.get("key_talking_points", []),
                    "risk_notes": llm_result.get("risk_notes", ""),
                    "next_steps": llm_result.get("next_steps", []),
                    "status": "proposal_draft_ready",
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "client": client,
                    "proposal": {
                        "title": f"{client}合作方案",
                        "value": "提升3倍运营效率",
                        "deliverables": ["AI客服", "内容自动化", "数据看板"],
                        "pricing": {"setup": 5000, "monthly": 2000},
                    },
                    "status": "proposal_draft_ready",
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
