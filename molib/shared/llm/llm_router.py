"""
墨麟 — LLM 路由器 (LLMRouter)
智能 LLM 路由：按任务复杂度/类型自动选择性价比最优模型。

从 Integuru + Ouroboros 提取的设计模式：
- 单例池化: 全局共享 LLM 实例池，避免重复创建
- 按任务类型路由: simple→cheap, reasoning→pro, code→frontier
- 运行时切换: set_default_model() / switch_to_alternate()
- 兼容现有 model_router.py，作为上层封装

用法:
    from molib.shared.llm.llm_router import LLMRouter

    # 获取适合简单任务的模型
    model = LLMRouter.for_task("simple")   # -> "deepseek/deepseek-chat"

    # 切换到更强推理模型
    model = LLMRouter.for_task("reasoning")
"""

from typing import Dict, Optional, Literal


# ── 模型等级定义 ──────────────────────────────────────────────────

TaskType = Literal["simple", "reasoning", "code", "creative", "vision", "video"]

_MODEL_TIER: Dict[TaskType, str] = {
    "simple":    "deepseek/deepseek-chat",       # flash 级，低成本
    "reasoning": "deepseek/deepseek-rasoner",    # pro 级，复杂分析
    "code":      "deepseek/deepseek-chat",       # 代码用标准模型
    "creative":  "deepseek/deepseek-chat",       # 创作用标准
    "vision":    "qwen3-vl-plus",                # 视觉用千问
    "video":     "happyhorse-1.0-t2v",           # 视频用百炼
}

_TIER_COST_HINT: Dict[TaskType, str] = {
    "simple":    "最便宜，适合分类/提取/简单问答",
    "reasoning": "最强推理，适合复杂分析/决策/长文",
    "code":      "平衡型，适合代码生成",
    "creative":  "平衡型，适合内容创作",
    "vision":    "视觉专用，图片识别/生成",
    "video":     "视频专用，文本到视频",
}


# ── LLM 路由器 ────────────────────────────────────────────────────


class LLMRouter:
    """
    智能 LLM 路由：按任务类型选择最优模型。

    用法:
        model = LLMRouter.for_task("simple")
        # 切换到高级模型
        LLMRouter.switch_to_alternate()
        model = LLMRouter.for_task("reasoning")
    """

    _default_model: str = "deepseek/deepseek-chat"
    _alternate_model: str = "deepseek/deepseek-rasoner"
    _current_task: Optional[TaskType] = None

    @classmethod
    def for_task(cls, task_type: TaskType) -> str:
        """
        根据任务类型获取最合适的模型名称。

        参数:
            task_type: 任务类型
                - simple: 简单分类/提取/问答 → flash
                - reasoning: 复杂分析/决策/长文 → rasoner
                - code: 代码生成 → chat
                - creative: 内容创作 → chat
                - vision: 图片识别/生成 → qwen-vl
                - video: 视频生成 → happyhorse

        返回:
            str — 模型名称（OpenRouter 格式）
        """
        cls._current_task = task_type
        return _MODEL_TIER.get(task_type, cls._default_model)

    @classmethod
    def set_default_model(cls, model: str):
        """运行时切换默认模型"""
        cls._default_model = model

    @classmethod
    def switch_to_alternate(cls) -> str:
        """
        切换到更强的替代模型（用于复杂代码生成或高难度任务）。
        返回切换后的模型名。
        """
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
    def cost_hint(cls, task_type: TaskType) -> str:
        """返回某任务类型的成本提示"""
        return _TIER_COST_HINT.get(task_type, "未知")

    @classmethod
    def supported_tasks(cls) -> Dict[TaskType, str]:
        """返回所有支持的任务类型"""
        return dict(_MODEL_TIER)


# ── 快捷函数 ──────────────────────────────────────────────────────


def route_model(task_type: TaskType) -> str:
    """快捷函数：按任务类型获取模型名"""
    return LLMRouter.for_task(task_type)
