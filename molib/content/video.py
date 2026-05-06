"""
墨麟视频引擎 — FFmpeg无GPU管线
===============================

支持的视频类型:
- 幻灯片视频 (图片+TTS+字幕)
- 文字动画视频
- 素材混剪
- 屏幕录制

所有处理纯CPU，无需GPU。
"""

import logging
from datetime import datetime

logger = logging.getLogger("molin.video")


class VideoPipeline:
    """FFmpeg视频生产管线"""

    # 视频预设
    PRESETS = {
        "xiaohongshu": {
            "resolution": "1080x1920",  # 竖屏9:16
            "duration_range": "15-60s",
            "format": "mp4",
            "codec": "h264",
        },
        "douyin": {
            "resolution": "1080x1920",
            "duration_range": "15-180s",
            "format": "mp4",
            "codec": "h264",
        },
        "bilibili": {
            "resolution": "1920x1080",  # 横屏16:9
            "duration_range": "60-600s",
            "format": "mp4",
            "codec": "h264",
        },
    }

    # FFmpeg命令模板
    COMMANDS = {
        "slideshow": (
            "ffmpeg -loop 1 -i {{image}} -i {{audio}} "
            "-vf \"scale={{width}}:{{height}}:force_original_aspect_ratio=decrease,"
            "pad={{width}}:{{height}}:(ow-iw)/2:(oh-ih)/2,"
            "drawtext=text='{{text}}':fontsize=48:fontcolor=white:"
            "x=(w-tw)/2:y=h-th-40:box=1:boxcolor=black@0.5:boxborderw=10\" "
            "-c:v libx264 -preset fast -crf 23 -c:a aac -b:a 128k "
            "-shortest -movflags +faststart {{output}}"
        ),
        "text_animation": (
            "ffmpeg -f lavfi -i color=c=#1a1a2e:s={{width}}x{{height}}:d={{duration}} "
            "-vf \"drawtext=text='{{text}}':fontsize=42:fontcolor=white:"
            "x=(w-tw)/2:y=(h-th)/2:enable='between(t,0,{{duration}})'\" "
            "-c:v libx264 -preset fast -crf 23 {{output}}"
        ),
        "concat_clips": (
            "ffmpeg -f concat -safe 0 -i {{filelist}} "
            "-c:v libx264 -preset fast -crf 23 -c:a aac {{output}}"
        ),
    }

    def __init__(self):
        self.pipeline_log = []

    def create_slideshow(self, images: list[str], audio: str, text: str,
                         platform: str = "xiaohongshu") -> dict:
        """创建幻灯片视频"""
        preset = self.PRESETS.get(platform, self.PRESETS["xiaohongshu"])
        w, h = preset["resolution"].split("x")

        command = self.COMMANDS["slideshow"]
        command = command.replace("{{image}}", images[0] if images else "input.jpg")
        command = command.replace("{{audio}}", audio)
        command = command.replace("{{width}}", w)
        command = command.replace("{{height}}", h)
        command = command.replace("{{text}}", text.replace("'", "\\'"))
        command = command.replace("{{output}}", f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

        return {
            "type": "slideshow",
            "platform": platform,
            "command": command,
            "resolution": preset["resolution"],
            "no_gpu_required": True,
            "status": "ready",
        }

    def create_text_video(self, text: str, duration: int = 30,
                          platform: str = "xiaohongshu") -> dict:
        """创建文字动画视频"""
        preset = self.PRESETS.get(platform, self.PRESETS["xiaohongshu"])
        w, h = preset["resolution"].split("x")

        command = self.COMMANDS["text_animation"]
        command = command.replace("{{width}}", w)
        command = command.replace("{{height}}", h)
        command = command.replace("{{duration}}", str(duration))
        command = command.replace("{{text}}", text.replace("'", "\\'"))
        command = command.replace("{{output}}", f"text_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")

        return {
            "type": "text_animation",
            "platform": platform,
            "command": command,
            "duration": duration,
            "no_gpu_required": True,
            "status": "ready",
        }


# 全局实例
video_pipeline = VideoPipeline()


def generate(topic: str = ""):
    """CLI入口"""
    result = video_pipeline.create_text_video(
        text=f"AI一人公司: {topic or '自动化内容生产'}",
        duration=30,
    )
    print(f"🎬 视频管线就绪 (无GPU)")
    print(f"   类型: {result['type']}")
    print(f"   平台预设: {result['platform']}")
    print(f"   分辨率: {result['resolution']}")
    return result
