"""
墨单订单 Worker — 完整版
========================
负责从询盘到收款的订单全生命周期管理。

整合:
- Invoice Ninja 设计模式 (发票引擎)
- Kill Bill 设计模式 (支付追踪)
- PocketBase 本地后端 (统一数据存储)

Worker 方法:
  create_order       — 创建新订单
  create_invoice     — 为订单生成发票
  record_payment     — 记录付款并自动更新发票状态
  get_order_status   — 获取订单+发票+支付完整视图
  list_orders        — 列出订单
  transition_order   — 推进订单状态
  stats              — 综合统计报告
  daily_report       — 每日报告文本
  remind_overdue     — 逾期发票提醒

Author: 墨麟AI集团 · 墨单订单子公司
Version: 2.0 — 完整集成版
"""

from __future__ import annotations

import json
import time
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


class OrderWorker(SubsidiaryWorker):
    worker_id = "order_worker"
    worker_name = "墨单订单"
    description = "订单 Worker：询盘处理、报价生成、交付跟踪、状态管理、发票与支付"
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
        tax_regime: str = "CN_SMALL",
        due_days: int = 30,
    ) -> dict:
        """为订单创建发票。

        Args:
            order_id: 订单ID
            items: [{"name": "服务费", "amount": 1000, "quantity": 1}, ...]
                  若为 None，则自动从订单 estimated_value 生成单行项目
        """
        from molib.agencies.order.invoice_engine import InvoiceEngine

        order = self._store.get(order_id)
        if not order:
            return {"error": f"订单不存在: {order_id}"}

        if not customer_name:
            customer_name = f"客户 ({order.source})"

        if not items:
            items = [{
                "name": order.title,
                "amount": order.estimated_value or 0,
                "quantity": 1,
                "description": order.description[:100] if order.description else "",
            }]

        engine = InvoiceEngine()
        invoice = engine.create_invoice(
            customer_name=customer_name,
            items=items,
            customer_email=customer_email,
            notes=notes or f"订单 {order_id}: {order.title}",
            tax_regime=tax_regime,
            due_days=due_days,
        )

        return {
            "invoice_id": invoice.invoice_id,
            "order_id": order_id,
            "customer_name": invoice.customer_name,
            "subtotal": invoice.subtotal_amount,
            "tax": invoice.tax_amount,
            "total": invoice.total_amount,
            "status": invoice.status,
            "due_date": invoice.due_date,
            "items_count": len(invoice.items),
        }

    def record_payment(
        self,
        invoice_id: str,
        amount: float,
        method: str = "wechat",
        note: str = "",
    ) -> dict:
        """记录一笔付款，并自动更新发票状态"""
        from molib.agencies.order.invoice_engine import InvoiceEngine
        from molib.agencies.order.payment_tracker import PaymentTracker

        tracker = PaymentTracker()
        engine = InvoiceEngine()

        # 创建支付记录
        payment = tracker.create_payment(
            invoice_id=invoice_id,
            amount=amount,
            method=method,
            notes=note,
        )

        # 检查发票总金额，判断是否全额支付
        invoice = engine.get_invoice(invoice_id)
        if invoice:
            # 获取该发票的所有支付总额
            all_payments = tracker.get_by_invoice(invoice_id)
            total_paid = sum(p.amount for p in all_payments if p.status == "paid")
            total_paid += amount  # 加上当前支付

            if total_paid >= invoice.total_amount:
                # 全额支付 - 标记支付为已付 + 发票为已付
                tracker.mark_paid(payment.payment_id)
                engine.mark_paid(invoice_id, method=method)

        return {
            "payment_id": payment.payment_id,
            "invoice_id": invoice_id,
            "amount": amount,
            "method": method,
            "verify_code": payment.verify_code,
        }

    def get_order_status(self, order_id: str) -> dict:
        """获取订单完整状态：订单 + 发票 + 支付"""
        from molib.agencies.order.invoice_engine import InvoiceEngine
        from molib.agencies.order.payment_tracker import PaymentTracker

        order = self._store.get(order_id)
        if not order:
            return {"error": f"订单不存在: {order_id}"}

        # 发票（通过备注字段关联，因为 Invoice 没有 order_id 字段）
        engine = InvoiceEngine()
        all_invoices = engine.list_invoices()
        order_invoices = [
            inv.to_dict() for inv in all_invoices
            if order_id in (inv.notes or "")
        ]

        # 支付
        tracker = PaymentTracker()
        payments = []
        for inv in order_invoices:
            inv_payments = tracker.get_by_invoice(inv["invoice_id"])
            payments.extend([p.to_dict() for p in inv_payments])

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
            "timeline": order.timeline[-5:],
            "deliverables": order.deliverables,
            "invoices": order_invoices,
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
                    "priority": o.priority,
                    "updated_at": datetime.fromtimestamp(o.updated_at).isoformat(),
                }
                for o in orders
            ],
        }

    def transition_order(self, order_id: str, new_status: str) -> dict:
        """推进订单状态"""
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
        from molib.agencies.order.invoice_engine import InvoiceEngine
        from molib.agencies.order.payment_tracker import PaymentTracker

        order_stats = self._store.stats()
        engine = InvoiceEngine()
        invoice_report = engine.get_report()
        tracker = PaymentTracker()
        payment_report = tracker.get_report()

        return {
            "orders": order_stats,
            "invoices": invoice_report,
            "payments": payment_report,
            "generated_at": datetime.now().isoformat(),
        }

    def daily_report(self) -> str:
        """生成每日订单报告"""
        data = self.stats()
        lines = [
            "=" * 50,
            "  墨单订单 · 每日报告",
            f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 50,
        ]

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
        lines.append(f"\n  发票: 总计 {invoices.get('total_count', 0)} 张")
        lines.append(f"    已收: ¥{invoices.get('paid_amount', 0):,.2f}")
        lines.append(f"    未收: ¥{invoices.get('unpaid_amount', 0):,.2f}")

        payments = data["payments"]
        lines.append(f"\n  支付: 共 {payments.get('total_payments', 0)} 笔")
        lines.append(f"    已付: {payments.get('paid_count', 0)} 笔 ¥{payments.get('paid_amount', 0):,.2f}")
        lines.append(f"    待付: {payments.get('pending_count', 0)} 笔 ¥{payments.get('pending_amount', 0):,.2f}")

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)

    def remind_overdue(self) -> dict:
        """检查逾期发票并生成提醒"""
        from molib.agencies.order.invoice_engine import InvoiceEngine
        from molib.agencies.order.payment_tracker import PaymentTracker

        engine = InvoiceEngine()
        overdue = engine.check_overdue()
        tracker = PaymentTracker()
        reminders = tracker.get_pending_reminders(overdue_only=True)

        return {
            "overdue_invoices": len(overdue),
            "overdue_amount": sum(inv.total_amount for inv in overdue),
            "pending_reminders": len(reminders),
            "details": [
                {
                    "invoice_id": inv.invoice_id,
                    "customer": inv.customer_name,
                    "amount": inv.total_amount,
                    "due_date": inv.due_date,
                }
                for inv in overdue
            ],
        }

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
                    tax_regime=payload.get("tax_regime", "CN_SMALL"),
                    due_days=payload.get("due_days", 30),
                )
            elif action == "record_payment":
                result = self.record_payment(
                    invoice_id=payload.get("invoice_id", ""),
                    amount=payload.get("amount", 0.0),
                    method=payload.get("method", "wechat"),
                    note=payload.get("note", ""),
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
            elif action == "remind_overdue":
                result = self.remind_overdue()
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
