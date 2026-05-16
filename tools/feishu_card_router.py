#!/usr/bin/env python3
"""
墨麟OS · FeishuCardRouter
功能：根据消息内容和上下文，自动决定使用哪种飞书输出格式
所有Agent在发送飞书消息前调用此路由器
"""
from __future__ import annotations
from enum import Enum


class Fmt(Enum):
    TEXT          = "text"          # T0 纯文字（80%+消息）
    CARD_DATA     = "card_data"     # T1 数据简报卡片
    CARD_APPROVE  = "card_approve"  # T2 审批决策卡片
    CARD_CONTENT  = "card_content"  # T3 内容预览卡片
    CARD_ALERT    = "card_alert"    # T4 告警卡片


class FeishuCardRouter:
    """飞书消息格式自动路由器"""

    # 关键词集合（中英文均支持）
    _ALERT   = {"失败","错误","异常","超限","中断","告警","402","断连",
                 "error","failed","alert","critical","budget_exceeded"}
    _APPROVE = {"L2","L3","审批","待审","确认发布","请批准","报价审批",
                 "approve","pending_approval"}
    _CONTENT = {"草稿","文案已就绪","脚本已生成","内容预览","大纲已完成",
                 "draft_ready","content_preview"}
    _DATA    = {"简报","日报","周报","报表","统计","汇总","数据","产出",
                 "brief","report","summary","analytics"}

    @classmethod
    def route(cls, message: str, ctx: dict | None = None) -> Fmt:
        """
        路由决策（优先级从高到低）：
          告警 > 审批 > 内容预览 > 数据报表 > 纯文字
        
        Args:
            message: 消息内容
            ctx: 上下文，支持的key:
                governance_level: str  L0/L1/L2/L3
                has_draft: bool        是否含内容草稿
                field_count: int       数据字段数量（≥3触发数据卡）
                is_error: bool         是否为错误消息
                is_cron: bool          是否为定时任务产出
        Returns:
            Fmt: 应使用的消息格式类型
        """
        c = ctx or {}

        # P1 — 告警优先（最高）
        if c.get("is_error") or cls._match(message, cls._ALERT):
            return Fmt.CARD_ALERT

        # P2 — 治理审批（L2/L3必须用审批卡）
        gov = c.get("governance_level", "L0")
        if gov in ("L2", "L3") or cls._match(message, cls._APPROVE):
            return Fmt.CARD_APPROVE

        # P3 — 内容草稿预览
        if c.get("has_draft") or cls._match(message, cls._CONTENT):
            return Fmt.CARD_CONTENT

        # P4 — 数据简报（字段≥3或含报表关键词）
        if c.get("field_count", 0) >= 3 or cls._match(message, cls._DATA):
            return Fmt.CARD_DATA

        # P5 — 默认纯文字（80%+消息应该走这里）
        return Fmt.TEXT

    @staticmethod
    def _match(text: str, keywords: set) -> bool:
        return any(kw in text for kw in keywords)

    @classmethod
    def render(cls, message: str, data: dict | None = None,
               ctx: dict | None = None) -> dict:
        """
        一站式：路由 + 构建飞书消息payload
        Returns: 可直接发送的飞书消息字典
        """
        fmt = cls.route(message, ctx)
        d = data or {}

        if fmt == Fmt.TEXT:
            return {"msg_type": "text", "content": {"text": message}}

        # 构建卡片基础结构
        card = {
            "msg_type": "interactive",
            "card": {
                "elements": [],
                "header": {}
            }
        }

        color_map = {
            Fmt.CARD_ALERT:   "red",
            Fmt.CARD_APPROVE: "orange",
            Fmt.CARD_CONTENT: "wathet",
            Fmt.CARD_DATA:    "turquoise",
        }

        title_map = {
            Fmt.CARD_ALERT:   d.get("alert_title", "⚠️ 系统告警"),
            Fmt.CARD_APPROVE: d.get("title", "✅ 待审批"),
            Fmt.CARD_CONTENT: d.get("title", "📝 内容草稿"),
            Fmt.CARD_DATA:    d.get("title", "📊 数据简报"),
        }

        card["card"]["header"] = {
            "title": {"tag": "plain_text", "content": title_map[fmt]},
            "template": color_map[fmt]
        }

        # 主体内容
        preview = message[:300] + ("..." if len(message) > 300 else "")
        card["card"]["elements"].append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": preview}
        })

        # 审批卡片加按钮
        if fmt == Fmt.CARD_APPROVE:
            card["card"]["elements"].append({
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "✅ 批准"},
                     "type": "primary", "value": {"action": "approve"}},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "✏️ 修改"},
                     "type": "default", "value": {"action": "modify"}},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "❌ 拒绝"},
                     "type": "danger", "value": {"action": "reject"}},
                ]
            })

        # 内容预览卡片加操作按钮
        if fmt == Fmt.CARD_CONTENT:
            card["card"]["elements"].append({
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "📤 发布"},
                     "type": "primary", "value": {"action": "publish"}},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "✏️ 修改"},
                     "type": "default", "value": {"action": "modify"}},
                    {"tag": "button", "text": {"tag": "plain_text", "content": "🗑️ 丢弃"},
                     "type": "danger", "value": {"action": "discard"}},
                ]
            })

        # 告警卡片加处理按钮
        if fmt == Fmt.CARD_ALERT:
            card["card"]["elements"].append({
                "tag": "action",
                "actions": [
                    {"tag": "button", "text": {"tag": "plain_text", "content": "⚡ 立刻处理"},
                     "type": "danger", "value": {"action": "handle_alert"}},
                ]
            })

        return card


# ── 使用示例 ──────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # 示例1：普通通知 → T0纯文字
    result = FeishuCardRouter.render("✅ 闲鱼今日5条消息已自动回复")
    print("T0:", result["msg_type"])

    # 示例2：内容草稿 → T3预览卡
    result = FeishuCardRouter.render(
        "文案草稿已就绪：《AI副业年入百万》1247字",
        ctx={"has_draft": True}
    )
    print("T3:", result["card"]["header"]["template"])

    # 示例3：系统告警 → T4告警卡
    result = FeishuCardRouter.render(
        "API余额不足，5个定时任务失败",
        ctx={"is_error": True}
    )
    print("T4:", result["card"]["header"]["template"])
