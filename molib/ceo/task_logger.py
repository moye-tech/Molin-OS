"""
墨麟OS — CEO 全链路可视化任务日志（单卡汇总版）
==============================================
将CEO Orchestrator的6个关键阶段合并为一张飞书卡片，
避免6张卡片刷屏。只在非简单任务时推送。

包含：
1. 🧠 意图分析
2. ⚠️ 风险评估
3. 📋 DAG任务分解
4. 🔄 子公司调度与执行
5. ✅ 质量门控
6. 🎉 最终产出

条件推送：仅在非简单(complexity_score >= 25)任务时推送。
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

SIMPLE_THRESHOLD = 25  # complexity_score >= 25 时推送


def should_push_log(intent: Any) -> bool:
    """判断是否推送日志：非简单任务才推送"""
    try:
        return intent.complexity_score >= SIMPLE_THRESHOLD
    except AttributeError:
        return True


# ── 单张汇总卡片（替代原来的6张独立卡片） ────────────────────────

def build_summary_card(
    task_id: str,
    user_input: str,
    intent: Any,
    risk: Any,
    dag: Any = None,
    execution_result: dict | None = None,
    quality_gate_result: dict | None = None,
    final_result: dict | None = None,
    elapsed: float = 0,
) -> dict:
    """单张汇总卡片：包含全部6阶段信息"""
    
    intent_risk_icon = {
        "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴",
    }.get(intent.risk_level, "⚪")
    
    route_labels = {
        "trivial": "闲聊", "cache": "缓存", "llm": "LLM路由", "keyword": "关键词",
    }
    
    card = CardBuilder(f"🚀 CEO任务执行报告 · {task_id[:8]}", BLUE)
    
    # ══════════════ 阶段①: 用户输入 & 意图分析 ══════════════
    card.add_section("🧠 ① 意图分析", [
        f"📝 输入: {user_input[:200]}",
    ])
    card.add_fields_row([
        ("🎯 意图类型", intent.intent_type),
        (f"{intent_risk_icon} 风险等级", intent.risk_level),
    ])
    card.add_fields_row([
        ("📊 复杂度", f"{intent.complexity_score:.1f}/100"),
        ("🎯 路由来源", route_labels.get(intent.route_source, intent.route_source)),
    ])
    if intent.target_vps:
        card.add_field("🏢 目标VP", ", ".join(intent.target_vps))
    if intent.target_subsidiaries:
        card.add_field("🏭 目标子公司", ", ".join(intent.target_subsidiaries))
    if intent.entities:
        card.add_field("🔍 实体", str(intent.entities)[:150])
    
    card.add_hr()
    
    # ══════════════ 阶段②: 风险评估 ══════════════
    risk_emoji = "🔴" if risk.risk_score > 80 else ("🟡" if risk.risk_score > 60 else "🟢")
    card.add_section(f"{risk_emoji} ② 风险评估", [
        f"综合评分: {risk.risk_score:.1f}/100 | 需要审批: {'是' if risk.requires_approval else '否'}",
        f"💰资金{risk.financial_risk:.1f} · 📋合规{risk.compliance_risk:.1f} · ⚖️法律{risk.legal_risk:.1f} · 🔒隐私{risk.privacy_risk:.1f}",
    ])
    if risk.flags:
        card.add_section("🚩 风险标记", [f"· {f.get('reason', str(f))}" for f in risk.flags[:3]])
    
    if risk.risk_score > 80:
        card.add_div("**⛔ 高风险 — 任务被拒绝**")
        card.add_hr()
        card.add_note(f"耗时: {elapsed:.2f}s · 墨麟OS CEO引擎 · {_timestamp()}")
        return card.build()
    
    card.add_hr()
    
    # ══════════════ 阶段③: DAG任务分解 ══════════════
    if dag:
        card.add_section("📋 ③ 任务分解", [
            f"总步数: {len(dag.tasks)} | 并行组: {len(dag.parallel_groups)} | 预估: {dag.total_sp}s",
        ])
        for i, t in enumerate(dag.tasks):
            deps = f"←{','.join(t.depends_on)}" if t.depends_on else ""
            vp = f" [{t.assigned_vp}]" if t.assigned_vp else ""
            model = f"({t.model_tier})" if t.model_tier else ""
            card.add_field(f"  {i+1}. {t.step_id}", f"{t.description}{deps}{vp}{model}")
        card.add_hr()
    
    # ══════════════ 阶段④: 子公司调度与执行 ══════════════
    if execution_result:
        vps_used = execution_result.get("vps_used", [])
        if vps_used:
            vp_lines = []
            for v in vps_used:
                icon = {"completed": "✅", "error": "❌", "success": "✅", "skipped": "⏭️"}.get(v.get("status", ""), "❓")
                vp_lines.append(f"{icon} {v['name']}: {v['status']} {v.get('summary','')[:60]}")
            card.add_section("🔄 ④ 子公司调度", vp_lines)
        
        # 子公司执行细节
        results_list = execution_result.get("results", [])
        if results_list:
            sub_lines = []
            for r_item in results_list:
                details = r_item.get("details", [])
                for d in details:
                    q = d.get("quality_score", "N/A")
                    sub_lines.append(f"· {d.get('subsidiary', '?')}: {d.get('status', '?')} (质量:{q})")
            if sub_lines:
                card.add_section("🏭 子公司执行详情", sub_lines[:6])
        
        qs = execution_result.get("quality_summary", {})
        if qs:
            card.add_field("📊 执行质量", f"平均{qs.get('avg_score',0)} · 通过{qs.get('passed_count',0)}/{qs.get('total',0)}")
        
        card.add_hr()
    
    # ══════════════ 阶段⑤: 质量门控 ══════════════
    if quality_gate_result:
        score = quality_gate_result.get("score", 0)
        passed = quality_gate_result.get("passed", False)
        score_float = float(score) / 10.0
        q_emoji = "🌟" if score_float >= 8 else ("✅" if score_float >= 6 else "⚠️" if score_float >= 4 else "❌")
        
        card.add_section(f"{q_emoji} ⑤ 质量门控", [
            f"评分: {score_float}/10 | 通过: {'是✅' if passed else '否❌'}",
            f"评估模型: {quality_gate_result.get('model_used', 'N/A')}",
        ])
        
        issues = quality_gate_result.get("issues", [])
        improvements = quality_gate_result.get("improvements", [])
        if issues:
            card.add_section("📋 问题", [f"· {i}" for i in issues[:3]])
        if improvements:
            card.add_section("💡 改进", [f"· {s}" for s in improvements[:3]])
        
        card.add_hr()
    
    # ══════════════ 阶段⑥: 最终产出 ══════════════
    if final_result:
        status = final_result.get("status", "completed")
        status_emoji = {"completed": "✅", "partial": "⚠️", "error": "❌", "skipped": "⏭️"}.get(status, "❓")
        
        card.add_section(f"{status_emoji} ⑥ 任务完成", [
            f"状态: {status} | 总耗时: {final_result.get('duration', elapsed):.2f}s",
        ])
        
        sop_id = final_result.get("sop_record_id")
        if sop_id:
            card.add_field("📦 SOP记录", f"`{sop_id}`")
    
    card.add_hr()
    card.add_note(f"墨麟OS CEO引擎 · {_timestamp()}" + (f" · 总耗时 {elapsed:.2f}s" if elapsed else ""))
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
