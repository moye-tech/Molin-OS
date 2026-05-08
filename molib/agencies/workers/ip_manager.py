"""墨韵IP Worker — IP衍生、商标、版权、品牌管理

所属: VP营销
技能: ai-taste-quality
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class IpManager(SubsidiaryWorker):
    worker_id = "ip_manager"
    worker_name = "墨韵IP"
    description = "IP衍生、商标、版权、品牌管理"
    oneliner = "IP衍生、商标、版权、品牌管理"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "IP人设打造与角色设计",
            "商标与版权管理",
            "品牌授权方案制定",
            "IP视觉风格统一管控",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨韵IP",
            "vp": "营销",
            "description": "IP衍生、商标、版权、品牌管理",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            ip_name = task.payload.get("ip_name", "未命名IP")
            ip_type = task.payload.get("ip_type", "虚拟角色")
            personality = task.payload.get("personality", ["专业", "亲和"])
            visual_style = task.payload.get("visual_style", "扁平插画风")
            audience = task.payload.get("audience", "Z世代职场人")
            brand_context = task.payload.get("brand_context", "")

            system = (
                "你是墨韵IP——墨麟AI集团旗下的IP衍生与品牌管理子公司。"
                "你的专长是：IP人设打造与角色设计、商标与版权管理、"
                "品牌授权方案制定、IP视觉风格统一管控。"
                "你精通IP商业价值评估，能设计出既有创意又具商业潜力的IP方案。"
                "请输出结构化的IP设计方案。"
            )
            prompt = (
                f"请为以下IP进行专业设计：\n\n"
                f"IP名称：{ip_name}\n"
                f"IP类型：{ip_type}\n"
                f"性格特征：{', '.join(personality) if isinstance(personality, list) else personality}\n"
                f"视觉风格：{visual_style}\n"
                f"目标受众：{audience}\n"
                f"品牌背景：{brand_context if brand_context else '无特殊背景'}\n\n"
                f"请输出JSON格式，包含：\n"
                f"- ip_name（IP名称）\n"
                f"- ip_type（IP类型）\n"
                f"- persona（人设对象，含：name名称, personality性格数组, visual_style视觉风格, "
                f"target_audience目标受众, backstory背景故事, core_values核心价值观）\n"
                f"- visual_guidelines（视觉规范说明）\n"
                f"- commercialization（商业化方向建议）\n"
                f"- trademark_notes（商标/版权注意事项）\n"
                f"- status（固定为'ip_spec_ready'）"
            )

            llm_result = await self.llm_chat_json(prompt, system=system)
            if llm_result:
                output = {
                    "ip_name": llm_result.get("ip_name", ip_name),
                    "ip_type": llm_result.get("ip_type", ip_type),
                    "persona": llm_result.get("persona", {
                        "name": ip_name,
                        "personality": personality,
                        "visual_style": visual_style,
                        "target_audience": audience,
                    }),
                    "visual_guidelines": llm_result.get("visual_guidelines", ""),
                    "commercialization": llm_result.get("commercialization", []),
                    "trademark_notes": llm_result.get("trademark_notes", ""),
                    "status": "ip_spec_ready",
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "ip_name": ip_name,
                    "ip_type": ip_type,
                    "persona": {
                        "name": ip_name,
                        "personality": personality,
                        "visual_style": visual_style,
                        "target_audience": audience,
                    },
                    "status": "ip_spec_ready",
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
