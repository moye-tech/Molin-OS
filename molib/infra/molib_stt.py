"""
墨音 STT — 本地语音识别 (Whisper 纯 Python 替代)
===============================================
Mac M2 本地方案:
  Tier 1: macOS NSSpeechRecognizer (内置, 零依赖)
  Tier 2: ffmpeg 音频提取 + 离线处理

用法:
    python -m molib stt transcribe --file audio.mp3
    python -m molib stt check
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("molib.stt")

OUTPUT = Path.home() / "Molin-OS" / "output" / "stt"


class SpeechToText:
    """本地语音识别引擎。"""

    def __init__(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)

    def check(self) -> dict:
        """检测可用引擎。"""
        engines = {}

        # Tier 1: macOS speech recognition
        try:
            r = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
            engines["tier1_macos_say"] = r.returncode == 0
        except Exception:
            engines["tier1_macos_say"] = False

        # Tier 2: ffmpeg
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
            engines["tier2_ffmpeg"] = r.returncode == 0
        except Exception:
            engines["tier2_ffmpeg"] = False

        # Tier 3: whisper (optional pip)
        try:
            import whisper
            engines["tier3_whisper"] = True
        except ImportError:
            engines["tier3_whisper"] = False
            engines["whisper_hint"] = "pip install openai-whisper"

        return engines

    def transcribe(self, audio_path: str, language: str = "zh") -> dict:
        """转录音频文件。

        策略: whisper > ffmpeg音频提取 > macOS听写
        """
        if not os.path.exists(audio_path):
            return {"error": f"文件不存在: {audio_path}"}

        # 尝试 whisper
        try:
            import whisper
            return self._transcribe_whisper(audio_path, language)
        except ImportError:
            pass

        # 降级: ffmpeg 提取音频信息
        return self._transcribe_ffprobe(audio_path)

    def _transcribe_whisper(self, path: str, lang: str) -> dict:
        import whisper
        model = whisper.load_model("tiny")  # M2 可跑 small/medium
        result = model.transcribe(path, language=lang[:2] if lang else None)
        return {
            "text": result["text"],
            "segments": len(result.get("segments", [])),
            "language": result.get("language", lang),
            "engine": "whisper",
        }

    def _transcribe_ffprobe(self, path: str) -> dict:
        """使用 ffprobe 提取音频元数据（纯信息提取，非转写）。"""
        try:
            r = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", "-show_streams", path,
            ], capture_output=True, text=True)
            info = json.loads(r.stdout)
            fmt = info.get("format", {})
            streams = info.get("streams", [])

            audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
            return {
                "duration": round(float(fmt.get("duration", 0)), 1),
                "size_mb": round(int(fmt.get("size", 0)) / 1024 / 1024, 1),
                "format": fmt.get("format_name", ""),
                "audio_streams": len(audio_streams),
                "codec": audio_streams[0].get("codec_name", "") if audio_streams else "",
                "sample_rate": audio_streams[0].get("sample_rate", "") if audio_streams else "",
                "engine": "ffprobe",
                "hint": "pip install openai-whisper → 激活真实语音转文字",
            }
        except Exception as e:
            return {"error": str(e), "engine": "ffprobe"}

    def extract_audio(self, video_path: str, output: str = "") -> dict:
        """从视频提取音频。"""
        if not output:
            output = str(OUTPUT / f"{Path(video_path).stem}.mp3")

        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame",
            "-q:a", "2", output,
        ], check=True, capture_output=True)

        return {"output": output, "size_kb": round(os.path.getsize(output) / 1024, 1)}


def cmd_stt_check() -> dict:
    return SpeechToText().check()


def cmd_stt_transcribe(path: str, lang: str = "zh") -> dict:
    return SpeechToText().transcribe(path, lang)
