""""
墨麟OS — 美观版结果卡片 (result_card_v7 吸收)
=================================================
⚠️ 已弃用 — 请使用 molib.ceo.feishu_card 中的 CardBuilder / build_*_card 系列函数。

从 molin-os-ultra/integrations/feishu/result_card_v7.py 吸收的历史函数。
为保持向后兼容保留此文件，新代码应直接使用 feishu_card 模块。

用法（新）：
    from molib.ceo.feishu_card import CardBuilder, build_simple_card, build_report_card
    card = CardBuilder("标题").add_div("内容").build_json()

如发现此文件中某函数无对应替代，请将其迁移到 feishu_card.py 后删除此文件。
"""

import json
import logging
import re
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger("molin.ceo.result_card_v7")

# ── 工具函数 ──────────────────────────────────────────────────

def strip_markdown(text: str) -> str:
    """将Markdown转飞书lark_md安全格式"""
    if not text:
        return ""
    text = re.sub(r'^#{1,6}\s*(.+)$', r'**\1**', text, flags=re.MULTILINE)
    text = re.sub(r'^[-=]{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def truncate(text: str, max_len: int = 200, suffix: str = "…") -> str:
    text = strip_markdown(text)
    if len(text) <= max_len:
        return text
    return text[:max_len] + suffix


def _agency_display_name(agency_id: str) -> str:
    names = {
        "growth": "增长部", "research": "研究部", "edu": "教培部",
        "ads": "广告部", "crm": "私域运营", "bd": "商务拓展",
        "ip": "内容IP部", "dev": "开发部", "ai": "AI工程部",
        "shop": "成交部", "data": "数据分析", "finance": "财务部",
        "cs": "客服部", "legal": "法务部", "knowledge": "知识管理",
        "global_market": "全球市场", "devops": "运维部",
        "order": "订单管理", "secure": "安全合规", "product": "产品部",
        # 兼容我们的子公司名
        "content_writer": "墨笔文创", "designer": "墨图设计",
        "research": "墨研竞情", "crm": "墨域私域",
        "ecommerce": "墨链电商", "bd": "墨商BD",
    }
    return names.get(agency_id, agency_id.upper())


def _status_icon(status: str) -> str:
    return {
        "executed": "✅", "llm_executed": "✅", "success": "✅",
        "completed": "✅", "pending_approval": "⏳", "running": "⚙️",
        "error": "❌", "failed": "❌", "skipped": "⏭️",
    }.get(status, "🔄")


def _extract_key_points(text: str, max_points: int = 4) -> list[str]:
    """从长文本中提取关键要点"""
    lines = text.split('\n')
    points = []
    for line in lines:
        line = line.strip()
        if re.match(r'^[\d]+[\.、]\s+.{10,}', line):
            points.append(re.sub(r'^[\d]+[\.、]\s+', '', line))
        elif re.match(r'^[-*•]\s+.{10,}', line):
            points.append(re.sub(r'^[-*•]\s+', '', line))
        elif line.startswith('**') and len(line) < 60:
            points.append(line.replace('**', ''))
        if len(points) >= max_points:
            break
    return points


# ── CEO 回复卡片 ────────────────────────────────────────────

def build_ceo_response_card(
    understanding: str = "",
    assumption: str = "",
    ceo_response: str = "",
    state_action: str = "direct_response",
    dispatch_plan: Optional[list[dict]] = None,
    pending_question: Optional[str] = None,
    risks: Optional[list[str]] = None,
    session_id: str = "",
) -> dict:
    """CEO回复类卡片（exploring/clarifying/dispatching/direct_response）"""
    elements = []

    if understanding:
        elements.append({"tag": "div", "text": {"tag": "lark_md",
            "content": f"**📌 我的理解**\n{strip_markdown(understanding)}"}})

    if assumption and assumption.strip():
        elements.append({"tag": "div", "text": {"tag": "lark_md",
            "content": f"*💡 合理假设：{strip_markdown(assumption)}*"}})

    elements.append({"tag": "hr"})

    clean_response = strip_markdown(ceo_response)
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": clean_response}})

    # 派发计划
    if state_action == "dispatching" and dispatch_plan:
        elements.append({"tag": "hr"})
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "**🚀 正在派发任务**"}})
        for item in dispatch_plan[:6]:
            agency = item.get("agency", "")
            task_desc = item.get("task", "")
            priority = item.get("priority", "medium")
            p_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            elements.append({"tag": "div", "text": {"tag": "lark_md",
                "content": f"{p_icon} **{_agency_display_name(agency)}**: {truncate(task_desc, 60)}"}})

    # 待回答问题
    if pending_question:
        elements.append({"tag": "hr"})
        elements.append({"tag": "div", "text": {"tag": "lark_md",
            "content": f"**❓ 需要确认**\n{strip_markdown(pending_question)}"}})

    # 风险提示
    if risks:
        elements.append({"tag": "hr"})
        risk_lines = "\n".join([f"⚠️ {strip_markdown(r)}" for r in risks[:2]])
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": risk_lines}})

    elements.append({"tag": "note", "elements": [{
        "tag": "plain_text",
        "content": f"{time.strftime('%H:%M')} · 墨麟OS · {session_id[:8] if session_id else '—'}"
    }]})

    state_template = {"dispatching": "blue", "clarifying": "orange",
                       "exploring": "wathet", "direct_response": "turquoise"}.get(state_action, "blue")
    state_title = {"dispatching": "🚀 任务派发中", "clarifying": "🤔 需要确认一个问题",
                    "exploring": "💬 理解需求中", "direct_response": "💡 直接回答"}.get(state_action, "💬 CEO")

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": state_title}, "template": state_template},
        "elements": elements,
    }


# ── 执行结果卡片 ────────────────────────────────────────────

def build_execution_result_card(
    understanding: str = "",
    synthesized_summary: str = "",
    agency_results: Optional[list[dict]] = None,
    cost: float = 0.0,
    latency: float = 0.0,
    session_id: str = "",
    detail_ids: Optional[dict[str, str]] = None,
) -> dict:
    """任务执行完成卡片 — 美观版
    结构：理解摘要 → 合成人话 → 子公司字段组 → 底部元信息
    """
    elements = []

    if understanding:
        elements.append({"tag": "div", "text": {"tag": "lark_md",
            "content": f"**📌 我的理解**\n{strip_markdown(understanding)}"}})
        elements.append({"tag": "hr"})

    clean_summary = strip_markdown(synthesized_summary)
    elements.append({"tag": "div", "text": {"tag": "lark_md", "content": clean_summary}})

    # 子公司结果明细（字段组格式）
    if agency_results:
        elements.append({"tag": "hr"})
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "**📊 各部门执行情况**"}})

        fields = []
        for r in agency_results:
            agency_id = r.get("agency", "?")
            status = r.get("status", "unknown")
            output = r.get("output", "")
            icon = _status_icon(status)
            name = _agency_display_name(agency_id)
            preview = truncate(output, 50) if output else "已完成"
            fields.append({
                "is_short": True,
                "text": {"tag": "lark_md", "content": f"{icon} **{name}**\n{preview}"}
            })

        for i in range(0, len(fields), 2):
            elements.append({"tag": "div", "fields": fields[i:i+2]})

    # 各子公司"查看完整报告"按钮
    actions = []
    detail_ids = detail_ids or {}
    shown = 0
    for r in (agency_results or []):
        if shown >= 3:
            break
        agency_id = r.get("agency", "")
        did = detail_ids.get(agency_id, "")
        status = r.get("status", "")
        if status in ("executed", "llm_executed", "success", "completed") and did:
            actions.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": f"📄 {_agency_display_name(agency_id)}完整报告"},
                "type": "default",
            })
            shown += 1

    if actions:
        elements.append({"tag": "hr"})
        elements.append({"tag": "action", "actions": actions})

    # 底部元信息
    meta_parts = [f"🕐 {time.strftime('%H:%M:%S')}"]
    if latency > 0:
        meta_parts.append(f"⚡ {latency:.1f}s")
    if cost > 0:
        meta_parts.append(f"¥{cost:.4f}")
    if session_id:
        meta_parts.append(f"ID: {session_id[:8]}")
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "  ·  ".join(meta_parts)}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "✅ 任务完成"}, "template": "green"},
        "elements": elements,
    }


# ── 错误卡片 ────────────────────────────────────────────────

def build_error_card_v7(
    error_message: str,
    understanding: str = "",
    partial_results: Optional[list[dict]] = None,
    session_id: str = "",
) -> dict:
    """执行失败卡片"""
    elements = []

    if understanding:
        elements.append({"tag": "div", "text": {"tag": "lark_md",
            "content": f"*📌 {strip_markdown(understanding)}*"}})
        elements.append({"tag": "hr"})

    elements.append({"tag": "div", "text": {"tag": "lark_md",
        "content": f"**遇到了问题**\n{strip_markdown(error_message)}"}})

    if partial_results:
        success = [r for r in partial_results if r.get("status") in ("executed", "success", "llm_executed")]
        failed = [r for r in partial_results if r.get("status") == "error"]

        if success:
            elements.append({"tag": "hr"})
            lines = ["**✅ 已完成**"] + [
                f"• {_agency_display_name(r.get('agency','?'))}: {truncate(r.get('output',''), 60)}"
                for r in success
            ]
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})

        if failed:
            elements.append({"tag": "hr"})
            lines = ["**❌ 失败**"] + [
                f"• {_agency_display_name(r.get('agency','?'))}: {truncate(r.get('error',''), 60)}"
                for r in failed
            ]
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})

    elements.append({"tag": "hr"})
    elements.append({"tag": "action", "actions": [{
        "tag": "button", "text": {"tag": "plain_text", "content": "🔄 重试"},
        "type": "primary",
    }]})
    elements.append({"tag": "note", "elements": [{
        "tag": "plain_text",
        "content": f"🕐 {time.strftime('%H:%M:%S')}  ·  {session_id[:8] if session_id else '—'}"
    }]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "❌ 执行遇到问题"}, "template": "red"},
        "elements": elements,
    }
