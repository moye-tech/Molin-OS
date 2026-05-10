"""墨声配音 Worker — v2.1 开源武装升级 (CosyVoice ⭐21k)

升级内容:
  - synthesize: DashScope CosyVoice v3 真实TTS合成 (替代纯描述输出)
  - list_voices: 列出可用音色
  - 保留原有配音方案设计功能 (plan模式)
"""
from .base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


class VoiceActor(_Base):
    worker_id = "voice_actor"
    worker_name = "墨声配音"
    description = "AI语音合成 (v2.1: CosyVoice v3真实TTS + 配音方案设计)"
    oneliner = "真实语音合成+多音色+情绪控制+多语言配音"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "真实TTS语音合成 (CosyVoice v3 ⭐21k)",
            "6+音色可选 (含方言/情绪控制)",
            "播客与有声书制作",
            "音频参数调节（语速/情感）",
            "配音方案智能设计",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨声配音",
            "vp": "营销",
            "description": "AI语音合成 (v2.1: CosyVoice v3)",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "synthesize")

            # ── v2.1: 真实TTS合成 ──
            if action in ("synthesize", "tts", "配音"):
                output = await self._synthesize(task.payload)

            # 列出可用音色
            elif action in ("list_voices", "voices"):
                try:
                    from molib.infra.external.cosyvoice import list_voices
                    output = {"voices": list_voices(), "action": "list_voices", "status": "success"}
                except Exception:
                    output = {"voices": [], "action": "list_voices", "status": "unavailable"}

            # 原有配音方案设计 (plan模式)
            else:
                output = await self._plan_voice(task.payload)

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

    async def _synthesize(self, payload: dict) -> dict:
        """真实TTS合成 (CosyVoice v3)"""
        text = payload.get("text", "")
        voice = payload.get("voice", "longxiaochun")
        emotion = payload.get("emotion", "neutral")
        speed = payload.get("speed", 1.0)

        if not text:
            return {"error": "text不能为空", "status": "error"}

        # 尝试真实API
        try:
            from molib.infra.external.cosyvoice import synthesize
            import os
            output_path = payload.get("output_path", os.path.expanduser(f"~/Desktop/tts_output.mp3"))
            result = synthesize(
                text=text,
                voice=voice,
                emotion=emotion,
                speed=speed,
                output_path=output_path,
            )
            if result.get("status") == "success":
                return result
        except Exception:
            pass

        # fallback: macOS say
        try:
            import subprocess, tempfile, os
            output_path = payload.get("output_path") or os.path.expanduser("~/Desktop/tts_output.aiff")
            voice_map = {"longxiaochun": "Tingting", "longwan": "Sinji", "longcheng": "Meijia"}
            mac_voice = voice_map.get(voice, "Tingting")
            subprocess.run(["say", "-v", mac_voice, "-o", output_path, text], timeout=30)
            return {"text": text, "voice": voice, "fallback": "macos_say", "output_path": output_path, "status": "success"}
        except Exception:
            return {"text": text, "voice": voice, "error": "TTS不可用(cosyvoice+macos均失败)", "status": "unavailable"}

    async def _plan_voice(self, payload: dict) -> dict:
        """配音方案设计 (原有功能保留)"""
        text = payload.get("text", "需配音文本")
        voice = payload.get("voice", "标准女声")
        lang = payload.get("language", "zh-CN")
        speed = payload.get("speed", 1.0)
        pitch = payload.get("pitch", 1.0)

        system = "你是专业AI配音导演，精通多音色TTS。请给出最优配音方案。"
        prompt = (
            f"文本: {text}\n音色: {voice}\n语言: {lang}\n语速: {speed}\n音调: {pitch}\n"
            "输出JSON: voice_profile, language, tts_config(engine/speed/pitch/emotion), text_analysis, estimated_duration_sec, notes"
        )
        result = await self.llm_chat_json(prompt, system=system)
        if result:
            return {"text_length": len(text), **result, "source": "llm"}
        return {"text_length": len(text), "voice_profile": voice, "tts_config": {"engine": "cosyvoice_v3", "speed": speed, "emotion": "neutral"}, "status": "plan_ready", "source": "mock"}
