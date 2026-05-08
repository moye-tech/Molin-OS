"""墨声配音 Worker — AI语音合成、播客制作

所属: VP营销
技能: molin-audio-engine, songwriting
"""
import json
from .base import SubsidiaryWorker, Task, WorkerResult

class VoiceActor(SubsidiaryWorker):
    worker_id = "voice_actor"
    worker_name = "墨声配音"
    description = "AI语音合成、播客制作"
    oneliner = "AI语音合成、播客制作"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "多音色文本转语音（TTS）",
            "多语言配音（中/英/日等）",
            "播客与有声书制作",
            "音频参数调节（语速/音调/情感）",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨声配音",
            "vp": "营销",
            "description": "AI语音合成、播客制作",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            text = task.payload.get("text", "需配音文本")
            voice = task.payload.get("voice", "标准女声")
            lang = task.payload.get("language", "zh-CN")
            speed = task.payload.get("speed", 1.0)
            pitch = task.payload.get("pitch", 1.0)

            # ── LLM 注入：配音分析与参数优化 ──
            system_prompt = (
                "你是一位专业的AI配音导演，精通多音色TTS合成、语音参数调优。"
                "请根据文本内容、目标语言和音色偏好，给出最优配音方案。"
            )
            prompt = (
                f"请为以下内容生成配音方案：\n"
                f"文本：{text}\n"
                f"目标音色：{voice}\n"
                f"语言：{lang}\n"
                f"用户希望的语速：{speed}\n"
                f"用户希望的音调：{pitch}\n\n"
                "以JSON格式输出，包含以下字段：\n"
                "{\n"
                '  "voice_profile": "推荐音色配置",\n'
                '  "language": "语言代码",\n'
                '  "tts_config": {\n'
                '    "engine": "推荐引擎",\n'
                '    "speed": 语速值,\n'
                '    "pitch": 音调值,\n'
                '    "emotion": "情感基调"\n'
                '  },\n'
                '  "text_analysis": "文本分段与语气建议",\n'
                '  "estimated_duration_sec": 预计时长,\n'
                '  "notes": ["配音建议1", "配音建议2"]\n'
                "}"
            )

            llm_result = await self.llm_chat_json(prompt, system=system_prompt)

            if llm_result and "voice_profile" in llm_result:
                output = {
                    "text_length": len(text),
                    "voice_profile": llm_result.get("voice_profile", voice),
                    "language": llm_result.get("language", lang),
                    "tts_config": llm_result.get("tts_config", {
                        "engine": "dashscope_tts",
                        "speed": speed,
                        "pitch": pitch,
                    }),
                    "text_analysis": llm_result.get("text_analysis", ""),
                    "estimated_duration_sec": llm_result.get("estimated_duration_sec", len(text) * 0.25),
                    "notes": llm_result.get("notes", []),
                    "status": "tts_ready",
                    "source": "llm",
                }
            else:
                # ── fallback：原有 mock ──
                output = {
                    "text_length": len(text),
                    "voice_profile": voice,
                    "language": lang,
                    "tts_config": {
                        "engine": "dashscope_tts",
                        "speed": speed,
                        "pitch": pitch,
                    },
                    "estimated_duration_sec": len(text) * 0.25,
                    "status": "tts_ready",
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
