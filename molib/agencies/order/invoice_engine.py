"""
墨单订单 — 发票引擎
===================
吸收 invoiceninja (9K⭐) 设计模式：
- 模板化发票生成
- 在线支付状态追踪
- 税务支持（中国增值税）
- 客户门户数据导出

Mac M2: stdlib-only, 零外部依赖。

用法:
    from molib.agencies.order.invoice_engine import InvoiceEngine
    engine = InvoiceEngine()
    inv = engine.create_invoice("客户A", [{"name": "服务费", "amount": 1000}])
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

INVOICE_DIR = Path.home() / ".molin" / "orders" / "invoices"

TAX_RATES = {
    "CN": 0.13,   # 中国增值税 13%
    "CN_SMALL": 0.03,  # 小规模纳税人 3%
    "NONE": 0.0,
}


@dataclass
class InvoiceItem:
    name: str
    amount: float       # 不含税金额
    quantity: int = 1
    unit: str = "项"
    tax_rate: float = 0.13
    description: str = ""

    @property
    def subtotal(self) -> float:
        return self.amount * self.quantity

    @property
    def tax(self) -> float:
        return round(self.subtotal * self.tax_rate, 2)

    @property
    def total(self) -> float:
        return round(self.subtotal + self.tax, 2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "amount": self.amount,
            "quantity": self.quantity,
            "unit": self.unit,
            "tax_rate": self.tax_rate,
            "description": self.description,
            "subtotal": self.subtotal,
            "tax": self.tax,
            "total": self.total,
        }


@dataclass
class Invoice:
    invoice_id: str
    customer_name: str
    customer_email: str = ""
    items: list[InvoiceItem] = field(default_factory=list)
    status: str = "draft"  # draft → sent → paid → overdue → cancelled
    notes: str = ""
    tax_regime: str = "CN"  # CN / CN_SMALL / NONE
    created_at: str = ""
    due_date: str = ""
    paid_at: str = ""
    payment_method: str = ""

    @property
    def subtotal_amount(self) -> float:
        return sum(i.subtotal for i in self.items)

    @property
    def tax_amount(self) -> float:
        return sum(i.tax for i in self.items)

    @property
    def total_amount(self) -> float:
        return round(self.subtotal_amount + self.tax_amount, 2)

    def to_dict(self) -> dict:
        return {
            "invoice_id": self.invoice_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "items": [i.to_dict() for i in self.items],
            "status": self.status,
            "notes": self.notes,
            "tax_regime": self.tax_regime,
            "subtotal": self.subtotal_amount,
            "tax": self.tax_amount,
            "total": self.total_amount,
            "created_at": self.created_at,
            "due_date": self.due_date,
            "paid_at": self.paid_at,
            "payment_method": self.payment_method,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Invoice:
        items = [InvoiceItem(**i) for i in data.get("items", [])]
        return cls(
            invoice_id=data["invoice_id"],
            customer_name=data["customer_name"],
            customer_email=data.get("customer_email", ""),
            items=items,
            status=data.get("status", "draft"),
            notes=data.get("notes", ""),
            tax_regime=data.get("tax_regime", "CN"),
            created_at=data.get("created_at", ""),
            due_date=data.get("due_date", ""),
            paid_at=data.get("paid_at", ""),
            payment_method=data.get("payment_method", ""),
        )


class InvoiceEngine:
    """发票生成引擎。"""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or INVOICE_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Invoice] = {}

    # ── CRUD ──────────────────────────────────────────

    def create_invoice(
        self,
        customer_name: str,
        items: list[dict],
        *,
        customer_email: str = "",
        notes: str = "",
        tax_regime: str = "CN_SMALL",
        due_days: int = 30,
    ) -> Invoice:
        """创建发票。

        items: [{"name": "服务费", "amount": 1000, "quantity": 1}, ...]
        """
        inv = Invoice(
            invoice_id=f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            customer_name=customer_name,
            customer_email=customer_email,
            items=[InvoiceItem(
                name=i["name"],
                amount=i["amount"],
                quantity=i.get("quantity", 1),
                unit=i.get("unit", "项"),
                tax_rate=TAX_RATES.get(tax_regime, TAX_RATES["CN"]),
                description=i.get("description", ""),
            ) for i in items],
            status="draft",
            notes=notes,
            tax_regime=tax_regime,
            created_at=datetime.now().isoformat(),
            due_date=(datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d"),
        )
        self._save(inv)
        return inv

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        """获取发票。"""
        if invoice_id in self._cache:
            return self._cache[invoice_id]
        filepath = self.storage_dir / f"{invoice_id}.json"
        if filepath.exists():
            with open(filepath) as f:
                inv = Invoice.from_dict(json.load(f))
                self._cache[invoice_id] = inv
                return inv
        return None

    def list_invoices(self, status: str = "") -> list[Invoice]:
        """列出所有发票。"""
        invoices = []
        for fp in sorted(self.storage_dir.glob("*.json"), reverse=True):
            try:
                with open(fp) as f:
                    data = json.load(f)
                    inv = Invoice.from_dict(data)
                    if not status or inv.status == status:
                        invoices.append(inv)
            except Exception:
                continue
        return invoices

    def update_status(self, invoice_id: str, status: str, **kwargs) -> Optional[Invoice]:
        """更新发票状态。

        status: draft → sent → paid → overdue → cancelled
        """
        inv = self.get_invoice(invoice_id)
        if not inv:
            return None
        inv.status = status
        if status == "paid":
            inv.paid_at = datetime.now().isoformat()
            inv.payment_method = kwargs.get("payment_method", "")
        self._save(inv)
        return inv

    def mark_sent(self, invoice_id: str) -> Optional[Invoice]:
        return self.update_status(invoice_id, "sent")

    def mark_paid(self, invoice_id: str, method: str = "bank_transfer") -> Optional[Invoice]:
        return self.update_status(invoice_id, "paid", payment_method=method)

    def cancel(self, invoice_id: str) -> Optional[Invoice]:
        return self.update_status(invoice_id, "cancelled")

    def check_overdue(self) -> list[Invoice]:
        """检查逾期发票。"""
        overdue = []
        today = datetime.now().strftime("%Y-%m-%d")
        for inv in self.list_invoices():
            if inv.status in ("sent", "draft") and inv.due_date < today:
                inv.status = "overdue"
                self._save(inv)
                overdue.append(inv)
        return overdue

    # ── Report ────────────────────────────────────────

    def get_report(self, year: int = 0, month: int = 0) -> dict:
        """生成发票汇总报告。"""
        invoices = self.list_invoices()
        report = {
            "total_count": len(invoices),
            "total_amount": 0.0,
            "paid_amount": 0.0,
            "unpaid_amount": 0.0,
            "by_status": {},
            "by_customer": {},
        }
        for inv in invoices:
            report["total_amount"] += inv.total_amount
            report["by_status"][inv.status] = report["by_status"].get(inv.status, 0) + 1
            report["by_customer"][inv.customer_name] = (
                report["by_customer"].get(inv.customer_name, 0) + inv.total_amount
            )
            if inv.status == "paid":
                report["paid_amount"] += inv.total_amount
            else:
                report["unpaid_amount"] += inv.total_amount

        report["total_amount"] = round(report["total_amount"], 2)
        report["paid_amount"] = round(report["paid_amount"], 2)
        report["unpaid_amount"] = round(report["unpaid_amount"], 2)
        return report

    # ── HTML Generation ───────────────────────────────

    def generate_html(self, invoice_id: str) -> str:
        """生成发票 HTML。"""
        inv = self.get_invoice(invoice_id)
        if not inv:
            return "<p>Invoice not found</p>"

        items_html = "".join(
            f"""<tr>
                <td>{i.name}</td>
                <td>{i.description}</td>
                <td>{i.quantity}</td>
                <td>¥{i.amount:.2f}</td>
                <td>¥{i.subtotal:.2f}</td>
                <td>{(i.tax_rate*100):.0f}%</td>
                <td>¥{i.tax:.2f}</td>
            </tr>"""
            for i in inv.items
        )

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>发票 {inv.invoice_id}</title>
<style>
  body {{ font-family: 'PingFang SC', sans-serif; max-width: 800px; margin: 40px auto; color: #333; }}
  .header {{ display: flex; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 20px; }}
  .invoice-id {{ font-size: 1.4em; font-weight: bold; }}
  .status {{ padding: 4px 12px; border-radius: 4px; font-size: .9em; }}
  .status.draft {{ background: #eee; }}
  .status.paid {{ background: #d4edda; color: #155724; }}
  .status.overdue {{ background: #f8d7da; color: #721c24; }}
  .customer {{ margin: 20px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
  th {{ background: #f5f5f5; }}
  .total {{ text-align: right; font-size: 1.2em; margin-top: 20px; }}
  .footer {{ margin-top: 40px; color: #999; font-size: .85em; }}
</style></head>
<body>
<div class="header">
  <div>
    <h1>发票</h1>
    <div class="invoice-id">{inv.invoice_id}</div>
    <span class="status {inv.status}">{inv.status}</span>
  </div>
  <div style="text-align:right">
    <p>日期: {inv.created_at[:10]}</p>
    <p>到期: {inv.due_date}</p>
  </div>
</div>
<div class="customer">
  <strong>客户:</strong> {inv.customer_name}<br>
  {f'<strong>邮箱:</strong> {inv.customer_email}<br>' if inv.customer_email else ''}
</div>
<table>
  <tr><th>项目</th><th>描述</th><th>数量</th><th>单价</th><th>小计</th><th>税率</th><th>税额</th></tr>
  {items_html}
</table>
<div class="total">
  <p>小计: ¥{inv.subtotal_amount:.2f}</p>
  <p>税额: ¥{inv.tax_amount:.2f}</p>
  <p><strong>总计: ¥{inv.total_amount:.2f}</strong></p>
</div>
{'' if inv.status != 'paid' else f'<p>✅ 已支付 · {inv.paid_at[:10]} · {inv.payment_method}</p>'}
<div class="footer">
  <p>{inv.notes}</p>
  <p>墨麟AI集团 · 墨单订单 自动化发票系统</p>
</div>
</body></html>"""

    # ── Internal ──────────────────────────────────────

    def _save(self, inv: Invoice) -> None:
        filepath = self.storage_dir / f"{inv.invoice_id}.json"
        with open(filepath, "w") as f:
            json.dump(inv.to_dict(), f, ensure_ascii=False, indent=2)
        self._cache[inv.invoice_id] = inv


# ── CLI ──────────────────────────────────────────────

def cmd_order_invoice(action: str, *args) -> str:
    engine = InvoiceEngine()

    if action == "create":
        # args: customer_name, item_name, amount
        if len(args) < 3:
            return "Usage: invoice create <customer> <item_name> <amount>"
        inv = engine.create_invoice(
            args[0],
            [{"name": args[1], "amount": float(args[2])}],
        )
        return f"✅ Invoice {inv.invoice_id}\n   Total: ¥{inv.total_amount:.2f}\n   Due: {inv.due_date}"

    elif action == "list":
        status_filter = args[0] if args else ""
        invoices = engine.list_invoices(status_filter)
        if not invoices:
            return "No invoices found"
        lines = [f"{'ID':<30} {'Customer':<20} {'Status':<10} {'Total':>10}"]
        for inv in invoices[:20]:
            lines.append(f"{inv.invoice_id:<30} {inv.customer_name:<20} {inv.status:<10} ¥{inv.total_amount:>8.2f}")
        return "\n".join(lines)

    elif action == "report":
        report = engine.get_report()
        return json.dumps(report, ensure_ascii=False, indent=2)

    elif action == "status":
        if len(args) < 2:
            return "Usage: invoice status <invoice_id> <new_status>"
        inv = engine.update_status(args[0], args[1])
        return f"✅ Invoice {args[0]} → {args[1]}" if inv else "Invoice not found"

    return f"Unknown action: {action}"


if __name__ == "__main__":
    engine = InvoiceEngine()
    inv = engine.create_invoice("测试客户", [{"name": "AI咨询", "amount": 1000}])
    print(f"Created: {inv.invoice_id} ¥{inv.total_amount:.2f}")
    print(engine.get_report())
