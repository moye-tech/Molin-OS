"""
墨麟OS — DashScope CosyVoice TTS 集成 (⭐21k)
===============================================
通过阿里云 DashScope API 调用 CosyVoice 3.0 进行中文TTS。

替代本地Docker部署，Mac M2 8GB无GPU也完全可用。

用法:
    from molib.infra.external.cosyvoice import synthesize
    result = synthesize("你好，欢迎使用墨麟OS", voice="longxiaochun", emotion="happy")

支持音色:
  longxiaochun (龙小春-女声)、longxiaoxia (龙小夏-男声)、
  longwan (龙婉-温柔女声)、longcheng (龙程-成熟男声) 等
"""

from __future__ import annotations

import os
import base64
import json
import hashlib
import time
from pathlib import Path


def _get_api_key() -> str:
    return os.environ.get("DASHSCOPE_API_KEY", "")


def synthesize(
    text: str,
    voice: str = "longxiaochun",
    emotion: str = "neutral",
    speed: float = 1.0,
    output_path: str = "",
    output_format: str = "mp3",
) -> dict:
    """
    调用 DashScope CosyVoice API 生成语音。

    Args:
        text: 要合成的文本 (中文为主，支持中英混合)
        voice: 音色 (longxiaochun/longxiaoxia/longwan/longcheng...)
        emotion: 情绪 (neutral/happy/sad/angry/fearful)
        speed: 语速 (0.5-2.0)
        output_path: 输出路径 (空则返回base64)
        output_format: 输出格式 (mp3/wav/pcm)

    Returns:
        {"audio_base64": str, "output_path": str, "duration_ms": int, "status": str}
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "DASHSCOPE_API_KEY not set", "status": "no_api_key"}

    try:
        import urllib.request

        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "cosyvoice-v3",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": text}
                        ]
                    }
                ]
            },
            "parameters": {
                "voice": voice,
                "emotion": emotion,
                "speed": speed,
                "format": output_format,
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))

        audio_b64 = ""
        duration_ms = 0

        # DashScope CosyVoice 返回格式：output.audio.data (base64)
        output = data.get("output", {})
        if isinstance(output, dict):
            audio_b64 = output.get("audio", {}).get("data", "") if isinstance(output.get("audio"), dict) else ""
            duration_ms = output.get("audio", {}).get("duration_ms", 0) if isinstance(output.get("audio"), dict) else 0

        result = {
            "text": text,
            "voice": voice,
            "emotion": emotion,
            "duration_ms": duration_ms,
            "source": "dashscope-cosyvoice-v3",
            "status": "success",
        }

        # 保存到文件
        if audio_b64 and output_path:
            audio_bytes = base64.b64decode(audio_b64)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(audio_bytes)
            result["output_path"] = output_path
            result["audio_base64"] = ""
        elif audio_b64:
            result["audio_base64"] = audio_b64
            result["output_path"] = ""

        return result

    except ImportError:
        # stdlib fallback for urllib (always works)
        return {"error": "Network unavailable", "status": "error"}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")[:500] if hasattr(e, 'read') else str(e)
        return {"error": f"HTTP {e.code}: {err_body}", "status": "error"}
    except Exception as e:
        return {"error": str(e), "status": "error"}


def list_voices() -> list[dict]:
    """列出可用音色"""
    return [
        {"id": "longxiaochun", "name": "龙小春", "gender": "female", "style": "清脆活泼", "tags": ["播客", "短视频"]},
        {"id": "longxiaoxia", "name": "龙小夏", "gender": "male", "style": "温暖磁性", "tags": ["课程", "解说"]},
        {"id": "longwan", "name": "龙婉", "gender": "female", "style": "温柔知性", "tags": ["客服", "有声书"]},
        {"id": "longcheng", "name": "龙程", "gender": "male", "style": "沉稳大气", "tags": ["商务", "播报"]},
        {"id": "longye", "name": "龙烨", "gender": "male", "style": "激情澎湃", "tags": ["营销", "演讲"]},
    ]
