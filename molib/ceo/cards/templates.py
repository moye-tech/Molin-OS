"""墨麟OS — 飞书卡片模板函数

提供 build_*_card 系列工厂函数。
"""
from molib.ceo.cards.builder import (
    CardBuilder, BLUE, INDIGO, PURPLE, RED, ORANGE,
    _timestamp,
)

__all__ = [
    "build_status_card",
    "build_approval_card",
    "build_daily_briefing_card",
    "build_report_card",
    "build_task_card",
    "build_simple_card",
]


def build_status_card(
    title: str,
    status_items: list[tuple[str, str]],
    alerts: list[str] | None = None,
    actions: list[str] | None = None,
    color: str = INDIGO,
) -> dict:
    """系统状态概览卡片"""
    card = CardBuilder(title, color)
    card.add_fields_row(status_items[:4])
    for k, v in status_items[4:]:
        card.add_field(k, v)
    if alerts:
        card.add_hr()
        card.add_section("⚠️ 需关注", alerts)
    if actions:
        card.add_hr()
        card.add_section("🎯 建议行动", actions)
    card.add_hr()
    card.add_note(f"墨麟OS · {_timestamp()}")
    return card.build()


def build_approval_card(
    task_id: str, description: str,
    risk_score: float, risk_reason: str,
    intent_type: str, target_vps: list[str],
    target_subsidiaries: list[str] | None = None,
    budget_estimate: float = 0.0,
) -> dict:
    """审批卡片（带风险颜色）"""
    color = RED if risk_score > 80 else (ORANGE if risk_score > 60 else BLUE)
    risk_icon = "🔴" if risk_score > 80 else "🟡"
    card = CardBuilder(f"{risk_icon} Plan Mode — 需要你审批", color)
    card.add_field("📋 任务", description or "（无描述）")
    card.add_fields_row([("风险评分", f"{risk_score:.1f}/100"), ("意图类型", intent_type)])
    card.add_field("⚠️ 风险原因", risk_reason[:200])
    card.add_field("🎯 目标 VP", ", ".join(target_vps) if target_vps else "未指定")
    if target_subsidiaries:
        card.add_field("🏢 目标子公司", ", ".join(target_subsidiaries))
    if budget_estimate > 0:
        card.add_field("💰 预算估算", f"¥{budget_estimate:.0f}")
    card.add_field("🔑 任务 ID", f"`{task_id}`")
    card.add_hr()
    card.add_div(f"✅ 回复 **批准 {task_id}** 或 **拒绝 {task_id} [原因]**")
    card.add_note("此消息由墨麟OS PlanMode 引擎自动发送")
    return card.build()


def build_daily_briefing_card(
    date: str, stats: dict, highlights: list[str],
    warnings: list[str] | None = None, color: str = BLUE,
) -> dict:
    """每日简报卡片"""
    card = CardBuilder(f"☀️ CEO 每日简报 · {date}", color)
    if stats:
        items = list(stats.items())
        card.add_fields_row(items[:4])
        for k, v in items[4:]:
            card.add_field(k, str(v))
    if highlights:
        card.add_hr()
        card.add_section("✨ 亮点", highlights)
    if warnings:
        card.add_hr()
        card.add_section("⚠️ 需关注", warnings)
    card.add_note(f"墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


def build_report_card(
    report_type: str, content: str,
    meta: dict[str, str] | None = None,
    color: str = PURPLE,
) -> dict:
    """报告型卡片"""
    card = CardBuilder(f"📋 {report_type}", color)
    card.add_div(content)
    if meta:
        card.add_hr()
        for k, v in meta.items():
            card.add_field(k, v)
    card.add_note(f"墨麟OS · {_timestamp()}")
    return card.build()


def build_task_card(
    task_id: str, description: str, status: str,
    assignee: str = "", priority: str = "medium",
    color: str = BLUE,
) -> dict:
    """任务状态卡片"""
    icons = {"completed": "✅", "in_progress": "🔄", "pending": "⏳", "blocked": "🚫", "cancelled": "❌"}
    icon = icons.get(status, "📋")
    card = CardBuilder(f"{icon} 任务 {task_id}", color)
    card.add_field("📋 描述", description)
    card.add_fields_row([("状态", status), ("优先级", priority)])
    if assignee:
        card.add_field("👤 负责人", assignee)
    card.add_note(f"墨麟OS · {_timestamp()}")
    return card.build()


def build_simple_card(title: str, lines: list[str], color: str = BLUE) -> dict:
    """简易卡片：传入行列表，自动识别分割线和加粗"""
    card = CardBuilder(title, color)
    for line in lines:
        if line.startswith("---"):
            card.add_hr()
        elif line.startswith("## "):
            card.add_div(f"**{line[3:]}**")
        else:
            card.add_div(line)
    card.add_note(f"墨麟OS · {_timestamp()}")
    return card.build()
