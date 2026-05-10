"""
订单 Worker — 负责询盘处理、报价生成、交付跟踪、订单状态更新
=============================================================
整合 Invoice Ninja 发票引擎 + Kill Bill 支付追踪。

Worker 方法:
  create_order    — 创建新订单
  create_invoice  — 为订单生成发票
  record_payment  — 记录付款
  get_order_status — 获取订单状态
  list_orders     — 列出订单
  daily_report    — 日报摘要
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from molib.agencies.workers.base import (
    SubsidiaryWorker,
    Task,
    WorkerResult,
)
from molib.business.order_engine import (
    Order,
    OrderStatus,
    OrderStore,
    VALID_TRANSITIONS,
)

# ── 存储目录 ─────────────────────────────────────────────────
ORDER_DIR = Path.home() / ".molin" / "orders"
ORDER_DIR.mkdir(parents=True, exist_ok=True)


class OrderWorker(SubsidiaryWorker):
    worker_id = "order_worker"
    worker_name = "墨单订单"
    description = "订单 Worker：询盘处理、报价生成、交付跟踪、订单状态更新、发票与支付"
    oneliner = "从询盘到收款，全生命周期订单管理"

    def __init__(self):
        self._store = OrderStore()

    # ── 核心操作方法 ──────────────────────────────────────

    def create_order(
        self,
        source: str,
        title: str,
        description: str,
        estimated_value: float = 0.0,
        tags: list[str] | None = None,
    ) -> dict:
        """创建新订单"""
        order = self._store.create(
            source=source,
            title=title,
            description=description,
            estimated_value=estimated_value,
            tags=tags or [],
        )
        return {
            "order_id": order.id,
            "title": order.title,
            "source": order.source,
            "status": order.status.value,
            "estimated_value": order.estimated_value,
            "created_at": datetime.fromtimestamp(order.created_at).isoformat(),
        }

    def create_invoice(
        self,
        order_id: str,
        items: list[dict] | None = None,
        customer_name: str = "",
        customer_email: str = "",
        notes: str = "",
        tax_rate: float = 0.0,
        due_days: int = 30,
    ) -> dict:
        """为订单创建发票"""
        from molib.agencies.order.invoice_engine import Invoice, InvoiceItem

        order = self._store.get(order_id)
        if not order:
            return {"error": f"订单不存在: {order_id}"}

        if not customer_name:
            customer_name = f"客户 ({order.source})"

        invoice = Invoice(
            invoice_id="",
            customer_name=customer_name,
            customer_email=customer_email,
            tax_rate=tax_rate,
            status="draft",
            notes=notes or f"订单 {order_id}: {order.title}",
            order_id=order_id,
        )

        if items:
            for item_data in items:
                invoice.add_item(
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", 1.0),
                    unit_price=item_data.get("unit_price", 0.0),
                    tax_rate=item_data.get("tax_rate", tax_rate),
                )
        else:
            # 自动从订单生成行项目
            invoice.add_item(
                description=order.title,
                quantity=1.0,
                unit_price=order.estimated_value,
                tax_rate=tax_rate,
            )

        filepath = invoice.save()
        return {
            "invoice_id": invoice.invoice_id,
            "order_id": order_id,
            "total": invoice.total,
            "status": invoice.status,
            "saved_to": filepath,
            "text_preview": invoice.generate_text(),
        }

    def record_payment(
        self,
        invoice_id: str,
        amount: float,
        method: str = "unknown",
        note: str = "",
        order_id: str = "",
    ) -> dict:
        """记录一笔支付"""
        from molib.agencies.order.payment_tracker import PaymentStore

        store = PaymentStore()
        payment = store.record_payment(
            invoice_id=invoice_id,
            amount=amount,
            method=method,
            note=note,
            order_id=order_id,
        )
        balance = store.get_balance(invoice_id)

        # 如果已全额支付，更新发票状态
        if balance["balance"] <= 0:
            from molib.agencies.order.invoice_engine import Invoice
            invoice = Invoice.load(invoice_id)
            if invoice:
                invoice.status = "paid"
                invoice.paid_at = time.time()
                invoice.save()

        return {
            "payment_id": payment.payment_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "method": method,
            "balance": balance,
        }

    def get_order_status(self, order_id: str) -> dict:
        """获取订单详细信息"""
        order = self._store.get(order_id)
        if not order:
            return {"error": f"订单不存在: {order_id}"}

        # 加载关联的发票
        from molib.agencies.order.invoice_engine import Invoice
        invoices = [
            inv.to_dict()
            for inv in Invoice.list_all()
            if inv.order_id == order_id
        ]

        # 加载关联的支付
        from molib.agencies.order.payment_tracker import PaymentStore
        payment_store = PaymentStore()
        payments = [
            p.to_dict()
            for p in payment_store.list_payments(order_id=order_id)
        ]

        return {
            "order_id": order.id,
            "title": order.title,
            "source": order.source,
            "description": order.description,
            "status": order.status.value,
            "estimated_value": order.estimated_value,
            "actual_value": order.actual_value,
            "priority": order.priority,
            "tags": order.tags,
            "timeline": order.timeline[-5:],  # 最近5条
            "deliverables": order.deliverables,
            "invoices": invoices,
            "payments": payments,
            "created_at": datetime.fromtimestamp(order.created_at).isoformat(),
            "updated_at": datetime.fromtimestamp(order.updated_at).isoformat(),
        }

    def list_orders(
        self,
        status: str | None = None,
        source: str | None = None,
    ) -> dict:
        """列出订单"""
        status_enum = None
        if status:
            try:
                status_enum = OrderStatus(status)
            except ValueError:
                pass

        orders = self._store.list(status=status_enum, source=source)
        return {
            "count": len(orders),
            "orders": [
                {
                    "order_id": o.id,
                    "title": o.title,
                    "source": o.source,
                    "status": o.status.value,
                    "estimated_value": o.estimated_value,
                    "actual_value": o.actual_value,
                    "updated_at": datetime.fromtimestamp(o.updated_at).isoformat(),
                }
                for o in orders
            ],
        }

    def transition_order(self, order_id: str, new_status: str) -> dict:
        """手动推进订单状态"""
        try:
            status_enum = OrderStatus(new_status)
        except ValueError:
            return {"error": f"无效状态: {new_status}"}

        ok = self._store.update_status(order_id, status_enum)
        if not ok:
            order = self._store.get(order_id)
            current = order.status.value if order else "?"
            allowed = [s.value for s in VALID_TRANSITIONS.get(
                order.status, []
            )] if order else []
            return {
                "error": f"不允许 {current} → {new_status}",
                "allowed_transitions": allowed,
            }

        order = self._store.get(order_id)
        return {
            "order_id": order_id,
            "new_status": new_status,
            "updated_at": datetime.fromtimestamp(order.updated_at).isoformat(),
        }

    def stats(self) -> dict:
        """订单 + 发票 + 支付综合统计"""
        from molib.agencies.order.invoice_engine import get_invoice_stats
        from molib.agencies.order.payment_tracker import PaymentStore

        order_stats = self._store.stats()
        invoice_stats = get_invoice_stats()
        payment_store = PaymentStore()
        revenue = payment_store.total_revenue()

        return {
            "orders": order_stats,
            "invoices": invoice_stats,
            "revenue": revenue,
            "generated_at": datetime.now().isoformat(),
        }

    def daily_report(self) -> str:
        """生成每日订单报告（纯文本）"""
        data = self.stats()
        lines = []
        lines.append("=" * 50)
        lines.append("  墨单订单 · 每日报告")
        lines.append(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 50)

        orders = data["orders"]
        lines.append(f"\n  订单总数: {orders['total']}")
        lines.append(f"  成交总额: ¥{orders.get('total_value', 0):,.2f}")
        lines.append(f"  待审批门控: {orders.get('pending_gates', 0)}")

        by_status = orders.get("by_status", {})
        if by_status:
            lines.append("\n  按状态分布:")
            for s, c in sorted(by_status.items()):
                lines.append(f"    {s}: {c}")

        invoices = data["invoices"]
        lines.append(f"\n  发票总数: {invoices.get('total', 0)}")
        lines.append(f"  已收款总额: ¥{invoices.get('total_paid_value', 0):,.2f}")
        by_inv_status = invoices.get("by_status", {})
        if by_inv_status:
            for s, c in sorted(by_inv_status.items()):
                lines.append(f"    发票 {s}: {c}")

        revenue = data["revenue"]
        lines.append(f"\n  实收总额: ¥{revenue.get('total', 0):,.2f}")
        lines.append(f"  支付笔数: {revenue.get('count', 0)}")
        by_method = revenue.get("by_method", {})
        if by_method:
            lines.append("  按方式:")
            for m, v in sorted(by_method.items()):
                lines.append(f"    {m}: ¥{v:,.2f}")

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)

    # ── Worker 协议实现 ───────────────────────────────────

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        """统一执行入口"""
        payload = task.payload if isinstance(task.payload, dict) else {}
        action = payload.get("action", task.task_type)

        try:
            if action == "create_order":
                result = self.create_order(
                    source=payload.get("source", "direct"),
                    title=payload.get("title", ""),
                    description=payload.get("description", ""),
                    estimated_value=payload.get("estimated_value", 0.0),
                    tags=payload.get("tags"),
                )
            elif action == "create_invoice":
                result = self.create_invoice(
                    order_id=payload.get("order_id", ""),
                    items=payload.get("items"),
                    customer_name=payload.get("customer_name", ""),
                    customer_email=payload.get("customer_email", ""),
                    notes=payload.get("notes", ""),
                    tax_rate=payload.get("tax_rate", 0.0),
                    due_days=payload.get("due_days", 30),
                )
            elif action == "record_payment":
                result = self.record_payment(
                    invoice_id=payload.get("invoice_id", ""),
                    amount=payload.get("amount", 0.0),
                    method=payload.get("method", "unknown"),
                    note=payload.get("note", ""),
                    order_id=payload.get("order_id", ""),
                )
            elif action == "get_order_status":
                result = self.get_order_status(
                    order_id=payload.get("order_id", ""),
                )
            elif action == "list_orders":
                result = self.list_orders(
                    status=payload.get("status"),
                    source=payload.get("source"),
                )
            elif action == "transition":
                result = self.transition_order(
                    order_id=payload.get("order_id", ""),
                    new_status=payload.get("new_status", ""),
                )
            elif action == "stats":
                result = self.stats()
            elif action == "daily_report":
                result = {"report": self.daily_report()}
            else:
                return WorkerResult(
                    task_id=task.task_id,
                    worker_id=self.worker_id,
                    status="error",
                    error=f"未知操作: {action}",
                )

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=result if isinstance(result, dict) else {"data": str(result)},
            )

        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                error=str(e),
            )

    def quality_check(self, output: dict) -> float:
        return 90.0
