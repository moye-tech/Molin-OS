"""
墨麟OS — fal.ai FLUX.2 图像生成集成 (⭐20k)
============================================
通过 fal.ai API 调用 FLUX.2，SOTA图像质量，无需本地GPU。

替代 ComfyUI+Docker 本地部署方案，Mac M2 8GB完全可用。

用法:
    from molib.infra.external.fal_flux import generate_image
    result = generate_image("一只在月球上弹吉他的熊猫", style="photorealistic")

支持模型:
  flux/dev  (默认，性价比)
  flux/pro  (专业质量，稍慢)
  flux/schnell  (最快，适合批量)
"""

from __future__ import annotations

import os
import json
import base64
from pathlib import Path


def _get_api_key() -> str:
    return os.environ.get("FAL_KEY", "")


def generate_image(
    prompt: str,
    negative_prompt: str = "",
    model: str = "fast-flux",
    width: int = 1024,
    height: int = 1024,
    num_images: int = 1,
    guidance_scale: float = 3.5,
    output_path: str = "",
) -> dict:
    """
    调用 fal.ai FLUX 模型生成图像。

    Args:
        prompt: 正向提示词 (英文效果最佳)
        negative_prompt: 负向提示词
        model: 模型 (fast-flux/flux/dev/flux-pro)
        width/height: 图像尺寸
        num_images: 生成数量
        guidance_scale: CFG引导强度
        output_path: 保存路径 (空则返回URL)

    Returns:
        {"images": [{"url": str, "width": int, "height": int}], "prompt": str, "status": str}
    """
    api_key = _get_api_key()
    if not api_key:
        return {"prompt": prompt, "error": "FAL_KEY not set. Get key at https://fal.ai/dashboard", "status": "no_api_key"}

    try:
        import urllib.request

        model_map = {
            "flux": "fal-ai/flux/dev",
            "flux/dev": "fal-ai/flux/dev",
            "flux-pro": "fal-ai/flux-pro",
            "flux/schnell": "fal-ai/flux/schnell",
            "fast-flux": "fal-ai/fast-flux",
        }
        model_id = model_map.get(model, "fal-ai/fast-flux")

        url = f"https://fal.run/{model_id}"
        headers = {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "image_size": {"width": width, "height": height},
            "num_images": num_images,
            "guidance_scale": guidance_scale,
            "enable_safety_checker": True,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        # fal.ai 可能需要较长时间
        import urllib.error
        try:
            resp = urllib.request.urlopen(req, timeout=120)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")[:500] if hasattr(e, 'read') else str(e)
            return {"prompt": prompt, "error": f"FAL HTTP {e.code}: {err_body}", "status": "error"}

        data = json.loads(resp.read().decode("utf-8"))

        images = []
        for i, img_data in enumerate(data.get("images", [])):
            img_info = {
                "url": img_data.get("url", ""),
                "width": img_data.get("width", width),
                "height": img_data.get("height", height),
            }

            # 如果指定了输出路径，下载图片
            if output_path and img_info["url"]:
                if num_images > 1:
                    stem = Path(output_path).stem
                    ext = Path(output_path).suffix or ".png"
                    parent = Path(output_path).parent
                    local_path = str(parent / f"{stem}_{i}{ext}")
                else:
                    local_path = output_path
                try:
                    img_req = urllib.request.Request(img_info["url"])
                    img_resp = urllib.request.urlopen(img_req, timeout=30)
                    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(local_path).write_bytes(img_resp.read())
                    img_info["local_path"] = local_path
                except Exception:
                    pass

            images.append(img_info)

        return {
            "prompt": prompt,
            "model": model_id,
            "images": images,
            "count": len(images),
            "status": "success",
            "source": "fal-ai-flux",
        }

    except Exception as e:
        return {"prompt": prompt, "error": str(e), "status": "error"}


def design_cover(title: str, subtitle: str = "", style: str = "modern-clean") -> dict:
    """
    快捷封面图生成。
    自动构建优化后的FLUX提示词。
    """
    style_prompts = {
        "modern-clean": "modern clean minimalist design, professional marketing cover, high-end aesthetic",
        "tech-future": "futuristic tech design, cyberpunk elements, neon accents, dark gradient background",
        "warm-education": "warm educational illustration, soft colors, knowledge theme, book elements",
        "bold-marketing": "bold eye-catching marketing poster, vibrant colors, dynamic composition",
    }

    base = style_prompts.get(style, style_prompts["modern-clean"])
    full_prompt = f"{base}, title text '{title}'{', subtitle: ' + subtitle if subtitle else ''}, magazine cover quality, 8k, professional"

    return generate_image(full_prompt, width=1080, height=1080)
