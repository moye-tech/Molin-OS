"""墨声客服 Worker — 自动化客服（消息检测→回复）

所属: VP运营
技能: molin-customer-service, xianyu-automation
"""
import json
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult

class CustomerService(_Base):
    worker_id = "customer_service"
    worker_name = "墨声客服"
    description = "自动化客服（消息检测→回复）"
    oneliner = "自动化客服（消息检测→回复）"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "多平台消息自动检测与收集",
            "AI智能回复生成",
            "人工转接与工单管理",
            "常见问题知识库匹配",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨声客服",
            "vp": "运营",
            "description": "自动化客服（消息检测→回复）",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            messages = task.payload.get("messages", [])
            platform = task.payload.get("platform", "闲鱼")
            knowledge_base = task.payload.get("knowledge_base", {})

            # ── LLM 注入：智能客服回复 ──
            system_prompt = (
                "你是一位专业的AI客服专家，精通多平台客服话术、客户情绪管理、问题分类与转接。"
                "请根据收到的消息列表，智能分类并生成合适的回复。"
            )

            messages_summary = "\n".join(
                f"[{m.get('sender','用户')}] {m.get('content','')}"
                for m in messages
            ) if messages else "暂无新消息"

            kb_summary = json.dumps(knowledge_base, ensure_ascii=False)[:1000] if knowledge_base else "无预设知识库"

            prompt = (
                f"请处理以下{platform}平台的客服消息：\n"
                f"消息列表：\n{messages_summary}\n\n"
                f"知识库信息：\n{kb_summary}\n\n"
                "以JSON格式输出客服处理方案：\n"
                "{\n"
                '  "total_messages": 总消息数,\n'
                '  "auto_replied": 自动回复数,\n'
                '  "replies": [\n'
                '    {\n'
                '      "index": 消息序号,\n'
                '      "category": "问题分类(价格咨询/售后/产品咨询/其他)",\n'
                '      "sentiment": "用户情绪(正面/中性/负面)",\n'
                '      "auto_reply": true/false,\n'
                '      "reply_content": "AI自动生成的回复内容",\n'
                '      "needs_human": false\n'
                '    }\n'
                '  ],\n'
                '  "pending_manual": ["需要人工处理的消息摘要"],\n'
                '  "common_questions": {\n'
                '    "高频问题": "标准回复"\n'
                '  },\n'
                '  "satisfaction_prediction": "预估满意度(高/中/低)",\n'
                '  "status": "messages_processed"\n'
                "}"
            )

            llm_result = await self.llm_chat_json(prompt, system=system_prompt)

            if llm_result and "total_messages" in llm_result:
                output = llm_result
                output["platform"] = platform
                output["source"] = "llm"
            else:
                # ── fallback：原有 mock ──
                auto_replied = len([m for m in messages if m.get("auto_reply", False)])
                pending = [m for m in messages if m.get("needs_human", False)]
                output = {
                    "total_messages": len(messages),
                    "auto_replied": auto_replied,
                    "replies": [],
                    "pending_manual": pending,
                    "common_questions": {
                        "价格咨询": "话术: 标准定价回复",
                        "售后问题": "话术: 已转人工",
                    },
                    "platform": platform,
                    "status": "messages_processed",
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
