"""
墨麟OS — 思维链实时卡片 & 进度条卡片（弃用）
=========================================

此文件已弃用，所有功能已迁移至 cards 子包。

请改用：
    from molib.ceo.cards import (
        ThinkingCardManager, ProgressCardManager,
        CEO_THINKING_STEPS, PROGRESS_STEPS,
    )

此文件保留仅为向后兼容，内容为空壳。新代码不要 import 此模块。
"""

import warnings as _warnings

_warnings.warn(
    "thinking_card.py 已弃用，请从 feishu_card.py 导入 ThinkingCardManager/ProgressCardManager。",
    DeprecationWarning,
    stacklevel=2,
)

from molib.ceo.feishu_card import (
    ThinkingCardManager,
    ProgressCardManager,
    CEO_THINKING_STEPS,
    STEP_ICONS,
    PROGRESS_STEPS,
)

__all__ = [
    "ThinkingCardManager",
    "ProgressCardManager",
    "CEO_THINKING_STEPS",
    "STEP_ICONS",
    "PROGRESS_STEPS",
]
