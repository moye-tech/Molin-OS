"""
墨麟数字人 — Mac M2 本地渲染引擎
================================
Tier 1: ffmpeg + macOS say → 零依赖，立即可用
Tier 2: SadTalker + PyTorch MPS → 唇形同步（可选 pip install torch）

用法:
    python -m molib avatar create --text "你好" --image portrait.jpg
    python -m molib avatar list-voices
    python -m molib avatar batch --script script.txt --image profile.png
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molin.digital_human")

OUTPUT_DIR = Path.home() / "Molin-OS" / "output" / "avatars"
DEFAULT_VOICE = "Tingting"  # 中文女声
DEFAULT_RATE = 200           # 语速 (words/min)


@dataclass
class AvatarConfig:
    image_path: str
    text: str
    voice: str = DEFAULT_VOICE
    rate: int = DEFAULT_RATE
    output_path: str = ""
    resolution: str = "720p"      # 480p | 720p | 1080p
    duration_seconds: int = 0     # 0=自动计算
    background: str = ""          # 背景色 (空=原图)


class DigitalHuman:
    """Mac M2 本地数字人引擎。"""

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 语音合成 (macOS say) ─────────────────────────────────

    @staticmethod
    def list_voices(language: str = "") -> list[dict[str, str]]:
        """列出 macOS 可用语音。"""
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
        voices = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("#")
            if len(parts) >= 2:
                name_lang = parts[0].strip().split()
                name = name_lang[0] if name_lang else ""
                lang = name_lang[1] if len(name_lang) > 1 else ""
                desc = parts[1].strip()
                if not language or lang.startswith(language):
                    voices.append({"name": name, "lang": lang, "desc": desc})
        return voices

    def _synthesize_speech(self, text: str, voice: str, rate: int) -> str:
        """用 macOS say 合成语音 → aiff → wav。"""
        aiff_path = tempfile.mktemp(suffix=".aiff")
        wav_path = tempfile.mktemp(suffix=".wav")

        # TTS
        subprocess.run(
            ["say", "-v", voice, "-r", str(rate), "-o", aiff_path, text],
            check=True, capture_output=True,
        )

        # 转 WAV（ffmpeg 兼容）
        subprocess.run(
            ["ffmpeg", "-y", "-i", aiff_path, "-acodec", "pcm_s16le", wav_path],
            check=True, capture_output=True,
        )

        os.unlink(aiff_path)
        return wav_path

    def _get_audio_duration(self, audio_path: str) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True,
        )
        return float(result.stdout.strip()) if result.stdout.strip() else 5.0

    # ── 视频合成 (ffmpeg) ────────────────────────────────────

    def _composite_video(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        resolution: str,
        background: str,
    ) -> str:
        """图片 + 音频 → 视频（缩放/居中/背景填充）。"""
        duration = self._get_audio_duration(audio_path)

        # 分辨率映射
        res_map = {"480p": "854:480", "720p": "1280:720", "1080p": "1920:1080"}
        target_size = res_map.get(resolution, "1280:720")

        filters = []

        if background:
            # 加背景色，图片居中
            filters.append(
                f"scale={target_size}:force_original_aspect_ratio=decrease,"
                f"pad={target_size}:(ow-iw)/2:(oh-ih)/2:color={background}"
            )
        else:
            # 缩放填充
            filters.append(
                f"scale={target_size}:force_original_aspect_ratio=increase,"
                f"crop={target_size}"
            )

        filter_str = ",".join(filters)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", image_path,
            "-i", audio_path,
            "-vf", filter_str,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-shortest",
            output_path,
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        return output_path

    # ── 主流程 ──────────────────────────────────────────────

    def create(self, config: AvatarConfig) -> dict[str, Any]:
        """创建数字人视频。

        Args:
            config: AvatarConfig with image, text, voice, etc.

        Returns:
            {"video_path": "...", "duration": 12.5, "size_mb": 3.2}
        """
        image = Path(config.image_path)
        if not image.exists():
            return {"error": f"图片不存在: {config.image_path}"}

        output = config.output_path or str(
            OUTPUT_DIR / f"avatar_{int(os.path.getmtime(config.image_path))}.mp4"
        )

        logger.info(f"🎙 合成语音 [{config.voice}]: {config.text[:50]}...")
        audio_path = self._synthesize_speech(config.text, config.voice, config.rate)

        logger.info(f"🎬 合成视频: {output}")
        self._composite_video(
            config.image_path, audio_path, output,
            config.resolution, config.background,
        )

        # 清理临时音频
        os.unlink(audio_path)

        size_mb = os.path.getsize(output) / 1024 / 1024
        duration = self._get_audio_duration(
            subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", output],
                capture_output=True, text=True,
            ).stdout.strip() or "0"
        )

        return {
            "video_path": output,
            "duration": float(duration) if duration else 0,
            "size_mb": round(size_mb, 1),
            "status": "ok",
        }

    def batch(self, script_file: str, image_path: str, voice: str = DEFAULT_VOICE) -> list[dict]:
        """批量生成：脚本文件每行一个片段。

        脚本格式:
            # 标题行（以 # 开头 = 文件名）
            ## intro
            大家好，欢迎收看今天的墨麟日报。
            ## news
            今天的主要新闻有三条...
        """
        if not Path(script_file).exists():
            return [{"error": f"脚本不存在: {script_file}"}]

        # 解析脚本
        segments = []
        current_title = ""
        current_lines = []

        with open(script_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("## "):
                    if current_lines:
                        segments.append((current_title, "".join(current_lines)))
                    current_title = line[3:].strip()
                    current_lines = []
                elif line and not line.startswith("#"):
                    current_lines.append(line)
            if current_lines:
                segments.append((current_title, "".join(current_lines)))

        results = []
        for i, (title, text) in enumerate(segments):
            if not text.strip():
                continue
            output_path = str(OUTPUT_DIR / f"{title}.mp4")
            config = AvatarConfig(
                image_path=image_path,
                text=text,
                voice=voice,
                output_path=output_path,
            )
            result = self.create(config)
            result["segment"] = title
            results.append(result)
            logger.info(f"  [{i+1}/{len(segments)}] {title}: {result.get('duration', 0):.1f}s")

        return results


# ═══════════════════════════════════════════════════════════════
# SadTalker Tier 2 (可选)
# ═══════════════════════════════════════════════════════════════

def check_sadtalker() -> dict[str, Any]:
    """检查 SadTalker 是否可用。"""
    try:
        import torch
        mps_ok = torch.backends.mps.is_available()
    except ImportError:
        return {"available": False, "reason": "PyTorch 未安装 → pip install torch"}

    sadtalker_path = Path.home() / "SadTalker"
    if not sadtalker_path.exists():
        return {
            "available": False,
            "reason": "SadTalker 未下载 → git clone https://github.com/OpenTalker/SadTalker ~/SadTalker",
        }

    return {
        "available": True,
        "mps": mps_ok,
        "path": str(sadtalker_path),
        "note": "M2 GPU 加速可用，质量优于 ffmpeg 静态合成",
    }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_avatar_create(
    text: str = "",
    image: str = "",
    voice: str = DEFAULT_VOICE,
    rate: int = DEFAULT_RATE,
    resolution: str = "720p",
):
    dh = DigitalHuman()
    config = AvatarConfig(
        image_path=image,
        text=text,
        voice=voice,
        rate=rate,
        resolution=resolution,
    )
    result = dh.create(config)
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"✅ 数字人视频已生成")
        print(f"   📁 {result['video_path']}")
        print(f"   ⏱ {result['duration']:.1f}s | {result['size_mb']}MB")


def cmd_avatar_list_voices(lang: str = ""):
    voices = DigitalHuman.list_voices(lang)
    print(f"🎙 macOS 可用语音 ({len(voices)} 个):")
    for v in voices:
        print(f"   {v['name']:15s} {v['lang']:6s} {v['desc']}")


def cmd_avatar_check():
    result = check_sadtalker()
    print(f"🔍 数字人引擎检测:")
    print(f"   Tier 1 (ffmpeg+say): ✅ 可用")
    print(f"   Tier 2 (SadTalker): {'✅' if result['available'] else '❌'} {result.get('reason', result.get('note', ''))}")
