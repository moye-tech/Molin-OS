#!/usr/bin/env python3
"""
Vibe Workflow — Creative Workflow Engine
=========================================
Absorbed from SamurAIGPT/Vibe-Workflow design patterns.

Core concept: composable workflow nodes that chain together to form
creative pipelines. Each node has input_schema → process() → output,
enabling dynamic construction of AI-powered workflows.

Preset workflows:
  - ecommerce_main_image: 电商主图生成 (product + tagline → composited image)
  - video_script_to_storyboard: 脚本→分镜转换
  - brand_style_transfer: 品牌风格迁移

Usage:
    python -m molib.shared.ai.vibe_workflow --preset ecommerce --params '{"product":"火花思维","tagline":"不刷题让孩子讲题"}'
    python -m molib.shared.ai.vibe_workflow --preset storyboard --params '{"script":"小猫在花园玩耍"}'
    python -m molib.shared.ai.vibe_workflow --list-presets
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
import types
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("vibe_workflow")


# ── Data Models ──────────────────────────────────────────────────────────────


@dataclass
class NodeInput:
    """Input data for a workflow node."""
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value


@dataclass
class NodeOutput:
    """Output data from a workflow node."""
    success: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    node_name: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


# ── WorkflowNode Base ────────────────────────────────────────────────────────


class WorkflowNode:
    """Base class for all workflow nodes in the pipeline.

    Subclasses must override process() to implement their logic.
    """

    name: str = "base_node"
    description: str = "Base workflow node"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {},
    }

    def __init__(self, name: str | None = None, **kwargs):
        if name:
            self.name = name
        self._config = kwargs
        self._output: NodeOutput | None = None

    @property
    def output(self) -> NodeOutput | None:
        return self._output

    def validate_input(self, node_input: NodeInput) -> list[str]:
        """Validate input against schema. Returns list of error messages."""
        errors: list[str] = []
        props = self.input_schema.get("properties", {})
        required = self.input_schema.get("required", [])
        for key in required:
            if key not in node_input.data or node_input.data[key] is None:
                errors.append(f"Missing required field: '{key}'")
        for key, schema in props.items():
            val = node_input.data.get(key)
            if val is not None:
                expected_type = schema.get("type", "string")
                if expected_type == "string" and not isinstance(val, str):
                    errors.append(f"Field '{key}' should be string, got {type(val).__name__}")
                elif expected_type == "object" and not isinstance(val, dict):
                    errors.append(f"Field '{key}' should be object, got {type(val).__name__}")
        return errors

    def process(self, node_input: NodeInput) -> NodeOutput:
        """Process input and return output. Override in subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} must implement process()")

    def __call__(self, node_input: NodeInput) -> NodeOutput:
        errors = self.validate_input(node_input)
        if errors:
            self._output = NodeOutput(
                success=False,
                error="; ".join(errors),
                node_name=self.name,
            )
            return self._output
        t0 = time.time()
        try:
            self._output = self.process(node_input)
            self._output.node_name = self.name
            self._output.duration_ms = (time.time() - t0) * 1000
        except Exception as e:
            logger.exception(f"Node '{self.name}' failed")
            self._output = NodeOutput(
                success=False,
                error=str(e),
                node_name=self.name,
                duration_ms=(time.time() - t0) * 1000,
            )
        return self._output

    def reset(self) -> None:
        """Reset node state for re-use."""
        self._output = None


# ── Pre-built Nodes ──────────────────────────────────────────────────────────


class TextNode(WorkflowNode):
    """Process text input — format, template, or transform text content."""

    name = "text_node"
    description = "Process and format text content"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Input text content"},
            "template": {"type": "string", "description": "Template string with {placeholders}"},
            "operation": {"type": "string", "description": "Operation: format | template | passthrough"},
        },
        "required": ["text"],
    }

    def process(self, node_input: NodeInput) -> NodeOutput:
        text = node_input.get("text", "")
        template = node_input.get("template", "")
        operation = node_input.get("operation", "passthrough")

        if operation == "format":
            # Apply simple formatting: capitalize, clean whitespace
            result = " ".join(text.split())
        elif operation == "template" and template:
            # Use template string with placeholders
            params = node_input.data.get("params", node_input.data)
            try:
                result = template.format(**params)
            except KeyError as e:
                return NodeOutput(success=False, error=f"Template key missing: {e}")
        else:
            result = text

        return NodeOutput(success=True, data={
            "text": result,
            "original_text": text,
            "operation": operation,
            "char_count": len(result),
        })


class ImageGenNode(WorkflowNode):
    """Generate image description/prompt for downstream rendering.

    In a real deployment, this would call an image generation API.
    Here it produces structured JSON prompt output suitable for
    image generation engines.
    """

    name = "image_gen"
    description = "Generate structured image description from text prompt"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Text prompt for image"},
            "style": {"type": "string", "description": "Visual style"},
            "width": {"type": "number", "description": "Image width"},
            "height": {"type": "number", "description": "Image height"},
        },
        "required": ["prompt"],
    }

    def process(self, node_input: NodeInput) -> NodeOutput:
        prompt = node_input.get("prompt", "")
        style = node_input.get("style", "电商摄影")
        width = node_input.get("width", 1024)
        height = node_input.get("height", 1024)

        # Build structured generation params
        gen_params = {
            "prompt": prompt,
            "style": style,
            "width": width,
            "height": height,
            "negative_prompt": "低质量, 模糊, 变形, 文字错误",
            "cfg_scale": 7.0,
            "steps": 30,
        }

        return NodeOutput(success=True, data={
            "generation_params": gen_params,
            "prompt": prompt,
            "style": style,
            "dimensions": f"{width}x{height}",
        })


class StyleTransferNode(WorkflowNode):
    """Apply style transfer — maps source content to target visual style."""

    name = "style_transfer"
    description = "Apply visual style transfer to content"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Content description"},
            "style_ref": {"type": "string", "description": "Target style reference"},
            "intensity": {"type": "number", "description": "Style intensity 0-1"},
        },
        "required": ["content", "style_ref"],
    }

    def process(self, node_input: NodeInput) -> NodeOutput:
        content = node_input.get("content", "")
        style_ref = node_input.get("style_ref", "")
        intensity = min(1.0, max(0.0, node_input.get("intensity", 0.7)))

        # Blend content and style into a combined prompt
        style_map = {
            "日系": "soft lighting, pastel tones, minimalist composition, Japanese aesthetic",
            "赛博朋克": "neon lights, dark background, cyberpunk aesthetic, high contrast",
            "极简": "clean lines, minimal elements, ample whitespace, modern design",
            "国潮": "Chinese traditional patterns, bold red/gold palette, modern illustration style",
            "muji": "natural materials, earthy tones, simple product photography, zen-like",
            "苹果风": "clean white background, minimalist, premium feel, studio lighting",
        }

        style_desc = style_map.get(style_ref, f"{style_ref} aesthetic, consistent style")
        blended_prompt = f"{content}. Style: {style_desc}. Intensity: {intensity:.1f}"

        return NodeOutput(success=True, data={
            "blended_prompt": blended_prompt,
            "content": content,
            "style_reference": style_ref,
            "intensity": intensity,
            "style_description": style_desc,
        })


class CompositionNode(WorkflowNode):
    """Compose multiple elements into a structured scene description."""

    name = "composition"
    description = "Compose multiple visual elements into a scene"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "elements": {"type": "object", "description": "Dict of named elements with descriptions"},
            "layout": {"type": "string", "description": "Layout type: center | grid | split | overlay"},
            "background": {"type": "string", "description": "Background description"},
        },
        "required": ["elements"],
    }

    def process(self, node_input: NodeInput) -> NodeOutput:
        elements = node_input.get("elements", {})
        layout = node_input.get("layout", "center")
        background = node_input.get("background", "纯色背景，干净简约")

        layout_descriptions = {
            "center": "主体居中，周围环绕辅助元素",
            "grid": "元素以网格形式均匀排列",
            "split": "左右或上下分割布局",
            "overlay": "主体在前，次要元素以叠加方式排列",
        }

        element_list = []
        for name, desc in elements.items():
            element_list.append(f"- {name}: {desc}")

        composition_desc = (
            f"构图方式: {layout_descriptions.get(layout, layout)}\n"
            f"背景: {background}\n"
            f"元素:\n" + "\n".join(element_list)
        )

        return NodeOutput(success=True, data={
            "composition_description": composition_desc,
            "elements": elements,
            "layout": layout,
            "background": background,
            "element_count": len(elements),
        })


class CompositeNode(WorkflowNode):
    """Final composition — merge all upstream outputs into final result."""

    name = "composite"
    description = "Merge all node outputs into final composite result"
    input_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "nodes_output": {"type": "object", "description": "Dict of node_name → NodeOutput"},
            "output_format": {"type": "string", "description": "json | image | markdown"},
        },
        "required": ["nodes_output"],
    }

    def process(self, node_input: NodeInput) -> NodeOutput:
        nodes_output = node_input.get("nodes_output", {})
        output_format = node_input.get("output_format", "json")

        composite = {
            "workflow_result": {},
            "metadata": {
                "nodes_used": list(nodes_output.keys()),
                "output_format": output_format,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

        for node_name, node_out in nodes_output.items():
            if isinstance(node_out, NodeOutput):
                composite["workflow_result"][node_name] = node_out.data
            elif isinstance(node_out, dict):
                composite["workflow_result"][node_name] = node_out
            else:
                composite["workflow_result"][node_name] = str(node_out)

        return NodeOutput(success=True, data={
            "composite": composite,
            "output_format": output_format,
            "node_count": len(nodes_output),
        })


# ── WorkflowPipeline ─────────────────────────────────────────────────────────


class WorkflowPipeline:
    """Chain multiple workflow nodes together into a pipeline.

    Nodes execute in order; each node's output becomes part of the
    context passed to the next node.
    """

    def __init__(self, name: str = "pipeline", description: str = ""):
        self.name = name
        self.description = description
        self.nodes: list[WorkflowNode] = []
        self._context: dict[str, Any] = {}
        self._results: dict[str, NodeOutput] = {}

    def add_node(self, node: WorkflowNode) -> WorkflowPipeline:
        """Add a node to the pipeline. Returns self for chaining."""
        self.nodes.append(node)
        return self

    def run(self, initial_input: NodeInput | dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute the pipeline: run each node in sequence.

        Each node receives the accumulated context as input.
        Returns dict with all results and final output.
        """
        if initial_input is None:
            initial_input = NodeInput()
        elif isinstance(initial_input, dict):
            initial_input = NodeInput(data=initial_input)

        self._context = dict(initial_input.data)
        self._results = {}
        pipeline_start = time.time()

        logger.info(f"Pipeline '{self.name}' starting with {len(self.nodes)} nodes")

        for i, node in enumerate(self.nodes):
            node.reset()
            node_in = NodeInput(data=dict(self._context))
            t0 = time.time()
            node_out = node(node_in)
            elapsed = (time.time() - t0) * 1000

            self._results[node.name] = node_out
            self._context[f"_{node.name}_output"] = node_out.data
            # Also merge node output into context for downstream nodes
            if node_out.success and node_out.data:
                self._context.update(node_out.data)

            status = "✅" if node_out.success else "❌"
            logger.info(f"  [{i+1}/{len(self.nodes)}] {status} {node.name} ({elapsed:.0f}ms)")
            if not node_out.success:
                logger.error(f"    Error: {node_out.error}")
                break

        pipeline_elapsed = (time.time() - pipeline_start) * 1000

        # Build final result
        all_success = all(n.success for n in self._results.values())

        # Gather final output from the last successful node's data
        final_data = {}
        last_node_name = list(self.nodes[-1].name for _ in [1])[0] if self.nodes else ""
        if last_node_name and last_node_name in self._results:
            last_out = self._results[last_node_name]
            if last_out.success and last_out.data:
                final_data = last_out.data

        return {
            "pipeline": self.name,
            "success": all_success,
            "total_nodes": len(self.nodes),
            "completed_nodes": len(self._results),
            "duration_ms": round(pipeline_elapsed, 1),
            "node_results": {
                name: out.to_dict() for name, out in self._results.items()
            },
            "final_output": final_data,
        }

    def _build_final_output(self) -> dict[str, Any]:
        """Build the final aggregated output from all node results."""
        output = {}
        for name, node_out in self._results.items():
            if node_out.success and node_out.data:
                for key, val in node_out.data.items():
                    if not key.startswith("_"):  # Skip internal context vars
                        output[f"{name}_{key}"] = val
        return output

    def get_result(self, node_name: str) -> NodeOutput | None:
        """Get result from a specific node."""
        return self._results.get(node_name)

    def summary(self) -> str:
        """Return a human-readable pipeline summary."""
        lines = [f"Pipeline: {self.name} ({self.description})"]
        lines.append(f"Nodes: {len(self.nodes)}")
        for node in self.nodes:
            result = self._results.get(node.name)
            status = "✅" if result and result.success else "⏳" if result is None else "❌"
            lines.append(f"  {status} {node.name}")
        if self._results:
            all_ok = all(n.success for n in self._results.values())
            lines.append(f"Status: {'✅ ALL PASS' if all_ok else '❌ FAILED'}")
        return "\n".join(lines)


# ── Preset Workflows ─────────────────────────────────────────────────────────


def build_ecommerce_workflow(product: str = "产品", tagline: str = "") -> WorkflowPipeline:
    """电商主图生成工作流"""
    pipeline = WorkflowPipeline(
        name="ecommerce_main_image",
        description="电商主图生成: 产品描述 → 风格化 → 合成",
    )

    # Node 1: TextNode — format product text
    text_node = TextNode(name="product_text")
    text_node.input_schema = {
        "type": "object",
        "properties": {
            "product": {"type": "string"},
            "tagline": {"type": "string"},
        },
        "required": ["product"],
    }

    def text_process(self, node_input: NodeInput) -> NodeOutput:
        product = node_input.get("product", "")
        tagline = node_input.get("tagline", "")
        full_text = f"{product}"
        if tagline:
            full_text += f" | {tagline}"
        # Generate image prompt from product info
        prompt = f"电商主图展示: {product}"
        if tagline:
            prompt += f", 标语: {tagline}"
        prompt += ", 产品居中展示, 高清, 商业摄影风格, 纯色背景"
        # Build elements for composition
        elements = {
            "产品主体": f"{product}，居中放置",
        }
        if tagline:
            elements["标语文字"] = f"{tagline}，置于底部或侧边"
        return NodeOutput(success=True, data={
            "product": product,
            "tagline": tagline,
            "full_title": full_text,
            "prompt": prompt,
            "elements": elements,
            "background": "纯色渐变背景，干净简约",
        })
    import types
    text_node.process = types.MethodType(text_process, text_node)

    pipeline.add_node(text_node)

    # Node 2: ImageGenNode — generate image description
    image_node = ImageGenNode(name="ecommerce_image_gen")
    pipeline.add_node(image_node)

    # Node 3: CompositionNode — compose scene with product info
    comp_node = CompositionNode(name="ecommerce_layout")
    pipeline.add_node(comp_node)

    return pipeline


def build_storyboard_workflow(script: str = "") -> WorkflowPipeline:
    """视频脚本→分镜工作流"""
    pipeline = WorkflowPipeline(
        name="video_script_to_storyboard",
        description="视频脚本转换为分镜头描述",
    )

    # Node 1: Parse script into scenes
    def parse_script(self, node_input: NodeInput) -> NodeOutput:
        text = node_input.get("text", node_input.get("script", ""))
        import re
        scenes = [s.strip() for s in re.split(r'[。！？\n]+', text) if s.strip()]
        if not scenes:
            scenes = [text]
        panels = []
        for i, scene in enumerate(scenes):
            panels.append({
                "panel_id": f"P{i+1:02d}",
                "sequence": i + 1,
                "description": scene,
                "shot_size": "中景(MS)" if len(scene) < 20 else "远景(LS)",
                "camera_angle": "平视",
                "duration_sec": max(2.0, min(8.0, len(scene) * 0.3)),
            })
        # Build content and style_ref for StyleTransferNode
        content = " | ".join(s[:30] for s in scenes[:3])
        return NodeOutput(success=True, data={
            "script": text,
            "panels": panels,
            "panel_count": len(panels),
            "total_duration_sec": sum(p["duration_sec"] for p in panels),
            "content": f"故事板分镜: {content}",
            "style_ref": "影视级",
        })

    script_parser = TextNode(name="script_parser")
    script_parser.process = types.MethodType(parse_script, script_parser)
    pipeline.add_node(script_parser)

    # Node 2: Style transfer for each panel
    style_node = StyleTransferNode(name="panel_styling")
    pipeline.add_node(style_node)

    return pipeline


def build_brand_style_workflow(
    content: str = "", style_ref: str = "日系"
) -> WorkflowPipeline:
    """品牌风格迁移工作流"""
    pipeline = WorkflowPipeline(
        name="brand_style_transfer",
        description="品牌风格迁移: 内容 → 品牌风格适配",
    )

    # Node 1: Text analysis
    text_node = TextNode(name="content_analysis")
    pipeline.add_node(text_node)

    # Node 2: Style transfer
    style_node = StyleTransferNode(name="brand_styling")
    pipeline.add_node(style_node)

    return pipeline


# ── Preset Registry ──────────────────────────────────────────────────────────


PRESETS: dict[str, dict[str, Any]] = {
    "ecommerce": {
        "name": "电商主图生成",
        "description": "电商产品主图全自动生成: 产品信息 → 风格化 → 合成输出",
        "default_params": {"product": "智能手表", "tagline": "科技改变生活"},
        "build": lambda params: build_ecommerce_workflow(
            product=params.get("product", "产品"),
            tagline=params.get("tagline", ""),
        ),
    },
    "storyboard": {
        "name": "脚本→分镜转换",
        "description": "将视频脚本文本转换为结构化分镜头描述",
        "default_params": {"script": "一只小猫在花园里追逐蝴蝶"},
        "build": lambda params: build_storyboard_workflow(
            script=params.get("script", params.get("text", ""))
        )
    },
    "brand_style": {
        "name": "品牌风格迁移",
        "description": "将内容按目标品牌风格进行视觉迁移",
        "default_params": {"content": "产品展示页面", "style_ref": "日系"},
        "build": lambda params: build_brand_style_workflow(
            content=params.get("content", ""),
            style_ref=params.get("style_ref", "日系"),
        ),
    },
}


def list_presets() -> dict[str, str]:
    """List all available workflow presets."""
    return {
        name: f"{info['name']} — {info['description']}"
        for name, info in PRESETS.items()
    }


def run_preset(preset_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build and run a preset workflow by name."""
    if preset_name not in PRESETS:
        available = list(PRESETS.keys())
        return {"error": f"Unknown preset '{preset_name}'. Available: {available}"}

    preset = PRESETS[preset_name]
    merged_params = dict(preset["default_params"])
    if params:
        merged_params.update(params)

    pipeline = preset["build"](merged_params)
    result = pipeline.run(NodeInput(data=merged_params))
    result["preset"] = preset_name
    result["preset_name"] = preset["name"]
    result["params_used"] = merged_params
    return result


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Vibe Workflow — Creative Workflow Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--preset", "-p",
        choices=list(PRESETS.keys()) + ["list"],
        help="Workflow preset to run. Use 'list' to show available presets.",
    )
    parser.add_argument(
        "--params", "-P",
        type=str,
        default="{}",
        help='JSON string of parameters for the preset, e.g. \'{"product":"火花思维"}\'',
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="",
        help="Output file path for the result (JSON)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if args.preset == "list":
        presets = list_presets()
        print("Available presets:")
        for name, desc in presets.items():
            print(f"  {name}: {desc}")
        return

    if not args.preset:
        parser.print_help()
        return

    try:
        params = json.loads(args.params)
    except json.JSONDecodeError as e:
        print(f"Error parsing --params JSON: {e}", file=sys.stderr)
        sys.exit(1)

    result = run_preset(args.preset, params)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Result written to {out_path}")

    # Pretty print summary
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
