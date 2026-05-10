"""
MolibComfy — ComfyUI MPS 集成桥（60K★ 本地激活）
================================================
Mac M2 Metal 加速，PyTorch 2.11 MPS backend。
不下载完整 ComfyUI repo（网络限制），直接调用 PyTorch MPS 进行 AI 图像生成。

用法:
    python -m molib comfy generate --prompt "一只猫" --steps 20 --output cat.png
    python -m molib comfy check
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molib.comfy")

OUTPUT_DIR = Path.home() / "Molin-OS" / "output" / "comfy"
COMFY_PATH = Path.home() / "ComfyUI"


class MolibComfy:
    """ComfyUI MPS 集成桥。"""

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def check(self) -> dict[str, Any]:
        """检测 ComfyUI 环境状态。"""
        result = {"tier1_ffmpeg": False, "tier2_torch_mps": False, "tier3_comfyui": False}

        # Tier 1: ffmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            result["tier1_ffmpeg"] = True
        except Exception:
            pass

        # Tier 2: PyTorch MPS
        try:
            import torch
            result["tier2_torch_mps"] = torch.backends.mps.is_available()
            result["torch_version"] = torch.__version__
        except ImportError:
            result["tier2_torch_mps"] = False

        # Tier 3: ComfyUI
        if COMFY_PATH.exists():
            result["tier3_comfyui"] = True
            result["comfy_path"] = str(COMFY_PATH)
        else:
            result["tier3_comfyui"] = False
            result["comfy_hint"] = f"git clone https://github.com/comfyanonymous/ComfyUI.git {COMFY_PATH}"

        return result

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        steps: int = 20,
        width: int = 512,
        height: int = 512,
        seed: int = -1,
    ) -> dict:
        """使用 PyTorch MPS 生成图像（ComfyUI 离线模式）。

        如果 ComfyUI 未安装，使用 PyTorch MPS 直接生成简单噪声图案作为占位。
        实际部署后接入 ComfyUI API。
        """
        import torch
        import random

        if seed < 0:
            seed = random.randint(0, 2**31 - 1)
        torch.manual_seed(seed)

        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        # 检查是否有 ComfyUI
        if COMFY_PATH.exists():
            return self._generate_via_comfy(prompt, negative_prompt, steps, width, height, seed)

        # 离线模式：用 PyTorch MPS 生成图案
        return self._generate_via_torch(prompt, steps, width, height, seed, device)

    def _generate_via_torch(
        self, prompt: str, steps: int, width: int, height: int, seed: int, device
    ) -> dict:
        """PyTorch MPS 直接生成（无预训练模型时的降级方案）。"""
        import torch
        import torch.nn.functional as F
        from PIL import Image
        import numpy as np

        # 用 prompt hash 生成确定性纹理
        prompt_hash = abs(hash(prompt)) % (2**31)
        torch.manual_seed(seed + prompt_hash)

        # 生成分层噪声纹理
        x = torch.randn(1, 3, height, width, device=device)
        for i in range(min(steps, 10)):
            kernel = torch.randn(3, 1, 5, 5, device=device) * 0.1
            x = F.conv2d(F.pad(x, (2, 2, 2, 2), mode='reflect'), kernel, groups=3)

        # 归一化到 0-255
        x = (x - x.min()) / (x.max() - x.min() + 1e-8)
        img_array = (x.squeeze(0).permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)

        output_path = str(OUTPUT_DIR / f"comfy_{seed}.png")
        Image.fromarray(img_array).save(output_path)

        return {
            "output": output_path,
            "prompt": prompt,
            "seed": seed,
            "steps": steps,
            "size": f"{width}x{height}",
            "device": str(device),
            "mode": "torch_mps_fallback",
            "note": "ComfyUI 未安装。安装后获得 Stable Diffusion 真实生成: git clone https://github.com/comfyanonymous/ComfyUI.git ~/ComfyUI",
        }

    def _generate_via_comfy(
        self, prompt: str, neg: str, steps: int, width: int, height: int, seed: int
    ) -> dict:
        """通过 ComfyUI API 生成。"""
        import urllib.request

        workflow = {
            "3": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": steps, "cfg": 7.0}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg or "ugly, blurry"}},
            "8": {"class_type": "VAEDecode", "inputs": {}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "molib_comfy"}},
        }

        try:
            data = json.dumps({"prompt": workflow}).encode()
            req = urllib.request.Request("http://127.0.0.1:8188/prompt", data=data)
            with urllib.request.urlopen(req, timeout=300) as resp:
                result = json.loads(resp.read())

            return {
                "prompt_id": result.get("prompt_id", ""),
                "prompt": prompt,
                "seed": seed,
                "device": "mps",
                "mode": "comfyui_api",
            }
        except Exception as e:
            return {"error": f"ComfyUI API 不可达: {e}", "mode": "comfyui_offline"}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_comfy_check() -> dict:
    return MolibComfy().check()


def cmd_comfy_generate(args: list[str]) -> dict:
    c = MolibComfy()
    prompt = neg = ""
    steps, width, height, seed = 20, 512, 512, -1
    i = 0
    while i < len(args):
        if args[i] == "--prompt" and i + 1 < len(args):
            prompt = args[i + 1]; i += 2
        elif args[i] == "--negative" and i + 1 < len(args):
            neg = args[i + 1]; i += 2
        elif args[i] == "--steps" and i + 1 < len(args):
            steps = int(args[i + 1]); i += 2
        elif args[i] == "--width" and i + 1 < len(args):
            width = int(args[i + 1]); i += 2
        elif args[i] == "--height" and i + 1 < len(args):
            height = int(args[i + 1]); i += 2
        elif args[i] == "--seed" and i + 1 < len(args):
            seed = int(args[i + 1]); i += 2
        else:
            i += 1
    return c.generate(prompt, neg, steps, width, height, seed) if prompt else {"error": "需要 --prompt"}
