"""
Video Tool Integrator (MoneyPrinterTurbo)
为墨迹内容子公司提供自动化短视频生成能力：输入主题 → 生成脚本 → 配音 → 合成视频。
"""
from typing import Dict, Any
import os
import aiohttp
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter


class VideoTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="video_tool")
        self.api_base = os.getenv("VIDEO_TOOL_API_BASE", "http://localhost:8501")
        self.register_command("generate_video", self._generate_video)
        self.register_command("get_status", self._get_status)
        logger.info(f"VideoTool (MoneyPrinterTurbo) initialized, API: {self.api_base}")

    async def _generate_video(self, params: Dict[str, Any]) -> Dict[str, Any]:
        topic = params.get("topic")
        if not topic:
            raise ValueError("topic parameter is required for video generation.")

        async with aiohttp.ClientSession() as session:
            resp = await session.post(
                f"{self.api_base}/api/v1/videos",
                json={
                    "video_subject": topic,
                    "video_language": params.get("language", "zh-CN"),
                    "video_length": params.get("duration_s", 60),
                    "voice_name": params.get("voice", "zh-CN-YunxiNeural"),
                    "platform": params.get("platform", "douyin"),
                },
                timeout=aiohttp.ClientTimeout(total=300),
            )
            data = await resp.json()

        return {
            "task_id": data.get("task_id"),
            "status": "queued",
            "platform": params.get("platform", "douyin"),
        }

    async def _get_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        if not task_id:
            raise ValueError("task_id parameter is required.")

        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                f"{self.api_base}/api/v1/tasks/{task_id}",
                timeout=aiohttp.ClientTimeout(total=10),
            )
            data = await resp.json()

        return {
            "task_id": task_id,
            "status": data.get("status", "unknown"),
            "progress": data.get("progress", 0),
            "video_url": data.get("video_url"),
        }


_video_tool = VideoTool()

def get_video_tool() -> VideoTool:
    return _video_tool
