"""
MolibOrder — 订单生命周期引擎（MedusaJS + Kill Bill 纯 Python 替代）
===================================================================
对标 MedusaJS (27K★) + Kill Bill (4K★): 订单管理 · 发票生成 · 支付追踪
Mac M2: <8MB 内存，纯 stdlib，SQLite 存证。

用法:
    python -m molib order create --customer "张三" --items '[{"name":"AI文案", "price":99}]'
    python -m molib order list --status pending
    python -m molib order invoice --order-id 1
    python -m molib order stats
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molib.order")

DB_PATH = Path.home() / ".hermes" / "molib_order.db"

# ═══════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════

ORDER_STATUSES = ["pending", "confirmed", "paid", "processing", "shipped", "completed", "cancelled", "refunded"]
STATUS_FLOW = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["paid", "cancelled"],
    "paid": ["processing", "refunded"],
    "processing": ["shipped", "cancelled"],
    "shipped": ["completed", "refunded"],
    "completed": [],
    "cancelled": [],
    "refunded": [],
}


@dataclass
class OrderItem:
    name: str
    price: float
    quantity: int = 1
    description: str = ""


class MolibOrder:
    """订单生命周期引擎。"""

    def __init__(self, db_path: str = ""):
        self.db_path = db_path or str(DB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_no TEXT UNIQUE NOT NULL,
                    customer_name TEXT NOT NULL,
                    customer_email TEXT DEFAULT '',
                    customer_phone TEXT DEFAULT '',
                    items_json TEXT NOT NULL DEFAULT '[]',
                    total_amount REAL NOT NULL DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    platform TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    method TEXT DEFAULT '',
                    transaction_id TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    paid_at TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT UNIQUE NOT NULL,
                    order_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT DEFAULT 'issued',
                    issued_at TEXT DEFAULT (datetime('now')),
                    due_at TEXT,
                    paid_at TEXT
                );
                CREATE TABLE IF NOT EXISTS order_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    from_status TEXT,
                    to_status TEXT,
                    note TEXT DEFAULT '',
                    created_at TEXT DEFAULT (datetime('now'))
                );
            """)
            conn.commit()

    # ── Create ────────────────────────────────────────────────

    def create_order(
        self,
        customer: str,
        items: list[dict],
        email: str = "",
        phone: str = "",
        platform: str = "",
        notes: str = "",
    ) -> dict:
        """创建订单。"""
        order_no = f"MOL-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        total = sum(it.get("price", 0) * it.get("quantity", 1) for it in items)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO orders (order_no, customer_name, customer_email, customer_phone,
                   items_json, total_amount, platform, notes)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (order_no, customer, email, phone, json.dumps(items, ensure_ascii=False),
                 total, platform, notes),
            )
            order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # 记录日志
            conn.execute(
                "INSERT INTO order_log (order_id, from_status, to_status, note) VALUES (?,'','pending','订单创建')",
                (order_id,),
            )
            conn.commit()

        return {
            "order_id": order_id,
            "order_no": order_no,
            "customer": customer,
            "total": round(total, 2),
            "items_count": len(items),
            "status": "pending",
        }

    # ── Read ──────────────────────────────────────────────────

    def get_order(self, order_id: int = 0, order_no: str = "") -> dict:
        with sqlite3.connect(self.db_path) as conn:
            if order_no:
                row = conn.execute("SELECT * FROM orders WHERE order_no=?", (order_no,)).fetchone()
            else:
                row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()

            if not row:
                return {"error": "订单不存在"}

        return self._row_to_dict(row)

    def list_orders(self, status: str = "", limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM orders WHERE status=? ORDER BY id DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,),
                ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def _row_to_dict(self, row) -> dict:
        return {
            "id": row[0], "order_no": row[1], "customer": row[2],
            "email": row[3], "phone": row[4],
            "items": json.loads(row[5]), "total": row[6],
            "status": row[7], "platform": row[8], "notes": row[9],
            "created_at": row[10], "updated_at": row[11],
        }

    # ── Update ────────────────────────────────────────────────

    def update_status(self, order_id: int, new_status: str, note: str = "") -> dict:
        """更新订单状态（带流转校验）。"""
        if new_status not in ORDER_STATUSES:
            return {"error": f"无效状态: {new_status}，可选 {ORDER_STATUSES}"}

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT id, status FROM orders WHERE id=?", (order_id,)).fetchone()
            if not row:
                return {"error": "订单不存在"}

            current = row[1]
            allowed = STATUS_FLOW.get(current, [])
            if new_status not in allowed and current != "":
                return {"error": f"不允许 {current} → {new_status}，允许: {allowed}"}

            conn.execute(
                "UPDATE orders SET status=?, updated_at=datetime('now') WHERE id=?",
                (new_status, order_id),
            )
            conn.execute(
                "INSERT INTO order_log (order_id, from_status, to_status, note) VALUES (?,?,?,?)",
                (order_id, current, new_status, note),
            )
            conn.commit()

        return {"order_id": order_id, "status": new_status, "previous": current}

    # ── Invoice ───────────────────────────────────────────────

    def create_invoice(self, order_id: int) -> dict:
        """为订单生成发票。"""
        order = self.get_order(order_id=order_id)
        if "error" in order:
            return order

        invoice_no = f"INV-{datetime.now().strftime('%y%m%d')}-{order_id:04d}"

        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "INSERT INTO invoices (invoice_no, order_id, amount, due_at) VALUES (?,?,?,datetime('now','+7 days'))",
                    (invoice_no, order_id, order["total"]),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                return {"error": "该订单已有发票"}

        return {
            "invoice_no": invoice_no,
            "order_no": order["order_no"],
            "customer": order["customer"],
            "amount": order["total"],
            "items": order["items"],
            "status": "issued",
        }

    def list_invoices(self, status: str = "") -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM invoices WHERE status=? ORDER BY id DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
        return [{"id": r[0], "invoice_no": r[1], "order_id": r[2], "amount": r[3],
                 "status": r[4], "issued_at": r[5], "due_at": r[6]} for r in rows]

    # ── Payment ───────────────────────────────────────────────

    def record_payment(self, order_id: int, amount: float, method: str = "", txn_id: str = "") -> dict:
        """记录付款。"""
        order = self.get_order(order_id=order_id)
        if "error" in order:
            return order

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO payments (order_id, amount, method, transaction_id, status, paid_at) VALUES (?,?,?,?,'completed',datetime('now'))",
                (order_id, amount, method, txn_id),
            )
            # 自动更新订单状态
            conn.execute("UPDATE orders SET status='paid', updated_at=datetime('now') WHERE id=?", (order_id,))
            conn.execute(
                "INSERT INTO order_log (order_id, from_status, to_status, note) VALUES (?,(SELECT status FROM orders WHERE id=?),'paid','收到付款')",
                (order_id, order_id),
            )
            conn.commit()

        return {"order_id": order_id, "amount": amount, "method": method, "status": "paid"}

    # ── Stats ─────────────────────────────────────────────────

    def stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
            by_status = dict(conn.execute(
                "SELECT status, COUNT(*) FROM orders GROUP BY status"
            ).fetchall())
            revenue = conn.execute(
                "SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status IN ('paid','processing','shipped','completed')"
            ).fetchone()[0]
            pending_revenue = conn.execute(
                "SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE status='pending'"
            ).fetchone()[0]
            invoices = conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            payments = conn.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM payments WHERE status='completed'").fetchone()

        return {
            "total_orders": total,
            "by_status": by_status,
            "revenue_completed": round(revenue, 2),
            "revenue_pending": round(pending_revenue, 2),
            "invoices": invoices,
            "payments_count": payments[0],
            "payments_total": round(payments[1], 2),
        }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def cmd_order_create(args: list[str]) -> dict:
    order = MolibOrder()
    customer = items = email = phone = platform = ""
    i = 0
    while i < len(args):
        if args[i] == "--customer" and i + 1 < len(args):
            customer = args[i + 1]; i += 2
        elif args[i] == "--items" and i + 1 < len(args):
            items = json.loads(args[i + 1]); i += 2
        elif args[i] == "--email" and i + 1 < len(args):
            email = args[i + 1]; i += 2
        elif args[i] == "--phone" and i + 1 < len(args):
            phone = args[i + 1]; i += 2
        elif args[i] == "--platform" and i + 1 < len(args):
            platform = args[i + 1]; i += 2
        else:
            i += 1
    if not customer or not items:
        return {"error": "需要 --customer 和 --items"}
    return order.create_order(customer, items, email, phone, platform)


def cmd_order_list(args: list[str]) -> dict:
    order = MolibOrder()
    status = ""
    i = 0
    while i < len(args):
        if args[i] == "--status" and i + 1 < len(args):
            status = args[i + 1]; i += 2
        else:
            i += 1
    return {"orders": order.list_orders(status)}


def cmd_order_invoice(args: list[str]) -> dict:
    order = MolibOrder()
    order_id = 0
    i = 0
    while i < len(args):
        if args[i] == "--order-id" and i + 1 < len(args):
            order_id = int(args[i + 1]); i += 2
        else:
            i += 1
    return order.create_invoice(order_id) if order_id else {"error": "需要 --order-id"}


def cmd_order_stats() -> dict:
    return MolibOrder().stats()
