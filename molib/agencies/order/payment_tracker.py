"""
墨单订单 — 支付追踪器 (Payment Tracker)
=========================================
吸收自 Kill Bill (github.com/killbill/killbill 4k stars)
支付网关抽象和 Invoice Ninja 的在线支付追踪。

纯标准库实现：
- 记录支付
- 查余额/对账
- 支付列表
- JSON 持久化存储

零外部依赖。
"""

import json
import uuid
import time
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ── 存储目录 ─────────────────────────────────────────────────
PAYMENTS_DIR = Path.home() / ".molin" / "orders"
PAYMENTS_DIR.mkdir(parents=True, exist_ok=True)
PAYMENTS_FILE = PAYMENTS_DIR / "payments.json"


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass
class Payment:
    """一笔支付记录"""
    payment_id: str
    invoice_id: str
    amount: float
    method: str = "未知"  # wechat | alipay | bank_transfer | cash | other
    status: str = "completed"  # completed | pending | failed | refunded
    paid_at: Optional[float] = None
    note: str = ""
    order_id: str = ""

    def __post_init__(self):
        if not self.payment_id:
            self.payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        if self.paid_at is None and self.status == "completed":
            self.paid_at = time.time()

    def to_dict(self) -> dict:
        return {
            "payment_id": self.payment_id,
            "invoice_id": self.invoice_id,
            "amount": self.amount,
            "method": self.method,
            "status": self.status,
            "paid_at": self.paid_at,
            "note": self.note,
            "order_id": self.order_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Payment":
        return cls(
            payment_id=data.get("payment_id", ""),
            invoice_id=data.get("invoice_id", ""),
            amount=data.get("amount", 0.0),
            method=data.get("method", "未知"),
            status=data.get("status", "completed"),
            paid_at=data.get("paid_at"),
            note=data.get("note", ""),
            order_id=data.get("order_id", ""),
        )


# ═══════════════════════════════════════════════════════════════
# 支付仓库
# ═══════════════════════════════════════════════════════════════

class PaymentStore:
    """支付存储 — JSON 持久化"""

    def __init__(self):
        self._payments: dict[str, Payment] = {}
        self._load()

    def _load(self):
        if PAYMENTS_FILE.exists():
            try:
                data = json.loads(PAYMENTS_FILE.read_text(encoding="utf-8"))
                for pdata in data.get("payments", []):
                    payment = Payment.from_dict(pdata)
                    self._payments[payment.payment_id] = payment
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self):
        """持久化全部支付到文件"""
        data = {
            "payments": [p.to_dict() for p in self._payments.values()],
            "updated_at": time.time(),
        }
        PAYMENTS_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def record_payment(
        self,
        invoice_id: str,
        amount: float,
        method: str = "未知",
        note: str = "",
        order_id: str = "",
    ) -> Payment:
        """记录一笔支付"""
        payment = Payment(
            payment_id="",
            invoice_id=invoice_id,
            amount=amount,
            method=method,
            status="completed",
            note=note,
            order_id=order_id,
        )
        self._payments[payment.payment_id] = payment
        self._save()
        return payment

    def get_balance(self, invoice_id: str) -> dict:
        """
        获取某发票的支付余额。

        从 invoice_engine 加载发票总金额，
        减去已付金额，返回未付余额。
        """
        try:
            from molib.agencies.order.invoice_engine import Invoice
            invoice = Invoice.load(invoice_id)
            total = invoice.total if invoice else 0.0
        except Exception:
            total = 0.0

        paid = sum(
            p.amount
            for p in self._payments.values()
            if p.invoice_id == invoice_id and p.status == "completed"
        )

        return {
            "invoice_id": invoice_id,
            "total": round(total, 2),
            "paid": round(paid, 2),
            "balance": round(total - paid, 2),
        }

    def list_payments(
        self,
        invoice_id: str | None = None,
        status: str | None = None,
        order_id: str | None = None,
    ) -> list[Payment]:
        """列出支付记录，可按发票/状态/订单过滤"""
        payments = list(self._payments.values())
        if invoice_id:
            payments = [p for p in payments if p.invoice_id == invoice_id]
        if status:
            payments = [p for p in payments if p.status == status]
        if order_id:
            payments = [p for p in payments if p.order_id == order_id]
        payments.sort(key=lambda p: p.paid_at or 0, reverse=True)
        return payments

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        return self._payments.get(payment_id)

    def update_status(self, payment_id: str, status: str) -> bool:
        """更新支付状态"""
        payment = self._payments.get(payment_id)
        if not payment:
            return False
        payment.status = status
        self._save()
        return True

    def total_revenue(self) -> dict:
        """总收入统计"""
        total = 0.0
        by_method = {}
        for p in self._payments.values():
            if p.status == "completed":
                total += p.amount
                by_method[p.method] = by_method.get(p.method, 0.0) + p.amount
        return {
            "total": round(total, 2),
            "count": len(self._payments),
            "by_method": {k: round(v, 2) for k, v in by_method.items()},
        }
