"""
墨域OS — 飞书消息卡片构建器
================================
基于 feishu-message-formatter skill 的纯文本卡片格式，
生成结构化、分级透明的飞书消息。

所有对外发送给尹建业的消息都应经过此模块格式化。
"""

import json
from datetime import datetime
from typing import Any


def card_header(title: str, subtitle: str = "", emoji: str = "") -> str:
    """生成卡片标题行"""
    lines = []
    if emoji:
        lines.append(f"{emoji} {title}")
    else:
        lines.append(f"━━━ {title} ━━━")
    if subtitle:
        lines.append(f"  {subtitle}")
    lines.append("")
    return "\n".join(lines)


def card_divider() -> str:
    """分隔线"""
    return "─" * 30 + "\n"


def card_kv(key: str, value: str, indent: int = 0) -> str:
    """键值对行"""
    prefix = "  " * indent
    return f"{prefix}{key}: {value}\n"


def card_section(title: str, items: list[str]) -> str:
    """带标题的区块"""
    lines = [f"▸ {title}", ""]
    for item in items:
        lines.append(f"  • {item}")
    lines.append("")
    return "\n".join(lines)


def card_table(headers: list[str], rows: list[list[str]]) -> str:
    """简单表格（纯文本对齐）"""
    if not rows:
        return ""
    # 计算每列最大宽度
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    lines = []
    # 表头
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    # 分隔
    lines.append("-+-".join("-" * w for w in col_widths))
    # 行
    for row in rows:
        line = " | ".join(
            (row[i] if i < len(row) else "").ljust(col_widths[i])
            for i in range(len(headers))
        )
        lines.append(line)

    return "\n".join(lines) + "\n\n"


def card_footer(
    timestamp: str = "",
    source: str = "墨域OS",
    status: str = "",
) -> str:
    """底部信息"""
    parts = []
    if timestamp:
        parts.append(timestamp)
    if source:
        parts.append(f"来自 {source}")
    if status:
        parts.append(f"状态: {status}")
    return f"· {' · '.join(parts)}\n"


def build_system_status_card(
    title: str,
    status_items: list[tuple[str, str]],
    alerts: list[str] | None = None,
    actions: list[str] | None = None,
) -> str:
    """
    构建系统状态概览卡片。

    参数:
        title: 卡片标题
        status_items: [(标签, 值), ...]
        alerts: 告警列表
        actions: 建议行动列表

    返回: 格式化文本
    """
    lines = [card_header(title, emoji="📊")]

    for label, value in status_items:
        lines.append(card_kv(label, value))

    if alerts:
        lines.append("")
        lines.append(card_section("⚠️ 需关注", alerts))

    if actions:
        lines.append("")
        lines.append(card_section("🎯 建议行动", actions))

    lines.append(card_divider())
    lines.append(card_footer(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")))

    return "".join(lines)


def build_daily_briefing_card(
    date: str,
    stats: dict[str, Any],
    highlights: list[str],
    warnings: list[str] | None = None,
) -> str:
    """
    构建每日简报卡片。

    参数:
        date: 日期字符串
        stats: {类别: 数值} 字典
        highlights: 今日亮点列表
        warnings: 需关注事项列表

    返回: 格式化文本
    """
    lines = [card_header(f"CEO 每日简报 · {date}", emoji="☀️")]

    if stats:
        lines.append("📈 系统状态")
        for key, value in stats.items():
            lines.append(card_kv(key, str(value)))
        lines.append("")

    if highlights:
        lines.append(card_section("✨ 亮点", highlights))

    if warnings:
        lines.append(card_section("⚠️ 需关注", warnings))

    lines.append(card_divider())
    lines.append(card_footer(source="CEO引擎"))

    return "".join(lines)


def build_report_card(
    report_type: str,
    content: str,
    meta: dict[str, str] | None = None,
) -> str:
    """
    构建报告型卡片（财务、情报分析等）。

    参数:
        report_type: 报告类型
        content: 正文
        meta: 元数据键值对
    """
    lines = [card_header(report_type, emoji="📋"), ""]
    lines.append(content)
    lines.append("")
    if meta:
        for key, value in meta.items():
            lines.append(card_kv(key, value))
    lines.append("")
    lines.append(card_divider())
    lines.append(card_footer())
    return "".join(lines)


def build_task_card(
    task_id: str,
    description: str,
    status: str,
    assignee: str = "",
    priority: str = "medium",
) -> str:
    """
    构建任务卡片。

    状态颜色映射: completed=✅, in_progress=🔄, pending=⏳, blocked=🚫
    """
    status_icons = {
        "completed": "✅",
        "in_progress": "🔄",
        "pending": "⏳",
        "blocked": "🚫",
        "cancelled": "❌",
    }
    icon = status_icons.get(status, "📋")

    lines = [card_header(f"{icon} 任务 {task_id}"), ""]
    lines.append(f"  {description}\n")
    lines.append(f"  状态: {status}")
    if assignee:
        lines.append(f"  负责人: {assignee}")
    lines.append(f"  优先级: {priority}")
    lines.append("")
    lines.append(card_divider())
    lines.append(card_footer())

    return "".join(lines)


if __name__ == "__main__":
    # 测试输出
    test_card = build_system_status_card(
        title="系统状态测试",
        status_items=[("SKILL 总数", "492"), ("Worker", "20"), ("状态", "正常")],
        alerts=["无"],
        actions=["继续执行整改计划"],
    )
    print(test_card)
