"""
墨麟AIOS — ModelRouter (LLM路由引擎)
参考 Google ADK Agent评估 & LLM路由思路，实现6级路由表。
根据任务复杂度、类型、预算自动选择最优模型。
"""

import re
import math
from typing import Optional

# ───────── 6级路由表 ─────────
MODEL_TABLE = {
    "qwen-turbo": {
        "cost_per_1k_input": 0.0003,   # ¥0.0003/1K tokens
        "cost_per_1k_output": 0.0006,
        "price_per_call": 0.012,
        "max_tokens": 32768,
        "complexity_range": (0, 25),
        "capabilities": {"text", "reasoning_basic"},
        "provider": "qwen",
    },
    "qwen-plus": {
        "cost_per_1k_input": 0.0008,
        "cost_per_1k_output": 0.002,
        "price_per_call": 0.04,
        "max_tokens": 131072,
        "complexity_range": (26, 50),
        "capabilities": {"text", "reasoning_intermediate", "code", "tool_use"},
        "provider": "qwen",
    },
    "qwen-long": {
        "cost_per_1k_input": 0.001,
        "cost_per_1k_output": 0.002,
        "price_per_call": 0.06,
        "max_tokens": 10000000,
        "complexity_range": (51, 75),
        "capabilities": {"text", "long_context", "reasoning_intermediate", "code"},
        "provider": "qwen",
    },
    "qwen-max": {
        "cost_per_1k_input": 0.002,
        "cost_per_1k_output": 0.008,
        "price_per_call": 0.12,
        "max_tokens": 32768,
        "complexity_range": (76, 100),
        "capabilities": {"text", "reasoning_advanced", "code", "tool_use", "agentic"},
        "provider": "qwen",
    },
    "qwen-vl": {
        "cost_per_1k_input": 0.0015,
        "cost_per_1k_output": 0.0045,
        "price_per_call": 0.02,
        "max_tokens": 8192,
        "complexity_range": (0, 100),
        "capabilities": {"vision", "ocr", "text", "reasoning_basic"},
        "provider": "qwen",
    },
    "deepseek-chat": {
        "cost_per_1k_input": 0.00014,
        "cost_per_1k_output": 0.00028,
        "price_per_call": 0.014,
        "max_tokens": 65536,
        "complexity_range": (0, 60),
        "capabilities": {"text", "code", "reasoning_intermediate", "tool_use"},
        "provider": "deepseek",
    },
}

# ───────── 复杂度信号权重 ─────────
COMPLEXITY_SIGNALS = [
    # (pattern, weight, max_boost)
    (r"\b(architecture|design|plan|strategy)\b", 10, 30),
    (r"\b(analyze|compare|contrast|evaluate|critique)\b", 8, 25),
    (r"\b(code|function|class|algorithm|debug|refactor)\b", 6, 20),
    (r"\b(optimize|performance|scalable|distributed)\b", 7, 20),
    (r"\b(summarize|explain|describe|list)\b", -5, -15),
    (r"\b(hello|hi|who are you|simple)\b", -10, -20),
    (r"(\d{4,})", 3, 10),       # long numbers → complexity
    (r"\b(agent|multi.?step|workflow|orchestrat)\b", 12, 30),
    (r"\b(translate|rewrite|grammar|spelling)\b", 2, 8),
    (r"\b(image|photo|picture|vision|visual|diagram)\b", 5, 15),
]

TASK_TYPE_KEYWORDS = {
    "vision": [r"\b(image|photo|picture|vision|ocr|visual|diagram|screenshot|chart)\b"],
    "code": [r"\b(code|function|class|python|javascript|bug|debug|refactor|api)\b"],
    "long_context": [r"\b(summarize long|large document|book|paper|report|10k)\b"],
    "creative": [r"\b(write|story|poem|essay|create|draft|content)\b"],
    "analysis": [r"\b(analyze|compare|evaluate|review|assess|audit)\b"],
    "reasoning": [r"\b(reason|logic|math|puzzle|solve|plan|strategy|decision)\b"],
    "chat": [r"\b(chat|talk|conversation|问答|帮助)\b"],
}


class ModelRouter:
    """LLM路由引擎 — 根据任务复杂度、类型和预算选择最佳模型。"""

    def __init__(self, model_table: Optional[dict] = None):
        self.model_table = model_table or MODEL_TABLE
        self._signal_cache: dict[str, int] = {}

    # ───────── 复杂度评分 ─────────

    def complexity_score(self, task_description: str) -> int:
        """
        评估任务复杂度 (0-100)。
        基于关键词信号加权、长度因子、特殊模式识别。
        """
        if not task_description or not task_description.strip():
            return 10

        text = task_description.lower()
        score = 20  # 基础分

        # 1. 关键词信号加权
        for pattern, weight, max_boost in COMPLEXITY_SIGNALS:
            matches = re.findall(pattern, text)
            if matches:
                boost = weight * min(len(matches), 3)
                boost = max(-abs(max_boost), min(boost, abs(max_boost)))
                score += boost

        # 2. 长度因子 — 长文本通常更复杂
        word_count = len(text.split())
        if word_count > 100:
            score += 5
        if word_count > 300:
            score += 8
        if word_count > 1000:
            score += 10

        # 3. 特殊句式 — 多步骤/条件
        if "step" in text and ("first" in text or "then" in text or "finally" in text):
            score += 8
        if "if" in text and "then" in text:
            score += 5
        if "not only" in text and "but also" in text:
            score += 3

        # 4. 数字/数据复杂度
        data_patterns = len(re.findall(r"\b\d+[.,]?\d*\b", text))
        if data_patterns > 10:
            score += 5

        return max(0, min(100, int(score)))

    # ───────── 任务类型检测 ─────────

    def detect_task_type(self, task_description: str) -> str:
        """检测任务类型：vision / code / long_context / creative / analysis / reasoning / chat"""
        text = task_description.lower()
        task_scores = {}
        for task_type, patterns in TASK_TYPE_KEYWORDS.items():
            score = 0
            for pat in patterns:
                matches = re.findall(pat, text)
                score += len(matches) * 2
                if matches:
                    score += 3  # 命中奖励
            task_scores[task_type] = score

        if not any(task_scores.values()):
            return "chat"

        # 视觉任务优先
        if task_scores.get("vision", 0) >= 3:
            return "vision"

        return max(task_scores, key=task_scores.get)

    # ───────── 模型选择 ─────────

    def select_model(
        self,
        complexity: int,
        task_type: str = "chat",
        budget: Optional[float] = None,
        preferred_provider: Optional[str] = None,
    ) -> dict:
        """
        根据复杂度、任务类型和预算选择最优模型。

        Args:
            complexity: 复杂度评分 0-100
            task_type: 任务类型
            budget: 预算上限 (¥)
            preferred_provider: 首选供应商

        Returns:
            dict: {model, provider, cost, reason, capabilities}
        """
        # 1. 视觉任务特殊路由
        if task_type == "vision":
            model_info = self.model_table.get("qwen-vl")
            if model_info and (budget is None or model_info["price_per_call"] <= budget):
                return {
                    "model": "qwen-vl",
                    "provider": "qwen",
                    "cost": model_info["price_per_call"],
                    "reason": "视觉任务 → qwen-vl (¥0.02)",
                    "capabilities": list(model_info["capabilities"]),
                }

        # 2. 常规文本模型筛选
        candidates = []
        for model_name, info in self.model_table.items():
            if model_name == "qwen-vl":
                continue  # 视觉模型不由文本路由选择
            if task_type == "long_context" and info["max_tokens"] < 100000:
                continue  # 长上下文任务需要大窗口
            low, high = info["complexity_range"]
            if low <= complexity <= high:
                candidates.append((model_name, info))

        if not candidates:
            # fallback: 找最接近的
            candidates = []
            for model_name, info in self.model_table.items():
                if model_name == "qwen-vl":
                    continue
                low, high = info["complexity_range"]
                # 计算距离
                dist = 0
                if complexity < low:
                    dist = low - complexity
                elif complexity > high:
                    dist = complexity - high
                candidates.append((dist, model_name, info))
            candidates.sort(key=lambda x: x[0])
            _, model_name, info = candidates[0]
        else:
            # 按价格排序（预算优先时选便宜、否则选最强）
            if budget is not None:
                candidates = [c for c in candidates if c[1]["price_per_call"] <= budget]
            if not candidates:
                # 预算不足，选最便宜的
                candidates = sorted(candidates if candidates else
                                    [(n, i) for n, i in self.model_table.items() if n != "qwen-vl"],
                                    key=lambda x: x[1]["price_per_call"])
                model_name, info = candidates[0]
                reason = f"预算¥{budget}不足，选择最便宜模型"
            else:
                # 选最适合复杂度的
                candidates.sort(key=lambda x: abs(complexity - (x[1]["complexity_range"][0] + x[1]["complexity_range"][1]) / 2))
                model_name, info = candidates[0]
                low, high = info["complexity_range"]
                reason = f"复杂度{complexity}匹配范围[{low}-{high}]"

        # 3. 首选供应商偏好
        if preferred_provider and info["provider"] != preferred_provider:
            for alt_name, alt_info in self.model_table.items():
                if alt_name != "qwen-vl" and alt_info["provider"] == preferred_provider:
                    alt_low, alt_high = alt_info["complexity_range"]
                    if alt_low <= complexity <= alt_high:
                        model_name, info = alt_name, alt_info
                        reason = f"首选供应商{preferred_provider}匹配"
                        break

        return {
            "model": model_name,
            "provider": info["provider"],
            "cost": info["price_per_call"],
            "reason": reason if 'reason' in dir() else f"复杂度{complexity} → {model_name}",
            "capabilities": list(info["capabilities"]),
            "max_tokens": info["max_tokens"],
        }

    # ───────── 成本估算 ─────────

    def estimate_cost(self, model: str, tokens: int) -> float:
        """
        估算模型调用成本 (¥)。

        Args:
            model: 模型名称
            tokens: token数量

        Returns:
            float: 估算成本 (人民币)
        """
        info = self.model_table.get(model)
        if not info:
            return 0.0

        input_cost = (tokens / 1000) * info["cost_per_1k_input"]
        output_cost = (tokens / 1000) * info["cost_per_1k_output"]
        total = input_cost + output_cost

        # 保底：不低于单次调用价格
        return round(max(total, info["cost_per_1k_input"] * 0.5), 6)

    # ───────── 一键路由 ─────────

    def route(self, task_description: str, budget: Optional[float] = None) -> dict:
        """
        一键路由：复杂度评估 → 类型检测 → 模型选择。

        Args:
            task_description: 任务描述
            budget: 预算上限

        Returns:
            dict: {complexity, task_type, model, provider, cost, reason, ...}
        """
        complexity = self.complexity_score(task_description)
        task_type = self.detect_task_type(task_description)
        selection = self.select_model(complexity, task_type, budget)

        return {
            "complexity": complexity,
            "task_type": task_type,
            **selection,
        }

    # ───────── 工具方法 ─────────

    def list_models(self, task_type: Optional[str] = None) -> list[dict]:
        """列出可用模型及其规格。"""
        results = []
        for name, info in self.model_table.items():
            if task_type and task_type not in info["capabilities"]:
                continue
            results.append({
                "model": name,
                "provider": info["provider"],
                "price": info["price_per_call"],
                "max_tokens": info["max_tokens"],
                "complexity_range": info["complexity_range"],
                "capabilities": list(info["capabilities"]),
            })
        return sorted(results, key=lambda x: x["price"])


# ───────── 便捷函数 ─────────
def create_router() -> ModelRouter:
    """创建默认路由实例。"""
    return ModelRouter()
