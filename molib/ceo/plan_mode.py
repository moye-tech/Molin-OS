"""
墨麟OS — Plan Mode 飞书审批卡片
=================================
蓝图概念代码化。

当 RiskEngine 评分 > 60 时自动触发 Plan Mode，
通过 Hermes send_message 向飞书推送结构化审批卡片，
包含：风险评分、详情、批准/拒绝决策。

用法:
    plan = PlanMode()
    await plan.request_approval(task_id, risk_assessment, intent_result)

依赖:
    - Hermes Agent 的 send_message 工具（运行时注入）
    - risk_engine.RiskAssessment
    - intent_router.IntentResult
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("molin.ceo.plan_mode")


# 审批状态
APPROVAL_PENDING = "pending"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """审批请求"""
    task_id: str
    risk_score: float
    risk_reason: str
    intent_type: str
    target_vps: list[str]
    target_subsidiaries: list[str]
    description: str
    budget_estimate: float = 0.0
    status: str = APPROVAL_PENDING
    created_at: float = 0.0
    response_at: float = 0.0
    response: str = ""
    response_note: str = ""


class PlanMode:
    """
    Plan Mode 审批管理器。

    当任务风险评分 > 60 时，通过飞书推送审批卡片等待人类确认。
    拒绝则任务挂起，批准则继续执行。
    """

    def __init__(self):
        self._pending: dict[str, ApprovalRequest] = {}
        self._history: list[ApprovalRequest] = []
        self._message_sender: Callable | None = None

    def set_message_sender(self, sender: Callable):
        """设置消息发送函数（由运行时注入 Hermes 的 send_message）"""
        self._message_sender = sender

    def needs_approval(self, risk_score: float) -> bool:
        """判断是否需要审批"""
        # 蓝图规则：score > 60 需要 Plan Mode
        return risk_score > 60

    async def request_approval(
        self,
        task_id: str,
        risk_score: float,
        risk_reason: str,
        intent_type: str,
        target_vps: list[str],
        target_subsidiaries: list[str],
        description: str = "",
        budget_estimate: float = 0.0,
    ) -> ApprovalRequest:
        """
        发起审批请求。

        当 send_message 可用时推送飞书卡片；
        否则返回待审批状态，由外部轮询。

        返回:
            ApprovalRequest — status 可能为:
            - "pending" — 等待审批
            - "approved" — 已批准（低风险时自动通过）
            - "rejected" — 已拒绝
        """
        request = ApprovalRequest(
            task_id=task_id,
            risk_score=risk_score,
            risk_reason=risk_reason,
            intent_type=intent_type,
            target_vps=target_vps,
            target_subsidiaries=target_subsidiaries,
            description=description,
            budget_estimate=budget_estimate,
            status=APPROVAL_PENDING,
            created_at=time.time(),
        )
        self._pending[task_id] = request

        # 构建审批卡片文本
        card_text = self._build_card(request)
        logger.info("[PlanMode] 发起审批请求: task=%s risk=%.1f", task_id, risk_score)

        # 尝试推送飞书
        if self._message_sender:
            try:
                await self._message_sender(
                    target="origin",  # 推送到当前对话
                    message=card_text,
                )
                logger.info("[PlanMode] ✅ 审批卡片已推送到飞书: %s", task_id)
            except Exception as e:
                logger.warning("[PlanMode] ⚠️ 飞书推送失败: %s (任务将等待)", e)
        else:
            logger.info(
                "[PlanMode] ⚠️ 未配置消息发送器，审批请求已记录: %s", task_id
            )

        return request

    def approve(self, task_id: str, note: str = "") -> ApprovalRequest | None:
        """批准任务"""
        request = self._pending.get(task_id)
        if not request:
            logger.warning("[PlanMode] 未知任务ID: %s", task_id)
            return None
        request.status = APPROVAL_APPROVED
        request.response = "approved"
        request.response_note = note
        request.response_at = time.time()
        self._history.append(request)
        del self._pending[task_id]
        logger.info("[PlanMode] ✅ 任务已批准: %s", task_id)
        return request

    def reject(self, task_id: str, note: str = "") -> ApprovalRequest | None:
        """拒绝任务"""
        request = self._pending.get(task_id)
        if not request:
            logger.warning("[PlanMode] 未知任务ID: %s", task_id)
            return None
        request.status = APPROVAL_REJECTED
        request.response = "rejected"
        request.response_note = note
        request.response_at = time.time()
        self._history.append(request)
        del self._pending[task_id]
        logger.info("[PlanMode] ❌ 任务已拒绝: %s", task_id)
        return request

    def get_pending(self) -> list[ApprovalRequest]:
        """获取所有待审批任务"""
        return list(self._pending.values())

    def get_history(self, limit: int = 10) -> list[ApprovalRequest]:
        """获取审批历史"""
        return sorted(
            self._history,
            key=lambda r: r.response_at,
            reverse=True,
        )[:limit]

    def _build_card(self, request: ApprovalRequest) -> str:
        """构建飞书审批卡片文本"""
        risk_icon = "🔴" if request.risk_score > 80 else "🟡"
        budget_str = f"¥{request.budget_estimate:.0f}" if request.budget_estimate > 0 else "未指定"

        lines = [
            f"{risk_icon} **Plan Mode — 需要你的审批**",
            "",
            f"**任务描述:** {request.description or '（无描述）'}",
            f"**风险评分:** {request.risk_score:.1f}/100",
            f"**风险原因:** {request.risk_reason[:200]}",
            f"**意图类型:** {request.intent_type}",
            f"**目标VP:** {', '.join(request.target_vps) if request.target_vps else '未指定'}",
        ]
        if request.target_subsidiaries:
            lines.append(f"**目标子公司:** {', '.join(request.target_subsidiaries)}")

        lines.extend([
            f"**预算估算:** {budget_str}",
            f"**任务ID:** `{request.task_id}`",
            "",
            "---",
            "✅ 回复 `批准 {task_id}` 或 `拒绝 {task_id} [原因]`",
            "",
            "*此消息由墨麟OS PlanMode引擎自动发送*",
        ])
        return "\n".join(lines)

    def parse_response(self, text: str) -> tuple[str, str, str] | None:
        """
        解析飞书回复文本。
        支持格式:
            "批准 task-xxx"
            "拒绝 task-xxx 原因是不合理"
            "approve task-xxx"
            "reject task-xxx reason"

        返回:
            (action, task_id, note) 或 None（无法解析）
        """
        import re
        # 匹配: 批准/拒绝/approve/reject + task_id + 可选原因
        pattern = r"(批准|拒绝|approve|reject)\s+(task-\w[\w-]*)(?:\s+(.+))?"
        m = re.match(pattern, text.strip(), re.IGNORECASE)
        if not m:
            return None

        action_raw = m.group(1).lower()
        task_id = m.group(2)
        note = m.group(3) or ""

        if action_raw in ("批准", "approve"):
            action = "approve"
        else:
            action = "reject"

        return (action, task_id, note)
