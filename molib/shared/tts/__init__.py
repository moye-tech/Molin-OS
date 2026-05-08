"""molib.shared.tts — TTS 调用封装

轻量文本转语音封装，支持本地 ONNX（MOSS-TTS-Nano）和远程 API 两种后端。
零外部依赖（ONNX 运行时需额外安装）。
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class TTSConfig:
    """TTS 配置"""
    backend: str = "api"  # "api" | "onnx" | "auto"
    language: str = "zh"
    model_dir: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TTSResult:
    """TTS 结果"""
    text: str
    language: str
    output_path: str
    duration_sec: float = 0.0
    backend: str = ""
    success: bool = False
    error: Optional[str] = None


class TTSClient:
    """TTS 客户端

    配置后即可调用：
        client = TTSClient(TTSConfig(backend="onnx"))
        result = client.synthesize("你好世界")

        或者：

        client = TTSClient(TTSConfig(
            backend="api",
            api_url="https://studio.mosi.cn/api/v1/tts",
            api_key="your-key",
        ))
        result = client.synthesize("Hello world", language="en")
    """

    # MOSS-TTS-Nano 标准配置
    ONNX_DEFAULT_REPO = "OpenMOSS-Team/MOSS-TTS-Nano-100M-ONNX"
    ONNX_TOKENIZER_REPO = "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX"
    ONNX_SUPPORTED_LANGS = [
        "zh", "en", "de", "es", "fr", "ja", "it", "hu",
        "ko", "ru", "fa", "ar", "pl", "pt", "cs", "da",
        "sv", "el", "tr",
    ]

    def __init__(self, config: Optional[TTSConfig] = None):
        self.config = config or TTSConfig()

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib tts say --text "你好" --lang zh
    #   python -m molib tts clone --audio prompt.wav --text "你好世界"
    # ------------------------------------------------------------------

    def synthesize(self, text: str, language: str = "",
                   output_path: Optional[str] = None,
                   prompt_audio: Optional[str] = None) -> TTSResult:
        """文本转语音

        Args:
            text: 要合成的文本
            language: 语言代码 (zh/en/...)，默认使用 config.language
            output_path: 输出路径，None 则生成临时文件
            prompt_audio: 音色克隆参考音频路径 (onnx 模式)

        Returns:
            TTSResult
        """
        lang = language or self.config.language
        out = output_path or self._temp_output()

        if self.config.backend == "onnx":
            return self._synthesize_onnx(text, lang, out, prompt_audio)
        elif self.config.backend == "api":
            return self._synthesize_api(text, lang, out)
        else:
            # auto — 先试 onnx，不行降级 api
            result = self._synthesize_onnx(text, lang, out, prompt_audio)
            if result.success or not self.config.api_url:
                return result
            return self._synthesize_api(text, lang, out)

    def _synthesize_onnx(self, text: str, language: str,
                         output_path: str,
                         prompt_audio: Optional[str] = None) -> TTSResult:
        """ONNX 本地推理"""
        try:
            import importlib.util
            if importlib.util.find_spec("onnxruntime") is None:
                return TTSResult(
                    text=text, language=language,
                    output_path=output_path, backend="onnx",
                    success=False,
                    error="onnxruntime 未安装。运行: pip install onnxruntime",
                )

            model_dir = self.config.model_dir or "./models"
            cmd = ["python3", "infer_onnx.py"]

            if prompt_audio:
                cmd.extend(["--prompt-audio-path", prompt_audio])
            cmd.extend(["--text", text, "--output", output_path])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120,
                cwd=model_dir if os.path.isdir(model_dir) else None,
            )

            if result.returncode == 0 and os.path.exists(output_path):
                size = os.path.getsize(output_path)
                # 估算时长: 48kHz 2ch, ~45 字/秒（中文）
                dur = len(text) / 4.5 if language == "zh" else len(text) / 10
                return TTSResult(
                    text=text, language=language,
                    output_path=output_path, backend="onnx",
                    duration_sec=round(dur, 1),
                    success=True,
                )
            else:
                return TTSResult(
                    text=text, language=language,
                    output_path=output_path, backend="onnx",
                    success=False,
                    error=result.stderr[:500] or "推理失败",
                )

        except Exception as e:
            return TTSResult(
                text=text, language=language,
                output_path=output_path, backend="onnx",
                success=False, error=str(e),
            )

    def _synthesize_api(self, text: str, language: str,
                        output_path: str) -> TTSResult:
        """远程 API 调用"""
        if not self.config.api_url:
            return TTSResult(
                text=text, language=language,
                output_path=output_path, backend="api",
                success=False, error="api_url 未配置",
            )

        try:
            import urllib.request

            payload = json.dumps({
                "text": text,
                "language": language,
                "format": "wav",
            }).encode()

            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            req = urllib.request.Request(
                self.config.api_url, data=payload, headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()

            with open(output_path, "wb") as f:
                f.write(data)

            dur = len(text) / 4.5 if language == "zh" else len(text) / 10
            return TTSResult(
                text=text, language=language,
                output_path=output_path, backend="api",
                duration_sec=round(dur, 1),
                success=True,
            )

        except Exception as e:
            return TTSResult(
                text=text, language=language,
                output_path=output_path, backend="api",
                success=False, error=str(e),
            )

    @staticmethod
    def _temp_output() -> str:
        """生成临时输出路径"""
        import datetime
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"/tmp/tts_{ts}.wav"


# MOSS-TTS-Nano 标准配置
MOSS_TTS_CONFIG = TTSConfig(
    backend="onnx",
    language="zh",
    model_dir="./models",
)
