#!/usr/bin/env python3
"""
Screenplay Pipeline — Script to Storyboard to Frames
=====================================================
Absorbed from HBAI-Ltd/Toonflow-app — AI short drama/video planning pipeline.

This module implements a three-stage pipeline:
  1. script_to_storyboard(text) — Convert script text to storyboard panels
  2. storyboard_to_frames(storyboard) — Enrich storyboard with frame descriptions
  3. frames_to_video(frames) — Compose frame descriptions into video generation params

All stages work locally with PIL for visualization; no external API required.

Usage:
    python -m molib.agencies.screenplay --script "一只小猫在花园里玩耍" --output storyboard.json
    python -m molib.agencies.screenplay --script "..." --render --output-dir ./frames
    python -m molib.agencies.screenplay --from-storyboard storyboard.json --to-frames
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger("screenplay_pipeline")

# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_FRAME_COUNT = 6
SUPPORTED_GENRES = [
    "剧情", "喜剧", "爱情", "悬疑", "科幻", "奇幻",
    "恐怖", "动作", "动画", "教育", "广告", "短视频",
]

# ── Data Models ───────────────────────────────────────────────────────────────


class ShotSize(str, Enum):
    EXTREME_LONG = "大远景(ELS)"
    LONG = "远景(LS)"
    MEDIUM = "中景(MS)"
    MEDIUM_CLOSE = "中近景(MCS)"
    CLOSE_UP = "特写(CU)"
    EXTREME_CLOSE = "大特写(ECU)"


class CameraAngle(str, Enum):
    EYE_LEVEL = "平视"
    HIGH_ANGLE = "俯视"
    LOW_ANGLE = "仰视"
    BIRDS_EYE = "鸟瞰"
    DUTCH = "荷兰角"
    OVER_SHOULDER = "过肩"


@dataclass
class StoryboardPanel:
    """A single storyboard panel (shot) in the pipeline."""

    panel_id: str = ""
    sequence: int = 0
    scene_number: int = 0
    shot_size: str = "中景(MS)"
    camera_angle: str = "平视"
    camera_movement: str = "固定"
    duration_sec: float = 3.0
    description: str = ""
    dialogue: str = ""
    visual_style: str = "写实"
    color_palette: str = "自然色调"
    lighting: str = "自然光"
    notes: str = ""
    frame_description: str = ""  # Enriched frame-level description

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StoryboardPanel:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Storyboard:
    """Complete storyboard consisting of multiple panels/shots."""

    title: str = ""
    genre: str = ""
    total_duration_sec: float = 0.0
    panels: list[StoryboardPanel] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "genre": self.genre,
            "total_duration_sec": self.total_duration_sec,
            "panel_count": len(self.panels),
            "panels": [p.to_dict() for p in self.panels],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Storyboard:
        panels = [StoryboardPanel.from_dict(p) for p in data.get("panels", [])]
        return cls(
            title=data.get("title", ""),
            genre=data.get("genre", ""),
            total_duration_sec=data.get("total_duration_sec", 0.0),
            panels=panels,
        )


@dataclass
class FrameDescription:
    """A detailed frame description ready for video generation."""

    frame_id: str = ""
    panel_id: str = ""
    sequence: int = 0
    prompt: str = ""
    negative_prompt: str = ""
    width: int = 1920
    height: int = 1080
    duration_sec: float = 3.0
    camera_instruction: str = ""
    style_preset: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FrameDescription:
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


# ── Scene Parser ──────────────────────────────────────────────────────────────


def _parse_scenes(script_text: str) -> list[dict[str, Any]]:
    """Parse a script text into scene blocks.

    Scenes are separated by blank lines or explicit scene markers like
    '场景1', 'Scene 1', or '【场景】'.

    Args:
        script_text: Raw script text

    Returns:
        List of scene dicts with 'text' and 'scene_number'
    """
    lines = script_text.strip().split("\n")
    scenes: list[dict[str, Any]] = []
    current_scene: list[str] = []
    scene_num = 0

    for line in lines:
        stripped = line.strip()
        # Check for scene markers
        if re.match(r"^(场景|Scene|【场景】|\[场景\])\s*\d*", stripped, re.IGNORECASE):
            if current_scene:
                scene_num += 1
                scenes.append({"text": "\n".join(current_scene).strip(), "scene_number": scene_num})
                current_scene = []
            continue

        current_scene.append(line)

    if current_scene:
        scene_num += 1
        scenes.append({"text": "\n".join(current_scene).strip(), "scene_number": scene_num})

    # If no scenes found, treat whole text as one scene
    if not scenes:
        scenes.append({"text": script_text.strip(), "scene_number": 1})

    return scenes


def _guess_genre(script_text: str) -> str:
    """Guess the genre of a script based on keywords.

    Args:
        script_text: Raw script text

    Returns:
        Genre string
    """
    text_lower = script_text.lower()
    genre_keywords = {
        "喜剧": ["哈哈", "搞笑", "笑话", "欢乐", "喜剧", "幽默", "开心"],
        "悬疑": ["谋杀", "侦探", "秘密", "悬疑", "推理", "案件", "凶手", "黑暗"],
        "爱情": ["爱情", "浪漫", "吻", "约会", "恋人", "心动", "告白"],
        "科幻": ["未来", "科技", "机器人", "宇宙", "外星", "科幻", "AI", "赛博"],
        "恐怖": ["鬼", "恐怖", "害怕", "尖叫", "黑暗", "诡异", "惊悚"],
        "动作": ["战斗", "追逐", "爆炸", "打斗", "动作", "追击", "拳"],
        "广告": ["产品", "品牌", "优惠", "购买", "推广", "促销", "限时"],
        "教育": ["知识", "教学", "学习", "课程", "学生", "老师", "教程"],
        "动画": ["卡通", "动画", "拟人", "奇幻世界", "魔法"],
    }

    scores: dict[str, int] = {}
    for genre, keywords in genre_keywords.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[genre] = score

    if scores:
        return max(scores, key=scores.get)
    return "剧情"


def _infer_shot_preset(scene_text: str, scene_index: int) -> tuple[str, str, str, str]:
    """Infer shot size, camera angle, movement, and lighting from scene text.

    Args:
        scene_text: Scene description text
        scene_index: Position of scene in sequence

    Returns:
        Tuple of (shot_size, camera_angle, movement, lighting)
    """
    text_lower = scene_text.lower()

    # Shot size heuristics
    if any(kw in text_lower for kw in ["全景", "大场景", "风景", "城市", "远景"]):
        shot = "远景(LS)"
    elif any(kw in text_lower for kw in ["特写", "细节", "表情", "眼睛", "手"]):
        shot = "特写(CU)"
    elif any(kw in text_lower for kw in ["中景", "对话", "两人"]):
        shot = "中景(MS)"
    elif any(kw in text_lower for kw in ["近景", "面部", "半身"]):
        shot = "中近景(MCS)"
    else:
        shot = "大远景(ELS)" if scene_index == 0 else "中景(MS)"

    # Camera angle heuristics
    if any(kw in text_lower for kw in ["俯视", "从上往下", "俯瞰"]):
        angle = "俯视"
    elif any(kw in text_lower for kw in ["仰视", "从下往上"]):
        angle = "仰视"
    elif any(kw in text_lower for kw in ["鸟瞰", "高空"]):
        angle = "鸟瞰"
    elif any(kw in text_lower for kw in ["倾斜", "不稳定", "紧张"]):
        angle = "荷兰角"
    elif any(kw in text_lower for kw in ["过肩", "背后"]):
        angle = "过肩"
    else:
        angle = "平视"

    # Camera movement
    if any(kw in text_lower for kw in ["推进", "推近", "dolly in", "zoom in"]):
        movement = "推进"
    elif any(kw in text_lower for kw in ["拉远", "后退", "dolly out", "zoom out"]):
        movement = "拉远"
    elif any(kw in text_lower for kw in ["跟随", "跟踪", "跟拍"]):
        movement = "跟随"
    elif any(kw in text_lower for kw in ["摇摄", "环顾", "pan"]):
        movement = "摇摄"
    elif any(kw in text_lower for kw in ["上升", "升降", "crane"]):
        movement = "升降"
    elif any(kw in text_lower for kw in ["手持", "晃动"]):
        movement = "手持"
    else:
        movement = "固定"

    # Lighting
    if any(kw in text_lower for kw in ["暗", "夜晚", "黑暗", "阴影", "低调"]):
        lighting = "低调暗光"
    elif any(kw in text_lower for kw in ["明亮", "白天", "阳光", "高调"]):
        lighting = "高调亮光"
    elif any(kw in text_lower for kw in ["暖", "黄昏", "日落", "金色"]):
        lighting = "暖色黄昏光"
    elif any(kw in text_lower for kw in ["冷", "蓝色", "月光", "科技"]):
        lighting = "冷色科技光"
    elif any(kw in text_lower for kw in ["逆光", "剪影", "背光"]):
        lighting = "逆光剪影"
    else:
        lighting = "自然光"

    return shot, angle, movement, lighting


def _build_frame_prompt(panel: StoryboardPanel) -> str:
    """Build a visually rich frame prompt from a storyboard panel.

    Args:
        panel: Storyboard panel data

    Returns:
        Image generation prompt string
    """
    parts = [
        panel.description or panel.notes,
        f"景别: {panel.shot_size}",
        f"机位: {panel.camera_angle}",
        f"运镜: {panel.camera_movement}",
        f"光线: {panel.lighting}",
        f"色调: {panel.color_palette}",
        f"视觉风格: {panel.visual_style}",
    ]
    return ", ".join(p for p in parts if p)


def _build_negative_prompt() -> str:
    """Build standard negative prompt for video frames.

    Returns:
        Negative prompt string
    """
    return (
        "文字拼写错误, 模糊, 变形, 低质量, 扭曲的面部, "
        "多余的手, 畸形的四肢, 水印, 签名, 低分辨率, 色差"
    )


# ── Pipeline Stages ───────────────────────────────────────────────────────────


def script_to_storyboard(
    script_text: str,
    title: str = "",
    genre: str = "",
    max_panels: int = DEFAULT_FRAME_COUNT,
) -> Storyboard:
    """Convert a text script into a structured storyboard.

    This is Stage 1 of the pipeline. It parses the script,
    infers cinematographic parameters, and produces a list
    of storyboard panels.

    Args:
        script_text: Raw script text (Chinese or English)
        title: Title for the storyboard (auto-generated if empty)
        genre: Genre hint (auto-detected if empty)
        max_panels: Maximum number of panels to generate

    Returns:
        Storyboard object with panels

    Example:
        >>> storyboard = script_to_storyboard("一只小猫在花园里追蝴蝶...")
        >>> print(storyboard.to_dict()["panel_count"])
        6
    """
    if not script_text.strip():
        raise ValueError("Script text cannot be empty")

    inferred_genre = genre or _guess_genre(script_text)
    inferred_title = title or f"{inferred_genre}短片 - {time.strftime('%Y%m%d')}"

    # Parse scenes
    scenes = _parse_scenes(script_text)

    # Build panels
    panels: list[StoryboardPanel] = []
    total_duration = 0.0

    for scene_idx, scene in enumerate(scenes[:max_panels]):
        shot_size, camera_angle, movement, lighting = _infer_shot_preset(
            scene["text"], scene_idx
        )

        # Generate dialogue if present
        dialogue = ""
        dialogue_match = re.search(
            r'[：:]\s*[""」」](.+?)[""」」]|说[：:](.+?)(?:\n|$)',
            scene["text"],
        )
        if dialogue_match:
            dialogue = dialogue_match.group(1) or dialogue_match.group(2) or ""

        # Determine duration based on scene complexity
        word_count = len(scene["text"])
        duration = max(2.0, min(8.0, word_count / 10))

        panel = StoryboardPanel(
            panel_id=str(uuid.uuid4())[:8],
            sequence=scene_idx + 1,
            scene_number=scene["scene_number"],
            shot_size=shot_size,
            camera_angle=camera_angle,
            camera_movement=movement,
            duration_sec=duration,
            description=scene["text"][:200],
            dialogue=dialogue[:100],
            visual_style="写实" if scene_idx % 2 == 0 else "电影感",
            color_palette="自然色调" if scene_idx % 3 != 0 else "暖色调",
            lighting=lighting,
            notes=f"Scene {scene['scene_number']} — {inferred_genre} tone",
        )
        panels.append(panel)
        total_duration += duration

    storyboard = Storyboard(
        title=inferred_title,
        genre=inferred_genre,
        total_duration_sec=total_duration,
        panels=panels,
    )

    logger.info(
        "Storyboard created: %d panels, %.1fs total, genre=%s",
        len(panels),
        total_duration,
        inferred_genre,
    )
    return storyboard


def storyboard_to_frames(
    storyboard: Storyboard,
    width: int = 1920,
    height: int = 1080,
) -> list[FrameDescription]:
    """Convert a storyboard into detailed frame descriptions.

    This is Stage 2 of the pipeline. Each panel gets enriched with
    pixel-level frame parameters ready for image/video generation.

    Args:
        storyboard: Storyboard from script_to_storyboard()
        width: Output frame width
        height: Output frame height

    Returns:
        List of FrameDescription objects

    Example:
        >>> sb = script_to_storyboard("故事文本")
        >>> frames = storyboard_to_frames(sb)
        >>> print(frames[0].prompt[:50])
    """
    frames: list[FrameDescription] = []

    for panel in storyboard.panels:
        prompt = _build_frame_prompt(panel)
        negative = _build_negative_prompt()

        # Map shot size to camera instruction
        camera_guide = f"{panel.shot_size} + {panel.camera_angle}"
        if panel.camera_movement != "固定":
            camera_guide += f" + {panel.camera_movement}运镜"

        fd = FrameDescription(
            frame_id=str(uuid.uuid4())[:8],
            panel_id=panel.panel_id,
            sequence=panel.sequence,
            prompt=prompt,
            negative_prompt=negative,
            width=width,
            height=height,
            duration_sec=panel.duration_sec,
            camera_instruction=camera_guide,
            style_preset=panel.visual_style,
        )
        frames.append(fd)

    logger.info("Frames generated: %d frames at %dx%d", len(frames), width, height)
    return frames


def frames_to_video(frames: list[FrameDescription]) -> dict[str, Any]:
    """Convert frame descriptions into video generation parameters.

    This is Stage 3 of the pipeline. It packages all frame data into
    a format compatible with pixelle-video or other video generation engines.

    Args:
        frames: List of FrameDescription from storyboard_to_frames()

    Returns:
        Dict with video generation parameters:
        {
            "frames": [...],
            "total_duration": float,
            "resolution": (w, h),
            "generation_plan": [...]
        }

    Example:
        >>> params = frames_to_video(frames)
        >>> print(params["total_duration"])
    """
    total_duration = sum(f.duration_sec for f in frames)

    generation_plan = []
    for fd in frames:
        plan_step = {
            "step": fd.sequence,
            "type": "image_to_video",
            "prompt": fd.prompt,
            "negative_prompt": fd.negative_prompt,
            "duration_sec": fd.duration_sec,
            "camera": fd.camera_instruction,
            "resolution": f"{fd.width}x{fd.height}",
            "style": fd.style_preset,
        }
        generation_plan.append(plan_step)

    result = {
        "frames": [fd.to_dict() for fd in frames],
        "total_duration": total_duration,
        "resolution": (frames[0].width, frames[0].height) if frames else (1920, 1080),
        "frame_count": len(frames),
        "generation_plan": generation_plan,
    }

    logger.info("Video plan ready: %d frames, %.1fs total", len(frames), total_duration)
    return result


# ── Rendering (PIL Visualization) ────────────────────────────────────────────


def render_storyboard_preview(
    storyboard: Storyboard,
    output_dir: str = "output/storyboard",
) -> list[str]:
    """Render storyboard panels as preview images using PIL.

    Creates a visual representation of each storyboard panel with
    shot info overlay. Useful for quick review before video generation.

    Args:
        storyboard: Storyboard to render
        output_dir: Directory to save preview images

    Returns:
        List of saved image paths

    Example:
        >>> paths = render_storyboard_preview(storyboard)
        >>> print(f"Rendered {len(paths)} panels")
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
    except ImportError:
        logger.error("PIL not installed. Install with: pip install Pillow")
        return []

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    saved_paths: list[str] = []

    # Try to load a font
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except (OSError, IOError):
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    for panel in storyboard.panels:
        img = Image.new("RGB", (800, 450), color=(35, 35, 50))
        draw = ImageDraw.Draw(img)

        # Background gradient
        for y in range(450):
            r = int(35 + (y / 450) * 30)
            g = int(35 + (y / 450) * 25)
            b = int(50 + (y / 450) * 35)
            draw.line([(0, y), (800, y)], fill=(r, g, b))

        # Shot frame border
        draw.rectangle([15, 15, 785, 300], outline=(100, 120, 150), width=2)
        draw.rectangle([17, 17, 783, 298], outline=(60, 70, 90), width=1)

        # Panel header
        header = f"Shot {panel.sequence:02d} | {panel.shot_size} | {panel.camera_angle}"
        draw.text((25, 22), header, fill=(200, 220, 255), font=title_font)

        # Camera movement
        draw.text(
            (25, 48),
            f"运镜: {panel.camera_movement} | 光线: {panel.lighting} | {panel.duration_sec:.1f}s",
            fill=(160, 180, 210),
            font=small_font,
        )

        # Description (wrapped)
        desc = panel.description[:150]
        words = desc.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=body_font)
            if bbox[2] - bbox[0] > 740:
                lines.append(current)
                current = word
            else:
                current = test
        lines.append(current)

        y_pos = 80
        for line in lines[:6]:
            draw.text((25, y_pos), line, fill=(180, 190, 210), font=body_font)
            y_pos += 22

        # Dialogue
        if panel.dialogue:
            draw.text((25, y_pos + 5), f"对话: {panel.dialogue}", fill=(180, 220, 180), font=body_font)

        # Bottom info bar
        info_y = 320
        draw.rectangle([15, info_y, 785, info_y + 120], outline=(60, 70, 90), width=1)
        info_lines = [
            f"视觉风格: {panel.visual_style} | 色调: {panel.color_palette}",
            f"Panel ID: {panel.panel_id} | Scene: {panel.scene_number}",
            f"备注: {panel.notes}",
        ]
        for i, line in enumerate(info_lines):
            draw.text((25, info_y + 8 + i * 22), line, fill=(150, 160, 180), font=small_font)

        # Save
        panel_path = output_path / f"panel_{panel.sequence:02d}.png"
        img.save(str(panel_path))
        saved_paths.append(str(panel_path))

    # Create a contact sheet
    if len(saved_paths) > 1:
        _create_contact_sheet(saved_paths, str(output_path / "storyboard_overview.png"))

    logger.info("Rendered %d panels to %s", len(saved_paths), output_dir)
    return saved_paths


def _create_contact_sheet(image_paths: list[str], output_path: str) -> None:
    """Create a contact sheet from multiple panel images.

    Args:
        image_paths: List of image file paths
        output_path: Output contact sheet path
    """
    try:
        from PIL import Image  # noqa: PLC0415

        images = [Image.open(p) for p in image_paths if Path(p).exists()]
        if not images:
            return

        cols = min(3, len(images))
        rows = (len(images) + cols - 1) // cols
        thumb_w = 240
        thumb_h = 140
        sheet_w = cols * (thumb_w + 10) + 10
        sheet_h = rows * (thumb_h + 10) + 10

        sheet = Image.new("RGB", (sheet_w, sheet_h), color(25, 25, 40))
        for i, img in enumerate(images):
            thumb = img.resize((thumb_w, thumb_h), Image.LANCZOS)
            x = 10 + (i % cols) * (thumb_w + 10)
            y = 10 + (i // cols) * (thumb_h + 10)
            sheet.paste(thumb, (x, y))

        sheet.save(output_path)
        logger.info("Contact sheet saved to %s", output_path)
    except Exception as e:
        logger.warning("Failed to create contact sheet: %s", e)


# ── CLI ────────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Screenplay Pipeline — Script → Storyboard → Frame descriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s --script \"一只小猫在花园里追蝴蝶\"\n"
            "  %(prog)s --script \"...\" --render --output-dir ./frames\n"
            "  %(prog)s --from-storyboard storyboard.json --to-frames\n"
            "  %(prog)s --script \"...\" --max-panels 12 --output storyboard.json\n"
        ),
    )

    parser.add_argument("--script", type=str, default="", help="剧本文本")
    parser.add_argument("--script-file", type=str, default="", help="从文件读取剧本")
    parser.add_argument("--title", type=str, default="", help="故事板标题")
    parser.add_argument("--genre", type=str, default="", help=f"类型: {SUPPORTED_GENRES}")
    parser.add_argument("--max-panels", type=int, default=DEFAULT_FRAME_COUNT, help=f"最大面板数 (default: {DEFAULT_FRAME_COUNT})")
    parser.add_argument("--output", type=str, default="", help="输出JSON路径")
    parser.add_argument("--render", action="store_true", help="渲染预览图片")
    parser.add_argument("--output-dir", type=str, default="output/storyboard", help="预览图片输出目录")
    parser.add_argument("--from-storyboard", type=str, default="", help="从已有的storyboard JSON继续处理")
    parser.add_argument("--to-frames", action="store_true", help="将storyboard转换为帧描述")
    parser.add_argument("--to-video-plan", action="store_true", help="输出视频生成计划")
    parser.add_argument("--width", type=int, default=1920, help="帧宽度")
    parser.add_argument("--height", type=int, default=1080, help="帧高度")

    return parser


def main() -> int:
    """CLI entry point for the Screenplay Pipeline.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = _build_parser()
    args = parser.parse_args()

    # Read script from file or arg
    script_text = args.script
    if args.script_file:
        try:
            script_text = Path(args.script_file).read_text(encoding="utf-8")
        except OSError as e:
            logger.error("Failed to read script file: %s", e)
            return 1

    # Load from existing storyboard JSON
    storyboard: Storyboard | None = None
    if args.from_storyboard:
        try:
            data = json.loads(Path(args.from_storyboard).read_text(encoding="utf-8"))
            storyboard = Storyboard.from_dict(data)
            logger.info("Loaded storyboard: %s (%d panels)", storyboard.title, len(storyboard.panels))
        except (OSError, json.JSONDecodeError) as e:
            logger.error("Failed to load storyboard: %s", e)
            return 1

    # If we have script text and no loaded storyboard, generate storyboard
    if storyboard is None:
        if not script_text:
            parser.print_help()
            print("\n请提供 --script 或 --script-file", file=sys.stderr)
            return 1

        storyboard = script_to_storyboard(
            script_text=script_text,
            title=args.title,
            genre=args.genre,
            max_panels=args.max_panels,
        )

    # Determine output path
    output_path = args.output or f"output/screenplay_{int(time.time())}.json"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save storyboard
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(storyboard.to_dict(), f, ensure_ascii=False, indent=2)
    logger.info("Storyboard saved to %s", output_path)

    # Render preview images
    if args.render:
        rendered = render_storyboard_preview(storyboard, args.output_dir)
        logger.info("Rendered %d preview panels", len(rendered))

    # Stage 2: to frames
    if args.to_frames or args.to_video_plan:
        frames = storyboard_to_frames(storyboard, width=args.width, height=args.height)
        frames_path = output_path.replace(".json", "_frames.json")
        with open(frames_path, "w", encoding="utf-8") as f:
            json.dump(
                {"frames": [fd.to_dict() for fd in frames]},
                f,
                ensure_ascii=False,
                indent=2,
            )
        logger.info("Frames saved to %s (%d frames)", frames_path, len(frames))

        # Stage 3: video plan
        if args.to_video_plan:
            video_plan = frames_to_video(frames)
            plan_path = output_path.replace(".json", "_video_plan.json")
            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(video_plan, f, ensure_ascii=False, indent=2)
            logger.info("Video plan saved to %s", plan_path)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  ✅ 故事板生成成功!")
    print(f"  标题: {storyboard.title}")
    print(f"  类型: {storyboard.genre}")
    print(f"  面板数: {len(storyboard.panels)}")
    print(f"  总时长: {storyboard.total_duration_sec:.1f}s")
    print(f"  输出: {output_path}")
    print(f"{'=' * 60}")

    return 0


def color(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Helper to create RGB color tuple (avoids linting issues with tuples)."""
    return (r, g, b)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    sys.exit(main())
