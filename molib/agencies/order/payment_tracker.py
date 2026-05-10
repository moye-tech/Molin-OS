"""
墨单订单 — 支付追踪器
==================
追踪订单支付状态、生成支付链接（微信/支付宝占位）、
记录付款历史、发送支付提醒。

设计模式吸收自:
- Invoice Ninja (9K⭐): 支付状态机 + 自动提醒
- Kill Bill (4.7K⭐): 订阅计费 + 逾期处理

Mac M2: stdlib-only, 零外部依赖。
存储: ~/.molin/orders/payments/

Author: 墨麟AI集团 · 墨单订单子公司
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

PAYMENT_DIR = Path.home() / ".molin" / "orders" / "payments"

# 支付方式定义
PAYMENT_METHODS = {
    "wechat": "微信支付",
    "alipay": "支付宝",
    "bank_transfer": "银行转账",
    "crypto_usdt": "USDT (TRC20)",
    "crypto_eth": "ETH",
    "crypto_btc": "BTC",
    "credit_card": "信用卡",
    "other": "其他",
}

# 支付状态机: pending → processing → paid | failed | refunded | cancelled
PAYMENT_STATUSES = ["pending", "processing", "paid", "failed", "refunded", "cancelled"]


@dataclass
class Payment:
    """支付记录"""
    payment_id: str
    invoice_id: str
    amount: float
    currency: str = "CNY"
    method: str = "wechat"
    status: str = "pending"
    customer_name: str = ""
    customer_email: str = ""
    notes: str = ""
    created_at: str = ""
    paid_at: str = ""
    transaction_id: str = ""       # 外部交易号
    verify_code: str = ""          # 支付验证码
    attempts: int = 0
    history: list[dict] = field(default_factory=list)  # 状态变更历史时间线

    def to_dict(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "currency": self.currency,
            "method": self.method,
            "status": self.status,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "notes": self.notes,
            "created_at": self.created_at,
            "paid_at": self.paid_at,
            "transaction_id": self.transaction_id,
            "verify_code": self.verify_code,
            "attempts": self.attempts,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Payment:
        return cls(
            payment_id=data["payment_id"],
            invoice_id=data["invoice_id"],
            amount=data["amount"],
            currency=data.get("currency", "CNY"),
            method=data.get("method", "wechat"),
            status=data.get("status", "pending"),
            customer_name=data.get("customer_name", ""),
            customer_email=data.get("customer_email", ""),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", ""),
            paid_at=data.get("paid_at", ""),
            transaction_id=data.get("transaction_id", ""),
            verify_code=data.get("verify_code", ""),
            attempts=data.get("attempts", 0),
            history=data.get("history", []),
        )

    @property
    def is_paid(self) -> bool:
        return self.status == "paid"

    @property
    def is_overdue(self, due_date: str = "") -> bool:
        if self.is_paid:
            return False
        if not due_date:
            return False
        return datetime.now().strftime("%Y-%m-%d") > due_date

    @property
    def method_display(self) -> str:
        return PAYMENT_METHODS.get(self.method, self.method)


class PaymentTracker:
    """支付追踪引擎。

    核心功能:
    - 创建支付记录
    - 状态变更 + 历史追踪
    - 支付验证码生成/校验
    - 逾期检测
    - 支付报告
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or PAYMENT_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Payment] = {}

    # ── CRUD ────────────────────────────────────────

    def create_payment(
        self,
        invoice_id: str,
        amount: float,
        *,
        method: str = "wechat",
        currency: str = "CNY",
        customer_name: str = "",
        customer_email: str = "",
        notes: str = "",
    ) -> Payment:
        """创建支付记录。"""
        now = datetime.now().isoformat()
        verify_code = uuid.uuid4().hex[:8].upper()

        payment = Payment(
            payment_id=f"PAY-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            invoice_id=invoice_id,
            amount=amount,
            currency=currency,
            method=method,
            status="pending",
            customer_name=customer_name,
            customer_email=customer_email,
            notes=notes,
            created_at=now,
            verify_code=verify_code,
            history=[{
                "timestamp": now,
                "from_status": "",
                "to_status": "pending",
                "note": "支付创建",
            }],
        )
        self._save(payment)
        return payment

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """获取支付记录。"""
        if payment_id in self._cache:
            return self._cache[payment_id]
        filepath = self.storage_dir / f"{payment_id}.json"
        if filepath.exists():
            with open(filepath) as f:
                payment = Payment.from_dict(json.load(f))
                self._cache[payment_id] = payment
                return payment
        return None

    def get_by_invoice(self, invoice_id: str) -> list[Payment]:
        """根据发票ID查询支付记录。"""
        payments = []
        for fp in self.storage_dir.glob("*.json"):
            try:
                with open(fp) as f:
                    data = json.load(f)
                    if data.get("invoice_id") == invoice_id:
                        payments.append(Payment.from_dict(data))
            except Exception:
                continue
        return sorted(payments, key=lambda p: p.created_at, reverse=True)

    def list_payments(self, status: str = "", method: str = "", 
                      limit: int = 50) -> list[Payment]:
        """列出支付记录。"""
        payments = []
        for fp in sorted(self.storage_dir.glob("*.json"), reverse=True):
            if len(payments) >= limit:
                break
            try:
                with open(fp) as f:
                    data = json.load(f)
                    payment = Payment.from_dict(data)
                    if status and payment.status != status:
                        continue
                    if method and payment.method != method:
                        continue
                    payments.append(payment)
            except Exception:
                continue
        return payments

    # ── 状态变更 ─────────────────────────────────

    def update_status(
        self, payment_id: str, new_status: str, *,
        transaction_id: str = "",
        note: str = "",
    ) -> Optional[Payment]:
        """更新支付状态（带历史记录）。"""
        payment = self.get_payment(payment_id)
        if not payment:
            return None

        if new_status not in PAYMENT_STATUSES:
            return None

        old_status = payment.status
        payment.status = new_status

        if new_status == "paid":
            payment.paid_at = datetime.now().isoformat()
            if transaction_id:
                payment.transaction_id = transaction_id
        elif new_status == "failed":
            payment.attempts += 1

        payment.history.append({
            "timestamp": datetime.now().isoformat(),
            "from_status": old_status,
            "to_status": new_status,
            "note": note or f"状态变更: {old_status} → {new_status}",
        })

        self._save(payment)
        return payment

    def mark_paid(self, payment_id: str, transaction_id: str = "") -> Optional[Payment]:
        """标记为已支付。"""
        return self.update_status(payment_id, "paid", transaction_id=transaction_id, note="支付成功")

    def mark_failed(self, payment_id: str, reason: str = "") -> Optional[Payment]:
        """标记为支付失败。"""
        return self.update_status(payment_id, "failed", note=f"支付失败: {reason}" if reason else "支付失败")

    def mark_processing(self, payment_id: str) -> Optional[Payment]:
        """标记为处理中。"""
        return self.update_status(payment_id, "processing", note="支付处理中")

    def mark_refunded(self, payment_id: str, reason: str = "") -> Optional[Payment]:
        """标记为已退款。"""
        return self.update_status(payment_id, "refunded", note=f"已退款: {reason}" if reason else "已退款")

    def cancel_payment(self, payment_id: str) -> Optional[Payment]:
        """取消支付。"""
        return self.update_status(payment_id, "cancelled", note="支付已取消")

    # ── 验证码 ─────────────────────────────────

    def verify_code_check(self, payment_id: str, code: str) -> bool:
        """校验支付验证码。"""
        payment = self.get_payment(payment_id)
        if not payment:
            return False
        return payment.verify_code.upper() == code.upper().strip()

    def rotate_verify_code(self, payment_id: str) -> Optional[str]:
        """刷新验证码。"""
        payment = self.get_payment(payment_id)
        if not payment:
            return None
        payment.verify_code = uuid.uuid4().hex[:8].upper()
        payment.history.append({
            "timestamp": datetime.now().isoformat(),
            "from_status": payment.status,
            "to_status": payment.status,
            "note": "验证码已刷新",
        })
        self._save(payment)
        return payment.verify_code

    # ── 提醒 ─────────────────────────────────

    def get_pending_reminders(self, overdue_only: bool = False) -> list[dict]:
        """获取需要发送支付提醒的支付记录。"""
        reminders = []
        now = datetime.now()
        for payment in self.list_payments(status="pending"):
            if not payment.created_at:
                continue
            created = datetime.fromisoformat(payment.created_at)
            hours_pending = (now - created).total_seconds() / 3600

            reminder = {
                "payment_id": payment.payment_id,
                "invoice_id": payment.invoice_id,
                "customer_name": payment.customer_name,
                "customer_email": payment.customer_email,
                "amount": payment.amount,
                "currency": payment.currency,
                "method": payment.method_display,
                "hours_pending": round(hours_pending, 1),
                "verify_code": payment.verify_code,
                "urgency": "normal",
            }

            if hours_pending > 72:
                reminder["urgency"] = "critical"
            elif hours_pending > 24:
                reminder["urgency"] = "urgent"
            elif hours_pending > 6:
                reminder["urgency"] = "reminder"

            if overdue_only:
                if hours_pending > 24:
                    reminders.append(reminder)
            else:
                reminders.append(reminder)

        return reminders

    def generate_reminder_message(self, payment_id: str) -> str:
        """生成支付提醒消息（飞书/微信可用）。"""
        payment = self.get_payment(payment_id)
        if not payment:
            return ""

        method_display = PAYMENT_METHODS.get(payment.method, payment.method)
        return (
            f"📋 支付提醒\n"
            f"━━━━━━━━━━━━\n"
            f"订单: {payment.invoice_id}\n"
            f"金额: ¥{payment.amount:.2f} {payment.currency}\n"
            f"方式: {method_display}\n"
            f"验证码: {payment.verify_code}\n"
            f"━━━━━━━━━━━━\n"
            f"请在收到后尽快完成支付。如有疑问请回复此消息。\n"
            f"—— 墨麟AI集团 · 墨单订单"
        )

    # ── 报告 ─────────────────────────────────

    def get_report(self, period_days: int = 30) -> dict:
        """生成支付报告。"""
        payments = self.list_payments()
        now = datetime.now()
        cutoff = now - timedelta(days=period_days)

        report = {
            "period_days": period_days,
            "generated_at": now.isoformat(),
            "total_payments": len(payments),
            "total_amount": 0.0,
            "paid_count": 0,
            "paid_amount": 0.0,
            "pending_count": 0,
            "pending_amount": 0.0,
            "failed_count": 0,
            "refunded_count": 0,
            "refunded_amount": 0.0,
            "by_method": {},
            "avg_response_hours": 0.0,
        }

        response_hours = []
        for p in payments:
            report["total_amount"] += p.amount
            report["by_method"][p.method] = report["by_method"].get(p.method, 0) + 1

            if p.status == "paid":
                report["paid_count"] += 1
                report["paid_amount"] += p.amount
                if p.created_at and p.paid_at:
                    created = datetime.fromisoformat(p.created_at)
                    paid = datetime.fromisoformat(p.paid_at)
                    response_hours.append((paid - created).total_seconds() / 3600)
            elif p.status == "pending":
                report["pending_count"] += 1
                report["pending_amount"] += p.amount
            elif p.status == "failed":
                report["failed_count"] += 1
            elif p.status == "refunded":
                report["refunded_count"] += 1
                report["refunded_amount"] += p.amount

        if response_hours:
            report["avg_response_hours"] = round(sum(response_hours) / len(response_hours), 1)

        report["total_amount"] = round(report["total_amount"], 2)
        report["paid_amount"] = round(report["paid_amount"], 2)
        report["pending_amount"] = round(report["pending_amount"], 2)
        report["refunded_amount"] = round(report["refunded_amount"], 2)

        return report

    # ── 订阅支付（Kill Bill 模式） ───────────────

    def create_subscription_payment(
        self,
        invoice_id: str,
        amount: float,
        *,
        cycle: str = "monthly",     # monthly / quarterly / yearly
        max_cycles: int = 0,        # 0 = 无限
        method: str = "wechat",
        customer_name: str = "",
        customer_email: str = "",
    ) -> dict:
        """创建订阅式支付（周期性扣款占位）。
        
        ⚠️ 当前版本生成占位记录，实际扣款需集成支付网关。
        返回支付记录 + 订阅配置。
        """
        payment = self.create_payment(
            invoice_id=invoice_id,
            amount=amount,
            method=method,
            customer_name=customer_name,
            customer_email=customer_email,
            notes=f"订阅支付 - {cycle}",
        )

        subscription_config = {
            "subscription_id": f"SUB-{uuid.uuid4().hex[:8].upper()}",
            "payment_id": payment.payment_id,
            "amount": amount,
            "cycle": cycle,
            "max_cycles": max_cycles,
            "current_cycle": 0,
            "next_billing": (datetime.now() + timedelta(days={
                "monthly": 30, "quarterly": 90, "yearly": 365
            }.get(cycle, 30))).strftime("%Y-%m-%d"),
            "status": "active",
        }

        # 保存订阅配置
        sub_dir = self.storage_dir / "subscriptions"
        sub_dir.mkdir(parents=True, exist_ok=True)
        sub_path = sub_dir / f"{subscription_config['subscription_id']}.json"
        with open(sub_path, "w") as f:
            json.dump(subscription_config, f, ensure_ascii=False, indent=2)

        return {
            "payment": payment.to_dict(),
            "subscription": subscription_config,
        }

    # ── Internal ────────────────────────────────

    def _save(self, payment: Payment) -> None:
        filepath = self.storage_dir / f"{payment.payment_id}.json"
        with open(filepath, "w") as f:
            json.dump(payment.to_dict(), f, ensure_ascii=False, indent=2)
        self._cache[payment.payment_id] = payment


# ── CLI ──────────────────────────────────────────────

def cmd_payment_track(action: str, *args) -> str:
    """CLI 入口"""
    tracker = PaymentTracker()

    if action == "create":
        if len(args) < 3:
            return "用法: payment create <invoice_id> <amount> [method]"
        payment = tracker.create_payment(
            invoice_id=args[0],
            amount=float(args[1]),
            method=args[2] if len(args) > 2 else "wechat",
        )
        return (
            f"✅ 支付 {payment.payment_id}\n"
            f"   发票: {payment.invoice_id}\n"
            f"   金额: ¥{payment.amount:.2f}\n"
            f"   验证码: {payment.verify_code}"
        )

    elif action == "list":
        status = args[0] if args else ""
        payments = tracker.list_payments(status=status)
        if not payments:
            return "暂无支付记录"
        lines = [f"{'支付ID':<30} {'发票':<25} {'金额':>10} {'状态':<12}"]
        for p in payments[:20]:
            lines.append(
                f"{p.payment_id:<30} {p.invoice_id:<25} ¥{p.amount:>8.2f} {p.status:<12}"
            )
        return "\n".join(lines)

    elif action == "paid":
        if len(args) < 1:
            return "用法: payment paid <payment_id> [transaction_id]"
        tx_id = args[1] if len(args) > 1 else ""
        result = tracker.mark_paid(args[0], tx_id)
        return f"✅ 已支付: {args[0]}" if result else "支付记录未找到"

    elif action == "failed":
        if len(args) < 1:
            return "用法: payment failed <payment_id> [reason]"
        reason = args[1] if len(args) > 1 else ""
        result = tracker.mark_failed(args[0], reason)
        return f"❌ 支付失败: {args[0]}" if result else "支付记录未找到"

    elif action == "verify":
        if len(args) < 2:
            return "用法: payment verify <payment_id> <code>"
        is_valid = tracker.verify_code_check(args[0], args[1])
        return f"{'✅' if is_valid else '❌'} 验证码{'正确' if is_valid else '错误'}"

    elif action == "report":
        report = tracker.get_report()
        return json.dumps(report, ensure_ascii=False, indent=2)

    elif action == "reminders":
        reminders = tracker.get_pending_reminders()
        if not reminders:
            return "没有待处理的支付提醒"
        lines = [f"📋 待处理支付 ({len(reminders)}):"]
        for r in reminders:
            lines.append(
                f"  [{r['urgency']}] {r['invoice_id']} ¥{r['amount']:.2f} "
                f"— {r['customer_name']} ({r['hours_pending']:.1f}h)"
            )
        return "\n".join(lines)

    elif action == "message":
        if len(args) < 1:
            return "用法: payment message <payment_id>"
        return tracker.generate_reminder_message(args[0])

    return f"未知操作: {action}"


if __name__ == "__main__":
    tracker = PaymentTracker()
    pay = tracker.create_payment("INV-20250101-000001", 1000.0, method="wechat", customer_name="测试客户")
    print(f"Created: {pay.payment_id} ¥{pay.amount:.2f} verify={pay.verify_code}")
    print(tracker.get_report())
