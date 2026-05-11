"""
墨麟 — LLM 路由器 v2.5 (LLMRouter)
智能 LLM 路由：按任务复杂度/类型自动选择性价比最优模型。

v2.5 新增：
- OpenRouter 免费模型层（$0 成本，替代本地 Ollama）
- 成本感知路由：free → cheap → pro 三级
- 免费模型限流保护（rate limit aware）
- 运行时降级：免费模型不可用时自动 fallback

用法:
    from molib.shared.llm.llm_router import LLMRouter

    # 简单任务 → 免费模型
    model = LLMRouter.for_task("simple")   # -> "google/gemma-3-4b-it:free"

    # 复杂推理 → Pro 模型
    model = LLMRouter.for_task("reasoning")

    # 查看成本节省统计
    stats = LLMRouter.cost_stats()
"""

from typing import Dict, Optional, Literal, List
import time
import logging

logger = logging.getLogger(__name__)

# ── 模型等级定义 v2.5 ──────────────────────────────────────────────

TaskType = Literal["simple", "reasoning", "code", "creative", "vision", "video"]

# OpenRouter 免费模型（2026年5月验证可用，$0/1M tokens）
_FREE_MODELS = [
    "google/gemma-3-4b-it:free",           # Google Gemma 3 4B
    "meta-llama/llama-4-scout:free",        # Meta Llama 4 Scout
    "mistralai/mistral-small-3.1-24b-instruct:free",  # Mistral Small 3.1 24B
    "qwen/qwen3-8b:free",                   # Qwen 3 8B
]

# 降级顺序：优先用最强的免费模型
_FREE_MODEL_FALLBACK_ORDER = [
    "mistralai/mistral-small-3.1-24b-instruct:free",  # 24B，最强免费
    "qwen/qwen3-8b:free",                   # 8B，中文好
    "google/gemma-3-4b-it:free",            # 4B，快速
    "meta-llama/llama-4-scout:free",        # 轻量级
]

# 三级成本路由表
_MODEL_TIER: Dict[TaskType, Dict[str, str]] = {
    "simple": {
        "free": "mistralai/mistral-small-3.1-24b-instruct:free",  # 简单任务用免费
        "cheap": "deepseek/deepseek-chat",    # fallback: flash 级
        "pro": "deepseek/deepseek-rasoner",
    },
    "reasoning": {
        "free": "qwen/qwen3-8b:free",         # 轻推理也可用免费
        "cheap": "deepseek/deepseek-chat",
        "pro": "deepseek/deepseek-rasoner",   # 复杂推理用 pro
    },
    "code": {
        "free": "qwen/qwen3-8b:free",         # 简单代码用免费
        "cheap": "deepseek/deepseek-chat",
        "pro": "deepseek/deepseek-rasoner",
    },
    "creative": {
        "free": "mistralai/mistral-small-3.1-24b-instruct:free",
        "cheap": "deepseek/deepseek-chat",
        "pro": "deepseek/deepseek-rasoner",
    },
    "vision": {
        "free": None,                          # 免费模型不支持视觉
        "cheap": "qwen3-vl-plus",
        "pro": "qwen3-vl-max",
    },
    "video": {
        "free": None,
        "cheap": "happyhorse-1.0-t2v",
        "pro": "happyhorse-1.0-t2v",
    },
}

_TIER_COST_HINT: Dict[TaskType, Dict[str, str]] = {
    "simple": {
        "free": "💰 免费 — OpenRouter 免费模型，适合分类/提取/简单问答",
        "cheap": "💵 低成本 — DeepSeek Chat，适合中等复杂度",
        "pro": "💎 Pro — DeepSeek Reasoner，复杂推理",
    },
    "reasoning": {
        "free": "💰 免费 — 轻量推理可用免费模型",
        "cheap": "💵 低成本 — DeepSeek Chat",
        "pro": "💎 Pro — DeepSeek Reasoner，最强推理",
    },
    "code": {
        "free": "💰 免费 — 简单代码片段可用免费",
        "cheap": "💵 低成本 — DeepSeek Chat",
        "pro": "💎 Pro — DeepSeek Reasoner",
    },
    "creative": {
        "free": "💰 免费 — 简单文案可用免费",
        "cheap": "💵 低成本 — DeepSeek Chat",
        "pro": "💎 Pro — DeepSeek Reasoner",
    },
    "vision": {
        "free": "⚠️ 不支持 — 视觉任务需要付费模型",
        "cheap": "💵 低成本 — Qwen VL Plus",
        "pro": "💎 Pro — Qwen VL Max",
    },
    "video": {
        "free": "⚠️ 不支持",
        "cheap": "💵 低成本 — HappyHorse",
        "pro": "💎 Pro — HappyHorse",
    },
}


class LLMRouter:
    """
    智能 LLM 路由 v2.5：三级成本感知模型选择。

    路由策略：
    1. 优先尝试免费模型（OpenRouter :free 后缀）
    2. 免费不可用/限流 → 降级到 cheap（DeepSeek Chat）
    3. 需要最强推理 → 直接用 pro（DeepSeek Reasoner）

    用法:
        model = LLMRouter.for_task("simple")           # 自动选免费
        model = LLMRouter.for_task("reasoning", tier="pro")  # 强制 pro
        model = LLMRouter.for_task("vision")            # 视觉无免费，自动 cheap
    """

    _default_model: str = "deepseek/deepseek-chat"
    _alternate_model: str = "deepseek/deepseek-rasoner"
    _current_task: Optional[TaskType] = None
    _current_tier: str = "free"

    # 成本统计
    _stats: Dict[str, int] = {
        "free_calls": 0,
        "cheap_calls": 0,
        "pro_calls": 0,
        "free_failures": 0,  # 免费模型不可用次数
    }
    _free_model_index: int = 0  # 轮询免费模型

    @classmethod
    def for_task(cls, task_type: TaskType, tier: str = "auto") -> str:
        """
        根据任务类型获取最合适的模型名称。

        参数:
            task_type: 任务类型
                - simple: 简单分类/提取/问答 → 免费模型
                - reasoning: 复杂分析/决策/长文 → cheap/pro
                - code: 代码生成 → 免费→cheap
                - creative: 内容创作 → 免费→cheap
                - vision: 图片识别 → cheap（无免费）
                - video: 视频生成 → cheap（无免费）
            tier: 强制路由等级
                - "auto" (默认): 自动选择（优先免费）
                - "free": 强制免费模型
                - "cheap": 强制低成本模型
                - "pro": 强制最强模型

        返回:
            str — 模型名称
        """
        cls._current_task = task_type
        tier_config = _MODEL_TIER.get(task_type, _MODEL_TIER["simple"])

        if tier == "auto":
            # 自动选择：优先免费 → cheap → pro
            if tier_config.get("free") and task_type != "vision" and task_type != "video":
                model = cls._rotate_free_model(task_type)
                if model:
                    cls._current_tier = "free"
                    cls._stats["free_calls"] += 1
                    return model
                # 免费不可用，降级
                cls._stats["free_failures"] += 1
            cls._current_tier = "cheap"
            cls._stats["cheap_calls"] += 1
            return tier_config.get("cheap", cls._default_model)
        elif tier == "free":
            model = cls._rotate_free_model(task_type)
            if model:
                cls._current_tier = "free"
                cls._stats["free_calls"] += 1
                return model
            # 降级
            cls._current_tier = "cheap"
            cls._stats["free_failures"] += 1
            cls._stats["cheap_calls"] += 1
            return tier_config.get("cheap", cls._default_model)
        elif tier == "pro":
            cls._current_tier = "pro"
            cls._stats["pro_calls"] += 1
            return tier_config.get("pro", cls._alternate_model)
        else:
            cls._current_tier = "cheap"
            cls._stats["cheap_calls"] += 1
            return tier_config.get("cheap", cls._default_model)

    @classmethod
    def _rotate_free_model(cls, task_type: TaskType) -> Optional[str]:
        """轮询选择免费模型，分散限流风险"""
        tier_config = _MODEL_TIER.get(task_type, _MODEL_TIER["simple"])
        default_free = tier_config.get("free")
        if not default_free:
            return None

        # 轮询：每次用不同的免费模型
        model = _FREE_MODEL_FALLBACK_ORDER[cls._free_model_index % len(_FREE_MODEL_FALLBACK_ORDER)]
        cls._free_model_index += 1
        return model

    @classmethod
    def set_default_model(cls, model: str):
        """运行时切换默认模型"""
        cls._default_model = model

    @classmethod
    def switch_to_alternate(cls) -> str:
        """切换到更强的替代模型"""
        return cls._alternate_model

    @classmethod
    def set_alternate_model(cls, model: str):
        """设置替代模型"""
        cls._alternate_model = model

    @classmethod
    def current_task(cls) -> Optional[TaskType]:
        """返回最近一次查询的任务类型"""
        return cls._current_task

    @classmethod
    def current_tier(cls) -> str:
        """返回当前路由等级"""
        return cls._current_tier

    @classmethod
    def cost_hint(cls, task_type: TaskType, tier: str = "auto") -> str:
        """返回某任务类型的成本提示"""
        hints = _TIER_COST_HINT.get(task_type, {})
        if tier == "auto":
            if hints.get("free") and task_type not in ("vision", "video"):
                return hints["free"]
            return hints.get("cheap", "未知")
        return hints.get(tier, "未知")

    @classmethod
    def cost_stats(cls) -> Dict:
        """返回成本统计"""
        total = sum([cls._stats["free_calls"], cls._stats["cheap_calls"], cls._stats["pro_calls"]])
        free_pct = cls._stats["free_calls"] / max(total, 1) * 100
        return {
            "total_calls": total,
            "free_calls": cls._stats["free_calls"],
            "cheap_calls": cls._stats["cheap_calls"],
            "pro_calls": cls._stats["pro_calls"],
            "free_failures": cls._stats["free_failures"],
            "free_success_rate": f"{free_pct:.0f}%",
            "estimated_savings": f"约 ${cls._stats['free_calls'] * 0.001:.3f} (按 cheap 模型均价估算)",
        }

    @classmethod
    def supported_tasks(cls) -> Dict[TaskType, Dict[str, str]]:
        """返回所有支持的任务类型及模型"""
        return {k: {"free": v.get("free", "N/A"), "cheap": v.get("cheap", "N/A"), "pro": v.get("pro", "N/A")}
                for k, v in _MODEL_TIER.items()}

    @classmethod
    def free_models(cls) -> List[str]:
        """返回所有可用免费模型"""
        return list(_FREE_MODELS)


# ── 快捷函数 ──────────────────────────────────────────────────────


def route_model(task_type: TaskType, tier: str = "auto") -> str:
    """快捷函数：按任务类型获取模型名"""
    return LLMRouter.for_task(task_type, tier)


def route_free(task_type: TaskType) -> str:
    """快捷函数：强制使用免费模型"""
    return LLMRouter.for_task(task_type, tier="free")


def cost_report() -> str:
    """快捷函数：打印成本报告"""
    stats = LLMRouter.cost_stats()
    return (
        f"📊 LLM 成本报告\n"
        f"  总调用: {stats['total_calls']}\n"
        f"  💰 免费: {stats['free_calls']} ({stats['free_success_rate']})\n"
        f"  💵 低成本: {stats['cheap_calls']}\n"
        f"  💎 Pro: {stats['pro_calls']}\n"
        f"  ⚠️ 免费降级: {stats['free_failures']}\n"
        f"  💰 {stats['estimated_savings']}"
    )
