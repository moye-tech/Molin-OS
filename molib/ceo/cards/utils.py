"""墨麟OS — 飞书卡片工具函数

提供 card_to_text 等通用工具函数。
"""
import json
import logging

logger = logging.getLogger("molin.ceo.cards.utils")


def card_to_text(card_dict: dict) -> str:
    """将卡片字典转为纯文本（供 Hermes send_message 降级使用）"""
    title = card_dict.get("header", {}).get("title", {}).get("content", "")
    lines = [f"━━━ {title} ━━━", ""]
    for el in card_dict.get("elements", []):
        tag = el.get("tag")
        if tag == "div":
            lines.append(el.get("text", {}).get("content", ""))
        elif tag == "hr":
            lines.append("───")
        elif tag == "column_set":
            for col in el.get("columns", []):
                vals = [e.get("text", {}).get("content", "").replace("**", "") for e in col.get("elements", [])]
                lines.append(" | ".join(vals))
        elif tag == "note":
            lines.append(el.get("text", {}).get("content", ""))
        elif tag == "action":
            for act in el.get("actions", []):
                lines.append(f"[ {act.get('text', {}).get('content', '')} ]")
    return "\n".join(lines)


__all__ = ["card_to_text"]
