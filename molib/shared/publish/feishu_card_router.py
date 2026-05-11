"""
墨麟OS v2.5 — 飞书输出格式路由器 (FeishuCardRouter)

在 NoiseFilter 之后、发送之前，自动决定消息用哪种飞书格式输出。
解决"该用卡片还是纯文字"的决策缺失问题。

决策树:
  1. 消息目的: 闲聊→纯文字 / 通知→简单emoji / 数据→卡片 / 审批→审批卡片 / 异常→告警
  2. 数据量: 1-3数字→纯文字 / 3-8字段→数据卡片 / 综合报告→富卡片 / 草稿→预览卡片

5种标准格式:
  T1 日报/简报卡片 — 定时任务/数据汇总
  T2 审批/决策卡片 — L2/L3 治理级任务
  T3 内容预览卡片 — ContentWriter/Designer 输出草稿
  T4 告警/异常卡片 — 系统错误/限流/预算超标
  T5 纯文字 — 80%+ 的日常消息（默认）

用法:
    from molib.shared.publish.feishu_card_router import FeishuCardRouter

    fmt = FeishuCardRouter.route(message, {"governance_level": "L0"})
    if fmt == OutputFormat.CARD_ALERT:
        card = FeishuCardBuilder().header("异常", "red").section(msg)...
    elif fmt == OutputFormat.TEXT:
        bot.send_text(msg)  # 纯文字，不用卡片
"""

from __future__ import annotations

from enum import Enum
from typing import Optional


class OutputFormat(Enum):
    """飞书输出格式枚举"""
    TEXT = "text"               # 纯文字，≤3行
    CARD_DATA = "card_data"     # T1 日报/数据卡片
    CARD_APPROVE = "card_approve"  # T2 审批卡片（带按钮）
    CARD_CONTENT = "card_content"  # T3 内容预览卡片
    CARD_ALERT = "card_alert"   # T4 告警卡片


# ═══════════════════════════════════════════════════════════════
# 触发关键词集合
# ═══════════════════════════════════════════════════════════════

ALERT_KEYWORDS = {
    "失败", "异常", "错误", "超限", "中断", "超时",
    "error", "failed", "timeout", "exception", "crash",
    "预算超标", "API超限", "宕机", "不可用",
}

APPROVE_TRIGGERS = {
    "L2", "L3", "审批", "确认发布", "报价", "请审核",
    "待决定", "需要确认", "请批准",
}

CONTENT_TRIGGERS = {
    "草稿", "文案", "脚本", "大纲", "预览", "初稿",
    "内容已生成", "待发布内容", "文章初版",
}

DATA_TRIGGERS = {
    "简报", "报表", "统计", "数据", "产出", "日报",
    "周报", "月报", "汇总", "收入", "支出",
}


# ═══════════════════════════════════════════════════════════════
# 卡片模板配置
# ═══════════════════════════════════════════════════════════════

CARD_TEMPLATES = {
    OutputFormat.CARD_DATA: {
        "header_color": "turquoise",
        "header_icon": "📊",
        "header_label": "数据速报",
    },
    OutputFormat.CARD_APPROVE: {
        "header_color": "orange",
        "header_icon": "✅",
        "header_label": "待审批",
    },
    OutputFormat.CARD_CONTENT: {
        "header_color": "blue",
        "header_icon": "📝",
        "header_label": "内容预览",
    },
    OutputFormat.CARD_ALERT: {
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

    路由优先级:
      1. L2/L3 治理级别 → 审批卡片
      2. 错误关键词 → 告警卡片
      3. 草稿/文案关键词 → 内容预览卡片
      4. 数据/报表关键词或字段≥3 → 数据卡片
      5. 默认 → 纯文字（80%+ 消息应走这里）
    """

    @classmethod
    def route(
        cls,
        message: str,
        context: Optional[dict] = None,
    ) -> OutputFormat:
        """
        主路由方法。

        Args:
            message: 消息文本
            context: 上下文信息，可包含:
                - governance_level: "L0"|"L1"|"L2"|"L3"|"L4"
                - has_draft: bool, 是否包含内容草稿
                - field_count: int, 消息中的数据字段数
                - error_type: str, 异常类型
                - source: str, 消息来源 Worker

        Returns:
            OutputFormat 枚举值
        """
        ctx = context or {}
        governance = ctx.get("governance_level", "L0")

        # ── L2/L3 治理级别 → 审批卡片（强制）──
        if governance in ("L2", "L3") or _has_kw(message, APPROVE_TRIGGERS):
            return OutputFormat.CARD_APPROVE

        # ── 错误/异常 → 告警卡片 ──
        if _has_kw(message, ALERT_KEYWORDS) or ctx.get("error_type"):
            return OutputFormat.CARD_ALERT

        # ── 内容草稿 → 预览卡片 ──
        if _has_kw(message, CONTENT_TRIGGERS) or ctx.get("has_draft"):
            return OutputFormat.CARD_CONTENT

        # ── 数据/报表 → 数据卡片（字段≥3个时）──
        field_count = ctx.get("field_count", 0)
        if _has_kw(message, DATA_TRIGGERS) or field_count >= 3:
            return OutputFormat.CARD_DATA

        # ── 默认：纯文字 ──
        return OutputFormat.TEXT

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
                "format": OutputFormat 枚举值,
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
        """
        快速路由（无上下文版本），返回格式名。

        用于简单场景，无需完整 context。
        """
        fmt = cls.route(message)
        return fmt.value

    @classmethod
    def template_for(cls, fmt: OutputFormat) -> dict:
        """获取指定格式的卡片模板配置"""
        return CARD_TEMPLATES.get(fmt, {})

    @classmethod
    def all_formats(cls) -> dict:
        """返回所有支持的输出格式及触发规则"""
        return {
            "T1_CARD_DATA": {
                "format": "card_data",
                "trigger": "数据/报表/统计/简报关键词 或 field_count≥3",
                "example": "日报/周报、飞轮产出、收支报表",
                "template": "turquoise header + 数据表格 + 查看详情按钮",
            },
            "T2_CARD_APPROVE": {
                "format": "card_approve",
                "trigger": "L2/L3 治理级别 或 审批/确认/报价关键词",
                "example": "报价>¥100、外发内容发布前、新业务申请",
                "template": "orange header + 批准/修改/拒绝三按钮",
            },
            "T3_CARD_CONTENT": {
                "format": "card_content",
                "trigger": "草稿/文案/脚本/大纲/预览关键词",
                "example": "小红书文案草稿、短视频脚本、课程大纲",
                "template": "blue header + 内容preview + 发布/修改/丢弃按钮",
            },
            "T4_CARD_ALERT": {
                "format": "card_alert",
                "trigger": "错误/异常/失败/超限关键词 或 error_type存在",
                "example": "预算超标、API限流、飞轮中断、Worker执行失败",
                "template": "red header + 异常描述 + 影响范围 + 立即处理按钮",
            },
            "T5_TEXT": {
                "format": "text",
                "trigger": "默认（80%+消息应走这里）",
                "example": "进度通知、简单状态更新、闲聊、策略讨论",
                "template": "≤3行纯文字，emoji替代格式，不发卡片",
            },
        }


# ═══════════════════════════════════════════════════════════════
# 快捷函数
# ═══════════════════════════════════════════════════════════════


def route_feishu_format(message: str, context: Optional[dict] = None) -> OutputFormat:
    """快捷函数：路由飞书消息格式"""
    return FeishuCardRouter.route(message, context)


def should_use_card(message: str, context: Optional[dict] = None) -> bool:
    """快捷函数：是否应该使用卡片（vs 纯文字）"""
    return FeishuCardRouter.route(message, context) != OutputFormat.TEXT
