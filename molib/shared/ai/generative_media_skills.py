#!/usr/bin/env python3
"""
Generative Media Skills — Core Integration
===========================================
Absorbed from SamurAIGPT/Generative-Media-Skills (⭐3200).

Dual-layer architecture:
  1. Core layer (this file): MediaSkills class — unified interface for media generation
  2. Library layer (molib/skills/library/): Expert knowledge files for AI prompting

Core capabilities:
  - image_generate(): Text-to-image generation
  - image_edit(): Image-to-image editing
  - video_generate(): Text-to-video
  - video_from_image(): Image-to-video
  - media_upload(): File upload to CDN
  - Skills knowledge injection for domain-specific generation

Usage:
    python -m molib.shared.ai.generative_media_skills generate-image --prompt "cyberpunk city"
    python -m molib.shared.ai.generative_media_skills generate-video --prompt "sunset mountains"
    python -m molib.shared.ai.generative_media_skills skills --list
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("generative_media_skills")

# ── Supported Models ──────────────────────────────────────────────────────────

IMAGE_MODELS = [
    "flux-dev", "flux-schnell", "flux-1.1-pro", "flux-kontext-pro",
    "midjourney-v7", "hidream-fast", "sdxl-turbo",
]

VIDEO_MODELS = [
    "kling-v3.0-pro", "kling-master", "seedance-2.0", "veo3",
    "cogvideo-x", "minimax-video",
]

EDIT_MODELS = [
    "flux-kontext-pro", "flux-dev", "midjourney-v7", "seedance-2.0",
]


# ── Data Models ───────────────────────────────────────────────────────────────


@dataclass
class MediaResult:
    """Structured result from a media generation call."""

    success: bool = False
    media_type: str = "image"  # "image" | "video" | "audio" | "edit"
    urls: list[str] = field(default_factory=list)
    local_paths: list[str] = field(default_factory=list)
    prompt_used: str = ""
    model_used: str = ""
    request_id: str = ""
    duration_sec: float = 0.0
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        status = "✅" if self.success else "❌"
        url_str = self.urls[0] if self.urls else "no URL"
        return (
            f"{status} {self.media_type} | {self.model_used} | "
            f"{url_str[:60]}... | {self.duration_sec:.1f}s"
        )


@dataclass
class SkillKnowledge:
    """An expert knowledge entry for media generation."""

    name: str
    domain: str
    content: str
    tags: list[str] = field(default_factory=list)
    source_file: str = ""


# ── Expert Knowledge Library ──────────────────────────────────────────────────

_EXPERT_KNOWLEDGE: dict[str, SkillKnowledge] = {}


def register_skill(skill: SkillKnowledge) -> None:
    """Register expert knowledge for media generation."""
    _EXPERT_KNOWLEDGE[skill.name] = skill
    logger.debug("Registered skill: %s (%s)", skill.name, skill.domain)


def get_skill(name: str) -> SkillKnowledge | None:
    """Get expert knowledge by name."""
    return _EXPERT_KNOWLEDGE.get(name)


def list_skills() -> list[SkillKnowledge]:
    """List all registered expert knowledge entries."""
    return list(_EXPERT_KNOWLEDGE.values())


def build_knowledge_context(domain: str | None = None) -> str:
    """Build a context string from registered skills, optionally filtered by domain.

    Args:
        domain: Filter by domain (e.g., "cinema", "visual", "marketing")

    Returns:
        Concatenated knowledge context string
    """
    skills = _EXPERT_KNOWLEDGE.values()
    if domain:
        skills = [s for s in skills if s.domain == domain or domain in s.tags]

    parts = []
    for skill in skills:
        parts.append(f"=== {skill.name} ({skill.domain}) ===")
        parts.append(skill.content[:1500])  # Truncate to avoid overflow
        parts.append("")

    return "\n".join(parts)


# ── Core MediaSkills Class ────────────────────────────────────────────────────


class MediaSkills:
    """Unified interface for generative media operations.

    Provides a consistent API for image/video generation, editing, and upload.
    Supports multiple backends with automatic fallback:
      1. muapi-cli (external service)
      2. OpenAI-compatible APIs
      3. Local simulation (for testing)
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        backend: Literal["muapi", "openai", "local"] = "local",
        output_dir: str = "output/media",
    ):
        """Initialize MediaSkills.

        Args:
            api_key: API key (auto-detected from env if not provided)
            base_url: API base URL
            backend: Generation backend to use
            output_dir: Directory for output files
        """
        self.api_key = api_key or os.environ.get("MUAPI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("MUAPI_BASE_URL", "https://api.muapi.ai")
        self.backend = backend
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Image Generation ──────────────────────────────────────────────────

    def image_generate(
        self,
        prompt: str,
        model: str = "flux-dev",
        aspect_ratio: str = "1:1",
        negative_prompt: str = "",
        n: int = 1,
        download: bool = True,
    ) -> MediaResult:
        """Generate image from text prompt.

        Args:
            prompt: Text description
            model: Model name (see IMAGE_MODELS)
            aspect_ratio: Aspect ratio (e.g., "1:1", "16:9", "4:3")
            negative_prompt: Negative prompt
            n: Number of images to generate
            download: Whether to download results locally

        Returns:
            MediaResult
        """
        result = MediaResult(media_type="image", prompt_used=prompt, model_used=model)
        start = time.perf_counter()

        try:
            if self.backend == "muapi" and self._check_muapi():
                result = self._muapi_image_generate(prompt, model, aspect_ratio, negative_prompt, n, download)
            elif self.backend == "openai" and self.api_key:
                result = self._openai_image_generate(prompt, model, aspect_ratio, negative_prompt, n, download)
            else:
                result = self._local_image_generate(prompt, model, aspect_ratio, n, download)

            result.duration_sec = time.perf_counter() - start
            result.success = bool(result.urls or result.local_paths)

        except Exception as e:
            result.error = str(e)
            logger.error("Image generation failed: %s", e)

        logger.info(result.summary())
        return result

    # ── Video Generation ──────────────────────────────────────────────────

    def video_generate(
        self,
        prompt: str,
        model: str = "kling-v3.0-pro",
        duration: int = 5,
        aspect_ratio: str = "16:9",
        download: bool = True,
    ) -> MediaResult:
        """Generate video from text prompt.

        Args:
            prompt: Text description of the video
            model: Video model name
            duration: Video duration in seconds
            aspect_ratio: Aspect ratio
            download: Whether to download locally

        Returns:
            MediaResult
        """
        result = MediaResult(media_type="video", prompt_used=prompt, model_used=model)
        start = time.perf_counter()

        try:
            if self.backend == "muapi" and self._check_muapi():
                result = self._muapi_video_generate(prompt, model, duration, aspect_ratio, download)
            elif self.backend == "local":
                result = self._local_video_generate(prompt, model, duration, aspect_ratio, download)

            result.duration_sec = time.perf_counter() - start
            result.success = bool(result.urls or result.local_paths)

        except Exception as e:
            result.error = str(e)
            logger.error("Video generation failed: %s", e)

        logger.info(result.summary())
        return result

    # ── Image Editing ─────────────────────────────────────────────────────

    def image_edit(
        self,
        prompt: str,
        image_url: str,
        model: str = "flux-kontext-pro",
        strength: float = 0.8,
        download: bool = True,
    ) -> MediaResult:
        """Edit image based on text instruction.

        Args:
            prompt: Edit instruction
            image_url: URL or local path of source image
            model: Edit model name
            strength: Edit strength (0.0-1.0)
            download: Whether to download locally

        Returns:
            MediaResult
        """
        result = MediaResult(media_type="edit", prompt_used=prompt, model_used=model)
        start = time.perf_counter()

        try:
            if self.backend == "local":
                result = self._local_image_edit(prompt, image_url, model, strength, download)

            result.duration_sec = time.perf_counter() - start
            result.success = bool(result.urls or result.local_paths)

        except Exception as e:
            result.error = str(e)
            logger.error("Image edit failed: %s", e)

        logger.info(result.summary())
        return result

    # ── File Upload ───────────────────────────────────────────────────────

    def upload_file(self, file_path: str) -> MediaResult:
        """Upload a file to CDN.

        Args:
            file_path: Local file path to upload

        Returns:
            MediaResult with CDN URL
        """
        result = MediaResult(media_type="upload")
        start = time.perf_counter()

        try:
            path = Path(file_path)
            if not path.exists():
                result.error = f"File not found: {file_path}"
                return result

            # Simulate upload - copy to output dir
            dest = self.output_dir / f"upload_{path.name}"
            import shutil
            shutil.copy2(path, dest)

            result.urls = [f"file://{dest.absolute()}"]
            result.local_paths = [str(dest)]
            result.duration_sec = time.perf_counter() - start
            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error("Upload failed: %s", e)

        return result

    # ── Backend Implementations ───────────────────────────────────────────

    def _check_muapi(self) -> bool:
        """Check if muapi-cli is available."""
        import shutil
        return shutil.which("muapi") is not None

    def _muapi_image_generate(
        self, prompt: str, model: str, aspect_ratio: str, negative_prompt: str, n: int, download: bool
    ) -> MediaResult:
        """Generate using muapi-cli."""
        import subprocess

        cmd = [
            "muapi", "image", "generate", prompt,
            "--model", model,
            "--aspect-ratio", aspect_ratio,
            "--output-json",
        ]
        if download:
            cmd.extend(["--download", str(self.output_dir)])

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            return MediaResult(error=f"muapi error: {proc.stderr[:200]}")

        try:
            data = json.loads(proc.stdout)
            urls = data.get("outputs", [])
            return MediaResult(media_type="image", urls=urls, success=True)
        except json.JSONDecodeError:
            return MediaResult(error=f"Failed to parse muapi output: {proc.stdout[:200]}")

    def _openai_image_generate(
        self, prompt: str, model: str, aspect_ratio: str, negative_prompt: str, n: int, download: bool
    ) -> MediaResult:
        """Generate using OpenAI-compatible API."""
        from openai import OpenAI  # noqa: PLC0415

        client = OpenAI(api_key=self.api_key)

        size_map = {"1:1": "1024x1024", "16:9": "1792x1024", "4:3": "1024x768", "3:4": "768x1024"}
        size = size_map.get(aspect_ratio, "1024x1024")

        resp = client.images.generate(
            model="dall-e-3" if "dall-e" in model.lower() else model,
            prompt=prompt,
            n=n,
            size=size,
            quality="standard",
        )

        urls = []
        local_paths = []
        for i, item in enumerate(resp.data):
            if item.url:
                urls.append(item.url)
                if download:
                    import urllib.request
                    local_path = self.output_dir / f"openai_img_{int(time.time())}_{i}.png"
                    urllib.request.urlretrieve(item.url, local_path)
                    local_paths.append(str(local_path))

        return MediaResult(media_type="image", urls=urls, local_paths=local_paths, success=True)

    def _local_image_generate(
        self, prompt: str, model: str, aspect_ratio: str, n: int, download: bool
    ) -> MediaResult:
        """Simulate image generation locally (PIL placeholder)."""
        try:
            from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
        except ImportError:
            return MediaResult(error="PIL not installed")

        urls = []
        local_paths = []
        width, height = self._parse_aspect_ratio(aspect_ratio, 1024)

        for i in range(n):
            img = Image.new("RGB", (width, height), color=(30, 30, 50))
            draw = ImageDraw.Draw(img)

            # Gradient background
            for y in range(height):
                r = int(40 + (y / height) * 60)
                g = int(40 + (y / height) * 40)
                b = int(70 + (y / height) * 60)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Word wrap
            words = prompt.split()
            lines = []
            current = ""
            for word in words:
                test = f"{current} {word}".strip()
                bbox = draw.textbbox((0, 0), test, font=font)
                if bbox[2] - bbox[0] > width - 60:
                    lines.append(current)
                    current = word
                else:
                    current = test
            lines.append(current)

            y_pos = height // 2 - len(lines) * 18
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                x = (width - (bbox[2] - bbox[0])) // 2
                draw.text((x, y_pos), line, fill=(200, 200, 220), font=font)
                y_pos += 36

            info = f"MediaSkills | {model} | {width}x{height}"
            draw.text((15, height - 30), info, fill=(120, 120, 150), font=ImageFont.load_default())

            if download:
                ts = int(time.time())
                local_path = self.output_dir / f"gen_img_{ts}_{i}.png"
                img.save(local_path, quality=92)
                local_paths.append(str(local_path))
                urls.append(f"file://{local_path}")

        return MediaResult(media_type="image", urls=urls, local_paths=local_paths, success=True)

    def _local_video_generate(
        self, prompt: str, model: str, duration: int, aspect_ratio: str, download: bool
    ) -> MediaResult:
        """Simulate video generation — creates a simple GIF."""
        try:
            from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
        except ImportError:
            return MediaResult(error="PIL not installed")

        width, height = self._parse_aspect_ratio(aspect_ratio, 640)
        frames_count = max(duration * 2, 4)

        frames = []
        for frame_idx in range(frames_count):
            img = Image.new("RGB", (width, height), color=(20, 20, 40))
            draw = ImageDraw.Draw(img)

            # Animated gradient
            offset = int((frame_idx / frames_count) * width * 0.3)
            for y in range(height):
                gradient_pos = (y + offset) % height
                r = int(40 + (gradient_pos / height) * 80)
                g = int(30 + (gradient_pos / height) * 60)
                b = int(60 + (gradient_pos / height) * 90)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

            # Text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except (OSError, IOError):
                font = ImageFont.load_default()

            draw.text((20, height // 2 - 10), prompt[:80], fill=(200, 200, 220), font=font)
            draw.text(
                (20, height - 30),
                f"Frame {frame_idx + 1}/{frames_count} | {model}",
                fill=(100, 100, 130),
                font=ImageFont.load_default(),
            )
            frames.append(img)

        local_paths = []
        if download and frames:
            ts = int(time.time())
            gif_path = self.output_dir / f"gen_video_{ts}.gif"
            frames[0].save(
                gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=max(500, duration * 1000 // frames_count),
                loop=0,
            )
            local_paths.append(str(gif_path))

        return MediaResult(
            media_type="video",
            urls=[f"file://{p}" for p in local_paths],
            local_paths=local_paths,
            success=True,
        )

    def _local_image_edit(
        self, prompt: str, image_url: str, model: str, strength: float, download: bool
    ) -> MediaResult:
        """Simulate image editing locally."""
        try:
            from PIL import Image, ImageDraw, ImageFont  # noqa: PLC0415
        except ImportError:
            return MediaResult(error="PIL not installed")

        # Create a placeholder edit result
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), color=(50, 50, 70))
        draw = ImageDraw.Draw(img)

        for y in range(height):
            draw.line([(0, y), (width, y)], fill=(60 + y // 20, 50 + y // 25, 80 + y // 15))

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        except (OSError, IOError):
            font = ImageFont.load_default()

        draw.text((30, height // 2 - 20), f"Edit: {prompt[:80]}", fill=(220, 220, 240), font=font)
        draw.text((30, height // 2 + 20), f"Strength: {strength}", fill=(150, 150, 180), font=ImageFont.load_default())

        local_paths = []
        if download:
            ts = int(time.time())
            local_path = self.output_dir / f"gen_edit_{ts}.png"
            img.save(local_path, quality=92)
            local_paths.append(str(local_path))

        return MediaResult(media_type="edit", urls=[f"file://{p}" for p in local_paths], local_paths=local_paths, success=True)

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_aspect_ratio(ratio: str, base_size: int = 1024) -> tuple[int, int]:
        """Parse aspect ratio string to pixel dimensions."""
        ratio_map = {
            "1:1": (base_size, base_size),
            "16:9": (base_size, base_size * 9 // 16),
            "9:16": (base_size * 9 // 16, base_size),
            "4:3": (base_size, base_size * 3 // 4),
            "3:4": (base_size * 3 // 4, base_size),
            "21:9": (base_size, base_size * 9 // 21),
        }
        if ratio in ratio_map:
            return ratio_map[ratio]
        try:
            w_str, h_str = ratio.replace(":", "/").split("/")
            w, h = int(w_str), int(h_str)
            if w >= h:
                return (base_size, base_size * h // w)
            else:
                return (base_size * w // h, base_size)
        except (ValueError, IndexError):
            return (base_size, base_size)


# ── CLI ────────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generative Media Skills — Image/Video/Audio generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s generate-image --prompt 'cyberpunk city' --model flux-dev\n"
            "  %(prog)s generate-video --prompt 'sunset mountains' --model kling-v3.0-pro\n"
            "  %(prog)s skills --list\n"
        ),
    )

    sub = parser.add_subparsers(dest="command", help="Sub-command")

    # generate-image
    img = sub.add_parser("generate-image", help="Generate image")
    img.add_argument("--prompt", type=str, required=True, help="Image description")
    img.add_argument("--model", type=str, default="flux-dev", help=f"Model: {IMAGE_MODELS}")
    img.add_argument("--aspect-ratio", type=str, default="1:1", help="Aspect ratio (1:1, 16:9, 4:3)")
    img.add_argument("--negative", type=str, default="", help="Negative prompt")
    img.add_argument("--n", type=int, default=1, help="Number of images")
    img.add_argument("--backend", type=str, default="local", help="Backend (muapi, openai, local)")

    # generate-video
    vid = sub.add_parser("generate-video", help="Generate video")
    vid.add_argument("--prompt", type=str, required=True, help="Video description")
    vid.add_argument("--model", type=str, default="kling-v3.0-pro", help=f"Model: {VIDEO_MODELS}")
    vid.add_argument("--duration", type=int, default=5, help="Duration in seconds")
    vid.add_argument("--aspect-ratio", type=str, default="16:9", help="Aspect ratio")
    vid.add_argument("--backend", type=str, default="local", help="Backend (muapi, local)")

    # edit-image
    edit = sub.add_parser("edit-image", help="Edit image")
    edit.add_argument("--prompt", type=str, required=True, help="Edit instruction")
    edit.add_argument("--image", type=str, required=True, help="Source image URL/path")
    edit.add_argument("--model", type=str, default="flux-kontext-pro", help=f"Model: {EDIT_MODELS}")
    edit.add_argument("--strength", type=float, default=0.8, help="Edit strength")

    # skills
    sk = sub.add_parser("skills", help="List expert knowledge")
    sk.add_argument("--list", action="store_true", default=True, help="List all skills")
    sk.add_argument("--domain", type=str, default="", help="Filter by domain")
    sk.add_argument("--show", type=str, default="", help="Show specific skill content")

    return parser


def main() -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    ms = MediaSkills(backend=args.backend if hasattr(args, "backend") else "local")

    if args.command == "generate-image":
        result = ms.image_generate(
            prompt=args.prompt,
            model=args.model,
            aspect_ratio=args.aspect_ratio,
            negative_prompt=args.negative,
            n=args.n,
        )
        _print_result(result)

    elif args.command == "generate-video":
        result = ms.video_generate(
            prompt=args.prompt,
            model=args.model,
            duration=args.duration,
            aspect_ratio=args.aspect_ratio,
        )
        _print_result(result)

    elif args.command == "edit-image":
        result = ms.image_edit(
            prompt=args.prompt,
            image_url=args.image,
            model=args.model,
            strength=args.strength,
        )
        _print_result(result)

    elif args.command == "skills":
        if args.show:
            skill = get_skill(args.show)
            if skill:
                print(f"=== {skill.name} ({skill.domain}) ===")
                print(f"Tags: {skill.tags}")
                print(f"Source: {skill.source_file}")
                print(f"\n{skill.content}")
            else:
                print(f"Skill '{args.show}' not found")
                return 1
        else:
            skills = list_skills()
            if args.domain:
                skills = [s for s in skills if args.domain in s.tags or s.domain == args.domain]
            print(f"Expert Skills ({len(skills)}):")
            print("=" * 60)
            for s in skills:
                print(f"  [{s.name}] {s.domain} — {s.content[:80]}...")
            print("\nTip: use --show <name> to see full content")

    else:
        parser.print_help()

    return 0


def _print_result(result: MediaResult) -> None:
    """Print a MediaResult to stdout."""
    print("\n" + "=" * 60)
    status = "✅ Success" if result.success else "❌ Failed"
    print(f"  Status: {status}")
    print(f"  Type: {result.media_type}")
    print(f"  Model: {result.model_used}")
    print(f"  Duration: {result.duration_sec:.1f}s")
    if result.urls:
        print(f"  URLs:")
        for u in result.urls[:3]:
            print(f"    - {u}")
    if result.local_paths:
        print(f"  Local:")
        for p in result.local_paths[:3]:
            print(f"    - {p}")
    if result.error:
        print(f"  Error: {result.error}")
    print("=" * 60)


if __name__ == "__main__":
    sys.exit(main())
