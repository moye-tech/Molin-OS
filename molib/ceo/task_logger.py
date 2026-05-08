"""
墨麟OS — CEO 全链路可视化任务日志
==================================
为 CEO Orchestrator 的 process() 方法提供结构化日志卡片推送。

每个关键阶段推送一张飞书卡片到控制台群，包含：
1. 用户输入
2. CEO意图分析结果
3. 风险评估结果
4. DAG任务分解计划
5. 调度到VP/子公司
6. 子公司执行详情
7. 质量门控结果
8. 最终产出

条件推送：仅在非简单(complexity_score >= 30)任务时推送，避免高频噪声。
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

from molib.ceo.feishu_card import (
    CardBuilder, _timestamp, feishu_send_card,
    BLUE, GREEN, ORANGE, RED, PURPLE, INDIGO, TURQUOISE, YELLOW,
)

logger = logging.getLogger("molin.ceo.task_logger")

# 控制台群聊
CONSOLE_CHAT_ID = "oc_94c87f141e118b68c2da9852bf2f3bda"

# ── 条件判断 ──────────────────────────────────────────────────────────

SIMPLE_THRESHOLD = 30  # complexity_score < 30 视为简单任务，不推送


def should_push_log(intent: Any) -> bool:
    """判断是否推送日志：非简单任务才推送"""
    try:
        return intent.complexity_score >= SIMPLE_THRESHOLD
    except AttributeError:
        return True


# ── 阶段1: 用户输入 & 意图分析 ───────────────────────────────────

def build_intent_card(
    task_id: str,
    user_input: str,
    intent: Any,
    elapsed: float,
) -> dict:
    """阶段1卡片：用户输入 + 意图分析结果"""
    risk_icon = {
        "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴",
    }.get(intent.risk_level, "⚪")

    route_source_labels = {
        "trivial": "闲聊拦截",
        "cache": "缓存命中",
        "llm": "LLM语义路由",
        "keyword": "关键词兜底",
        "empty": "空输入",
    }

    vps_str = ", ".join(intent.target_vps) if intent.target_vps else "（待定）"
    subs_str = ", ".join(intent.target_subsidiaries) if intent.target_subsidiaries else "（待定）"

    card = CardBuilder(f"🧠 步骤① 意图分析 · {task_id[:8]}", PURPLE)
    card.add_field("📝 用户输入", user_input[:300])
    card.add_hr()

    card.add_fields_row([
        ("🎯 意图类型", intent.intent_type),
        ("📊 复杂度", f"{intent.complexity_score:.1f}/100"),
    ])
    card.add_fields_row([
        (f"{risk_icon} 风险等级", intent.risk_level),
        ("🎯 路由来源", route_source_labels.get(intent.route_source, intent.route_source)),
    ])
    card.add_field("🏢 目标 VP", vps_str)
    card.add_field("🏭 目标子公司", subs_str)
    if intent.entities:
        card.add_field("🔍 实体提取", str(intent.entities)[:200])
    card.add_field("🔑 任务 ID", f"`{task_id}`")

    card.add_hr()
    card.add_note(f"耗时: {elapsed:.2f}s · 墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


# ── 阶段2: 风险评估 ──────────────────────────────────────────────

def build_risk_card(
    task_id: str,
    risk: Any,
    elapsed: float,
) -> dict:
    """阶段2卡片：风险评估结果"""
    risk_color = RED if risk.risk_score > 80 else (ORANGE if risk.risk_score > 60 else GREEN)
    risk_emoji = "🔴" if risk.risk_score > 80 else ("🟡" if risk.risk_score > 60 else "🟢")

    card = CardBuilder(f"{risk_emoji} 步骤② 风险评估 · {task_id[:8]}", risk_color)

    card.add_fields_row([
        ("📊 综合评分", f"{risk.risk_score:.1f}/100"),
        ("✅ 需要审批", "是" if risk.requires_approval else "否"),
    ])
    card.add_fields_row([
        ("💰 资金风险", f"{risk.financial_risk:.1f}"),
        ("📋 合规风险", f"{risk.compliance_risk:.1f}"),
    ])
    card.add_fields_row([
        ("⚖️ 法律风险", f"{risk.legal_risk:.1f}"),
        ("🔒 隐私风险", f"{risk.privacy_risk:.1f}"),
    ])

    if risk.flags:
        card.add_hr()
        card.add_section("🚩 触发的风险标记", [f"· {f.get('reason', str(f))}" for f in risk.flags[:5]])

    if risk.reason:
        card.add_hr()
        card.add_field("📋 说明", risk.reason[:300])

    if risk.risk_score > 80:
        card.add_hr()
        card.add_div("**⛔ 高风险 — 任务已被拒绝**")
    elif risk.risk_score > 60:
        card.add_div("**⚠️ 中高风险 — 需要审批**")

    card.add_hr()
    card.add_note(f"耗时: {elapsed:.2f}s · 墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


# ── 阶段3: DAG任务分解 ──────────────────────────────────────────

def build_dag_card(
    task_id: str,
    dag: Any,
    elapsed: float,
) -> dict:
    """阶段3卡片：DAG任务分解计划"""
    card = CardBuilder(f"📋 步骤③ 任务分解 · {task_id[:8]}", INDIGO)

    card.add_fields_row([
        ("📊 总步数", f"{len(dag.tasks)}"),
        ("⚡ 并行组", f"{len(dag.parallel_groups)}"),
    ])
    card.add_field("⏱️ 预估耗时", f"{dag.total_sp}s")

    # 任务列表
    card.add_hr()
    steps_lines = []
    for i, task in enumerate(dag.tasks):
        deps = f" ← {','.join(task.depends_on)}" if task.depends_on else ""
        vp_info = f" [{task.assigned_vp}]" if task.assigned_vp else ""
        model_info = f" ({task.model_tier})" if task.model_tier else ""
        steps_lines.append(f"**{i+1}.** `{task.step_id}`{model_info}: {task.description}{deps}{vp_info}")

    card.add_section("🔄 执行步骤", steps_lines)

    # 并行组
    if dag.parallel_groups:
        group_desc = []
        for g in dag.parallel_groups:
            names = [dag.tasks[j].step_id for j in g]
            group_desc.append(f"· {' + '.join(names)}")
        card.add_hr()
        card.add_section("⚡ 可并行执行", group_desc)

    card.add_hr()
    card.add_note(f"耗时: {elapsed:.2f}s · 墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


# ── 阶段4: VP调度与执行 ─────────────────────────────────────────

def build_execution_card(
    task_id: str,
    execution_result: dict,
    elapsed: float,
) -> dict:
    """阶段4卡片：VP调度与子公司执行结果"""
    status = execution_result.get("status", "unknown")
    status_emoji = {"completed": "✅", "partial": "⚠️", "error": "❌", "skipped": "⏭️"}.get(status, "❓")

    card = CardBuilder(f"{status_emoji} 步骤④ VP执行 · {task_id[:8]}", TURQUOISE)

    vps_used = execution_result.get("vps_used", [])
    card.add_field("🎯 调度 VP", ", ".join(v["name"] for v in vps_used) if vps_used else "（无）")

    # 质量摘要
    qs = execution_result.get("quality_summary", {})
    if qs:
        card.add_fields_row([
            ("📊 平均质量", f"{qs.get('avg_score', 0)}"),
            ("✅ 通过数", f"{qs.get('passed_count', 0)}/{qs.get('total', 0)}"),
        ])

    # DAG摘要
    dag_summary = execution_result.get("dag_summary")
    if dag_summary:
        card.add_field("📋 DAG步数", f"{dag_summary.get('total_steps', 0)} 步 / {dag_summary.get('estimated_duration_s', 0)}s 预估")

    # 每个VP的执行详情
    card.add_hr()
    for vp in vps_used:
        vp_name = vp.get("name", "?")
        vp_status = vp.get("status", "?")
        vp_icon = {"completed": "✅", "error": "❌", "success": "✅"}.get(vp_status, "❓")
        summary = vp.get("summary", "")
        card.add_field(f"{vp_icon} {vp_name}", f"状态: {vp_status}" + (f" | {summary[:100]}" if summary else ""))

    # 子公司执行细节
    for result in execution_result.get("results", []):
        details = result.get("details", [])
        if details:
            card.add_hr()
            card.add_section(
                f"🏭 {result.get('vp', '子公司')} 执行详情",
                [f"· {d.get('subsidiary', '?')}: {d.get('status', '?')} (质量: {d.get('quality_score', 'N/A')})"
                 for d in details[:6]],
            )

    card.add_hr()
    card.add_note(f"耗时: {elapsed:.2f}s · 墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


# ── 阶段5: 质量门控 ─────────────────────────────────────────────

def build_quality_card(
    task_id: str,
    quality_gate_result: dict,
    elapsed: float,
) -> dict:
    """阶段5卡片：LLM质量门控结果"""
    score = quality_gate_result.get("score", 0)
    passed = quality_gate_result.get("passed", False)
    score_float = float(score) / 10.0  # normalize to 0-10 scale

    # 从1-10分映射到颜色
    if score_float >= 8:
        q_color = GREEN
        q_emoji = "🌟"
    elif score_float >= 6:
        q_color = BLUE
        q_emoji = "✅"
    elif score_float >= 4:
        q_color = ORANGE
        q_emoji = "⚠️"
    else:
        q_color = RED
        q_emoji = "❌"

    card = CardBuilder(f"{q_emoji} 步骤⑤ 质量门控 · {task_id[:8]}", q_color)

    card.add_fields_row([
        ("📊 评分", f"{score_float}/10"),
        ("✅ 是否通过", "是 ✅" if passed else "否 ❌"),
    ])
    card.add_field("🤖 评估模型", quality_gate_result.get("model_used", "N/A"))

    issues = quality_gate_result.get("issues", [])
    improvements = quality_gate_result.get("improvements", [])

    if issues:
        card.add_hr()
        card.add_section("📋 问题列表", [f"· {i}" for i in issues[:5]])

    if improvements:
        card.add_hr()
        card.add_section("💡 改进建议", [f"· {s}" for s in improvements[:5]])

    if not passed:
        card.add_hr()
        card.add_div("**⚠️ 未通过质量门控 — 建议复审或升级模型重试**")
    elif score_float >= 8:
        card.add_div("**🌟 高质量交付物 — 可直接使用**")

    card.add_hr()
    card.add_note(f"耗时: {elapsed:.2f}s · 墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


# ── 阶段6: 最终产出汇总 ─────────────────────────────────────────

def build_final_card(
    task_id: str,
    result: dict,
    elapsed: float,
) -> dict:
    """最终总结卡片：任务完整结果"""
    status = result.get("status", "unknown")
    status_emoji = {
        "completed": "✅", "partial": "⚠️", "error": "❌",
        "rejected": "🚫", "skipped": "⏭️",
    }.get(status, "❓")

    intent_info = result.get("intent", {})
    risk_info = result.get("risk", {})
    quality_info = result.get("quality_gate", {})

    card = CardBuilder(f"{status_emoji} CEO任务完成 · {task_id[:8]}", BLUE)

    # 概要行
    card.add_fields_row([
        ("📝 输入摘要", (result.get("execution", {}) or {}).get("vps_used", [{"name": "?"}])[0].get("name", "?") if status != "rejected" else "高风险拒绝"),
        ("⏱️ 总耗时", f"{result.get('duration', elapsed):.2f}s"),
    ])

    # 意图 & 风险
    card.add_hr()
    card.add_fields_row([
        ("🎯 意图类型", intent_info.get("type", "?")),
        ("📊 复杂度", f"{intent_info.get('complexity_score', 0):.1f}"),
    ])
    card.add_fields_row([
        ("⚠️ 风险评分", f"{risk_info.get('risk_score', 0):.1f}/100"),
        ("🌟 质量评分", f"{quality_info.get('score', 'N/A')}/10"),
    ])

    # 执行摘要
    execution = result.get("execution", {})
    if execution:
        vps_used = execution.get("vps_used", [])
        if vps_used:
            card.add_hr()
            vp_summaries = [f"· {v.get('name', '?')}: {v.get('status', '?')}" for v in vps_used]
            card.add_section("🎯 调度VP", vp_summaries)

        dag_summary = execution.get("dag_summary")
        if dag_summary:
            card.add_field("📋 DAG", f"{dag_summary.get('total_steps', 0)}步 / {dag_summary.get('estimated_duration_s', 0)}s")

    # SOP记录
    sop_id = result.get("sop_record_id")
    if sop_id:
        card.add_hr()
        card.add_field("📦 SOP记录", f"`{sop_id}`")

    card.add_hr()
    card.add_div(f"**任务状态: {status_emoji} {status}**")
    card.add_hr()
    card.add_note(f"墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


# ── 拒绝卡片 ────────────────────────────────────────────────────

def build_rejected_card(
    task_id: str,
    intent: Any,
    risk: Any,
    elapsed: float,
) -> dict:
    """任务被拒绝的告警卡片"""
    card = CardBuilder(f"🚫 任务被拒绝 · {task_id[:8]}", RED)

    card.add_field("📝 任务概要", intent.raw_text[:200] if hasattr(intent, 'raw_text') else "（无）")
    card.add_hr()
    card.add_fields_row([
        ("📊 风险评分", f"{risk.risk_score:.1f}/100"),
        ("🚩 触发策略", "风险>80自动拒绝"),
    ])
    if risk.reason:
        card.add_field("📋 拒绝原因", risk.reason[:300])

    if risk.flags:
        card.add_hr()
        card.add_section("🚩 触发的风险标记", [f"· {f.get('reason', str(f))}" for f in risk.flags[:5]])

    card.add_hr()
    card.add_note(f"耗时: {elapsed:.2f}s · 墨麟OS CEO引擎 · {_timestamp()}")
    return card.build()


# ── 异步推送包装 ─────────────────────────────────────────────────

async def push_card_async(card_dict: dict, chat_id: str = CONSOLE_CHAT_ID) -> dict:
    """异步推送飞书卡片（使用 feishu-cli）"""
    try:
        result = feishu_send_card(card_dict, chat_id=chat_id)
        if not result.get("success"):
            logger.warning("[TaskLogger] 卡片推送失败: %s", result.get("output", "?"))
        return result
    except Exception as e:
        logger.error("[TaskLogger] 卡片推送异常: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}
