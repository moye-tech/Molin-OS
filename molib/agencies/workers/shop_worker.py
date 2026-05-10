"""销售 Worker — 报价生成、合同草拟、交付物打包、销售话术 + 商品/交易管理

Now integrates with ProductManager and TransactionEngine for real ecommerce.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from molib.agencies.worker import ExecutionPlan, WorkerAgent


class ShopWorker(WorkerAgent):
    worker_id = "shop_worker"
    description = "销售 Worker：商品管理、闲鱼上架、交易追踪、销售话术、日报"
    available_tools = ["file_tool", "memory_tool", "web_tool"]

    deliverable_spec: Dict[str, Any] = {
        "format": "report",
        "sections": [
            "商品库存概览",
            "交易转化漏斗",
            "平台销售分析",
            "话术优化建议",
            "定价策略",
            "提升方案",
        ],
        "quality_criteria": [
            "数据准确完整",
            "转化路径可优化",
            "定价策略合理",
            "低库存有预警",
        ],
    }

    def __init__(self):
        super().__init__()
        self._product_manager = None
        self._transaction_engine = None

    @property
    def pm(self):
        if self._product_manager is None:
            from molib.agencies.shop.product_manager import ProductManager
            self._product_manager = ProductManager()
        return self._product_manager

    @property
    def te(self):
        if self._transaction_engine is None:
            from molib.agencies.shop.transaction_engine import TransactionEngine
            self._transaction_engine = TransactionEngine()
        return self._transaction_engine

    async def build_plan(self, subtask: Dict[str, Any]) -> ExecutionPlan:
        """LLM 驱动的执行计划 — 替代关键词 if-else 链。"""
        return await self._llm_build_plan(subtask)

    # ── Product Management ────────────────────────────────────────────

    def add_product(
        self,
        name: str,
        price: float,
        description: str = "",
        category: str = "",
        stock: int = 0,
        platform: str = "闲鱼",
        images: list[str] | None = None,
    ) -> dict:
        """Add a new product to the catalog."""
        from molib.agencies.shop.product_manager import Product

        product = Product(
            name=name,
            description=description,
            price=price,
            category=category,
            stock=stock,
            platform=platform,
            images=images or [],
            status="active",
        )
        self.pm.create(product)
        return {"status": "created", "product": product.to_dict()}

    def list_products(self, status: str = "") -> dict:
        """List all products, optionally filtered by status."""
        products = self.pm.list_all(status)
        return {
            "count": len(products),
            "products": [p.to_dict() for p in products],
            "summaries": [p.summary for p in products],
        }

    def get_product(self, product_id: str) -> Optional[dict]:
        """Get a single product by ID."""
        p = self.pm.get(product_id)
        return p.to_dict() if p else None

    def update_product(self, product_id: str, **kwargs) -> Optional[dict]:
        """Update a product's fields."""
        p = self.pm.update(product_id, **kwargs)
        return p.to_dict() if p else None

    def delete_product(self, product_id: str) -> bool:
        """Delete a product."""
        return self.pm.delete(product_id)

    # ── Listing Generation ────────────────────────────────────────────

    def create_listing(
        self,
        product_id: str,
        platform: str = "闲鱼",
        template: str = "",
    ) -> dict:
        """Generate a platform listing from product data.

        For 闲鱼 (Xianyu): generates HTML-style listing content.
        For generic: returns structured listing data.
        """
        p = self.pm.get(product_id)
        if not p:
            return {"error": f"Product {product_id} not found"}

        if platform == "闲鱼":
            listing_html = self._generate_xianyu_listing(p)
            return {
                "platform": "闲鱼",
                "product_id": product_id,
                "product_name": p.name,
                "price": p.price,
                "listing_html": listing_html,
                "preview": listing_html[:300],
            }

        # Generic listing
        return {
            "platform": platform,
            "product_id": product_id,
            "title": p.name,
            "description": p.description,
            "price": p.price,
            "category": p.category,
            "images": p.images,
            "status": "draft_ready",
        }

    def _generate_xianyu_listing(self, p) -> str:
        """Generate 闲鱼-style listing HTML from a Product."""
        cat_tag = f"#{p.category.replace(' ', '')}" if p.category else ""
        stock_note = ""
        if p.stock == 0:
            stock_note = '<span style="color:red">【已售罄】</span>'
        elif p.stock <= 5:
            stock_note = f'<span style="color:orange">【仅剩{p.stock}件】</span>'

        images_html = ""
        if p.images:
            images_html = (
                '<div class="images">\n'
                + "".join(f'  <img src="{img}" alt="{p.name}" loading="lazy"/>\n' for img in p.images[:9])
                + "</div>"
            )

        return f"""<div class="listing-xianyu" data-product-id="{p.id}">
  <h2 class="title">{p.name} {stock_note}</h2>
  <div class="price-block">
    <span class="price">¥{p.price:.0f}</span>
    {f'<span class="category-tag">{cat_tag}</span>' if cat_tag else ''}
  </div>
{images_html}
  <div class="description">
    <h3>商品描述</h3>
    <p>{p.description or '暂无详细描述，欢迎私信咨询～'}</p>
  </div>
  <div class="footer-meta">
    <span class="platform">🛒 闲鱼</span>
    <span class="date">发布于 {time.strftime('%Y-%m-%d', time.localtime(p.created_at))}</span>
  </div>
  <div class="seller-note">
    <p>💬 感兴趣的宝子直接私信我，看到会秒回～</p>
    <p>📦 下单后24小时内发货 | 🔒 支持平台担保交易</p>
  </div>
</div>"""

    # ── Transaction / Sale Recording ───────────────────────────────────

    def record_sale(
        self,
        product_id: str,
        customer: str,
        amount: float,
        quantity: int = 1,
        platform: str = "闲鱼",
        customer_contact: str = "",
        notes: str = "",
    ) -> dict:
        """Record a new sale/transaction."""
        from molib.agencies.shop.transaction_engine import Transaction

        p = self.pm.get(product_id)
        product_name = p.name if p else ""
        actual_amount = amount if amount > 0 else (p.price if p else 0)

        txn = Transaction(
            product_id=product_id,
            product_name=product_name,
            customer=customer,
            customer_contact=customer_contact,
            amount=actual_amount,
            quantity=quantity,
            platform=platform,
            notes=notes,
            status="pending",
        )
        self.te.create(txn)

        # Auto-deduct stock if product exists
        if p and p.stock > 0:
            self.pm.adjust_stock(product_id, -quantity)

        return {"status": "created", "transaction": txn.to_dict()}

    def update_transaction_status(self, txn_id: str, new_status: str, note: str = "") -> Optional[dict]:
        """Update a transaction's status."""
        txn = self.te.update_status(txn_id, new_status, note)
        return txn.to_dict() if txn else None

    def get_transaction(self, txn_id: str) -> Optional[dict]:
        """Get a transaction by ID."""
        txn = self.te.get(txn_id)
        return txn.to_dict() if txn else None

    def list_transactions(self, status: str = "") -> dict:
        """List transactions, optionally filtered."""
        txns = self.te.list_all(status)
        return {
            "count": len(txns),
            "transactions": [t.to_dict() for t in txns],
            "summaries": [t.summary for t in txns],
        }

    # ── Reporting ─────────────────────────────────────────────────────

    def get_daily_report(self) -> dict:
        """Generate a comprehensive daily report."""
        inv_report = self.pm.get_inventory_report()
        txn_report = self.te.get_daily_report()
        low_stock = self.pm.check_low_stock()

        # Active + urgent items
        urgent = [
            p.summary for p in low_stock
            if p.stock == 0
        ]

        return {
            "date": time.strftime("%Y-%m-%d"),
            "generated_at": time.time(),
            "inventory": inv_report,
            "transactions_today": txn_report,
            "alerts": {
                "low_stock_count": len(low_stock),
                "low_stock_items": [p.summary for p in low_stock],
                "out_of_stock": urgent,
            },
            "recommendations": self._generate_recommendations(inv_report, txn_report),
        }

    def _generate_recommendations(self, inv_report: dict, txn_report: dict) -> list[str]:
        """Generate action recommendations based on report data."""
        recs = []
        if inv_report.get("out_of_stock_items", 0) > 0:
            recs.append(f"⚠️ {inv_report['out_of_stock_items']} 款商品已售罄，建议补货")
        if inv_report.get("low_stock_items", 0) > 0:
            recs.append(f"📊 {inv_report['low_stock_items']} 款商品库存偏低")
        if txn_report.get("pending_payment", 0) > 0:
            recs.append(f"💳 {txn_report['pending_payment']} 笔订单待付款，建议催单")
        if txn_report.get("delivered", 0) == 0 and txn_report.get("total_transactions", 0) > 0:
            recs.append("📦 今日暂无完成交付，关注物流进度")
        if not recs:
            recs.append("✅ 今日运营正常，暂无需处理的事项")
        return recs

    def get_inventory_report(self) -> dict:
        """Get inventory health report."""
        return self.pm.get_inventory_report()

    def get_transaction_report(self, period: str = "all") -> dict:
        """Get transaction report for a period."""
        return self.te.get_report(period)

    # ── Bulk Operations ───────────────────────────────────────────────

    def import_products(self, products: list[dict]) -> dict:
        """Bulk import products from a list of dicts."""
        from molib.agencies.shop.product_manager import Product

        created = 0
        failed = 0
        results = []

        for item in products:
            try:
                p = Product(
                    name=item.get("name", "未命名"),
                    description=item.get("description", ""),
                    price=float(item.get("price", 0)),
                    category=item.get("category", ""),
                    stock=int(item.get("stock", 0)),
                    platform=item.get("platform", "闲鱼"),
                    images=item.get("images", []),
                    status=item.get("status", "active"),
                )
                self.pm.create(p)
                created += 1
                results.append({"status": "ok", "id": p.id})
            except Exception as e:
                failed += 1
                results.append({"status": "failed", "error": str(e)})

        return {"created": created, "failed": failed, "results": results}
