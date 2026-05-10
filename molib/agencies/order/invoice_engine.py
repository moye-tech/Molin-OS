"""
墨单订单 — 发票引擎 (Invoice Engine)
=====================================
吸收自 Invoice Ninja (github.com/invoiceninja/invoiceninja 9k stars)
和 Kill Bill (github.com/killbill/killbill 4k stars)

纯标准库实现：
- Invoice 数据模型
- HTML / 纯文本 模板渲染
- 序列化/反序列化
- 税计算
- 客户门面（Customer Portal 简化版）

零外部依赖。
"""

import json
import uuid
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# ── 存储目录 ─────────────────────────────────────────────────
INVOICE_DIR = Path.home() / ".molin" / "orders" / "invoices"
INVOICE_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════

@dataclass
class InvoiceItem:
    """发票行项目"""
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax_rate: float = 0.0  # e.g. 0.06 for 6%

    @property
    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    @property
    def tax_amount(self) -> float:
        return round(self.subtotal * self.tax_rate, 2)

    @property
    def total(self) -> float:
        return round(self.subtotal + self.tax_amount, 2)


@dataclass
class Invoice:
    """发票主体 — 吸收 Invoice Ninja 模板引擎设计"""
    invoice_id: str
    customer_name: str
    customer_email: str = ""
    customer_address: str = ""
    items: list[InvoiceItem] = field(default_factory=list)
    tax_rate: float = 0.0
    status: str = "draft"  # draft | sent | paid | overdue | cancelled
    notes: str = ""
    terms: str = "付款后 7 日内交付"
    currency: str = "¥"
    created_at: float = 0.0
    due_date: str = ""  # ISO format
    paid_at: Optional[float] = None
    order_id: str = ""

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
        if not self.due_date:
            self.due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        if not self.invoice_id:
            self.invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"

    # ── 金额计算 ─────────────────────────────────────────

    @property
    def subtotal(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    @property
    def total_tax(self) -> float:
        return round(sum(item.tax_amount for item in self.items), 2)

    @property
    def total(self) -> float:
        return round(self.subtotal + self.total_tax, 2)

    @property
    def balance_due(self) -> float:
        """待付余额（后续接入 payment_tracker 后联动）"""
        return self.total  # 默认全款未付

    @property
    def is_overdue(self) -> bool:
        if self.status == "paid":
            return False
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d")
            return datetime.now() > due
        except ValueError:
            return False

    def add_item(self, description: str, quantity: float = 1.0,
                 unit_price: float = 0.0, tax_rate: float | None = None) -> InvoiceItem:
        """添加行项目"""
        rate = tax_rate if tax_rate is not None else self.tax_rate
        item = InvoiceItem(
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            tax_rate=rate,
        )
        self.items.append(item)
        return item

    # ── 序列化 ───────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "invoice_id": self.invoice_id,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_address": self.customer_address,
            "items": [
                {
                    "description": i.description,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "tax_rate": i.tax_rate,
                }
                for i in self.items
            ],
            "tax_rate": self.tax_rate,
            "status": self.status,
            "notes": self.notes,
            "terms": self.terms,
            "currency": self.currency,
            "created_at": self.created_at,
            "due_date": self.due_date,
            "paid_at": self.paid_at,
            "order_id": self.order_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Invoice":
        inv = cls(
            invoice_id=data.get("invoice_id", ""),
            customer_name=data.get("customer_name", ""),
            customer_email=data.get("customer_email", ""),
            customer_address=data.get("customer_address", ""),
            tax_rate=data.get("tax_rate", 0.0),
            status=data.get("status", "draft"),
            notes=data.get("notes", ""),
            terms=data.get("terms", "付款后 7 日内交付"),
            currency=data.get("currency", "¥"),
            created_at=data.get("created_at", 0.0),
            due_date=data.get("due_date", ""),
            paid_at=data.get("paid_at"),
            order_id=data.get("order_id", ""),
        )
        for item_data in data.get("items", []):
            inv.items.append(InvoiceItem(
                description=item_data.get("description", ""),
                quantity=item_data.get("quantity", 1.0),
                unit_price=item_data.get("unit_price", 0.0),
                tax_rate=item_data.get("tax_rate", 0.0),
            ))
        return inv

    def save(self) -> str:
        """持久化到 JSON 文件"""
        filepath = INVOICE_DIR / f"{self.invoice_id}.json"
        filepath.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return str(filepath)

    @classmethod
    def load(cls, invoice_id: str) -> Optional["Invoice"]:
        """从 JSON 文件加载"""
        filepath = INVOICE_DIR / f"{invoice_id}.json"
        if not filepath.exists():
            return None
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return None

    @classmethod
    def list_all(cls) -> list["Invoice"]:
        """列出所有发票"""
        invoices = []
        if INVOICE_DIR.exists():
            for f in sorted(INVOICE_DIR.glob("INV-*.json")):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    invoices.append(cls.from_dict(data))
                except (json.JSONDecodeError, OSError):
                    pass
        return invoices

    # ── HTML 模板渲染（吸收 Invoice Ninja 设计）───────────

    def generate_html(self) -> str:
        """生成可打印的 HTML 发票"""
        items_html = ""
        for i, item in enumerate(self.items, 1):
            items_html += f"""
            <tr>
                <td>{i}</td>
                <td>{_escape(item.description)}</td>
                <td style="text-align:center">{item.quantity}</td>
                <td style="text-align:right">{self.currency}{item.unit_price:,.2f}</td>
                <td style="text-align:right">{self.currency}{item.subtotal:,.2f}</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>发票 {self.invoice_id}</title>
<style>
  body {{ font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 40px; color: #333; }}
  .header {{ display: flex; justify-content: space-between; margin-bottom: 40px; }}
  .company-info {{ font-size: 14px; }}
  .company-info h1 {{ margin: 0; font-size: 24px; }}
  .invoice-title {{ text-align: right; }}
  .invoice-title h2 {{ margin: 0; font-size: 28px; color: #1a73e8; }}
  .status {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
  .status-draft {{ background: #f0f0f0; color: #666; }}
  .status-sent {{ background: #e3f2fd; color: #1565c0; }}
  .status-paid {{ background: #e8f5e9; color: #2e7d32; }}
  .status-overdue {{ background: #ffebee; color: #c62828; }}
  .section {{ margin-bottom: 30px; }}
  .section-title {{ font-size: 14px; color: #666; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #f5f5f5; padding: 10px; text-align: left; font-size: 13px; border-bottom: 2px solid #ddd; }}
  td {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 14px; }}
  .totals {{ margin-top: 30px; text-align: right; }}
  .totals table {{ width: 300px; margin-left: auto; }}
  .totals td:first-child {{ text-align: left; font-weight: bold; }}
  .totals td:last-child {{ text-align: right; }}
  .grand-total {{ font-size: 18px; font-weight: bold; color: #1a73e8; }}
  .footer {{ margin-top: 60px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 20px; }}
  .notes {{ background: #fafafa; padding: 15px; border-radius: 4px; font-size: 13px; }}
</style>
</head>
<body>
<div class="header">
  <div class="company-info">
    <h1>墨麟 AI 集团</h1>
    <p>AI 自动化解决方案提供商</p>
    <p>invoice@molin.ai</p>
  </div>
  <div class="invoice-title">
    <h2>INVOICE</h2>
    <p>编号: {self.invoice_id}</p>
    <span class="status status-{self.status}">{_status_label(self.status)}</span>
  </div>
</div>

<div class="section">
  <div class="section-title">客户信息</div>
  <p><strong>{_escape(self.customer_name)}</strong></p>
  {f'<p>{_escape(self.customer_email)}</p>' if self.customer_email else ''}
  {f'<p>{_escape(self.customer_address)}</p>' if self.customer_address else ''}
</div>

<div class="section">
  <div class="section-title">发票明细</div>
  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>项目描述</th>
        <th style="text-align:center">数量</th>
        <th style="text-align:right">单价</th>
        <th style="text-align:right">小计</th>
      </tr>
    </thead>
    <tbody>
      {items_html}
    </tbody>
  </table>
</div>

<div class="totals">
  <table>
    <tr><td>小计</td><td>{self.currency}{self.subtotal:,.2f}</td></tr>
    <tr><td>税额 ({self.tax_rate*100:.0f}%)</td><td>{self.currency}{self.total_tax:,.2f}</td></tr>
    <tr class="grand-total"><td>总计</td><td>{self.currency}{self.total:,.2f}</td></tr>
  </table>
</div>

<div class="section" style="margin-top:30px">
  <div class="section-title">备注</div>
  <div class="notes">{_escape(self.notes) if self.notes else '无'}</div>
</div>

<div class="footer">
  <p>付款条件: {_escape(self.terms)}</p>
  <p>到期日: {self.due_date}</p>
  <p>生成时间: {datetime.fromtimestamp(self.created_at).strftime('%Y-%m-%d %H:%M')}</p>
  <p style="margin-top:10px">感谢您的合作！— 墨麟 AI 集团</p>
</div>
</body>
</html>"""

    def generate_text(self) -> str:
        """生成纯文本发票"""
        lines = []
        width = 60
        lines.append("=" * width)
        lines.append("  墨麟 AI 集团 — 发票".center(width - 4))
        lines.append("=" * width)
        lines.append(f"  发票编号: {self.invoice_id}")
        lines.append(f"  日期: {datetime.fromtimestamp(self.created_at).strftime('%Y-%m-%d')}")
        lines.append(f"  到期日: {self.due_date}")
        lines.append(f"  状态: {_status_label(self.status)}")
        lines.append("-" * width)
        lines.append(f"  客户: {self.customer_name}")
        if self.customer_email:
            lines.append(f"  邮箱: {self.customer_email}")
        if self.customer_address:
            lines.append(f"  地址: {self.customer_address}")
        lines.append("-" * width)
        lines.append(f"  {'项目':<28} {'数量':>6} {'单价':>10} {'小计':>10}")
        lines.append("-" * width)
        for item in self.items:
            desc = item.description[:26]
            lines.append(
                f"  {desc:<28} {item.quantity:>6.0f} "
                f"{self.currency}{item.unit_price:>8,.2f} "
                f"{self.currency}{item.subtotal:>8,.2f}"
            )
        lines.append("-" * width)
        lines.append(f"  {'小计:':>46} {self.currency}{self.subtotal:>10,.2f}")
        lines.append(f"  {'税额 (' + str(int(self.tax_rate*100)) + '%):':>46} {self.currency}{self.total_tax:>10,.2f}")
        lines.append(f"  {'总计:':>46} {self.currency}{self.total:>10,.2f}")
        lines.append("=" * width)
        if self.notes:
            lines.append(f"  备注: {self.notes}")
        lines.append(f"  付款条件: {self.terms}")
        lines.append("  感谢您的合作！— 墨麟 AI 集团")
        return "\n".join(lines)


# ── 模板占位符引擎 ────────────────────────────────────────


def generate_invoice_from_template(
    template: str,
    customer_name: str = "",
    total: float = 0.0,
    date: str = "",
    invoice_id: str = "",
    due_date: str = "",
    items_text: str = "",
    notes: str = "",
    **kwargs,
) -> str:
    """
    占位符模板引擎。

    支持的占位符:
      {customer_name} — 客户名
      {total} — 总金额
      {date} — 日期
      {invoice_id} — 发票编号
      {due_date} — 到期日
      {items} — 项目明细
      {notes} — 备注
      {currency} — 货币符号
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    currency = kwargs.get("currency", "¥")

    replacements = {
        "{customer_name}": customer_name,
        "{total}": f"{currency}{total:,.2f}",
        "{date}": date,
        "{invoice_id}": invoice_id,
        "{due_date}": due_date,
        "{items}": items_text,
        "{notes}": notes,
        "{currency}": currency,
    }

    result = template
    for key, val in replacements.items():
        result = result.replace(key, str(val))
    return result


# ── 工具函数 ──────────────────────────────────────────────


def _escape(text: str) -> str:
    """HTML 转义"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _status_label(status: str) -> str:
    labels = {
        "draft": "草稿",
        "sent": "已发送",
        "paid": "已付款",
        "overdue": "已逾期",
        "cancelled": "已取消",
    }
    return labels.get(status, status)


# ── 批量操作 ──────────────────────────────────────────────


def get_invoice_stats() -> dict:
    """获取发票统计"""
    invoices = Invoice.list_all()
    by_status = {}
    total_value = 0.0
    for inv in invoices:
        by_status[inv.status] = by_status.get(inv.status, 0) + 1
        if inv.status == "paid":
            total_value += inv.total
    return {
        "total": len(invoices),
        "by_status": by_status,
        "total_paid_value": round(total_value, 2),
    }
