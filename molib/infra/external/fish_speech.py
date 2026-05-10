"""
墨麟OS — Fish-Speech S2 API 集成 (⭐18k, TTS Arena ELO 1339)
===========================================================
替代方案：Fish Audio API 代替 CosyVoice 本地部署。
无Docker，无本地GPU，Mac M2 8GB完全可用。

支持 80+ 语言零样本克隆，情绪控制 ($15/百万字符 vs ElevenLabs $165)。

用法:
    from molib.infra.external.fish_speech import tts, list_voices
    result = tts("你好，欢迎使用墨麟OS", voice="default")
    # result["audio_path"]  → 本地音频文件路径

集成点:
    VoiceActor Worker: 配音/TTS/播客/音频
    ShortVideo Worker: 视频配音
"""

from __future__ import annotations

import os
import json
import base64
from pathlib import Path
from typing import Optional

OUTPUT_DIR = Path.home() / "Molin-OS" / "output" / "audio"


def _get_api_key() -> str:
    return os.environ.get("FISH_AUDIO_API_KEY", "")


def tts(
    text: str,
    voice: str = "default",
    speed: float = 1.0,
    emotion: str = "",
    output_path: str = "",
    language: str = "zh",
) -> dict:
    """
    Fish Audio TTS — 文本转语音。

    Args:
        text: 待合成文本
        voice: 音色ID (default/clone/scarlett等)
        speed: 语速 (0.5-2.0)
        emotion: 情绪标签 (whisper/excited/sad等)
        output_path: 输出路径
        language: 语言代码

    Returns:
        {"audio_path": str, "duration_sec": float, "voice": str}
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "FISH_AUDIO_API_KEY not set", "status": "no_api_key"}

    try:
        import urllib.request

        url = "https://api.fish.audio/v1/tts"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "speed": speed,
            "language": language,
        }
        if voice and voice != "default":
            payload["reference_id"] = voice
        if emotion:
            # 内联情绪控制: [whisper]text[/whisper]
            payload["text"] = f"[{emotion}]{text}[/{emotion}]"

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
        )
        resp = urllib.request.urlopen(req, timeout=60)
        audio_data = resp.read()

        # 保存
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        safe_name = text[:20].replace(" ", "_").replace("/", "_")
        output_file = output_path or str(OUTPUT_DIR / f"fish_{safe_name}_{hash(text) % 10000}.mp3")
        Path(output_file).write_bytes(audio_data)

        # 估算时长
        duration = len(audio_data) / 16000  # rough estimate

        return {
            "audio_path": output_file,
            "duration_sec": round(duration, 1),
            "voice": voice,
            "text": text,
            "status": "success",
            "source": "fish-speech-s2",
        }

    except Exception as e:
        return {"error": str(e), "status": "error"}


def list_voices() -> dict:
    """列出可用音色。"""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "FISH_AUDIO_API_KEY not set"}

    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.fish.audio/v1/voice",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())

        voices = []
        for v in data.get("items", [])[:20]:
            voices.append({
                "id": v.get("voice_id", ""),
                "title": v.get("title", ""),
                "language": v.get("language", ""),
                "tags": v.get("tags", []),
            })

        return {"voices": voices, "count": len(voices), "source": "fish-speech"}
    except Exception as e:
        return {"error": str(e)}


def clone_voice(reference_audio_path: str, title: str = "") -> dict:
    """
    声音克隆 —— 上传参考音频，创建个人音色。
    3秒参考音频即可克隆任意声音。
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "FISH_AUDIO_API_KEY not set"}

    if not os.path.exists(reference_audio_path):
        return {"error": f"参考音频不存在: {reference_audio_path}"}

    try:
        import urllib.request

        audio_bytes = Path(reference_audio_path).read_bytes()
        url = "https://api.fish.audio/v1/voice"
        headers = {"Authorization": f"Bearer {api_key}"}

        # 使用 multipart
        boundary = "----MolibFishSpeech"
        body = []
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="title"')
        body.append(b"")
        body.append((title or Path(reference_audio_path).stem).encode())
        body.append(f"--{boundary}".encode())
        body.append(f'Content-Disposition: form-data; name="audio"; filename="{Path(reference_audio_path).name}"'.encode())
        body.append(b"Content-Type: audio/mpeg")
        body.append(b"")
        body.append(audio_bytes)
        body.append(f"--{boundary}--".encode())

        req = urllib.request.Request(
            url,
            data=b"\r\n".join(body),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())

        return {
            "voice_id": data.get("voice_id", ""),
            "title": data.get("title", ""),
            "status": "success",
            "source": "fish-speech-clone",
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}
