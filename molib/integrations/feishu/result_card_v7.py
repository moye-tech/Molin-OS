"""
飞书结果卡片 — 美观版
重构要点：
  1. 彻底解决 raw markdown 显示问题（原始##/*/` 符号泄露到卡片）
  2. 摘要 + 折叠详情的层级结构，不再 dump 原始文本
  3. 子公司结果用字段组（field）展示，视觉清晰
  4. CEO 理解意图显示在卡片顶部，让老板知道系统懂了什么
  5. "查看完整报告"统一收纳为底部按钮，不散落在文本里
"""

import re
import json
import time
from typing import Dict, Any, List, Optional
from loguru import logger


# ── 工具函数 ──────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """
    将 Markdown 转为飞书 lark_md 安全格式。
    飞书 lark_md 支持: **bold**, *italic*, `code`, [text](url)
    但不支持: ### 标题, --- 分隔线, > 引用块（会显示原始符号）
    """
    if not text:
        return ""
    # 移除 ### 等标题标记（保留文字，加粗替代）
    text = re.sub(r'^#{1,6}\s*(.+)$', r'**\1**', text, flags=re.MULTILINE)
    # 移除 --- / === 分隔线
    text = re.sub(r'^[-=]{3,}$', '', text, flags=re.MULTILINE)
    # 引用块 > 转为普通文字
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    # 清理多余空行（最多保留1个空行）
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _truncate(text: str, max_len: int = 200, suffix: str = "…") -> str:
    text = _strip_markdown(text)
    if len(text) <= max_len:
        return text
    return text[:max_len] + suffix


def _agency_display_name(agency_id: str) -> str:
    """Agency ID → 中文显示名"""
    names = {
        "growth": "增长部", "research": "研究部", "edu": "教培部",
        "ads": "广告部", "crm": "私域运营", "bd": "商务拓展",
        "ip": "内容IP部", "dev": "开发部", "ai": "AI工程部",
        "shop": "成交部", "data": "数据分析", "finance": "财务部",
        "cs": "客服部", "legal": "法务部", "knowledge": "知识管理",
        "global_market": "全球市场", "devops": "运维部",
        "order": "订单管理", "secure": "安全合规", "product": "产品部",
    }
    return names.get(agency_id, agency_id.upper())


def _status_icon(status: str) -> str:
    return {
        "executed": "✅", "llm_executed": "✅", "success": "✅", "completed": "✅",
        "pending_approval": "⏳", "running": "⚙️",
        "error": "❌", "failed": "❌",
        "skipped": "⏭️",
    }.get(status, "🔄")


def _extract_key_points(text: str, max_points: int = 4) -> List[str]:
    """
    从长文本中提取关键要点（用于折叠前的摘要展示）。
    优先找编号列表、加粗项。
    """
    lines = text.split('\n')
    points = []
    for line in lines:
        line = line.strip()
        # 有序列表、无序列表
        if re.match(r'^[\d]+[\.、]\s+.{10,}', line):
            points.append(re.sub(r'^[\d]+[\.、]\s+', '', line))
        elif re.match(r'^[-*•]\s+.{10,}', line):
            points.append(re.sub(r'^[-*•]\s+', '', line))
        # 加粗开头的行（可能是小标题）
        elif line.startswith('**') and len(line) < 60:
            points.append(line.replace('**', ''))
        if len(points) >= max_points:
            break
    return points


# ── 主卡片构建函数 ──────────────────────────────────────────────

def build_ceo_response_card(
    understanding: str,
    assumption: str,
    ceo_response: str,
    state_action: str = "direct_response",
    dispatch_plan: Optional[List[Dict]] = None,
    pending_question: Optional[str] = None,
    risks: Optional[List[str]] = None,
    session_id: str = "",
) -> Dict[str, Any]:
    """
    CEO 回复类卡片（exploring / clarifying / dispatching / direct_response）
    用于 CEO 正在分析或提问的阶段，尚未有执行结果。
    """
    elements = []

    # ── 头部：CEO 理解摘要 ──
    if understanding:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**📌 我的理解**\n{_strip_markdown(understanding)}"
            }
        })

    # 假设条件（如有）
    if assumption and assumption.strip():
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"*💡 合理假设：{_strip_markdown(assumption)}*"
            }
        })

    elements.append({"tag": "hr"})

    # ── 主回复 ──
    clean_response = _strip_markdown(ceo_response)
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": clean_response}
    })

    # ── 派发计划（dispatching 状态时显示） ──
    if state_action == "dispatching" and dispatch_plan:
        elements.append({"tag": "hr"})
        fields = []
        for item in dispatch_plan[:6]:  # 最多显示6个
            agency = item.get("agency", "")
            task = item.get("task", "")
            priority = item.get("priority", "medium")
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"{priority_icon} **{_agency_display_name(agency)}**\n{_truncate(task, 60)}"
                }
            })
        if fields:
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "**🚀 正在派发任务**"},
            })
            # 每行最多2个字段
            for i in range(0, len(fields), 2):
                elements.append({
                    "tag": "div",
                    "fields": fields[i:i+2]
                })

    # ── 待回答问题（clarifying 状态） ──
    if pending_question:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**❓ 需要确认**\n{_strip_markdown(pending_question)}"
            }
        })

    # ── 风险提示（如有） ──
    if risks:
        elements.append({"tag": "hr"})
        risk_lines = "\n".join([f"⚠️ {_strip_markdown(r)}" for r in risks[:2]])
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": risk_lines}
        })

    # ── 底部 Note ──
    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": f"{time.strftime('%H:%M')} · 墨麟AI · {session_id[:8] if session_id else '—'}"
        }]
    })

    # ── 标题颜色 ──
    state_template = {
        "dispatching": "blue",
        "clarifying": "orange",
        "exploring": "wathet",
        "direct_response": "turquoise",
    }.get(state_action, "blue")

    state_title = {
        "dispatching": "🚀 任务派发中",
        "clarifying": "🤔 需要确认一个问题",
        "exploring": "💬 理解需求中",
        "direct_response": "💡 直接回答",
    }.get(state_action, "💬 Hermes CEO")

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": state_title},
            "template": state_template,
        },
        "elements": elements,
    }


def build_execution_result_card(
    understanding: str,
    synthesized_summary: str,
    agency_results: List[Dict[str, Any]],
    cost: float = 0.0,
    latency: float = 0.0,
    session_id: str = "",
    file_links: Optional[List[Dict]] = None,
    detail_ids: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    任务执行完成卡片 — 美观版。

    结构：
    ┌─────────────────────────────┐
    │  ✅ 任务完成                  │ ← 绿色头部
    ├─────────────────────────────┤
    │  📌 我的理解：[understanding]  │
    ├─────────────────────────────┤
    │  [synthesized_summary]       │ ← CEO 合成的人话摘要
    ├─────────────────────────────┤
    │  子公司执行明细               │ ← 字段组，视觉清晰
    │  ✅ 增长部 | ✅ 研究部 | ...   │
    ├─────────────────────────────┤
    │  [查看增长部完整报告] [下载]    │ ← 按钮，不在文本里
    └─────────────────────────────┘
    """
    elements = []

    # ── CEO 理解 ──
    if understanding:
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**📌 我的理解**\n{_strip_markdown(understanding)}"
            }
        })
        elements.append({"tag": "hr"})

    # ── 合成摘要（最重要） ──
    clean_summary = _strip_markdown(synthesized_summary)
    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": clean_summary}
    })

    # ── 子公司结果明细 ──
    if agency_results:
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": "**📊 各部门执行情况**"}
        })

        # 字段组：每行2个
        fields = []
        for r in agency_results:
            agency_id = r.get("agency", "?")
            status = r.get("status", "unknown")
            output = r.get("output", "")
            icon = _status_icon(status)
            name = _agency_display_name(agency_id)
            preview = _truncate(output, 50) if output else "已完成"
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"{icon} **{name}**\n{preview}"
                }
            })

        for i in range(0, len(fields), 2):
            elements.append({
                "tag": "div",
                "fields": fields[i:i+2]
            })

    # ── 操作按钮 ──
    actions = []

    # 各子公司"查看完整报告"按钮（最多3个，不是每个都展示）
    detail_ids = detail_ids or {}
    shown_detail = 0
    for r in agency_results:
        if shown_detail >= 3:
            break
        agency_id = r.get("agency", "")
        detail_id = detail_ids.get(agency_id, "")
        status = r.get("status", "")
        if status in ("executed", "llm_executed", "success", "completed") and detail_id:
            actions.append({
                "tag": "button",
                "text": {"tag": "plain_text", "content": f"📄 {_agency_display_name(agency_id)}完整报告"},
                "type": "default",
                "value": {"action": "view_detail", "detail_id": detail_id}
            })
            shown_detail += 1

    # 文件下载按钮
    if file_links:
        for fl in file_links[:2]:
            url = fl.get("url", "")
            name = fl.get("name", "下载文件")
            if url:
                actions.append({
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": f"⬇️ {name}"},
                    "type": "primary",
                    "url": url
                })

    if actions:
        elements.append({"tag": "hr"})
        elements.append({"tag": "action", "actions": actions})

    # ── 底部元信息 ──
    meta_parts = [f"🕐 {time.strftime('%H:%M:%S')}"]
    if latency > 0:
        meta_parts.append(f"⚡ {latency:.1f}s")
    if cost > 0:
        meta_parts.append(f"¥{cost:.4f}")
    if session_id:
        meta_parts.append(f"ID: {session_id[:8]}")
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": "  ·  ".join(meta_parts)}]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "✅ 任务完成"},
            "template": "green",
        },
        "elements": elements,
    }


def build_error_card_v7(
    error_message: str,
    understanding: str = "",
    partial_results: Optional[List[Dict]] = None,
    session_id: str = "",
) -> Dict[str, Any]:
    """执行失败卡片 v7"""
    elements = []

    if understanding:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"*📌 {_strip_markdown(understanding)}*"}
        })
        elements.append({"tag": "hr"})

    elements.append({
        "tag": "div",
        "text": {"tag": "lark_md", "content": f"**遇到了问题**\n{_strip_markdown(error_message)}"}
    })

    if partial_results:
        success = [r for r in partial_results if r.get("status") in ("executed", "success", "llm_executed")]
        failed = [r for r in partial_results if r.get("status") == "error"]

        if success:
            elements.append({"tag": "hr"})
            lines = ["**✅ 已完成**"] + [
                f"• {_agency_display_name(r.get('agency','?'))}: {_truncate(r.get('output',''), 60)}"
                for r in success
            ]
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})

        if failed:
            elements.append({"tag": "hr"})
            lines = ["**❌ 失败**"] + [
                f"• {_agency_display_name(r.get('agency','?'))}: {_truncate(r.get('error',''), 60)}"
                for r in failed
            ]
            elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}})

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "action",
        "actions": [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "🔄 重试"},
                "type": "primary",
                "value": {"action": "retry", "session_id": session_id}
            }
        ]
    })
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"🕐 {time.strftime('%H:%M:%S')}  ·  {session_id[:8] if session_id else '—'}"}]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "❌ 执行遇到问题"},
            "template": "red",
        },
        "elements": elements,
    }


def build_thinking_card(
    understanding: str,
    agencies_dispatched: List[str],
    session_id: str = "",
) -> Dict[str, Any]:
    """
    派发后的"执行中"状态卡片。
    老板发送指令后立即收到这张卡片，告知系统已理解并开始行动。
    """
    elements = []

    elements.append({
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**📌 我的理解**\n{_strip_markdown(understanding)}"
        }
    })
    elements.append({"tag": "hr"})

    if agencies_dispatched:
        lines = ["**正在协调以下部门执行：**"]
        for ag in agencies_dispatched:
            lines.append(f"⚙️ {_agency_display_name(ag)}")
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": "\n".join(lines)}
        })

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": f"🕐 {time.strftime('%H:%M:%S')}  ·  执行中，请稍候…"}]
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "⚙️ 正在执行"},
            "template": "blue",
        },
        "elements": elements,
    }


# ── 内存详情存储（供 get_detail_content 使用） ─────────────────

_detail_store: Dict[str, tuple] = {}


def store_detail_content(detail_id: str, agency_name: str, content: str) -> None:
    """存储子公司完整输出，供点击按钮时取回"""
    _detail_store[detail_id] = (agency_name, content)


def get_detail_content(detail_id: str) -> Optional[tuple]:
    """取回子公司完整输出。返回 (agency_display_name, content) 或 None。"""
    return _detail_store.get(detail_id)


# ── 向后兼容：保留原有函数签名 ────────────────────────────────

def build_result_card_from_response(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    从 CEO API 响应字典自动选择卡片模板（向后兼容原有 bot_main.py 调用）。
    """
    decision = data.get("decision", "")
    session_id = data.get("session_id", "")

    # 执行完成
    if decision == "GO":
        execution = data.get("execution_result", {})
        results = execution.get("results", []) if execution else []
        synthesized = execution.get("synthesized", data.get("message", "")) if execution else data.get("message", "")

        if not results:
            return None

        has_error = any(r.get("status") == "error" for r in results if isinstance(r, dict))
        all_error = all(r.get("status") == "error" for r in results if isinstance(r, dict))

        if all_error:
            return build_error_card_v7(
                error_message="所有子公司执行失败",
                understanding=data.get("understanding", ""),
                partial_results=results,
                session_id=session_id,
            )

        # 注册详情内容（让按钮可以查看完整报告）
        detail_ids = {}
        for r in results:
            if isinstance(r, dict):
                ag = r.get("agency", "")
                output = r.get("output", "")
                if ag and output and len(output) > 100:
                    import uuid
                    did = str(uuid.uuid4())[:12]
                    store_detail_content(did, _agency_display_name(ag), output)
                    detail_ids[ag] = did

        return build_execution_result_card(
            understanding=data.get("understanding", ""),
            synthesized_summary=synthesized or data.get("message", "任务执行完成"),
            agency_results=results,
            cost=data.get("cost", 0.0),
            latency=data.get("latency", 0.0),
            session_id=session_id,
            file_links=execution.get("file_links", []) if execution else [],
            detail_ids=detail_ids,
        )

    # CEO 正在对话（exploring/clarifying/dispatching）
    state_action = data.get("state_action", "direct_response")
    if state_action in ("dispatching", "clarifying", "exploring"):
        dispatch_plan = data.get("dispatch_plan", [])
        pending_questions = data.get("pending_questions", [])
        return build_ceo_response_card(
            understanding=data.get("understanding", ""),
            assumption=data.get("assumption", ""),
            ceo_response=data.get("response", data.get("message", "")),
            state_action=state_action,
            dispatch_plan=dispatch_plan,
            pending_question=pending_questions[0] if pending_questions else None,
            risks=data.get("risks", []),
            session_id=session_id,
        )

    # 直接回答
    if decision in ("DIRECT_RESPONSE",) or state_action == "direct_response":
        msg = data.get("message", data.get("response", ""))
        if not msg:
            return None
        return build_ceo_response_card(
            understanding="",
            assumption="",
            ceo_response=msg,
            state_action="direct_response",
            session_id=session_id,
        )

    return None


# 保留旧函数名（兼容）
build_success_card = None  # 已废弃，使用 build_execution_result_card
build_error_card = build_error_card_v7
