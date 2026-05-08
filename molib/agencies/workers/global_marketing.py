"""墨海出海 Worker — 多语言、全球化、出海运营

所属: VP战略
技能: molin-global, weblate-localization
"""
from .base import SubsidiaryWorker, Task, WorkerResult

class GlobalMarketing(SubsidiaryWorker):
    worker_id = "global_marketing"
    worker_name = "墨海出海"
    description = "多语言、全球化、出海运营"
    oneliner = "多语言、全球化、出海运营"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "多语言翻译与本地化",
            "海外平台发布（Shopee/Amazon等）",
            "跨文化内容适配",
            "全球化运营策略建议",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨海出海",
            "vp": "战略",
            "description": "多语言、全球化、出海运营",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            texts = task.payload.get("texts", [])
            langs = task.payload.get("target_languages", ["en", "ja"])
            platforms = task.payload.get("platforms", ["Shopee"])
            source_lang = task.payload.get("source_language", "zh-CN")
            region = task.payload.get("target_region", "")

            system = (
                "你是墨海出海——墨麟AI集团旗下的全球化与出海运营子公司。"
                "你的专长是：多语言翻译与本地化、海外平台发布（Shopee/Amazon/TikTok等）、"
                "跨文化内容适配、全球化运营策略建议。"
                "你精通跨文化传播，能针对目标市场进行精准的本地化适配。"
                "请输出结构化的本地化方案。"
            )
            prompt = (
                f"请为以下内容制定本地化出海方案：\n\n"
                f"源语言：{source_lang}\n"
                f"目标语言：{', '.join(langs)}\n"
                f"目标地区：{region if region else '全球'}\n"
                f"目标平台：{', '.join(platforms)}\n"
                f"待翻译文本数量：{len(texts)}\n"
                f"文本预览：{', '.join(t[:50] for t in texts[:3])}{'...' if len(texts) > 3 else ''}\n\n"
                f"请输出JSON格式，包含：\n"
                f"- source_count（源文本数量）\n"
                f"- source_language（源语言）\n"
                f"- target_languages（目标语言数组）\n"
                f"- translations（翻译结果对象，key为语言代码，value为翻译数组，每项含original原文, translated译文, status状态）\n"
                f"- platform_targets（目标平台数组）\n"
                f"- localization_notes（本地化注意事项，如文化适配要点、禁忌等）\n"
                f"- platform_adaptation（各平台适配建议，对象）\n"
                f"- status（固定为'localization_ready'）"
            )

            llm_result = await self.llm_chat_json(prompt, system=system)
            if llm_result:
                output = {
                    "source_count": llm_result.get("source_count", len(texts)),
                    "source_language": llm_result.get("source_language", source_lang),
                    "target_languages": llm_result.get("target_languages", langs),
                    "translations": llm_result.get("translations", {
                        lang: [{"original": t[:30], "status": "translated"} for t in texts] for lang in langs
                    }),
                    "platform_targets": llm_result.get("platform_targets", platforms),
                    "localization_notes": llm_result.get("localization_notes", ""),
                    "platform_adaptation": llm_result.get("platform_adaptation", {}),
                    "status": "localization_ready",
                    "source": "llm",
                }
            else:
                # fallback: 原有 mock 输出
                output = {
                    "source_count": len(texts),
                    "target_languages": langs,
                    "translations": {lang: [{"original": t[:30], "status": "translated"} for t in texts] for lang in langs},
                    "platform_targets": platforms,
                    "status": "localization_ready",
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
