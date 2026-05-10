"""
墨麟AIOS 飞书互动卡片模块 — FeishuCard
========================================

提供飞书消息卡片构建、渲染与发送能力，支持 5 种预设卡片类型及
按钮交互（含 pending_approval 审批态）。

卡片类型：
- CardType.SUCCESS      成功通知（绿色头部）
- CardType.FAILURE      失败告警（红色头部）
- CardType.APPROVAL     审批请求（橙色头部·带交互按钮）
- CardType.DAILY_BRIEF  每日简报（蓝色头部·多栏布局）
- CardType.ALERT        紧急告警（红色头部·高亮元素）

依赖：Python 标准库 + requests（发送 webhook）

参考项目：
- 飞书开放平台卡片搭建工具 (Feishu Card Builder)
- Lark Base 消息卡片文档
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# 枚举
# ═══════════════════════════════════════════════════════════════

class CardType(Enum):
    """飞书卡片类型枚举。

    每种类型对应不同的头部颜色、元素布局与按钮策略。
    """
    SUCCESS     = "success"       # 成功通知 — 绿色
    FAILURE     = "failure"       # 失败告警 — 红色
    APPROVAL    = "approval"      # 审批请求 — 橙色·需按钮交互
    DAILY_BRIEF = "daily_brief"   # 每日简报 — 蓝色·多栏
    ALERT       = "alert"         # 紧急告警 — 深红·高亮


# ═══════════════════════════════════════════════════════════════
# 卡片模板的头部颜色映射
# ═══════════════════════════════════════════════════════════════

_HEADER_TEMPLATES: Dict[CardType, str] = {
    CardType.SUCCESS:     "green",
    CardType.FAILURE:     "red",
    CardType.APPROVAL:    "orange",
    CardType.DAILY_BRIEF: "blue",
    CardType.ALERT:       "carmine",
}

# 审批状态常量
APPROVAL_PENDING  = "pending_approval"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"


# ═══════════════════════════════════════════════════════════════
# 按钮数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class CardButton:
    """飞书卡片按钮定义。

    Attributes:
        text: 按钮显示文本
        value: 按钮携带的值（用于回调识别）
        button_type: 按钮类型 — 'default' / 'primary' / 'danger'
        multi_url: 点击跳转 URL（若提供则忽略 value）
        confirm: 是否需要二次确认（仅对危险操作有效）
    """
    text: str
    value: str = ""
    button_type: str = "default"
    multi_url: Optional[str] = None
    confirm: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转为飞书按钮 JSON 结构。"""
        btn: Dict[str, Any] = {
            "tag": "button",
            "text": {"tag": "plain_text", "content": self.text},
            "type": self.button_type,
        }
        if self.multi_url:
            btn["multi_url"] = {"url": self.multi_url, "pc_url": "", "android_url": "", "ios_url": ""}
        else:
            btn["value"] = self.value

        if self.confirm:
            btn["confirm"] = {
                "title": {"tag": "plain_text", "content": "确认操作"},
                "text":  {"tag": "plain_text", "content": f"确定要 {self.text} 吗？"},
            }
        return btn


# ═══════════════════════════════════════════════════════════════
# 核心 API
# ═══════════════════════════════════════════════════════════════

def build_card(
    card_type: CardType,
    title: str,
    content: str,
    buttons: Optional[List[CardButton]] = None,
    *,
    subtitle: str = "",
    extra_fields: Optional[Dict[str, str]] = None,
    pending_approval: bool = False,
) -> Dict[str, Any]:
    """构建飞书消息卡片 JSON。

    根据 card_type 选择模板，组装 header + elements + buttons。

    Args:
        card_type:   卡片类型（SUCCESS / FAILURE / APPROVAL / DAILY_BRIEF / ALERT）
        title:       卡片主标题
        content:     卡片正文内容（支持 Markdown）
        buttons:     按钮列表（CardButton 对象），APPROVAL 类型默认追加审批按钮
        subtitle:    副标题（可选）
        extra_fields:额外键值对字段，以飞书 field 元素展示
        pending_approval: 是否处于待审批状态（仅 APPROVAL 类型生效）

    Returns:
        飞书消息卡片 JSON（可直接传入 send_card_via_webhook 或飞书 API）
    """
    header_color = _HEADER_TEMPLATES[card_type]
    elements: List[Dict[str, Any]] = []

    # ── 标题块 ──────────────────────────────────────────
    title_block: Dict[str, Any] = {
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**{_escape_md(title)}**",
        },
    }
    elements.append(title_block)

    if subtitle:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": _escape_md(subtitle)},
        })

    # ── 分隔线 ──────────────────────────────────────────
    elements.append({"tag": "hr"})

    # ── 正文内容 ────────────────────────────────────────
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": content},
    })

    # ── 额外字段（key-value） ───────────────────────────
    if extra_fields:
        for key, val in extra_fields.items():
            elements.append({
                "tag": "div",
                "fields": [
                    {"is_short": True, "text": {"tag": "lark_md", "content": f"**{_escape_md(key)}**"}},
                    {"is_short": True, "text": {"tag": "lark_md", "content": _escape_md(val)}},
                ],
            })

    # ── 备注（审批态标识） ──────────────────────────────
    if card_type == CardType.APPROVAL and pending_approval:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "note",
            "elements": [{
                "tag": "plain_text",
                "content": "⏳ 等待审批中… 请点击上方按钮操作",
            }],
        })

    # ── 按钮处理 ────────────────────────────────────────
    btn_list: List[CardButton] = list(buttons) if buttons else []

    if card_type == CardType.APPROVAL:
        if not any(b.value == APPROVAL_APPROVED for b in btn_list):
            btn_list.append(CardButton("✅ 批准", APPROVAL_APPROVED, "primary"))
        if not any(b.value == APPROVAL_REJECTED for b in btn_list):
            btn_list.append(CardButton("❌ 驳回", APPROVAL_REJECTED, "danger", confirm=True))

    # ── 每日简报：自动追加核按钮 ────────────────────────
    if card_type == CardType.DAILY_BRIEF:
        if not btn_list:
            btn_list.append(CardButton("📊 查看详情", "view_detail", "primary"))

    # ── 组装最终卡片 ────────────────────────────────────
    card: Dict[str, Any] = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": title,
            },
            "template": header_color,
        },
        "elements": elements,
    }

    if btn_list:
        card["elements"].append({
            "tag": "action",
            "actions": [b.to_dict() for b in btn_list],
        })

    return card


def send_card_via_webhook(
    card_json: Dict[str, Any],
    webhook_url: str,
    *,
    timeout: int = 10,
) -> Dict[str, Any]:
    """通过飞书 Webhook 发送卡片消息。

    Args:
        card_json:   build_card() 或手工构建的卡片 JSON
        webhook_url: 飞书机器人 Webhook 地址
        timeout:     HTTP 请求超时（秒）

    Returns:
        {"ok": True, "status_code": 200, "response": {...}}
        失败返回 {"ok": False, "error": str}
    """
    payload = {
        "msg_type": "interactive",
        "card": card_json,
    }

    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            timeout=timeout,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("StatusCode") == 0:
            logger.info("飞书卡片发送成功: status=%s", resp.status_code)
            return {"ok": True, "status_code": resp.status_code, "response": data}
        else:
            logger.warning("飞书卡片发送失败: status=%s body=%s", resp.status_code, data)
            return {"ok": False, "status_code": resp.status_code, "error": data}
    except requests.RequestException as exc:
        logger.error("飞书卡片发送异常: %s", exc)
        return {"ok": False, "error": str(exc)}


# ═══════════════════════════════════════════════════════════════
# 便捷工厂函数（每种类型一个快捷入口）
# ═══════════════════════════════════════════════════════════════

def success_card(title: str, content: str, **kwargs: Any) -> Dict[str, Any]:
    """构建成功通知卡片。"""
    return build_card(CardType.SUCCESS, title, content, **kwargs)


def failure_card(title: str, content: str, **kwargs: Any) -> Dict[str, Any]:
    """构建失败告警卡片。"""
    return build_card(CardType.FAILURE, title, content, **kwargs)


def approval_card(title: str, content: str, **kwargs: Any) -> Dict[str, Any]:
    """构建审批请求卡片（默认附带 批准/驳回 按钮）。"""
    return build_card(CardType.APPROVAL, title, content, **kwargs)


def daily_brief_card(title: str, content: str, **kwargs: Any) -> Dict[str, Any]:
    """构建每日简报卡片。"""
    return build_card(CardType.DAILY_BRIEF, title, content, **kwargs)


def alert_card(title: str, content: str, **kwargs: Any) -> Dict[str, Any]:
    """构建紧急告警卡片。"""
    return build_card(CardType.ALERT, title, content, **kwargs)


# ═══════════════════════════════════════════════════════════════
# 私有工具
# ═══════════════════════════════════════════════════════════════

def _escape_md(text: str) -> str:
    """对飞书 lark_md 中特殊字符做最小转义。

    仅转义正文中可能破坏格式的字符，保留 Markdown 标记。
    """
    # 飞书 lark_md 对 < > 敏感，需转义以防 XSS/渲染错误
    return text.replace("<", "\\<").replace(">", "\\>")
