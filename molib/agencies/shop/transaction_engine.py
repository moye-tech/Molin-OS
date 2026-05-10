"""墨链电商 — 交易引擎

Transaction lifecycle: pending → paid → shipped → delivered.
Order pipeline with status tracking, reporting, and fulfillment.
Storage: JSON at ~/.molin/shop/transactions.json
Stdlib-only, zero external dependencies.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Data Model ───────────────────────────────────────────────────────

VALID_STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled", "refunded"]
STATUS_TRANSITIONS = {
    "pending": ["paid", "cancelled"],
    "paid": ["shipped", "cancelled", "refunded"],
    "shipped": ["delivered", "refunded"],
    "delivered": ["refunded"],
    "cancelled": [],
    "refunded": [],
}


@dataclass
class Transaction:
    id: str
    product_id: str = ""
    product_name: str = ""
    customer: str = ""
    customer_contact: str = ""
    amount: float = 0.0
    quantity: int = 1
    status: str = "pending"
    platform: str = ""  # 闲鱼, 淘宝, etc.
    platform_order_id: str = ""
    shipping_carrier: str = ""
    shipping_tracking: str = ""
    notes: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    status_history: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.id:
            self.id = f"TXN-{str(uuid.uuid4())[:8].upper()}"
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.status_history:
            self.status_history = [{
                "status": self.status,
                "timestamp": self.created_at,
                "note": "Transaction created",
            }]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "customer": self.customer,
            "customer_contact": self.customer_contact,
            "amount": self.amount,
            "quantity": self.quantity,
            "status": self.status,
            "platform": self.platform,
            "platform_order_id": self.platform_order_id,
            "shipping_carrier": self.shipping_carrier,
            "shipping_tracking": self.shipping_tracking,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status_history": self.status_history,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Transaction:
        return cls(
            id=d.get("id", ""),
            product_id=d.get("product_id", ""),
            product_name=d.get("product_name", ""),
            customer=d.get("customer", ""),
            customer_contact=d.get("customer_contact", ""),
            amount=d.get("amount", 0.0),
            quantity=d.get("quantity", 1),
            status=d.get("status", "pending"),
            platform=d.get("platform", ""),
            platform_order_id=d.get("platform_order_id", ""),
            shipping_carrier=d.get("shipping_carrier", ""),
            shipping_tracking=d.get("shipping_tracking", ""),
            notes=d.get("notes", ""),
            created_at=d.get("created_at", 0.0),
            updated_at=d.get("updated_at", 0.0),
            status_history=d.get("status_history", []),
        )

    @property
    def summary(self) -> str:
        return (
            f"[{self.id}] {self.product_name} | ¥{self.amount:.0f} x{self.quantity} "
            f"| {self.customer} | {self.status}"
        )

    @property
    def total_amount(self) -> float:
        return self.amount * self.quantity


# ── Storage Layer ─────────────────────────────────────────────────────


class TransactionStore:
    """JSON-file-backed transaction storage."""

    def __init__(self, storage_dir: str = ""):
        if storage_dir:
            self._dir = Path(storage_dir)
        else:
            self._dir = Path.home() / ".molin" / "shop"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "transactions.json"

    def _load(self) -> dict[str, dict]:
        if not self._file.exists():
            return {}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self, data: dict[str, dict]) -> None:
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self._file)


# ── Transaction Engine ────────────────────────────────────────────────


class TransactionEngine:
    """Full transaction lifecycle management."""

    def __init__(self, storage_dir: str = ""):
        self._store = TransactionStore(storage_dir)

    # ── CRUD ──────────────────────────────────────────────────────

    def create(self, txn: Transaction) -> Transaction:
        data = self._store._load()
        if txn.id in data:
            raise ValueError(f"Transaction {txn.id} already exists")
        data[txn.id] = txn.to_dict()
        self._store._save(data)
        return txn

    def get(self, txn_id: str) -> Optional[Transaction]:
        data = self._store._load()
        d = data.get(txn_id)
        return Transaction.from_dict(d) if d else None

    def update_status(self, txn_id: str, new_status: str, note: str = "") -> Optional[Transaction]:
        """Transition a transaction to a new status with validation."""
        if new_status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}. Valid: {VALID_STATUSES}")

        data = self._store._load()
        d = data.get(txn_id)
        if not d:
            return None

        txn = Transaction.from_dict(d)
        if new_status not in STATUS_TRANSITIONS.get(txn.status, []):
            return None  # invalid transition, silently reject

        txn.status = new_status
        txn.updated_at = time.time()
        txn.status_history.append({
            "status": new_status,
            "timestamp": txn.updated_at,
            "note": note or f"Status changed to {new_status}",
        })
        data[txn_id] = txn.to_dict()
        self._store._save(data)
        return txn

    def update(self, txn_id: str, **kwargs) -> Optional[Transaction]:
        data = self._store._load()
        d = data.get(txn_id)
        if not d:
            return None
        allowed = {
            "customer", "customer_contact", "amount", "quantity",
            "platform", "platform_order_id", "shipping_carrier",
            "shipping_tracking", "notes", "product_name",
        }
        for k, v in kwargs.items():
            if k in allowed:
                d[k] = v
        d["updated_at"] = time.time()
        data[txn_id] = d
        self._store._save(data)
        return Transaction.from_dict(d)

    def list_all(self, status: str = "") -> list[Transaction]:
        data = self._store._load()
        txns = [Transaction.from_dict(d) for d in data.values()]
        if status:
            txns = [t for t in txns if t.status == status]
        txns.sort(key=lambda t: t.updated_at, reverse=True)
        return txns

    def search(self, query: str) -> list[Transaction]:
        q = query.lower()
        data = self._store._load()
        results = []
        for d in data.values():
            t = Transaction.from_dict(d)
            if (
                q in t.id.lower()
                or q in t.customer.lower()
                or q in t.product_name.lower()
                or q in t.product_id.lower()
            ):
                results.append(t)
        results.sort(key=lambda t: t.updated_at, reverse=True)
        return results

    # ── Order Pipeline ────────────────────────────────────────────

    def mark_paid(self, txn_id: str, note: str = "") -> Optional[Transaction]:
        return self.update_status(txn_id, "paid", note)

    def mark_shipped(self, txn_id: str, carrier: str = "", tracking: str = "") -> Optional[Transaction]:
        txn = self.update_status(txn_id, "shipped")
        if txn and (carrier or tracking):
            kwargs = {}
            if carrier:
                kwargs["shipping_carrier"] = carrier
            if tracking:
                kwargs["shipping_tracking"] = tracking
            self.update(txn_id, **kwargs)
        return txn

    def mark_delivered(self, txn_id: str) -> Optional[Transaction]:
        return self.update_status(txn_id, "delivered")

    def cancel(self, txn_id: str, note: str = "") -> Optional[Transaction]:
        return self.update_status(txn_id, "cancelled", note)

    def refund(self, txn_id: str, note: str = "") -> Optional[Transaction]:
        return self.update_status(txn_id, "refunded", note)

    # ── Reporting ─────────────────────────────────────────────────

    def get_report(self, period: str = "all") -> dict:
        """Generate a transaction report.
        
        period: 'today', 'week', 'month', 'all'
        """
        now = time.time()
        txns = self.list_all()

        if period == "today":
            cutoff = now - 86400
            txns = [t for t in txns if t.created_at >= cutoff]
        elif period == "week":
            cutoff = now - 7 * 86400
            txns = [t for t in txns if t.created_at >= cutoff]
        elif period == "month":
            cutoff = now - 30 * 86400
            txns = [t for t in txns if t.created_at >= cutoff]

        delivered = [t for t in txns if t.status == "delivered"]
        pending_payment = [t for t in txns if t.status == "pending"]
        in_transit = [t for t in txns if t.status in ("paid", "shipped")]
        cancelled = [t for t in txns if t.status in ("cancelled", "refunded")]

        total_revenue = sum(t.total_amount for t in delivered)
        pending_revenue = sum(t.total_amount for t in pending_payment)
        cancelled_loss = sum(t.total_amount for t in cancelled)

        # Conversion funnel
        total_created = len(txns)
        conversion_rate = (len(delivered) / total_created * 100) if total_created > 0 else 0

        return {
            "period": period,
            "total_transactions": total_created,
            "delivered": len(delivered),
            "pending_payment": len(pending_payment),
            "in_transit": len(in_transit),
            "cancelled_or_refunded": len(cancelled),
            "total_revenue": round(total_revenue, 2),
            "pending_revenue": round(pending_revenue, 2),
            "cancelled_loss": round(cancelled_loss, 2),
            "conversion_rate": round(conversion_rate, 1),
            "reported_at": now,
        }

    def get_daily_report(self) -> dict:
        """Convenience: today's report."""
        return self.get_report("today")

    def get_statistics(self) -> dict:
        """Lifetime statistics."""
        report = self.get_report("all")
        txns = self.list_all()

        # Per-platform stats
        platforms = {}
        for t in txns:
            plat = t.platform or "unknown"
            if plat not in platforms:
                platforms[plat] = {"count": 0, "revenue": 0.0}
            platforms[plat]["count"] += 1
            if t.status == "delivered":
                platforms[plat]["revenue"] += t.total_amount

        # Top products
        product_revenue = {}
        for t in txns:
            if t.status == "delivered":
                key = t.product_name or t.product_id
                product_revenue[key] = product_revenue.get(key, 0) + t.total_amount
        top_products = sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            **report,
            "by_platform": platforms,
            "top_products": [{"name": k, "revenue": round(v, 2)} for k, v in top_products],
        }

    def count(self) -> int:
        return len(self._store._load())


# ── Quick CLI helpers ─────────────────────────────────────────────────


def _parse_args(args: list[str]) -> dict:
    opts = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                opts[key] = args[i + 1]
                i += 2
            else:
                opts[key] = True
                i += 1
        else:
            i += 1
    return opts


def cmd_order(args: list[str]) -> dict:
    """CLI handler for order/transaction commands."""
    if not args:
        return {
            "error": "子命令: create | list | status | search | report | daily | stats | paid | ship | deliver | cancel | refund"
        }

    subcmd = args[0]
    rest = args[1:]
    opts = _parse_args(rest)
    te = TransactionEngine()

    if subcmd == "create":
        txn = Transaction(
            product_id=opts.get("product-id", opts.get("product_id", "")),
            product_name=opts.get("product-name", opts.get("product_name", "")),
            customer=opts.get("customer", "unknown"),
            customer_contact=opts.get("contact", ""),
            amount=float(opts.get("amount", 0)),
            quantity=int(opts.get("quantity", 1)),
            platform=opts.get("platform", "闲鱼"),
            notes=opts.get("notes", ""),
        )
        te.create(txn)
        return {"status": "created", "transaction": txn.to_dict()}

    elif subcmd == "list":
        status = opts.get("status", "")
        txns = te.list_all(status)
        return {
            "count": len(txns),
            "transactions": [t.to_dict() for t in txns],
            "summaries": [t.summary for t in txns],
        }

    elif subcmd == "search":
        query = opts.get("query", rest[0] if rest else "")
        if not query:
            return {"error": "--query is required"}
        results = te.search(query)
        return {"query": query, "count": len(results), "results": [t.to_dict() for t in results]}

    elif subcmd == "status":
        txn_id = opts.get("id", rest[0] if rest else "")
        if not txn_id:
            return {"error": "--id is required"}
        new_status = opts.get("set", "")
        if not new_status:
            txn = te.get(txn_id)
            if not txn:
                return {"error": f"Transaction {txn_id} not found"}
            return {"transaction": txn.to_dict()}
        txn = te.update_status(txn_id, new_status, opts.get("note", ""))
        if not txn:
            return {"error": f"Failed to update {txn_id} to {new_status} (invalid transition?)"}
        return {"status": "updated", "transaction": txn.to_dict()}

    elif subcmd == "report":
        period = opts.get("period", "all")
        return te.get_report(period)

    elif subcmd == "daily":
        return te.get_daily_report()

    elif subcmd == "stats":
        return te.get_statistics()

    elif subcmd == "paid":
        txn_id = opts.get("id", rest[0] if rest else "")
        if not txn_id:
            return {"error": "--id is required"}
        txn = te.mark_paid(txn_id, opts.get("note", "Payment received"))
        if not txn:
            return {"error": f"Cannot mark {txn_id} as paid"}
        return {"status": "paid", "transaction": txn.to_dict()}

    elif subcmd == "ship":
        txn_id = opts.get("id", rest[0] if rest else "")
        if not txn_id:
            return {"error": "--id is required"}
        txn = te.mark_shipped(txn_id, opts.get("carrier", ""), opts.get("tracking", ""))
        if not txn:
            return {"error": f"Cannot ship {txn_id}"}
        return {"status": "shipped", "transaction": txn.to_dict()}

    elif subcmd == "deliver":
        txn_id = opts.get("id", rest[0] if rest else "")
        if not txn_id:
            return {"error": "--id is required"}
        txn = te.mark_delivered(txn_id)
        if not txn:
            return {"error": f"Cannot mark {txn_id} as delivered"}
        return {"status": "delivered", "transaction": txn.to_dict()}

    elif subcmd == "cancel":
        txn_id = opts.get("id", rest[0] if rest else "")
        if not txn_id:
            return {"error": "--id is required"}
        txn = te.cancel(txn_id, opts.get("note", "Cancelled"))
        if not txn:
            return {"error": f"Cannot cancel {txn_id}"}
        return {"status": "cancelled", "transaction": txn.to_dict()}

    elif subcmd == "refund":
        txn_id = opts.get("id", rest[0] if rest else "")
        if not txn_id:
            return {"error": "--id is required"}
        txn = te.refund(txn_id, opts.get("note", "Refunded"))
        if not txn:
            return {"error": f"Cannot refund {txn_id}"}
        return {"status": "refunded", "transaction": txn.to_dict()}

    return {"error": f"未知子命令: {subcmd}"}
