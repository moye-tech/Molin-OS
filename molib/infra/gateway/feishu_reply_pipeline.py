"""
飞书 3 消息回复流水线
=====================
将 CEO 响应拆为 3 条有序消息：
  ① 思维链卡片（小字折叠，推理过程独立）
  ② 主回复卡片（结构化 interactive，无裸 Markdown）
  ③ 子公司详情卡片（按需展开）

用法:
    from molib.infra.gateway.feishu_reply_pipeline import FeishuReplyPipeline
    pipeline = FeishuReplyPipeline()
    messages = pipeline.build(user_query, ceo_result)
    # → [msg1, msg2, msg3]  每个都是飞书卡片 JSON
"""

from __future__ import annotations

from typing import Any

from molib.infra.gateway.feishu_card_builder import FeishuCardBuilder
from molib.infra.gateway.feishu_pre_send_validator import FeishuPreSendValidator


# 全局预发送验证器（单例）
_pre_send_validator = FeishuPreSendValidator()


class FeishuReplyPipeline:
    """飞书 3 消息回复流水线。"""

    def build(
        self,
        user_query: str,
        ceo_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """构建 3 条有序消息。

        Args:
            user_query: 用户原始提问
            ceo_result: CEO 完整执行结果 (来自 CEOOrchestrator.process())

        Returns:
            [thinking_card, main_reply_card, detail_cards...]
        """
        intent = ceo_result.get("intent", {})
        execution = ceo_result.get("execution", {})
        risk = ceo_result.get("risk", {})
        dag = ceo_result.get("dag", {})

        messages = []

        # ── 消息①: 思维链卡片 ──
        thinking = self._build_thinking_card(user_query, ceo_result)
        if thinking:
            messages.append(thinking)

        # ── 消息②: 主回复卡片 ──
        main = self._build_main_card(user_query, ceo_result)
        messages.append(main)

        # ── 消息③: 子公司详情卡（每个子公司一张） ──
        detail = self._build_detail_cards(ceo_result)
        messages.extend(detail)

        # ── 缺口③+④+⑤: pre-send 验证（每条消息） ──
        messages = self._validate_all(messages)

        return messages

    def _validate_all(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """对所有消息执行 pre-send 验证（thinking截断+markdown检测+长度检测）"""
        validated = []
        for msg in messages:
            if isinstance(msg, dict) and "content" in msg:
                text = msg.get("content", "")
                if isinstance(text, str) and text:
                    result = _pre_send_validator.validate(text, auto_fix=True)
                    msg["content"] = result["message"]
            validated.append(msg)
        return validated

    # ── 消息① ──────────────────────────────────────────────

    def _build_thinking_card(self, user_query: str, ceo_result: dict) -> dict | None:
        """构建思维链卡片。"""
        intent = ceo_result.get("intent", {})
        execution = ceo_result.get("execution", {})
        risk = ceo_result.get("risk", {})

        # 提取调度信息
        agencies = intent.get("target_subsidiaries", [])
        vps = intent.get("target_vps", [])
        all_agencies = list(set(agencies + vps))

        if not all_agencies:
            return None

        # 构建三层理解
        understanding = {
            "L1": f"意图类型: {intent.get('type', '未知')}",
            "L2": f"复杂度: {intent.get('complexity_score', 0):.0f}/10 · 匹配 {len(all_agencies)} 个子公司",
            "L3": f"风险等级: {intent.get('risk_level', 'low')} · 需审批: {risk.get('requires_approval', False)}",
        }

        duration = ceo_result.get("duration", 0)

        card = FeishuCardBuilder()
        card.thinking_card(
            user_query=user_query,
            understanding=understanding,
            agencies=[a[:10] for a in all_agencies[:6]],
            confidence=intent.get("confidence", 0.9),
            duration_s=duration,
        )

        return {"msg_type": "interactive", "card": card.build()}

    # ── 消息② ──────────────────────────────────────────────

    def _build_main_card(self, user_query: str, ceo_result: dict) -> dict:
        """构建主回复卡片。"""
        execution = ceo_result.get("execution", {})
        risk = ceo_result.get("risk", {})
        quality = ceo_result.get("quality_gate", {})

        card = FeishuCardBuilder()

        # 头部
        status = ceo_result.get("status", "completed")
        color = "green" if status == "completed" else "orange" if status == "partial" else "red"
        emoji = "✅" if status == "completed" else "⚠️" if status == "partial" else "❌"

        card.header(f"{emoji} 任务{status_map(status)}", template=color)

        # 执行摘要
        vps_used = execution.get("vps_used", [])
        if vps_used:
            vp_names = [v.get("name", v) if isinstance(v, dict) else str(v) for v in vps_used]
            card.field_list([
                ("调度子公司", " · ".join(vp_names[:6])),
                ("任务状态", status),
                ("质量评分", f"{quality.get('score', 0):.0f}/100"),
            ])

        # 核心结果
        results = execution.get("results", [])
        if results:
            card.divider()
            for i, r in enumerate(results[:5]):
                if isinstance(r, dict):
                    summary = r.get("summary", "") or r.get("result", "")
                    if isinstance(summary, dict):
                        summary = str(summary)[:200]
                    if summary:
                        card.section(f"📋 {r.get('vp', r.get('name', f'结果{i+1}'))}", str(summary)[:300])

        # 风险提示
        if risk.get("risk_score", 0) > 30:
            card.divider()
            flags = risk.get("flags", [])
            if flags:
                card.section("⚠️ 风险提示", "\n".join(f"• {f}" for f in flags))

        # 操作按钮
        card.divider()
        card.actions([
            {"text": "📋 导出报告", "type": "default", "value": {"action": "export"}},
            {"text": "💬 继续提问", "type": "primary", "value": {"action": "continue"}},
        ])

        card.note(f"墨麟AI v2.1 · {ceo_result.get('sop_record_id', '')[-8:]} · {len(vps_used)}子公司协作")

        return {"msg_type": "interactive", "card": card.build()}

    # ── 消息③ ──────────────────────────────────────────────

    def _build_detail_cards(self, ceo_result: dict) -> list[dict]:
        """为每个子公司构建详情卡片。"""
        execution = ceo_result.get("execution", {})
        results = execution.get("results", [])
        vps_used = execution.get("vps_used", [])

        cards = []
        for r in results[:5]:
            if not isinstance(r, dict):
                continue
            vp_name = r.get("vp", r.get("name", ""))
            if not vp_name:
                continue

            card = FeishuCardBuilder()
            card.header(f"📊 {vp_name} · 完整报告", template="blue")

            details = r.get("details", [])
            if details:
                for d in details[:8]:
                    if isinstance(d, dict):
                        name = d.get("subsidiary", d.get("name", ""))
                        result_text = str(d.get("result", ""))[:200]
                        if result_text:
                            card.section(name, result_text)

            summary = r.get("summary", "")
            if summary and not details:
                card.section("摘要", str(summary)[:400])

            card.divider()
            quality = r.get("quality_summary", {})
            card.note(f"质量: {quality.get('avg_score', 0):.0f} · {quality.get('passed_count', 0)}/{quality.get('total', 0)} 通过")

            cards.append({"msg_type": "interactive", "card": card.build()})

        return cards


def status_map(s: str) -> str:
    return {"completed": "完成", "partial": "部分完成", "rejected": "已拒绝", "error": "执行失败"}.get(s, s)
