"""
墨麟OS — 飞书卡片模块（cards 包）

使用方式：
    from molib.ceo.cards import (
        CardBuilder, FeishuCardSender,
        ThinkingCardManager, ProgressCardManager,
        build_status_card, build_approval_card,
        build_daily_briefing_card, build_report_card,
        build_task_card, build_simple_card,
        card_to_text,
    )
"""

from molib.ceo.cards.builder import CardBuilder, BLUE, WATARI, INDIGO, PURPLE, RED, ORANGE, YELLOW, GREEN, TURQUOISE, GREY
from molib.ceo.cards.sender import FeishuCardSender, card_payload, API_BASE
from molib.ceo.cards.templates import (
    build_status_card,
    build_approval_card,
    build_daily_briefing_card,
    build_report_card,
    build_task_card,
    build_simple_card,
)
from molib.ceo.cards.utils import card_to_text
from molib.ceo.cards.thinking import (
    ThinkingCardManager,
    ProgressCardManager,
    CEO_THINKING_STEPS,
    STEP_ICONS,
    PROGRESS_STEPS,
)

__all__ = [
    # builder
    "CardBuilder", "BLUE", "WATARI", "INDIGO", "PURPLE", "RED",
    "ORANGE", "YELLOW", "GREEN", "TURQUOISE", "GREY",
    # sender
    "FeishuCardSender", "card_payload", "API_BASE",
    # templates
    "build_status_card", "build_approval_card", "build_daily_briefing_card",
    "build_report_card", "build_task_card", "build_simple_card",
    # utils
    "card_to_text",
    # thinking
    "ThinkingCardManager", "ProgressCardManager",
    "CEO_THINKING_STEPS", "STEP_ICONS", "PROGRESS_STEPS",
]
