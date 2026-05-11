"""
墨麟OS — 飞书输出强制执行器 (Output Enforcer)

包装 FeishuCardSender，在每次发送前强制执行：
  1. pre_send 自检（思考前缀/噪声/Markdown残留/长度）
  2. CardRouter 路由（告警/审批/内容预览/数据简报 → 卡片）
  3. 长消息自动降级（doc import）
  4. 发送结果验证

这是三合一升级方案中「遗漏③ CardRouter 未被强制执行」的终极修复。
所有 cron 作业和交互式任务都应使用此模块发送飞书消息，
而非直接调用 FeishuCardSender 或裸写文本。

用法:
    from molib.infra.gateway.feishu_output_enforcer import FeishuOutputEnforcer

    enforcer = FeishuOutputEnforcer(chat_id="oc_xxx")
    result = enforcer.send(message, context={"field_count": 5})
    # → 自动路由到 T1 数据简报卡片

设计原则:
  - 卡在发送层，不依赖 Agent 自觉遵守规则
  - 零侵入：不修改现有 CardSender/CardBuilder/CardRouter 代码
  - 向后兼容：send() 签名与 FeishuCardSender.send_card() 兼容
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molin.infra.gateway.enforcer")


class FeishuOutputEnforcer:
    """飞书输出强制执行器。在发送前自动完成验证、路由和降级。"""

    def __init__(
        self,
        chat_id: str,
        sender=None,
        enable_validation: bool = True,
        enable_routing: bool = True,
        enable_doc_import: bool = True,
    ):
        """
        Args:
            chat_id: 飞书会话 ID
            sender: FeishuCardSender 实例（可选，自动创建）
            enable_validation: 启用 pre_send 自检
            enable_routing: 启用 CardRouter 自动路由
            enable_doc_import: 启用长消息自动 doc import
        """
        self.chat_id = chat_id
        self.enable_validation = enable_validation
        self.enable_routing = enable_routing
        self.enable_doc_import = enable_doc_import

        if sender is None:
            from molib.ceo.cards.sender import FeishuCardSender
            self._sender = FeishuCardSender()
        else:
            self._sender = sender

    def send(
        self,
        message: str,
        context: Optional[dict] = None,
        data: Optional[dict] = None,
    ) -> dict:
        """一站式发送：验证 → 路由 → 发送。

        Args:
            message: 消息文本
            context: 上下文（governance_level, field_count, is_cron, has_draft 等）
            data: 额外数据（alert_title, title, fields 等）

        Returns:
            {"status": "sent"|"routed"|"doc_imported"|"blocked",
             "format": "text"|"card_data"|"card_alert"|...,
             "violations": [...],
             "doc_url": "..."}
        """
        ctx = context or {}
        d = data or {}

        # ── Step 1: Pre-send 验证 ──
        if self.enable_validation:
            from molib.infra.gateway.feishu_pre_send import validate

            result = validate(message, ctx)

            # 拦截严重违规
            if result.has_errors():
                logger.warning(
                    "[Enforcer] BLOCKED: %d errors, %d warnings",
                    sum(1 for v in result.violations if v.severity.name == "ERROR"),
                    len(result.violations),
                )
                return {
                    "status": "blocked",
                    "violations": [
                        {"code": v.code, "message": v.message, "suggestion": v.suggestion}
                        for v in result.violations
                        if v.severity.name == "ERROR"
                    ],
                    "suggested_action": result.suggested_action,
                }

            # 应用自动修复
            message = result.cleaned

            # P4: 长消息降级
            if result.needs_doc_import and self.enable_doc_import:
                return self._handle_doc_import(message)

        # ── Step 2: CardRouter 路由 ──
        if self.enable_routing:
            from molib.shared.publish.feishu_card_router import (
                FeishuCardRouter,
                Fmt,
            )

            fmt = FeishuCardRouter.route(message, ctx)

            if fmt != Fmt.TEXT:
                # 需要卡片格式 → 走 CardRouter.render()
                payload = FeishuCardRouter.render(message, d, ctx)

                if payload.get("msg_type") == "interactive":
                    # 发送互动卡片
                    card_dict = payload.get("card", payload)
                    send_result = self._sender.send_card(card_dict, self.chat_id)
                    return {
                        "status": "routed",
                        "format": fmt.value,
                        "send_result": send_result,
                    }

        # ── Step 3: 纯文本发送 ──
        send_result = self._sender.send_text(self.chat_id, message)
        return {
            "status": "sent",
            "format": "text",
            "send_result": send_result,
        }

    def send_card(
        self,
        card_dict: dict,
        skip_validation: bool = False,
    ) -> dict:
        """直接发送飞书互动卡片（跳过路由，仅验证）。

        Args:
            card_dict: 飞书卡片 JSON
            skip_validation: 跳过 pre_send 验证

        Returns:
            发送结果
        """
        if not skip_validation and self.enable_validation:
            # 提取卡片中的文本进行验证
            text_parts = _extract_card_text(card_dict)
            full_text = " ".join(text_parts)

            from molib.infra.gateway.feishu_pre_send import validate
            result = validate(full_text)

            if result.has_errors():
                logger.warning("[Enforcer] Card blocked by validation")
                return {
                    "status": "blocked",
                    "violations": [
                        {"code": v.code, "message": v.message, "suggestion": v.suggestion}
                        for v in result.violations
                        if v.severity.name == "ERROR"
                    ],
                }

        send_result = self._sender.send_card(card_dict, self.chat_id)
        return {"status": "sent", "send_result": send_result}

    def send_alert(
        self,
        alert_title: str,
        what_happened: str,
        impact: str,
        action_needed: str,
    ) -> dict:
        """便捷方法：发送 T4 告警卡片。

        自动使用 3 句话原则 + 红色 header。
        """
        from molib.shared.publish.feishu_card_router import FeishuCardRouter

        message = (
            f"**发生了什么：**{what_happened}\n"
            f"**影响：**{impact}\n"
            f"**需要做：**{action_needed}"
        )

        payload = FeishuCardRouter.render(
            message=message,
            data={"alert_title": alert_title},
            ctx={"is_error": True},
        )

        if payload.get("msg_type") == "interactive":
            card_dict = payload.get("card", payload)
            send_result = self._sender.send_card(card_dict, self.chat_id)
            return {"status": "alert_sent", "send_result": send_result}

        return {"status": "error", "message": "Failed to build alert card"}

    def send_briefing(
        self,
        title: str,
        fields: dict[str, str],
        color: str = "turquoise",
        note: str = "",
    ) -> dict:
        """便捷方法：发送 T1 数据简报卡片。"""
        from molib.shared.publish.feishu_card_router import FeishuCardRouter

        payload = FeishuCardRouter.render(
            message=f"{title}\n" + "\n".join(f"**{k}:** {v}" for k, v in fields.items()),
            data={"title": title, "fields": fields, "color": color},
            ctx={"field_count": len(fields), "is_cron": True},
        )

        card_dict = payload.get("card", payload)
        if note:
            from molib.ceo.cards.builder import CardBuilder
            card = CardBuilder(title, color)
            for k, v in fields.items():
                card.add_field(k, v)
            card.add_note(note)
            card_dict = card.build()

        send_result = self._sender.send_card(card_dict, self.chat_id)
        return {"status": "briefing_sent", "send_result": send_result}

    def _handle_doc_import(self, message: str) -> dict:
        """长消息降级：写入 Markdown → doc import → 返回链接"""
        try:
            import tempfile
            from datetime import datetime

            ts = datetime.now().strftime("%m-%d %H:%M")

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8",
            ) as f:
                f.write(message)
                md_path = f.name

            doc_result = self._sender.doc_create(
                title=f"墨麟OS · 详细报告 ({ts})",
                content_path=md_path,
            )

            Path(md_path).unlink(missing_ok=True)

            doc_url = doc_result.get("url", doc_result.get("data", {}).get("url", ""))
            summary = message[:200].replace("\n", " ") + "…"

            # 发送摘要 + 链接
            if doc_url:
                self._sender.send_text(
                    self.chat_id,
                    f"📄 详细报告已生成\n{summary}\n\n🔗 {doc_url}",
                )

            return {
                "status": "doc_imported",
                "doc_url": doc_url,
                "summary": summary,
            }
        except Exception as e:
            logger.error("[Enforcer] doc_import failed: %s", e)
            # 降级：发送截断版本
            truncated = message[:1000] + "\n\n⚠️ 消息过长，完整内容导入失败"
            self._sender.send_text(self.chat_id, truncated)
            return {"status": "truncated", "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _extract_card_text(card_dict: dict) -> list[str]:
    """从飞书卡片 JSON 中提取所有文本内容（用于验证）"""
    texts = []

    if isinstance(card_dict, dict):
        header = card_dict.get("header", {})
        if isinstance(header, dict):
            title = header.get("title", {})
            if isinstance(title, dict):
                texts.append(title.get("content", ""))

        elements = card_dict.get("elements", [])
        for elem in elements:
            if isinstance(elem, dict):
                tag = elem.get("tag", "")
                if tag == "div":
                    text = elem.get("text", {})
                    if isinstance(text, dict):
                        texts.append(text.get("content", ""))
                elif tag == "note":
                    text = elem.get("text", {})
                    if isinstance(text, dict):
                        texts.append(text.get("content", ""))

    return texts


# ═══════════════════════════════════════════════════════════════
# 便捷工厂函数
# ═══════════════════════════════════════════════════════════════

def create_enforcer(chat_id: str) -> FeishuOutputEnforcer:
    """快捷创建强制执行器"""
    return FeishuOutputEnforcer(chat_id=chat_id)


def send_safe(
    message: str,
    chat_id: str,
    context: Optional[dict] = None,
) -> dict:
    """最简调用：文本消息自动验证+路由+发送"""
    enforcer = FeishuOutputEnforcer(chat_id=chat_id)
    return enforcer.send(message, context)
