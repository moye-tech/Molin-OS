"""
MolibComfy v2.0 — 方案2：纯 Python diffusers 替代 ComfyUI
==========================================================
Mac M2 Metal 加速（MPS），8GB 内存优化。
不依赖 ComfyUI 安装，直接用 HuggingFace diffusers + PyTorch MPS。

策略：
  Tier 2 (已有): PyTorch MPS 后端 ✅
  方案2 (新增): diffusers 纯 Python → sd-turbo / SD 1.5 / SDXL
  Tier 3 (备选): ComfyUI API（如 ComfyUI 后续安装）

8GB 内存优化:
  - 默认模型 sd-turbo（1-4步，~3.5GB）
  - enable_attention_slicing() 自动降内存
  - 可选 CPU offload（慢但省内存）

用法:
    molib comfy check                    # 环境诊断
    molib comfy generate --prompt "..."   # 生成图像
    molib comfy models                   # 列出可用模型
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molib.comfy")

OUTPUT_DIR = Path.home() / "Molin-OS" / "output" / "comfy"
CACHE_DIR = Path.home() / ".cache" / "huggingface" / "hub"
COMFY_PATH = Path.home() / "ComfyUI"

# 8GB 内存可用模型（按内存需求排序）
MODELS: dict[str, dict[str, Any]] = {
    "sd-turbo": {
        "id": "stabilityai/sd-turbo",
        "ram_gb": 3.5,
        "steps": 4,
        "description": "蒸馏 SD，1-4步出图，最快最省内存",
        "recommended": True,
    },
    "sd-1.5": {
        "id": "runwayml/stable-diffusion-v1-5",
        "ram_gb": 4.5,
        "steps": 20,
        "description": "经典 SD 1.5，质量好，需 attention slicing",
    },
    "sdxl-turbo": {
        "id": "stabilityai/sdxl-turbo",
        "ram_gb": 7.0,
        "steps": 4,
        "description": "SDXL 蒸馏版，高质量，8GB 极限",
    },
}

DEFAULT_MODEL = "sd-turbo"


class MolibComfy:
    """方案2：diffusers 纯 Python 图像生成引擎。"""

    def __init__(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 诊断 ────────────────────────────────────────────

    def check(self) -> dict[str, Any]:
        """环境全量诊断。"""
        result: dict[str, Any] = {
            "tier1_ffmpeg": False,
            "tier2_torch_mps": False,
            "tier2_diffusers": False,
            "tier3_comfyui": False,
            "strategy": "方案2-diffusers",
        }

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
            pass

        # Tier 2: diffusers
        try:
            import diffusers
            result["tier2_diffusers"] = True
            result["diffusers_version"] = diffusers.__version__
        except ImportError:
            result["tier2_diffusers"] = False

        # Tier 3: ComfyUI
        result["tier3_comfyui"] = COMFY_PATH.exists()

        # 缓存模型
        result["cached_models"] = self._list_cached_models()

        # 策略推荐
        if result["tier2_torch_mps"] and result["tier2_diffusers"]:
            result["ready"] = True
            result["recommendation"] = "方案2就绪 — 可用 diffusers MPS 直出"
        elif result["tier2_torch_mps"]:
            result["ready"] = False
            result["recommendation"] = "pip install diffusers accelerate safetensors"
        else:
            result["ready"] = False
            result["recommendation"] = "需 PyTorch MPS 支持"

        return result

    def _list_cached_models(self) -> list[str]:
        """列出已在本地缓存的模型。"""
        cached = []
        for name, info in MODELS.items():
            repo_id = info["id"].replace("/", "--")
            model_dir = CACHE_DIR / f"models--{repo_id}"
            if model_dir.exists():
                cached.append(name)
        return cached

    # ── 生成 ────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        steps: Optional[int] = None,
        width: int = 512,
        height: int = 512,
        seed: int = -1,
        model: str = DEFAULT_MODEL,
        guidance_scale: float = 0.0,
    ) -> dict:
        """方案2核心：diffusers MPS 生成图像。"""
        import torch

        if seed < 0:
            seed = random.randint(0, 2**31 - 1)

        if model not in MODELS:
            return {"error": f"未知模型 '{model}'，可选: {list(MODELS)}"}

        model_info = MODELS[model]
        if steps is None:
            steps = model_info["steps"]

        try:
            import diffusers
        except ImportError:
            return {
                "error": "diffusers 未安装。运行: pip install diffusers accelerate safetensors",
                "strategy": "方案2-需安装",
            }

        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        dtype = torch.float32

        start_time = time.time()

        try:
            pipe = self._load_pipeline(model_info["id"], device, dtype)

            generator = torch.Generator(device="cpu").manual_seed(seed)
            gen_kwargs: dict[str, Any] = {
                "prompt": prompt,
                "num_inference_steps": steps,
                "width": width,
                "height": height,
                "generator": generator,
                "guidance_scale": guidance_scale,
            }
            if negative_prompt and guidance_scale > 0:
                gen_kwargs["negative_prompt"] = negative_prompt

            with torch.no_grad():
                output = pipe(**gen_kwargs)

            filename = f"comfy_{model}_{seed}_{int(time.time())}.png"
            output_path = str(OUTPUT_DIR / filename)
            output.images[0].save(output_path)

            elapsed = time.time() - start_time

            return {
                "output": output_path,
                "prompt": prompt,
                "seed": seed,
                "steps": steps,
                "size": f"{width}x{height}",
                "model": model,
                "model_id": model_info["id"],
                "device": str(device),
                "elapsed_sec": round(elapsed, 1),
                "memory_mb": self._get_memory_usage(),
                "strategy": "方案2-diffusers",
            }

        except torch.cuda.OutOfMemoryError as e:
            return {
                "error": f"内存不足（{model_info['ram_gb']}GB 模型, 8GB 系统）。"
                         f"尝试: 降低尺寸/步数，或换 sd-turbo",
                "strategy": "OOM",
            }
        except Exception as e:
            return {"error": str(e), "strategy": "方案2-异常"}

    def _load_pipeline(self, model_id: str, device, dtype):
        """加载 diffusers pipeline（方案2核心）。"""
        from diffusers import AutoPipelineForText2Image

        logger.info(f"加载模型: {model_id}")

        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=dtype,
            variant="fp16" if "turbo" not in model_id else None,
            safety_checker=None,
            requires_safety_checker=False,
        )
        pipe = pipe.to(device)

        try:
            pipe.enable_attention_slicing()
        except Exception:
            pass

        if "turbo" in model_id:
            pipe.set_progress_bar_config(disable=True)

        return pipe

    # ── img2img ─────────────────────────────────────────

    def img2img(
        self,
        prompt: str,
        image_path: str,
        strength: float = 0.6,
        steps: Optional[int] = None,
        seed: int = -1,
        model: str = DEFAULT_MODEL,
    ) -> dict:
        """图像到图像生成。"""
        import torch
        from PIL import Image

        if not os.path.exists(image_path):
            return {"error": f"输入图像不存在: {image_path}"}

        if model not in MODELS:
            return {"error": f"未知模型 '{model}'"}

        model_info = MODELS[model]
        if steps is None:
            steps = model_info["steps"]
        if seed < 0:
            seed = random.randint(0, 2**31 - 1)

        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

        try:
            from diffusers import AutoPipelineForImage2Image

            init_image = Image.open(image_path).convert("RGB")
            pipe = AutoPipelineForImage2Image.from_pretrained(
                model_info["id"],
                torch_dtype=torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            ).to(device)

            try:
                pipe.enable_attention_slicing()
            except Exception:
                pass

            generator = torch.Generator(device="cpu").manual_seed(seed)
            output = pipe(
                prompt=prompt, image=init_image, strength=strength,
                num_inference_steps=steps, generator=generator,
            )

            filename = f"comfy_img2img_{model}_{seed}_{int(time.time())}.png"
            output_path = str(OUTPUT_DIR / filename)
            output.images[0].save(output_path)

            return {
                "output": output_path, "prompt": prompt,
                "input_image": image_path, "strength": strength,
                "seed": seed, "model": model, "strategy": "方案2-img2img",
            }
        except Exception as e:
            return {"error": str(e)}

    # ── 工具 ────────────────────────────────────────────

    def _get_memory_usage(self) -> int:
        try:
            import psutil
            return int(psutil.Process().memory_info().rss / 1024 / 1024)
        except ImportError:
            return -1

    def models(self) -> dict:
        cached = self._list_cached_models()
        return {
            "models": {n: {**i, "cached": n in cached} for n, i in MODELS.items()},
            "default": DEFAULT_MODEL,
            "cached_count": len(cached),
            "cache_dir": str(CACHE_DIR),
        }

    def preload(self, model: str = DEFAULT_MODEL) -> dict:
        import torch
        if model not in MODELS:
            return {"error": f"未知模型 '{model}'"}
        device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        model_info = MODELS[model]
        try:
            start = time.time()
            self._load_pipeline(model_info["id"], device, torch.float32)
            return {
                "status": "loaded", "model": model,
                "model_id": model_info["id"],
                "elapsed_sec": round(time.time() - start, 1),
                "memory_mb": self._get_memory_usage(),
            }
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_comfy_check() -> dict:
    return MolibComfy().check()


def cmd_comfy_generate(args: list[str]) -> dict:
    c = MolibComfy()
    kwargs: dict[str, Any] = {}
    i = 0
    while i < len(args):
        if args[i] == "--prompt" and i + 1 < len(args):
            kwargs["prompt"] = args[i + 1]; i += 2
        elif args[i] == "--negative" and i + 1 < len(args):
            kwargs["negative_prompt"] = args[i + 1]; i += 2
        elif args[i] == "--steps" and i + 1 < len(args):
            kwargs["steps"] = int(args[i + 1]); i += 2
        elif args[i] == "--width" and i + 1 < len(args):
            kwargs["width"] = int(args[i + 1]); i += 2
        elif args[i] == "--height" and i + 1 < len(args):
            kwargs["height"] = int(args[i + 1]); i += 2
        elif args[i] == "--seed" and i + 1 < len(args):
            kwargs["seed"] = int(args[i + 1]); i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            kwargs["model"] = args[i + 1]; i += 2
        elif args[i] == "--cfg" and i + 1 < len(args):
            kwargs["guidance_scale"] = float(args[i + 1]); i += 2
        else:
            i += 1

    if "prompt" not in kwargs:
        return {"error": "需要 --prompt", "usage": "molib comfy generate --prompt '...' [--model sd-turbo]"}
    return c.generate(**kwargs)


def cmd_comfy_models() -> dict:
    return MolibComfy().models()


def cmd_comfy_preload(args: list[str]) -> dict:
    model = DEFAULT_MODEL
    if len(args) >= 2 and args[0] == "--model":
        model = args[1]
    return MolibComfy().preload(model)


def cmd_comfy_img2img(args: list[str]) -> dict:
    c = MolibComfy()
    kwargs: dict[str, Any] = {}
    i = 0
    while i < len(args):
        if args[i] == "--prompt" and i + 1 < len(args):
            kwargs["prompt"] = args[i + 1]; i += 2
        elif args[i] == "--image" and i + 1 < len(args):
            kwargs["image_path"] = args[i + 1]; i += 2
        elif args[i] == "--strength" and i + 1 < len(args):
            kwargs["strength"] = float(args[i + 1]); i += 2
        elif args[i] == "--steps" and i + 1 < len(args):
            kwargs["steps"] = int(args[i + 1]); i += 2
        elif args[i] == "--seed" and i + 1 < len(args):
            kwargs["seed"] = int(args[i + 1]); i += 2
        elif args[i] == "--model" and i + 1 < len(args):
            kwargs["model"] = args[i + 1]; i += 2
        else:
            i += 1

    if "prompt" not in kwargs or "image_path" not in kwargs:
        return {"error": "需要 --prompt 和 --image"}
    return c.img2img(**kwargs)
