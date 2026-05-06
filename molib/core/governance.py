"""
墨麟治理系统 — 4级审批 + 预算控制 + 审计追踪
==============================================

基于 Paperclip (62K★) 设计模式:
- L0 自动执行 (零成本操作)
- L1 AI自审 (小额预算)
- L2 人工确认 (中额预算)
- L3 董事会审批 (重大决策)
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger("molin.governance")


class ApprovalLevel(Enum):
    L0_AUTO = 0       # 自动执行
    L1_AI_REVIEW = 1  # AI自审
    L2_HUMAN = 2      # 人工确认
    L3_BOARD = 3      # 董事会审批


class Decision:
    """待审批决策"""

    def __init__(self, title: str, cost: float, department: str, description: str = ""):
        self.id = f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.title = title
        self.cost = cost
        self.department = department
        self.description = description
        self.level = self._determine_level(cost)
        self.status = "pending"
        self.created_at = datetime.now()
        self.approved_at: Optional[datetime] = None

    def _determine_level(self, cost: float) -> ApprovalLevel:
        if cost <= 0:
            return ApprovalLevel.L0_AUTO
        elif cost <= 10:
            return ApprovalLevel.L1_AI_REVIEW
        elif cost <= 100:
            return ApprovalLevel.L2_HUMAN
        else:
            return ApprovalLevel.L3_BOARD


class Governance:
    """治理控制器"""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".molin" / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.decisions: list[Decision] = []

    def submit(self, title: str, cost: float, department: str, description: str = "") -> Decision:
        """提交待审批决策"""
        decision = Decision(title, cost, department, description)
        self.decisions.append(decision)
        self._log(decision)
        return decision

    def auto_approve(self, decision: Decision) -> bool:
        """自动审批 (L0/L1)"""
        if decision.level in (ApprovalLevel.L0_AUTO, ApprovalLevel.L1_AI_REVIEW):
            decision.status = "approved"
            decision.approved_at = datetime.now()
            self._log(decision)
            return True
        return False

    def needs_human_approval(self, decision: Decision) -> bool:
        """是否需要人工审批"""
        return decision.level in (ApprovalLevel.L2_HUMAN, ApprovalLevel.L3_BOARD)

    def approve(self, decision: Decision, approver: str = "Human") -> bool:
        """人工审批"""
        if decision.status == "pending":
            decision.status = "approved"
            decision.approved_at = datetime.now()
            self._log(decision, approver)
            return True
        return False

    def reject(self, decision: Decision, reason: str = "") -> bool:
        """驳回"""
        decision.status = "rejected"
        self._log(decision, reason=reason)
        return True

    def _log(self, decision: Decision, approver: str = "", reason: str = ""):
        """审计日志"""
        entry = {
            "id": decision.id,
            "title": decision.title,
            "cost": decision.cost,
            "level": decision.level.name,
            "department": decision.department,
            "status": decision.status,
            "created_at": decision.created_at.isoformat(),
            "approved_at": decision.approved_at.isoformat() if decision.approved_at else None,
            "approver": approver,
            "reason": reason,
        }
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# 全局实例
governance = Governance()
