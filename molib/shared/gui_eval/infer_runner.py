"""molib.shared.gui_eval.infer_runner — 多模型推理运行器

ClawGUI-Eval 的 Infer 阶段抽象：统一接口调用多模型，
输出标准化结果格式，支持本地 GPU 和远程 API。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class InferResult:
    """单条推理结果"""
    model_name: str
    benchmark: str
    sample_id: str
    raw_output: str
    actions: list[dict] = field(default_factory=list)
    latency_ms: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, data: str) -> "InferResult":
        return cls(**json.loads(data))


class InferRunner:
    """多模型推理调度器

    提供统一推理接口，支持自定义后端接入。
    """

    # 已知支持模型列表 (来自 ClawGUI-Eval)
    SUPPORTED_MODELS = frozenset({
        "qwen3-vl", "qwen2.5-vl", "ui-tars",
        "mai-ui", "gui-g2", "ui-venus",
        "gemini-pro-vision", "seed-1.8",
    })

    def __init__(self, backend: str = "api", max_retries: int = 3):
        self.backend = backend
        self.max_retries = max_retries

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib gui-eval infer --model qwen3-vl --benchmark screenspot-pro
    # ------------------------------------------------------------------

    def run(self, model_name: str, benchmark: str, samples: list[dict],
            backend_url: Optional[str] = None) -> list[InferResult]:
        """运行多模型推理

        Args:
            model_name: 模型名 (见 SUPPORTED_MODELS)
            benchmark: 基准名
            samples: 样本列表，每项含 image_path/text/ground_truth
            backend_url: 远程 API 地址 (api 模式下)

        Returns:
            InferResult 列表
        """
        results: list[InferResult] = []
        for idx, sample in enumerate(samples):
            result = self._run_single(
                model_name=model_name,
                benchmark=benchmark,
                sample_id=sample.get("id", str(idx)),
                sample=sample,
                backend_url=backend_url,
            )
            results.append(result)
        return results

    def _run_single(self, model_name: str, benchmark: str,
                    sample_id: str, sample: dict,
                    backend_url: Optional[str] = None) -> InferResult:
        start = time.time()
        try:
            if self.backend == "api":
                output = self._call_api(model_name, sample, backend_url)
            else:
                output = self._call_local(model_name, sample)
            elapsed = (time.time() - start) * 1000
            return InferResult(
                model_name=model_name,
                benchmark=benchmark,
                sample_id=sample_id,
                raw_output=output,
                latency_ms=round(elapsed, 1),
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return InferResult(
                model_name=model_name,
                benchmark=benchmark,
                sample_id=sample_id,
                raw_output="",
                latency_ms=round(elapsed, 1),
                error=str(e),
            )

    def _call_api(self, model_name: str, sample: dict,
                  backend_url: Optional[str] = None) -> str:
        """调用远程 API 进行推断"""
        url = backend_url or "http://localhost:8000/v1/chat/completions"
        import urllib.request

        payload = json.dumps({
            "model": model_name,
            "messages": [
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": sample.get("image_path", "")}},
                    {"type": "text", "text": sample.get("text", "What action to take?")},
                ]},
            ],
        }).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())
        return body.get("choices", [{}])[0].get("message", {}).get("content", "")

    def _call_local(self, model_name: str, sample: dict) -> str:
        """占位：本地 transformers 推理"""
        return f"[local inference placeholder] model={model_name} text={sample.get('text', '')}"
