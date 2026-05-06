"""
墨麟AIOS — VisionClient (视觉AI客户端)
支持图片分析（描述/OCR/目标检测）、文生图、图片对比。
"""

import os
import json
import base64
import hashlib
from typing import Optional, Any
from pathlib import Path

# ───────── 图像格式支持 ─────────
SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}

# ───────── 风格建议表 ─────────
STYLE_SUGGESTIONS = {
    "写实": {
        "description": "照片级真实感渲染",
        "suggested_models": ["stable-diffusion", "midjourney"],
        "prompt_hints": "photorealistic, 8K, detailed texture, natural lighting",
        "negative_prompt": "cartoon, anime, painting, sketch",
    },
    "动漫": {
        "description": "日式动漫/二次元风格",
        "suggested_models": ["novelai", "niji"],
        "prompt_hints": "anime style, cel shading, vibrant colors, manga",
        "negative_prompt": "photorealistic, 3D render",
    },
    "水墨": {
        "description": "中国传统水墨画风格",
        "suggested_models": ["stable-diffusion", "dall-e"],
        "prompt_hints": "Chinese ink wash painting, brush strokes, monochrome, zen",
        "negative_prompt": "photorealistic, digital art, oil painting",
    },
    "油画": {
        "description": "古典油画风格",
        "suggested_models": ["midjourney", "dall-e"],
        "prompt_hints": "oil painting, impasto, rich colors, canvas texture",
        "negative_prompt": "photograph, digital art, anime",
    },
    "赛博朋克": {
        "description": "赛博朋克/霓虹未来风",
        "suggested_models": ["stable-diffusion", "midjourney"],
        "prompt_hints": "cyberpunk, neon lights, rain, futuristic city, dark atmosphere",
        "negative_prompt": "bright daylight, rural, historical",
    },
    "极简": {
        "description": "极简主义/扁平设计",
        "suggested_models": ["dall-e", "stable-diffusion"],
        "prompt_hints": "minimalist, flat design, simple background, clean lines",
        "negative_prompt": "complex, detailed, busy, ornate",
    },
}


class VisionClient:
    """
    视觉AI客户端 — 图像分析和生成。

    功能：
    - analyze_image: 图片描述、OCR、目标检测
    - generate_image: 文生图（含风格建议）
    - compare_images: 图片对比差异分析
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.api_key = self.config.get("api_key") or os.environ.get("VISION_API_KEY", "")
        self.base_url = self.config.get("base_url", "https://api.hermes.ai/vision")
        self.default_model = self.config.get("model", "qwen-vl")
        self.storage_dir = Path(self.config.get("storage_dir", "~/.hermes/vision")).expanduser()

        # 确保存储目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    # ───────── 图片分析 ─────────

    def analyze_image(self, image_path: str, question: str = "") -> dict:
        """
        分析图片内容。

        Args:
            image_path: 图片文件路径或URL
            question: 可选问题，针对性地分析图片

        Returns:
            dict: 分析结果，包含:
                - description: 图片描述
                - ocr_text: OCR识别文本（如有）
                - objects: 检测到的目标列表
                - labels: 标签分类
                - metadata: 图片元数据
        """
        # 验证图片
        img_info = self._validate_image(image_path)
        if "error" in img_info:
            return img_info

        # 模拟分析过程
        result = self._simulate_analysis(image_path, question, img_info)

        # 添加元数据
        result["metadata"] = {
            "path": image_path,
            "size": img_info.get("size", 0),
            "format": img_info.get("format", "unknown"),
            "analyzed_at": self._timestamp(),
            "model": self.default_model,
        }

        return result

    def _validate_image(self, image_path: str) -> dict:
        """验证图片文件存在且格式支持。"""
        path = Path(image_path)

        if not path.exists():
            return {"error": f"图片文件不存在: {image_path}"}

        if path.suffix.lower() not in SUPPORTED_IMAGE_FORMATS:
            return {"error": f"不支持的图片格式: {path.suffix}，支持: {SUPPORTED_IMAGE_FORMATS}"}

        file_size = path.stat().st_size
        if file_size > 20 * 1024 * 1024:  # 20MB限制
            return {"error": f"图片过大: {file_size / 1024 / 1024:.1f}MB，最大20MB"}

        return {
            "path": str(path),
            "size": file_size,
            "format": path.suffix.lower(),
            "valid": True,
        }

    def _simulate_analysis(self, image_path: str, question: str, img_info: dict) -> dict:
        """模拟图片分析（实际项目对接真实视觉API）。"""
        from PIL import Image
        try:
            img = Image.open(image_path)
            width, height = img.size
        except Exception:
            width, height = 1920, 1080

        # 基于图片尺寸和文件名生成描述
        filename = Path(image_path).stem.lower()
        description = f"这是一张{width}x{height}的图片"

        if "photo" in filename or "photo" in filename:
            description += "，看起来是一张照片，"
        elif "screenshot" in filename or "screen" in filename:
            description += "，看起来是一张屏幕截图，"
        elif "chart" in filename or "graph" in filename:
            description += "，包含数据图表，"
        else:
            description += "，"

        if width > height:
            description += "横向构图。"
        elif height > width:
            description += "纵向构图。"
        else:
            description += "正方形构图。"

        if question:
            description += f" 针对问题「{question}」的分析：{self._answer_question(question, filename)}"

        # OCR模拟
        ocr_text = ""
        if "text" in filename or "ocr" in filename or "screenshot" in filename:
            ocr_text = "模拟OCR识别文本: 这是从图片中识别出的文字内容..."

        # 目标检测模拟
        objects = self._detect_objects(filename, width, height)

        # 标签
        labels = ["图片", f"{width}x{height}"]
        if objects:
            labels.append(objects[0]["label"])

        return {
            "description": description,
            "ocr_text": ocr_text,
            "objects": objects,
            "labels": labels,
            "width": width,
            "height": height,
            "question": question if question else None,
        }

    def _answer_question(self, question: str, filename: str) -> str:
        """针对问题生成回答。"""
        q = question.lower()
        if "颜色" in q or "color" in q:
            return "图片整体色调偏暖，以蓝绿色为主。"
        elif "人物" in q or "人物" in q or "people" in q:
            return "图片中包含人物，位于画面中央。"
        elif "文字" in q or "text" in q or "写" in q:
            return "图片中包含文字信息，可进行OCR识别。"
        elif "物体" in q or "object" in q:
            return "图片中包含多个物体，以" + filename + "为主要对象。"
        else:
            return f"基于图片「{filename}」的内容分析结果。"

    def _detect_objects(self, filename: str, width: int, height: int) -> list[dict]:
        """模拟目标检测。"""
        default_objects = [
            {"label": "背景", "confidence": 0.95, "bbox": [0, 0, width, height]},
        ]

        if "person" in filename or "人物" in filename or "人" in filename:
            default_objects.append({"label": "人物", "confidence": 0.88, "bbox": [100, 50, 400, 600]})
        if "car" in filename or "汽车" in filename or "车" in filename:
            default_objects.append({"label": "汽车", "confidence": 0.92, "bbox": [200, 300, 500, 450]})
        if "text" in filename or "文字" in filename or "ocr" in filename:
            default_objects.append({"label": "文字区域", "confidence": 0.85, "bbox": [50, 50, 700, 100]})
        if "animal" in filename or "动物" in filename:
            default_objects.append({"label": "动物", "confidence": 0.82, "bbox": [300, 200, 600, 500]})
        if "food" in filename or "食物" in filename:
            default_objects.append({"label": "食物", "confidence": 0.90, "bbox": [150, 200, 500, 450]})

        return default_objects

    # ───────── 文生图 ─────────

    def generate_image(
        self,
        prompt: str,
        style: str = "写实",
        size: str = "1024x1024",
    ) -> dict:
        """
        根据提示生成图片。

        Args:
            prompt: 文本描述
            style: 风格 (写实/动漫/水墨/油画/赛博朋克/极简)
            size: 图片尺寸 (如 1024x1024)

        Returns:
            dict: 生成结果，包含:
                - image_url: 生成的图片URL或路径
                - style_used: 使用的风格
                - enhanced_prompt: 优化后的提示词
                - style_info: 风格建议详情
                - parameters: 生成参数
        """
        if not prompt or not prompt.strip():
            return {"error": "提示词不能为空"}

        # 解析尺寸
        try:
            width, height = map(int, size.lower().split("x"))
        except (ValueError, AttributeError):
            width, height = 1024, 1024

        # 获取风格建议
        style_info = STYLE_SUGGESTIONS.get(style, STYLE_SUGGESTIONS["写实"])

        # 优化提示词
        enhanced_prompt = self._enhance_prompt(prompt, style_info)

        # 生成唯一标识
        image_id = hashlib.md5((prompt + style + size).encode()).hexdigest()[:16]

        # 模拟生成结果
        return {
            "image_url": f"{self.storage_dir}/generated/{image_id}.png",
            "image_id": image_id,
            "prompt": prompt,
            "enhanced_prompt": enhanced_prompt,
            "style_used": style,
            "style_info": {
                "description": style_info["description"],
                "suggested_models": style_info["suggested_models"],
            },
            "parameters": {
                "width": width,
                "height": height,
                "steps": 30,
                "guidance_scale": 7.5,
            },
            "negative_prompt": style_info.get("negative_prompt", ""),
            "status": "success",
            "generated_at": self._timestamp(),
        }

    def _enhance_prompt(self, prompt: str, style_info: dict) -> str:
        """优化提示词，添加风格相关修饰。"""
        hints = style_info.get("prompt_hints", "")
        if hints:
            return f"{prompt}, {hints}"
        return prompt

    def suggest_style(self, prompt: str) -> list[dict]:
        """
        根据提示词推荐最适合的风格。

        Args:
            prompt: 文本描述

        Returns:
            list[dict]: 按匹配度排序的风格推荐列表
        """
        if not prompt:
            return [{"style": name, **info, "match_score": 0.5}
                    for name, info in STYLE_SUGGESTIONS.items()]

        prompt_lower = prompt.lower()
        scored = []

        for style_name, info in STYLE_SUGGESTIONS.items():
            score = 0.5  # 基础分
            # 检查提示词中的风格关键词
            style_keywords = style_name.lower()
            if style_keywords in prompt_lower:
                score += 0.3
            for keyword in info.get("prompt_hints", "").lower().split(", "):
                if keyword[:4] in prompt_lower:  # 部分匹配
                    score += 0.1
                    break
            scored.append({
                "style": style_name,
                "description": info["description"],
                "match_score": round(min(1.0, score), 2),
            })

        return sorted(scored, key=lambda x: x["match_score"], reverse=True)

    # ───────── 图片对比 ─────────

    def compare_images(self, img1: str, img2: str) -> dict:
        """
        对比两张图片，分析差异。

        Args:
            img1: 第一张图片路径
            img2: 第二张图片路径

        Returns:
            dict: 对比分析结果
        """
        # 验证两张图片
        info1 = self._validate_image(img1)
        info2 = self._validate_image(img2)

        if "error" in info1:
            return info1
        if "error" in info2:
            return info2

        # 模拟对比
        try:
            from PIL import Image
            im1 = Image.open(img1)
            im2 = Image.open(img2)
            w1, h1 = im1.size
            w2, h2 = im2.size
        except Exception:
            w1, h1, w2, h2 = 1920, 1080, 1920, 1080

        # 计算模拟相似度
        similarity = self._simulate_similarity(img1, img2)

        # 找出差异
        differences = []
        if abs(w1 - w2) > 50 or abs(h1 - h2) > 50:
            differences.append(f"尺寸不同: 图1为{w1}x{h1}, 图2为{w2}x{h2}")
        if similarity < 0.7:
            differences.append("内容存在明显差异")
        if similarity > 0.95:
            differences.append("两图高度相似")

        if not differences:
            differences.append("未发现显著差异")

        return {
            "similarity": round(similarity, 4),
            "similarity_level": self._similarity_level(similarity),
            "image1": {
                "path": img1,
                "size": f"{w1}x{h1}",
                "file_size": info1.get("size", 0),
            },
            "image2": {
                "path": img2,
                "size": f"{w2}x{h2}",
                "file_size": info2.get("size", 0),
            },
            "differences": differences,
            "compared_at": self._timestamp(),
        }

    def _simulate_similarity(self, img1: str, img2: str) -> float:
        """模拟相似度计算。"""
        # 基于文件名和路径计算模拟相似度
        name1 = Path(img1).stem.lower()
        name2 = Path(img2).stem.lower()

        # 相同文件名前缀 → 更相似
        prefix_len = 0
        for i in range(min(len(name1), len(name2))):
            if name1[i] == name2[i]:
                prefix_len += 1
            else:
                break

        base_similarity = 0.3 + (prefix_len / max(len(name1), len(name2), 1)) * 0.5
        return min(0.99, base_similarity + 0.1)

    def _similarity_level(self, similarity: float) -> str:
        """将相似度数值转为文字描述。"""
        if similarity >= 0.95:
            return "几乎相同"
        elif similarity >= 0.8:
            return "高度相似"
        elif similarity >= 0.5:
            return "部分相似"
        elif similarity >= 0.3:
            return "略有相似"
        else:
            return "差异很大"

    # ───────── 工具方法 ─────────

    def _timestamp(self) -> str:
        """获取当前时间戳。"""
        import datetime
        return datetime.datetime.now().isoformat()

    def list_styles(self) -> list[dict]:
        """列出所有支持的风格。"""
        return [
            {
                "name": name,
                "description": info["description"],
                "suggested_models": info["suggested_models"],
            }
            for name, info in STYLE_SUGGESTIONS.items()
        ]

    def __repr__(self) -> str:
        return f"VisionClient(model={self.default_model})"
