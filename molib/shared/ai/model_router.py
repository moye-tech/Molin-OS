"""
墨麟AIOS — ModelRouter (LLM路由引擎)
基于 models.toml 配置驱动的智能模型路由 + 6级复杂度路由 + BudgetGuard 成本熔断。

从 models.toml 读取模型配置（若不存在则使用内置默认值）。
支持 deepseek- 前缀自动识别并路由至 DeepSeek V4 系列。
支持 prefix cache（前缀缓存）以降低长 system prompt 成本。
"""

import os
import re
import math
import tomllib
from pathlib import Path
from typing import Optional

# ── 配置加载 ──────────────────────────────────────────────────────

def _load_models_toml() -> dict:
    """尝试加载 models.toml，失败时返回空"""
    paths = [
        Path(os.getcwd()) / "config" / "models.toml",
        Path.home() / ".hermes" / "models.toml",
    ]
    for p in paths:
        if p.exists():
            with open(p, "rb") as f:
                return tomllib.load(f)
    return {}


def _config_to_model_table(config: dict) -> dict:
    """将 models.toml 的配置转为统一模型表"""
    table = {}
    for key, cfg in config.items():
        # 跳过 strategy 段（路由策略，不是模型）
        if key == "strategy":
            continue
        table[key] = {
            "cost_per_1k_input": cfg.get("cost_input", 0.0004),
            "cost_per_1k_output": cfg.get("cost_output", 0.0014),
            "max_tokens": cfg.get("max_tokens", 65536),
            "complexity_range": cfg.get("complexity_range", (0, 100)),
            "capabilities": set(cfg.get("capabilities", ["text"])),
            "provider": cfg.get("provider", "deepseek"),
            "display_name": cfg.get("display_name", key),
            "description": cfg.get("description", ""),
        }
    return table


# ── 内置默认模型表 ─────────────────────────────────────────────
BUILTIN_MODEL_TABLE = {
    "deepseek-v4-flash": {
        "cost_per_1k_input": 0.00014,
        "cost_per_1k_output": 0.00028,
        "max_tokens": 65536,
        "complexity_range": (0, 40),
        "capabilities": {"text", "code", "reasoning_basic", "tool_use"},
        "provider": "deepseek",
        "display_name": "DeepSeek V4 Flash",
        "description": "轻量快速，适合简单任务",
    },
    "deepseek-v4-pro": {
        "cost_per_1k_input": 0.0004,
        "cost_per_1k_output": 0.0014,
        "max_tokens": 131072,
        "complexity_range": (41, 100),
        "capabilities": {"text", "code", "reasoning_advanced", "tool_use", "agentic"},
        "provider": "deepseek",
        "display_name": "DeepSeek V4 Pro",
        "description": "高性能主力模型，适合复杂推理、LLM合成",
    },
    "qwen3-vl-plus": {
        "cost_per_1k_input": 0.0015,
        "cost_per_1k_output": 0.0045,
        "max_tokens": 8192,
        "complexity_range": (0, 100),
        "capabilities": {"vision", "ocr", "image_generation", "text", "reasoning_basic"},
        "provider": "qwen",
        "display_name": "Qwen3 VL Plus",
        "description": "图片分析/OCR/封面图/图表理解",
    },
    "happyhorse-t2v": {
        "cost_per_1k_input": 0.01,
        "cost_per_1k_output": 0.02,
        "max_tokens": 4096,
        "complexity_range": (0, 100),
        "capabilities": {"video", "animation", "render"},
        "provider": "qwen",
        "display_name": "HappyHorse-1.0-T2V",
        "description": "视频生成",
    },
}

# ── 复杂度信号权重 ──────────────────────────────────────────────
COMPLEXITY_SIGNALS = [
    (r"\b(architecture|design|plan|strategy|方案|设计|架构|策略)\b", 15, 35),
    (r"\b(analyze|compare|contrast|evaluate|critique|分析|对比|评估|审查)\b", 12, 30),
    (r"\b(code|function|class|algorithm|debug|refactor|开发|编程|代码|实现)\b", 10, 25),
    (r"\b(optimize|performance|scalable|distributed|优化|性能|扩展|分布式)\b", 10, 25),
    (r"\b(summarize|explain|describe|list|总结|解释|描述|列出)\b", -5, -15),
    (r"\b(hello|hi|who are you|simple|早上好|你好|谢谢|再见)\b", -10, -20),
    (r"(\d{4,})", 3, 10),
    (r"\b(agent|multi.?step|workflow|orchestrat|智能体|工作流|编排|多步)\b", 15, 35),
    (r"\b(translate|rewrite|grammar|spelling|翻译|改写|语法)\b", 2, 8),
    (r"\b(image|photo|picture|vision|visual|diagram|screenshot|chart|封面|截图|图片|视觉)\b", 8, 20),
    (r"\b(video|animation|render|clip|短片|短视频|动画|渲染)\b", 10, 25),
]

TASK_TYPE_KEYWORDS = {
    "vision": [r"\b(image|photo|picture|vision|ocr|visual|diagram|screenshot|chart|封面|截图)\b"],
    "video": [r"\b(video|animation|render|clip|短片|短视频|动画|渲染)\b"],
    "code": [r"\b(code|function|class|python|javascript|bug|debug|refactor|api)\b"],
}


class ModelRouter:
    """
    模型路由器 — 根据任务复杂度、类型、预算自动选择最优模型。

    支持:
    - models.toml 配置驱动
    - 6级复杂度路由
    - 自动降级（BudgetGuard 联动）
    - 特定任务类型匹配（code/vision/long_context）
    """

    def __init__(self):
        # 尝试从 models.toml 加载，失败用内置默认
        config = _load_models_toml()
        if config:
            self.model_table = _config_to_model_table(config)
        else:
            self.model_table = dict(BUILTIN_MODEL_TABLE)

        self._model_list = sorted(
            self.model_table.keys(),
            key=lambda m: self.model_table[m]["cost_per_1k_input"],
        )

    def select(self, user_input: str, task_type: Optional[str] = None,
               preferred_provider: Optional[str] = None) -> str:
        """
        选择最佳模型。

        Args:
            user_input: 用户输入文本
            task_type: 指定任务类型 (code/vision/video/None=自动)
            preferred_provider: 首选provider (deepseek/qwen/None=自动)

        Returns:
            str: 模型名称
        """
        # 1. 任务类型强制匹配
        if task_type == "vision":
            for model, info in self.model_table.items():
                if "vision" in info["capabilities"]:
                    return model
        if task_type == "video":
            for model, info in self.model_table.items():
                if "video" in info["capabilities"]:
                    return model

        # 2. 计算复杂度
        complexity = self._calc_complexity(user_input)

        # 3. 筛选符合条件的模型
        candidates = []
        for model, info in self.model_table.items():
            lo, hi = info["complexity_range"]
            if lo <= complexity <= hi:
                if preferred_provider and info["provider"] != preferred_provider:
                    continue
                candidates.append((model, info))

        if not candidates:
            # 兜底 — 最便宜的
            return self._model_list[0] if self._model_list else "deepseek-v4-flash"

        # 4. 按性价比排序：同复杂度选最便宜的
        candidates.sort(key=lambda x: x[1]["cost_per_1k_input"])
        return candidates[0][0]

    def select_with_fallback(self, user_input: str, task_type: Optional[str] = None,
                             preferred_provider: Optional[str] = None,
                             budget_guard: object = None) -> list[str]:
        """
        返回完整的降级链 — [首选, 次选, 兜底]

        Args:
            user_input: 用户输入
            task_type: 任务类型
            preferred_provider: 首选 provider
            budget_guard: BudgetGuard 实例（可选）

        Returns:
            list[str]: 降级链 [最佳, 降级, 兜底]
        """
        best = self.select(user_input, task_type, preferred_provider)

        # 构建降级链：从便宜到贵
        candidates = sorted(
            self.model_table.keys(),
            key=lambda m: self.model_table[m]["cost_per_1k_input"],
        )
        # 确保 best 在链中
        if best not in candidates:
            candidates.insert(0, best)
        else:
            # 移到最前
            candidates.remove(best)
            candidates.insert(0, best)

        # 取前3个作为降级链
        chain = candidates[:3]

        # BudgetGuard 影响：如果主动提示降级
        if budget_guard:
            result = budget_guard.check(best)
            if "flash" in result:
                return [m for m in chain if "flash" in m.lower()] + ["deepseek-v4-flash"]

        return chain

    def get_model_info(self, model_name: str) -> Optional[dict]:
        """获取模型的完整信息"""
        return self.model_table.get(model_name)

    def get_reasoning_model(self) -> str:
        """获取推理专用模型（复杂决策场景）"""
        for model, info in sorted(
            self.model_table.items(),
            key=lambda x: x[1]["cost_per_1k_input"],
            reverse=True,
        ):
            if "reasoning_deep" in info["capabilities"]:
                return model
        return "deepseek-reasoner"

    def get_flash_model(self) -> str:
        """获取最便宜的快速模型"""
        for model, info in sorted(
            self.model_table.items(),
            key=lambda x: x[1]["cost_per_1k_input"],
        ):
            if "flash" in model.lower() or "turbo" in model.lower():
                return model
        return self._model_list[0] if self._model_list else "deepseek-v4-flash"

    def get_vision_model(self) -> str:
        """获取图片分析/生成模型 (qwen3-vl-plus)"""
        for model, info in self.model_table.items():
            if "vision" in info["capabilities"] or "image_generation" in info["capabilities"]:
                return model
        return self._model_list[0] if self._model_list else "qwen3-vl-plus"

    def get_video_model(self) -> str:
        """获取视频生成模型 (HappyHorse-1.0-T2V)"""
        for model, info in self.model_table.items():
            if "video" in info["capabilities"]:
                return model
        return self._model_list[0] if self._model_list else "happyhorse-t2v"

    def list_models(self) -> list[dict]:
        """列出所有可用模型"""
        return [
            {
                "name": name,
                "display_name": info["display_name"],
                "provider": info["provider"],
                "cost_input": info["cost_per_1k_input"],
                "cost_output": info["cost_per_1k_output"],
                "capabilities": list(info["capabilities"]),
                "complexity_range": info["complexity_range"],
                "description": info.get("description", ""),
            }
            for name, info in self.model_table.items()
        ]

    def _calc_complexity(self, text: str) -> float:
        """计算文本复杂度 (0-100)"""
        score = 0.0
        text_lower = text.lower()

        # 长度因子
        length = len(text)
        if length > 200:
            score += 20
        elif length > 100:
            score += 10
        else:
            score += 5

        # 信号模式
        for pattern, weight, max_boost in COMPLEXITY_SIGNALS:
            if re.search(pattern, text, re.IGNORECASE):
                score += min(weight, max_boost)

        return min(round(max(score, 0), 1), 100.0)
