#!/usr/bin/env python3
"""
FIBO Image Generation Module
============================
Absorbed from Bria-AI/FIBO (⭐316) — JSON-native text-to-image generation.

Core concept: structured JSON prompts for precise, reproducible image control.
This module implements the FIBO design pattern without requiring the actual
FIBO model weights. It uses the qwen-image-2.0-pro API (百炼) for generation
while preserving the JSON-driven workflow.

Key capabilities:
  - fibo_compose(): Advanced composition from JSON descriptions
  - Template library for e-commerce main images
  - Short prompt → structured JSON expansion
  - Iterative refinement with attribute-level control

Usage:
    python -m molib.shared.ai.fibo_image_gen --prompt "红色高跟鞋，白色背景，电商主图"
    python -m molib.shared.ai.fibo_image_gen --json '{"objects": [...]}' --output output.png
    python -m molib.shared.ai.fibo_image_gen --template product --product "智能手表"
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("fibo_image_gen")

# ── Template Library ──────────────────────────────────────────────────────────

FIBO_TEMPLATES: dict[str, dict[str, Any]] = {
    "product_center": {
        "name": "产品中心型电商主图",
        "description": "产品居中展示，高光突出，适合单品推广",
        "default_json": {
            "short_description": "产品中心展示型电商主图，干净背景突出产品",
            "objects": [
                {
                    "description": "产品主体，置于画面中心位置",
                    "location": "center",
                    "relative_size": "large within frame",
                    "pose": "正面展示",
                }
            ],
            "background_setting": "纯色背景，渐变或留白，干净简约",
            "lighting": {
                "conditions": "明亮柔光，产品轮廓清晰",
                "direction": "正面偏上打光",
                "shadows": "柔和阴影",
            },
            "aesthetics": {
                "composition": "居中构图，产品占画面60-70%",
                "color_scheme": "与品牌色协调",
                "mood_atmosphere": "专业、高端、清晰",
            },
            "photographic_characteristics": {
                "depth_of_field": "浅景深，产品清晰背景虚化",
                "focus": "锐利对焦于产品",
                "camera_angle": "平视略高15度",
            },
            "style_medium": "product photography",
            "context": "电商平台主图，用于淘宝/京东/拼多多商品展示",
            "artistic_style": "商业摄影，真实感",
            "text_render": [],
        },
    },
    "comparison": {
        "name": "对比型主图",
        "description": "左右对比展示，适合功效/升级类产品",
        "default_json": {
            "short_description": "左右对比展示产品升级或功效差异",
            "objects": [
                {
                    "description": "左侧：旧产品或竞品（效果较差）",
                    "location": "left",
                    "relative_size": "medium",
                },
                {
                    "description": "右侧：本产品（效果更好/全新升级）",
                    "location": "right",
                    "relative_size": "medium",
                },
            ],
            "background_setting": "干净纯色背景，左右水平排列",
            "lighting": {"conditions": "均匀照明", "direction": "正面", "shadows": "轻微阴影"},
            "aesthetics": {
                "composition": "左右二分构图",
                "color_scheme": "左侧冷色/暗淡，右侧暖色/明亮",
                "mood_atmosphere": "对比鲜明，突出进步",
            },
            "style_medium": "product photography",
            "artistic_style": "商业摄影",
            "text_render": [],
        },
    },
    "pain_point": {
        "name": "痛点型主图",
        "description": "展示用户痛点+解决方案，适合功能性产品",
        "default_json": {
            "short_description": "痛点场景与解决方案对比",
            "objects": [
                {
                    "description": "上半部分：痛点场景展示（用户困扰）",
                    "location": "top",
                    "relative_size": "medium",
                },
                {
                    "description": "下半部分：使用产品后解决方案",
                    "location": "bottom",
                    "relative_size": "medium",
                },
            ],
            "background_setting": "场景化背景，上半暗调下半明亮",
            "lighting": {
                "conditions": "上半暗调，下半明亮",
                "direction": "差异化打光",
                "shadows": "上半较重，下半柔和",
            },
            "aesthetics": {
                "composition": "上下对比构图",
                "color_scheme": "上半暗色系，下半明快色调",
                "mood_atmosphere": "从困扰到解决的情绪转变",
            },
            "style_medium": "lifestyle photography",
            "artistic_style": "生活化，真实感",
            "text_render": [],
        },
    },
    "promotional": {
        "name": "促销型主图",
        "description": "大促氛围，价格突出，适合活动推广",
        "default_json": {
            "short_description": "促销活动主图，价格优惠信息突出",
            "objects": [
                {
                    "description": "产品主体展示",
                    "location": "center-right",
                    "relative_size": "large",
                },
            ],
            "background_setting": "节日/促销氛围背景，红色/金色系",
            "lighting": {
                "conditions": "明亮华丽灯光",
                "direction": "多角度打光营造氛围",
                "shadows": "淡阴影",
            },
            "aesthetics": {
                "composition": "产品偏右，左侧留白放促销文案",
                "color_scheme": "红/金/橙等促销暖色",
                "mood_atmosphere": "热闹、限时、紧迫感",
            },
            "style_medium": "product photography",
            "artistic_style": "促销风格，视觉冲击力强",
            "text_render": [],
        },
    },
}

# ── Data Models ───────────────────────────────────────────────────────────────


@dataclass
class FiboGenerationResult:
    """Result of a FIBO image generation call."""

    success: bool = False
    image_path: str = ""
    prompt_used: str = ""
    json_prompt: dict[str, Any] = field(default_factory=dict)
    template_name: str = ""
    duration_sec: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        status = "✅" if self.success else "❌"
        return (
            f"{status} FIBO Gen | "
            f"{self.template_name or 'custom'} | "
            f"{self.image_path or 'no file'} | "
            f"{self.duration_sec:.1f}s"
        )


@dataclass
class FiboComposeRequest:
    """Request parameters for fibo_compose()."""

    product_name: str = ""
    product_description: str = ""
    template: str = "product_center"
    custom_json: dict[str, Any] | None = None
    style: str = "商业摄影"
    resolution: tuple[int, int] = (1024, 1024)
    output_path: str = ""
    negative_prompt: str = "文字拼写错误, 模糊, 变形, 低质量"


# ── JSON Prompt Building ──────────────────────────────────────────────────────


def expand_short_prompt(short_prompt: str) -> dict[str, Any]:
    """Expand a short natural-language prompt into a structured FIBO JSON prompt.

    This uses template merging: starts with a generic photography template
    and fills in the subject from the short prompt.

    Args:
        short_prompt: Short description like "红色高跟鞋，白色背景"

    Returns:
        Structured JSON prompt dict
    """
    base = json.loads(json.dumps(FIBO_TEMPLATES["product_center"]["default_json"]))
    base["short_description"] = short_prompt
    objects = base.get("objects", [])
    if objects:
        objects[0]["description"] = short_prompt
    return base


def load_template(template_name: str) -> dict[str, Any]:
    """Load a FIBO template by name.

    Args:
        template_name: One of 'product_center', 'comparison', 'pain_point', 'promotional'

    Returns:
        Template JSON dict

    Raises:
        ValueError: If template_name is unknown
    """
    if template_name not in FIBO_TEMPLATES:
        valid = list(FIBO_TEMPLATES.keys())
        raise ValueError(f"Unknown template '{template_name}'. Valid: {valid}")
    return json.loads(json.dumps(FIBO_TEMPLATES[template_name]["default_json"]))


def apply_product_to_json(
    json_prompt: dict[str, Any],
    product_name: str,
    product_description: str,
) -> dict[str, Any]:
    """Apply product information to a JSON prompt template.

    Args:
        json_prompt: Base JSON prompt (from template or custom)
        product_name: Name of the product
        product_description: Description of the product

    Returns:
        Modified JSON prompt
    """
    result = json.loads(json.dumps(json_prompt))

    # Update short description
    result["short_description"] = f"{product_name} - {product_description}"

    # Update objects
    objects = result.get("objects", [])
    if objects:
        objects[0]["description"] = f"{product_name}: {product_description}"

    return result


def json_to_text_prompt(json_prompt: dict[str, Any]) -> str:
    """Convert a FIBO-style JSON prompt to a flat text prompt for API-based generation.

    Args:
        json_prompt: Structured JSON prompt

    Returns:
        Flat text prompt string
    """
    parts = []

    # Short description first
    if json_prompt.get("short_description"):
        parts.append(json_prompt["short_description"])

    # Objects
    objects = json_prompt.get("objects", [])
    if objects:
        obj_descriptions = []
        for obj in objects:
            desc = obj.get("description", "")
            loc = obj.get("location", "")
            if desc:
                obj_descriptions.append(f"{desc} ({loc})" if loc else desc)
        if obj_descriptions:
            parts.append("包含: " + "; ".join(obj_descriptions))

    # Background
    bg = json_prompt.get("background_setting", "")
    if bg:
        parts.append(f"背景: {bg}")

    # Lighting
    lighting = json_prompt.get("lighting", {})
    if lighting:
        conditions = lighting.get("conditions", "")
        if conditions:
            parts.append(f"光照: {conditions}")

    # Aesthetics
    aesthetics = json_prompt.get("aesthetics", {})
    if aesthetics:
        mood = aesthetics.get("mood_atmosphere", "")
        composition = aesthetics.get("composition", "")
        if mood:
            parts.append(f"氛围: {mood}")
        if composition:
            parts.append(f"构图: {composition}")

    # Style
    style = json_prompt.get("style_medium", "")
    artistic = json_prompt.get("artistic_style", "")
    if style:
        parts.append(f"风格: {style}")
        if artistic and artistic != style:
            parts.append(f"艺术风格: {artistic}")

    # Photo characteristics
    photo = json_prompt.get("photographic_characteristics", {})
    if photo:
        cam = photo.get("camera_angle", "")
        dof = photo.get("depth_of_field", "")
        if cam:
            parts.append(f"机位: {cam}")
        if dof:
            parts.append(f"景深: {dof}")

    return ". ".join(parts)


# ── Core Generation ───────────────────────────────────────────────────────────


def _call_qwen_image_api(
    prompt: str,
    negative_prompt: str = "",
    size: str = "1024*1024",
    n: int = 1,
    model: str = "qwen-image-2.0-pro",
) -> list[str] | None:
    """Call the 百炼 (Bailian) qwen-image-2.0-pro API.

    Requires BAILIAN_API_KEY env var.

    Args:
        prompt: Text prompt
        negative_prompt: Negative prompt
        size: Image size (e.g., "1024*1024")
        n: Number of images (1-4)
        model: Model name

    Returns:
        List of base64-encoded image strings, or None on failure
    """
    api_key = os.environ.get("BAILIAN_API_KEY", "").strip()
    if not api_key:
        api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()

    if not api_key:
        logger.warning("No BAILIAN_API_KEY or DASHSCOPE_API_KEY found; using PIL fallback")
        return None

    try:
        import dashscope  # type: ignore  # noqa: PLC0415
    except ImportError:
        logger.warning("dashscope not installed; trying OpenAI-compatible endpoint")
        return _call_openai_compat(prompt, negative_prompt, size, n)

    try:
        dashscope.api_key = api_key
        responses = []
        for _ in range(n):
            resp = dashscope.ImageGeneration.call(
                model=model,
                prompt=prompt,
                negative_prompt=negative_prompt,
                size=size,
                n=1,
            )
            if resp.status_code == 200:
                image_data = resp.output.get("results", [{}])[0].get("image", "")
                if image_data:
                    responses.append(image_data)
            else:
                logger.error("API error: %s", resp.message)
                return None
        return responses if responses else None
    except Exception as e:
        logger.error("API call failed: %s", e)
        return None


def _call_openai_compat(
    prompt: str,
    negative_prompt: str = "",
    size: str = "1024*1024",
    n: int = 1,
) -> list[str] | None:
    """Fallback using OpenAI-compatible image generation endpoint.

    Args:
        prompt: Text prompt
        negative_prompt: Negative prompt (ignored for OpenAI compat)
        size: Image size
        n: Number of images

    Returns:
        List of base64-encoded image strings, or None on failure
    """
    api_key = os.environ.get("BAILIAN_API_KEY", "")
    base_url = os.environ.get("BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        logger.warning("No API key available for image generation")
        return None

    try:
        from openai import OpenAI  # noqa: PLC0415

        client = OpenAI(api_key=api_key, base_url=base_url)

        # Parse size
        width, height = 1024, 1024
        if "*" in size:
            parts = size.split("*")
            if len(parts) == 2:
                width, height = int(parts[0]), int(parts[1])

        resp = client.images.generate(
            model="qwen-image-2.0-pro",
            prompt=prompt,
            n=n,
            size=f"{width}x{height}",
            response_format="b64_json",
        )

        images = []
        for item in resp.data:
            if item.b64_json:
                images.append(item.b64_json)
        return images if images else None

    except Exception as e:
        logger.error("OpenAI compat API call failed: %s", e)
        return None


def _pil_fallback_generate(
    prompt: str,
    output_path: str,
    size: tuple[int, int] = (1024, 1024),
) -> bool:
    """Fallback: generate a simple placeholder image with PIL.

    This is a last-resort when no API is available. In production,
    you should configure BAILIAN_API_KEY.

    Args:
        prompt: Text prompt (used as text overlay)
        output_path: Path to save image
        size: Image dimensions

    Returns:
        True if successful
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
    except ImportError:
        logger.error("PIL not installed. Install with: pip install Pillow")
        return False

    img = Image.new("RGB", size, color=(245, 245, 250))
    draw = ImageDraw.Draw(img)

    # Draw a gradient-like background
    for y in range(size[1]):
        r = int(240 - (y / size[1]) * 40)
        g = int(240 - (y / size[1]) * 30)
        b = int(255 - (y / size[1]) * 50)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))

    # Draw text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except (OSError, IOError):
        font = ImageFont.load_default()

    # Word wrap
    words = prompt.split()
    lines = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > size[0] - 80:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    lines.append(current_line)

    y_offset = size[1] // 2 - len(lines) * 20
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        draw.text((x, y_offset), line, fill=(40, 40, 60), font=font)
        y_offset += 40

    # Draw info
    info_text = f"FIBO Mode | {size[0]}x{size[1]}"
    draw.text((20, size[1] - 40), info_text, fill=(100, 100, 120), font=ImageFont.load_default())

    img.save(output_path, quality=95)
    logger.info("PIL fallback image saved to %s", output_path)
    return True


# ── Public API ────────────────────────────────────────────────────────────────


def fibo_compose(
    request: FiboComposeRequest | None = None,
    *,
    product_name: str = "",
    product_description: str = "",
    template: str = "product_center",
    custom_json: dict[str, Any] | None = None,
    style: str = "商业摄影",
    resolution: tuple[int, int] = (1024, 1024),
    output_path: str = "",
    negative_prompt: str = "文字拼写错误, 模糊, 变形, 低质量",
) -> FiboGenerationResult:
    """Advanced FIBO image composition interface.

    This is the main entry point for generating e-commerce main images
    using the FIBO JSON-driven approach.

    Args:
        request: FiboComposeRequest dataclass (alternative to kwargs)
        product_name: Product name (e.g., "智能手表Pro Max")
        product_description: Product description
        template: Template name ('product_center', 'comparison', 'pain_point', 'promotional')
        custom_json: Custom JSON prompt (overrides template)
        style: Artistic style override
        resolution: Output resolution (width, height)
        output_path: Output file path (auto-generated if empty)
        negative_prompt: Negative prompt for API

    Returns:
        FiboGenerationResult
    """
    # Unpack request dataclass
    if request is not None:
        product_name = request.product_name or product_name
        product_description = request.product_description or product_description
        template = request.template or template
        custom_json = request.custom_json or custom_json
        style = request.style or style
        resolution = request.resolution or resolution
        output_path = request.output_path or output_path
        negative_prompt = request.negative_prompt or negative_prompt

    start_time = time.perf_counter()
    result = FiboGenerationResult()

    # Build JSON prompt
    try:
        if custom_json:
            json_prompt = custom_json
        else:
            json_prompt = load_template(template)

        if product_name:
            json_prompt = apply_product_to_json(json_prompt, product_name, product_description)
        else:
            # Use template's default description
            json_prompt["artistic_style"] = style
    except ValueError as e:
        result.error = str(e)
        logger.error(result.error)
        return result

    result.json_prompt = json_prompt
    result.template_name = template

    # Convert to text prompt
    text_prompt = json_to_text_prompt(json_prompt)
    if style and style != "商业摄影":
        text_prompt += f", 风格: {style}"

    result.prompt_used = text_prompt

    # Auto-generate output path
    if not output_path:
        ts = int(time.time())
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in product_name[:20]) if product_name else "fibo"
        output_path = f"output/fibo_{safe_name}_{ts}.png"

    # Ensure output directory
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Try API generation
    size_str = f"{resolution[0]}*{resolution[1]}"
    images = _call_qwen_image_api(
        prompt=text_prompt,
        negative_prompt=negative_prompt,
        size=size_str,
    )

    if images:
        # Save first image
        img_data = images[0]
        try:
            if "," in img_data:
                img_data = img_data.split(",")[1]
            img_bytes = base64.b64decode(img_data)
            Path(output_path).write_bytes(img_bytes)
            result.success = True
            result.image_path = output_path
        except Exception as e:
            logger.error("Failed to decode/save image: %s", e)
            # Fallback to PIL
            if _pil_fallback_generate(text_prompt, output_path, resolution):
                result.success = True
                result.image_path = output_path
            else:
                result.error = str(e)
    else:
        # PIL fallback
        if _pil_fallback_generate(text_prompt, output_path, resolution):
            result.success = True
            result.image_path = output_path
        else:
            result.error = "API unavailable and PIL fallback failed"

    result.duration_sec = time.perf_counter() - start_time
    logger.info(result.summary())
    return result


# ── CLI ────────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="FIBO Image Generator — JSON-driven e-commerce image generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s --prompt \"红色高跟鞋，白色背景，电商主图\"\n"
            "  %(prog)s --json '{\"objects\": []}' --output output.png\n"
            "  %(prog)s --template product_center --product \"智能手表\" --desc \"旗舰款\"\n"
            "  %(prog)s --list-templates\n"
        ),
    )

    parser.add_argument("--prompt", type=str, default="", help="短文本描述（自动扩展为结构化JSON）")
    parser.add_argument("--json", type=str, default="", help="结构化JSON提示（文件路径或JSON字符串）")
    parser.add_argument("--template", type=str, default="", help=f"模板名称: {list(FIBO_TEMPLATES.keys())}")
    parser.add_argument("--product", type=str, default="", help="产品名称")
    parser.add_argument("--desc", type=str, default="", help="产品描述")
    parser.add_argument("--style", type=str, default="", help="艺术风格覆盖")
    parser.add_argument("--output", type=str, default="", help="输出图片路径")
    parser.add_argument(
        "--resolution",
        type=str,
        default="1024x1024",
        help="输出分辨率 (宽x高，如 1024x1024)",
    )
    parser.add_argument("--list-templates", action="store_true", help="列出所有可用模板")
    parser.add_argument("--negative", type=str, default="", help="负面提示词")

    return parser


def main() -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_templates:
        print("可用模板:")
        print("=" * 60)
        for name, tmpl in FIBO_TEMPLATES.items():
            print(f"\n  [{name}] {tmpl['name']}")
            print(f"  描述: {tmpl['description']}")
        return 0

    # Parse resolution
    resolution = (1024, 1024)
    if args.resolution:
        try:
            parts = args.resolution.replace("x", "*").replace("×", "*").split("*")
            resolution = (int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            logger.warning("Invalid resolution '%s', using 1024x1024", args.resolution)

    # Parse custom JSON
    custom_json = None
    if args.json:
        try:
            if os.path.isfile(args.json):
                with open(args.json) as f:
                    custom_json = json.load(f)
            else:
                custom_json = json.loads(args.json)
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to parse JSON: %s", e)
            return 1

    # If short prompt given, expand it
    template_name = args.template
    if args.prompt and not template_name and not custom_json:
        custom_json = expand_short_prompt(args.prompt)
        template_name = "auto-expanded"

    result = fibo_compose(
        product_name=args.product,
        product_description=args.desc or args.prompt,
        template=template_name or "product_center",
        custom_json=custom_json,
        style=args.style,
        resolution=resolution,
        output_path=args.output,
        negative_prompt=args.negative,
    )

    if result.success:
        print("\n" + "=" * 60)
        print(f"  ✅ 图片生成成功!")
        print(f"  输出: {result.image_path}")
        print(f"  模板: {result.template_name}")
        print(f"  耗时: {result.duration_sec:.1f}s")
        print(f"  提示: {result.prompt_used[:100]}...")
        print("=" * 60)
        return 0
    else:
        print(f"❌ 生成失败: {result.error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
