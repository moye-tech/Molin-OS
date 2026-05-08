"""
molib.shared.llm — LLM 路由与调度层

提供 LLMRouter 类，基于任务类型自动路由到最优模型。
不破坏现有 model_router.py 的接口。
"""

from .llm_router import LLMRouter

__all__ = ["LLMRouter"]
