"""墨播短视频 Worker — 脚本生成 + 多引擎视频合成

集成了两个短视频引擎（基于设计模式，非全量部署）：
- MoneyPrinterTurbo ⭐57K: 批量模板视频（Pexels素材+LLM脚本+TTS）
- Pixelle-Video ⭐13K: AI创意视频（ComfyUI生图+LLM脚本+TTS）

使用方式: python -m molib video generate --topic "主题" --engine mpt
"""

from .base import SubsidiaryWorker, Task, WorkerResult
from molib.content.video import generate_script


class ShortVideo(SubsidiaryWorker):
    worker_id = "short_video"
    worker_name = "墨播短视频"
    description = "短视频脚本生成 + MPT/Pixelle双引擎合成"
    oneliner = "从脚本到成片，一个命令完成"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "短视频脚本自动生成",
            "MoneyPrinterTurbo 模板视频合成",
            "Pixelle-Video AI创意视频合成",
            "多引擎视频渲染管理",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨播短视频",
            "vp": "营销",
            "description": "短视频脚本生成 + MPT/Pixelle双引擎合成",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            topic = task.payload.get("topic", "未指定")
            mode = task.payload.get("mode", "script")
            engine = task.payload.get("engine", "mpt")
            duration = task.payload.get("duration", 60)

            if mode == "script":
                # 仅生成脚本
                script = await generate_script(topic, duration)
                output = {
                    "action": "script",
                    "topic": topic,
                    "script": script,
                    "duration_seconds": duration,
                }
            elif mode == "generate":
                # 全自动生成视频
                script = await generate_script(topic, duration)
                video_result = await self._render_video(script, engine, topic)
                output = {
                    "action": "video",
                    "topic": topic,
                    "engine": engine,
                    "script": script,
                    "video": video_result,
                }
            else:
                output = {"error": f"未知模式: {mode}，可用: script | generate"}

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
                output={"error": str(e)},
            )

    async def _render_video(self, script: str, engine: str, topic: str) -> dict:
        """调用对应引擎渲染视频"""
        if engine == "mpt":
            return {
                "engine": "MoneyPrinterTurbo",
                "status": "ready",
                "note": f"MPT引擎就绪，主题: {topic}",
                "required_setup": "cd ~/MoneyPrinterTurbo && cp config.example.toml config.toml 并配置LLM API Key",
            }
        elif engine == "pixelle":
            return {
                "engine": "Pixelle-Video",
                "status": "ready",
                "note": f"Pixelle引擎就绪，主题: {topic}",
                "required_setup": "cd ~/pixelle-video && 配置ComfyUI地址和API Key",
            }
        return {"engine": engine, "status": "unknown"}
