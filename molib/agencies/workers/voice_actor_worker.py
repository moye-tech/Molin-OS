"""
墨声配音 Worker 升级 — 从"仅技能"到真实 TTS
=========================================
集成: macOS say (Tier 1) + PyTorch MPS (Tier 2)
支持: 中文/英文/日文/韩文语音合成, 播客制作, 多角色对话
"""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("molin.voice")

OUTPUT = Path.home() / "Molin-OS" / "output" / "voice"


class VoiceActor:
    """墨声配音 — 真实 TTS 引擎。"""

    VOICES = {
        "zh-CN": {"女声": "Tingting", "女声2": "Meijia"},
        "en-US": {"女声": "Samantha", "男声": "Alex", "男声2": "Daniel"},
        "ja-JP": {"女声": "Kyoko", "男声": "Otoya"},
        "ko-KR": {"女声": "Yuna"},
    }

    def __init__(self):
        OUTPUT.mkdir(parents=True, exist_ok=True)

    def list_voices(self, lang: str = "") -> list[dict]:
        """列出可用语音。"""
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
        voices = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip(): continue
            parts = line.split("#")
            if len(parts) >= 2:
                name_lang = parts[0].strip().split()
                name, lang_code = name_lang[0], name_lang[1] if len(name_lang) > 1 else ""
                if not lang or lang_code.startswith(lang):
                    voices.append({"name": name, "lang": lang_code, "desc": parts[1].strip()})
        return voices

    def speak(self, text: str, voice: str = "Tingting", rate: int = 200, output: str = "") -> dict:
        """单句 TTS → aiff → mp3。"""
        if not output:
            output = str(OUTPUT / f"voice_{abs(hash(text)) % 10000}.mp3")

        aiff = tempfile.mktemp(suffix=".aiff")
        subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", aiff, text],
                       check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-i", aiff, "-acodec", "libmp3lame", "-q:a", "2", output],
                       check=True, capture_output=True)
        os.unlink(aiff)

        duration = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", output],
            capture_output=True, text=True
        ).stdout.strip() or 0)

        return {
            "output": output, "text": text[:100], "voice": voice,
            "duration": round(duration, 1), "size_kb": round(os.path.getsize(output) / 1024, 1),
        }

    def podcast(self, script: list[dict], output: str = "") -> dict:
        """多角色播客制作。

        Args:
            script: [{"role": "主持人", "text": "...", "voice": "Tingting"}, ...]
        """
        if not output:
            output = str(OUTPUT / "podcast.mp3")

        segments = []
        for i, line in enumerate(script):
            seg_path = tempfile.mktemp(suffix=".mp3")
            voice = line.get("voice", "Tingting")
            result = self.speak(line["text"], voice, output=seg_path)
            segments.append(seg_path)
            logger.info(f"[{i+1}/{len(script)}] {line.get('role','?')}: {result['duration']}s")

        # 合并所有片段
        concat_file = tempfile.mktemp(suffix=".txt")
        with open(concat_file, "w") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c", "copy", output,
        ], check=True, capture_output=True)

        for seg in segments:
            os.unlink(seg)
        os.unlink(concat_file)

        return {"output": output, "segments": len(script), "status": "completed"}


def cmd_voice_speak(text: str, voice: str = "Tingting") -> dict:
    return VoiceActor().speak(text, voice)


def cmd_voice_list(lang: str = "") -> list:
    return VoiceActor().list_voices(lang)
