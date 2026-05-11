"""
墨麟OS v2.5 — 飞书输出格式路由器 (FeishuCardRouter)

在 NoiseFilter 之后、发送之前，自动决定消息用哪种飞书格式输出。
解决"该用卡片还是纯文字"的决策缺失问题。

决策树（优先级从高到低）:
  告警 > 审批 > 内容预览 > 数据报表 > 纯文字

5种标准格式:
  T0 纯文字 — 80%+ 消息的正确格式（默认）
  T1 数据简报卡片 — 日报/周报/统计/多字段数据
  T2 审批决策卡片 — L2/L3 治理级别
  T3 内容预览卡片 — ContentWriter/视频脚本/大纲草稿
  T4 告警卡片 — 系统错误/预算超限/关键失败

用法:
    from molib.shared.publish.feishu_card_router import FeishuCardRouter

    # 仅路由
    fmt = FeishuCardRouter.route(message, {"governance_level": "L0"})

    # 路由 + 构建卡片 payload
    payload = FeishuCardRouter.render(
        message="今日闲鱼5条消息已自动回复",
        ctx={"is_cron": True, "governance_level": "L0"}
    )
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class Fmt(Enum):
    """飞书输出格式枚举"""
    TEXT = "text"               # T0 纯文字
    CARD_DATA = "card_data"     # T1 数据简报
    CARD_APPROVE = "card_approve"  # T2 审批
    CARD_CONTENT = "card_content"  # T3 内容预览
    CARD_ALERT = "card_alert"   # T4 告警


# 向后兼容别名
OutputFormat = Fmt


# ═══════════════════════════════════════════════════════════════
# 触发关键词集合（按文档严格定义）
# ═══════════════════════════════════════════════════════════════

_ALERT = {
    "失败", "错误", "异常", "超限", "中断", "402", "error", "failed", "断连", "预警",
}

_APPROVE = {
    "L2", "L3", "审批", "确认发布", "报价", "待审", "需确认", "请批准",
}

_CONTENT = {
    "草稿", "文案", "脚本", "大纲", "预览", "内容已生成", "已就绪",
}

_DATA = {
    "简报", "报表", "统计", "日报", "周报", "产出", "数据汇总", "竞品监控",
}


# ═══════════════════════════════════════════════════════════════
# 卡片模板配置
# ═══════════════════════════════════════════════════════════════

CARD_TEMPLATES = {
    Fmt.CARD_DATA: {
        "header_color": "turquoise",
        "header_icon": "📊",
        "header_label": "数据速报",
    },
    Fmt.CARD_APPROVE: {
        "header_color": "orange",
        "header_icon": "✅",
        "header_label": "待审批",
    },
    Fmt.CARD_CONTENT: {
        "header_color": "blue",
        "header_icon": "📝",
        "header_label": "内容预览",
    },
    Fmt.CARD_ALERT: {
        "header_color": "red",
        "header_icon": "🚨",
        "header_label": "系统告警",
    },
}


# ═══════════════════════════════════════════════════════════════
# 路由器
# ═══════════════════════════════════════════════════════════════


def _has_kw(text: str, keywords: set) -> bool:
    """检查文本是否包含任一关键词"""
    return any(kw in text for kw in keywords)


class FeishuCardRouter:
    """
    根据消息内容和上下文自动选择飞书输出格式。

    路由优先级（从高到低）:
      P1 — 告警优先（最高优先级）
      P2 — 治理审批（L2/L3 必须用审批卡片）
      P3 — 内容草稿预览
      P4 — 数据简报（字段≥3 或 含报表关键词）
      P5 — 默认纯文字（80%+消息应该走这里）
    """

    @classmethod
    def route(cls, message: str, ctx: dict | None = None) -> Fmt:
        """
        路由决策（优先级从高到低）：
          告警 > 审批 > 内容预览 > 数据报表 > 纯文字

        ctx keys:
          governance_level: str   L0/L1/L2/L3
          has_draft: bool         是否含内容草稿
          field_count: int        数据字段数
          is_cron: bool           是否定时任务（倾向卡片）
          is_error: bool          是否为错误场景
        """
        c = ctx or {}

        # P1 — 告警优先（最高优先级）
        if _has_kw(message, _ALERT) or c.get("is_error"):
            return Fmt.CARD_ALERT

        # P2 — 治理审批（L2/L3 必须用审批卡片）
        gov = c.get("governance_level", "L0")
        if gov in ("L2", "L3") or _has_kw(message, _APPROVE):
            return Fmt.CARD_APPROVE

        # P3 — 内容草稿预览
        if c.get("has_draft") or _has_kw(message, _CONTENT):
            return Fmt.CARD_CONTENT

        # P4 — 数据简报（字段≥3 或 含报表关键词）
        if c.get("field_count", 0) >= 3 or _has_kw(message, _DATA):
            return Fmt.CARD_DATA

        # P5 — 默认纯文字（80%+消息应该走这里）
        return Fmt.TEXT

    @classmethod
    def render(
        cls,
        message: str,
        data: dict | None = None,
        ctx: dict | None = None,
    ) -> dict:
        """
        一站式：路由 + 构建飞书消息 payload。

        Args:
            message: 消息文本
            data: 额外数据
            ctx: 上下文
        Returns:
            dict: 飞书消息 payload
        """
        from molib.ceo.cards.builder import CardBuilder

        fmt = cls.route(message, ctx)
        d = data or {}

        if fmt == Fmt.TEXT:
            return {"msg_type": "text", "content": {"text": message}}

        # 获取模板配置
        tmpl = CARD_TEMPLATES.get(fmt, {})
        color = d.get("color", tmpl.get("header_color", "blue"))
        title = d.get("title") or d.get("alert_title") or tmpl.get("header_label", "消息")

        card = CardBuilder(f"{tmpl.get('header_icon', '📋')} {title}", color)

        if fmt == Fmt.CARD_ALERT:
            # T4 告警：3句话原则
            card.add_div(message)
        elif fmt == Fmt.CARD_APPROVE:
            # T2 审批：消息 + 审批提示
            card.add_div(message)
            card.add_hr()
            card.add_div("**操作:** 批准 / 修改 / 拒绝")
            card.add_note("请在24小时内处理")
        elif fmt == Fmt.CARD_CONTENT:
            # T3 内容预览：200字折叠
            preview = message[:300] + ("…" if len(message) > 300 else "")
            card.add_div(preview)
            if d.get("fields"):
                card.add_hr()
                for k, v in d["fields"].items():
                    card.add_div(f"**{k}:** {v}")
        elif fmt == Fmt.CARD_DATA:
            # T1 数据简报
            card.add_div(message)
            if d.get("fields"):
                card.add_hr()
                for k, v in d["fields"].items():
                    card.add_div(f"**{k}:** {v}")

        return card.build()

    @classmethod
    def format_message(
        cls,
        message: str,
        context: Optional[dict] = None,
    ) -> dict:
        """
        返回完整的格式化决策结果，供 FeishuCardBuilder 使用。

        Returns:
            {
                "format": Fmt 枚举值,
                "template": 卡片模板配置,
                "message": 原消息（已过滤噪声后的版本）
            }
        """
        fmt = cls.route(message, context)
        template = CARD_TEMPLATES.get(fmt, {})
        return {
            "format": fmt,
            "template": template,
            "message": message,
        }

    @classmethod
    def quick_route(cls, message: str) -> str:
        """快速路由（无上下文版本），返回格式名。"""
        fmt = cls.route(message)
        return fmt.value

    @classmethod
    def template_for(cls, fmt: Fmt) -> dict:
        """获取指定格式的卡片模板配置"""
        return CARD_TEMPLATES.get(fmt, {})

    @classmethod
    def all_formats(cls) -> dict:
        """返回所有支持的输出格式及触发规则"""
        return {
            "T0_TEXT": {
                "format": "text",
                "trigger": "默认（80%+消息应走这里）",
                "example": "进度通知、简单状态更新、闲聊、策略讨论",
                "template": "≤3行纯文字，emoji替代格式，不发卡片",
                "rules": {
                    "do": ["emoji替代格式", "≤3行"],
                    "dont": ["禁止技术路径", "禁止traceback"],
                },
            },
            "T1_CARD_DATA": {
                "format": "card_data",
                "trigger": "3+字段 或 数据/报表/统计/日报关键词",
                "example": "日报/周报、飞轮产出、收支报表",
                "template": "彩色header + section数据表格 + 查看详情按钮",
                "rules": {
                    "do": ["3+字段触发", "定时任务结果"],
                    "tip": ["每日简报/周报"],
                },
            },
            "T2_CARD_APPROVE": {
                "format": "card_approve",
                "trigger": "L2/L3 治理级别 或 审批/确认/报价关键词",
                "example": "报价>¥500、外发内容发布前、新业务申请",
                "template": "橙色header + 批准/修改/拒绝三按钮 + 24h截止备注",
                "rules": {
                    "do": ["governance_level=L2/L3"],
                    "dont": ["禁止无按钮审批卡"],
                },
            },
            "T3_CARD_CONTENT": {
                "format": "card_content",
                "trigger": "草稿/文案/脚本/大纲/预览关键词 或 has_draft=True",
                "example": "小红书文案草稿、短视频脚本、课程大纲",
                "template": "蓝色header + 内容preview(200字折叠) + 发布/修改/丢弃按钮",
                "rules": {
                    "do": ["has_draft=True", "200字折叠"],
                },
            },
            "T4_CARD_ALERT": {
                "format": "card_alert",
                "trigger": "错误/异常/失败/超限/断连关键词 或 is_error=True",
                "example": "API 402、飞轮中断、WebSocket断连、预算超标",
                "template": "红色header + 3句话原则(发生什么/影响什么/做什么) + 立即处理按钮",
                "rules": {
                    "dont": ["禁止traceback", "禁止技术日志"],
                    "do": ["3句话原则"],
                },
            },
        }


# ═══════════════════════════════════════════════════════════════
# 快捷函数（保持向后兼容）
# ═══════════════════════════════════════════════════════════════


def route_feishu_format(message: str, context: Optional[dict] = None) -> Fmt:
    """快捷函数：路由飞书消息格式"""
    return FeishuCardRouter.route(message, context)


def should_use_card(message: str, context: Optional[dict] = None) -> bool:
    """快捷函数：是否应该使用卡片（vs 纯文字）"""
    return FeishuCardRouter.route(message, context) != Fmt.TEXT
