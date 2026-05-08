"""
深度审批工作流 v6.6 — 审批驱动型任务流转
高危任务自动生成审批单，同意后自动推进，拒绝后写入学习记忆。

适配自 molin-os-ultra v6.6.0 infra/security/deep_approval.py
适配: loguru → logging, 整合到 SOP 引擎的 approval 步骤
"""
from __future__ import annotations

import json
import time
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ── 高危任务定义 ──

HIGH_RISK_RULES = [
    {
        "name": "vault_first_auth",
        "description": "凭证首次授权给新 Agency",
        "check": lambda ctx: ctx.get("is_new_credential")
        and ctx.get("agency") not in ("ceo",),
        "risk_level": "critical",
    },
    {
        "name": "large_transaction",
        "description": "单笔收款/退款超过阈值",
        "check": lambda ctx: ctx.get("amount", 0)
        > float(ctx.get("threshold", 500)),
        "risk_level": "high",
    },
    {
        "name": "mass_publish",
        "description": "发布超过指定平台数量的内容",
        "check": lambda ctx: ctx.get("publish_count", 0)
        > int(ctx.get("max_publish", 3)),
        "risk_level": "high",
    },
    {
        "name": "config_change",
        "description": "修改 SOP 或系统配置",
        "check": lambda ctx: ctx.get("action")
        in ("update_sop", "modify_config", "delete_config"),
        "risk_level": "high",
    },
    {
        "name": "data_delete",
        "description": "删除历史数据",
        "check": lambda ctx: ctx.get("action") == "delete_data",
        "risk_level": "critical",
    },
    {
        "name": "refund_dispute",
        "description": "买家要求退款或纠纷升级",
        "check": lambda ctx: ctx.get("intent")
        in ("refund", "dispute", "complaint"),
        "risk_level": "critical",
    },
]


@dataclass
class ApprovalRequest:
    approval_id: str
    title: str
    description: str
    context: Dict[str, Any]
    risk_level: str  # "low", "high", "critical"
    source_agency: str
    task_id: str
    created_at: float = field(default_factory=time.time)
    status: str = "pending"  # pending, approved, rejected
    reject_reason: str = ""


class ApprovalWorkflow:
    """审批工作流引擎 — 风险评估 + 审批创建 + 学习记忆（拒绝案例自动学习）"""

    def __init__(self):
        self._pending: Dict[str, ApprovalRequest] = {}
        self._history: List[Dict[str, Any]] = []
        self._learning_memory: List[Dict[str, Any]] = []
        self._on_approval_created: Optional[Callable] = None
        self._on_approval_resolved: Optional[Callable] = None

    # ── 回调注册 ──

    def on_approval_created(
        self, callback: Callable[[ApprovalRequest], None]
    ):
        """注册审批单创建回调（可用于推飞书卡片）"""
        self._on_approval_created = callback

    def on_approval_resolved(
        self, callback: Callable[[ApprovalRequest], None]
    ):
        """注册审批单解决回调"""
        self._on_approval_resolved = callback

    # ── 风险评估 ──

    def evaluate_risk(
        self, context: Dict[str, Any]
    ) -> tuple[str, List[str]]:
        """
        评估任务风险等级。

        Returns:
            (risk_level, triggered_rules)
        """
        triggered = []
        max_risk = "low"

        for rule in HIGH_RISK_RULES:
            try:
                if rule["check"](context):
                    triggered.append(rule["name"])
                    if rule["risk_level"] == "critical":
                        max_risk = "critical"
                    elif (
                        rule["risk_level"] == "high"
                        and max_risk != "critical"
                    ):
                        max_risk = "high"
            except Exception:
                pass

        return max_risk, triggered

    # ── 审批流程 ──

    async def create_approval(
        self,
        title: str,
        description: str,
        context: Dict[str, Any],
        source_agency: str,
        task_id: str,
    ) -> Optional[ApprovalRequest]:
        """创建审批单，返回 None 表示低风险自动放行"""
        risk_level, rules = self.evaluate_risk(context)

        if risk_level == "low" and not rules:
            logger.debug(
                f"[Approval] 低风险任务直接放行: {task_id}"
            )
            return None  # 不需要审批

        approval_id = f"apr_{int(time.time())}_{task_id[:8]}"
        req = ApprovalRequest(
            approval_id=approval_id,
            title=title,
            description=description,
            context={**context, "triggered_rules": rules},
            risk_level=risk_level,
            source_agency=source_agency,
            task_id=task_id,
        )
        self._pending[approval_id] = req

        logger.info(
            f"[Approval] 审批单已创建: {approval_id}, "
            f"risk={risk_level}, rules={rules}, agency={source_agency}"
        )

        if self._on_approval_created:
            try:
                self._on_approval_created(req)
            except Exception as e:
                logger.error(f"[Approval] 创建回调失败: {e}")

        return req

    def approve(
        self, approval_id: str, comment: str = ""
    ) -> Optional[ApprovalRequest]:
        """批准审批单"""
        req = self._pending.get(approval_id)
        if not req:
            return None
        req.status = "approved"
        self._history.append(
            {
                "approval_id": approval_id,
                "task_id": req.task_id,
                "action": "approved",
                "comment": comment,
                "time": time.time(),
            }
        )
        del self._pending[approval_id]
        logger.info(f"[Approval] 已批准: {approval_id}")

        if self._on_approval_resolved:
            try:
                self._on_approval_resolved(req)
            except Exception as e:
                logger.error(f"[Approval] 解决回调失败: {e}")

        return req

    def reject(
        self, approval_id: str, reason: str
    ) -> Optional[ApprovalRequest]:
        """拒绝审批单，写入学习记忆"""
        req = self._pending.get(approval_id)
        if not req:
            return None
        req.status = "rejected"
        req.reject_reason = reason

        self._history.append(
            {
                "approval_id": approval_id,
                "task_id": req.task_id,
                "action": "rejected",
                "reason": reason,
                "time": time.time(),
            }
        )

        # 写入学习记忆
        self._learning_memory.append(
            {
                "task_id": req.task_id,
                "context": req.context,
                "reason": reason,
                "time": time.time(),
            }
        )
        if len(self._learning_memory) > 100:
            self._learning_memory = self._learning_memory[-100:]

        del self._pending[approval_id]
        logger.info(
            f"[Approval] 已拒绝: {approval_id}, reason={reason[:50]}"
        )

        if self._on_approval_resolved:
            try:
                self._on_approval_resolved(req)
            except Exception as e:
                logger.error(f"[Approval] 解决回调失败: {e}")

        return req

    def get_pending(
        self, agency: Optional[str] = None
    ) -> List[ApprovalRequest]:
        pending = list(self._pending.values())
        if agency:
            pending = [
                r for r in pending if r.source_agency == agency
            ]
        return sorted(pending, key=lambda r: r.created_at, reverse=True)

    def should_reject_similar(
        self, context: Dict[str, Any], threshold: float = 0.7
    ) -> Optional[str]:
        """检查学习记忆中是否有类似的被拒绝案例"""
        for mem in self._learning_memory[-20:]:
            mem_ctx = mem.get("context", {})
            if (
                mem_ctx.get("action") == context.get("action")
                and mem_ctx.get("source_agency")
                == context.get("source_agency")
            ):
                return mem.get("reason", "类似案例曾被拒绝")
        return None

    def get_stats(self) -> Dict[str, Any]:
        """获取审批统计"""
        total = len(self._history)
        approved = sum(1 for h in self._history if h["action"] == "approved")
        rejected = sum(1 for h in self._history if h["action"] == "rejected")
        return {
            "pending": len(self._pending),
            "total_processed": total,
            "approved": approved,
            "rejected": rejected,
            "learning_memory_size": len(self._learning_memory),
        }


# 全局单例
_workflow: Optional[ApprovalWorkflow] = None


def get_approval_workflow() -> ApprovalWorkflow:
    global _workflow
    if _workflow is None:
        _workflow = ApprovalWorkflow()
    return _workflow
