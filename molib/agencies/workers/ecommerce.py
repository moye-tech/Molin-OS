"""墨链电商 Worker — 订单管理、交易、电商平台

Full ecommerce pipeline: Product → Listing → Order → Fulfillment.
Platform adapters: xianyu (闲鱼), generic.
Uses ProductManager + TransactionEngine as backend.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from molib.agencies.workers.base import SmartSubsidiaryWorker as _Base, Task, WorkerResult


# ── Platform Adapters ─────────────────────────────────────────────────


class PlatformAdapter:
    """Base adapter for ecommerce platforms."""

    platform_id: str = "generic"
    platform_name: str = "通用平台"

    def format_product(self, product: dict) -> dict:
        """Convert internal product to platform format."""
        return {
            "title": product.get("name", ""),
            "price": product.get("price", 0),
            "description": product.get("description", ""),
            "images": product.get("images", []),
            "category": product.get("category", ""),
        }

    def format_listing(self, product: dict) -> str:
        """Generate platform-specific listing content."""
        title = product.get("name", "未命名")
        price = product.get("price", 0)
        desc = product.get("description", "")
        return f"【{title}】¥{price:.0f}\n{desc}"

    def listing_tips(self, product: dict) -> list[str]:
        """Platform-specific listing optimization tips."""
        return [
            "标题包含核心关键词",
            "描述清晰，突出卖点",
            "图片清晰，多角度展示",
        ]


class XianyuAdapter(PlatformAdapter):
    """闲鱼 (Xianyu) platform adapter."""

    platform_id = "xianyu"
    platform_name = "闲鱼"

    def format_product(self, product: dict) -> dict:
        base = super().format_product(product)
        base["platform"] = "闲鱼"
        # 闲鱼 requires condition description
        base["condition"] = product.get("condition", "几乎全新")
        base["shipping"] = product.get("shipping", "包邮")
        base["tags"] = product.get("tags", [])
        return base

    def format_listing(self, product: dict) -> str:
        """Generate 闲鱼-style listing content."""
        name = product.get("name", "未命名")
        price = product.get("price", 0)
        desc = product.get("description", "")
        condition = product.get("condition", "几乎全新")
        tags = " ".join(f"#{t}" for t in product.get("tags", []))
        category = f"#{product.get('category', '').replace(' ', '')}" if product.get("category") else ""

        return (
            f"【{name}】{category}\n\n"
            f"💰 价格：¥{price:.0f}\n"
            f"📦 成色：{condition}\n"
            f"🚚 邮费：{product.get('shipping', '包邮')}\n"
            f"🏷️ {tags}\n\n"
            f"{desc}\n\n"
            f"💬 感兴趣的宝子直接私信，看到秒回～\n"
            f"🔒 支持平台担保交易 | 下单24h内发货"
        )

    def listing_tips(self, product: dict) -> list[str]:
        tips = super().listing_tips(product)
        return tips + [
            "闲鱼标题前加【转卖】或品牌名提高曝光",
            "标价略高于心理价，给砍价留空间",
            "每日擦亮商品提升排名",
            "鱼塘（社区）选择相关圈子发布",
            "实拍图比官方图转化率更高",
        ]


# ── Order Pipeline ────────────────────────────────────────────────────


@dataclass
class OrderPipeline:
    """Tracks an order through the ecommerce pipeline."""

    order_id: str
    product_id: str
    platform: str
    stage: str = "created"  # created → listed → ordered → paid → shipped → delivered
    actions: list[dict] = field(default_factory=list)

    STAGES = ["created", "listed", "ordered", "paid", "shipped", "delivered", "cancelled"]

    def advance(self, new_stage: str, note: str = "") -> None:
        if new_stage not in self.STAGES:
            raise ValueError(f"Invalid stage: {new_stage}")
        self.stage = new_stage
        self.actions.append({
            "stage": new_stage,
            "note": note,
            "timestamp": time.time(),
        })

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "product_id": self.product_id,
            "platform": self.platform,
            "stage": self.stage,
            "actions": self.actions,
        }


# ── Ecommerce Worker ──────────────────────────────────────────────────


class Ecommerce(_Base):
    worker_id = "ecommerce"
    worker_name = "墨链电商"
    description = "订单管理、交易、电商平台 — 商品上架、订单追踪、多平台适配"
    oneliner = "订单管理、交易、电商平台"

    # Platform adapters registry
    _adapters = {
        "xianyu": XianyuAdapter(),
        "闲鱼": XianyuAdapter(),
        "generic": PlatformAdapter(),
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

    def get_adapter(self, platform: str) -> PlatformAdapter:
        return self._adapters.get(platform.lower(), PlatformAdapter())

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "多平台商品上架管理（闲鱼/淘宝/拼多多）",
            "订单状态追踪与更新（pending→delivered全程）",
            "交易记录与对账报告",
            "平台特有格式适配（标题/描述/标签）",
            "商品库存管理与低库存预警",
            "销售数据统计分析",
            "闲鱼专属优化建议",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨链电商",
            "vp": "运营",
            "description": "订单管理、交易、电商平台",
            "platforms": ["闲鱼", "淘宝", "拼多多", "通用"],
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        """Main execution entry. Routes by action type."""
        try:
            action = task.payload.get("action", "list")
            platform = task.payload.get("platform", "闲鱼")

            if action == "add_product":
                result = self._handle_add_product(task.payload)
            elif action == "list_products":
                result = self._handle_list_products(task.payload)
            elif action == "generate_listing":
                result = self._handle_generate_listing(task.payload)
            elif action == "create_order":
                result = self._handle_create_order(task.payload)
            elif action == "list_orders":
                result = self._handle_list_orders(task.payload)
            elif action == "update_order":
                result = self._handle_update_order(task.payload)
            elif action == "report":
                result = self._handle_report(task.payload)
            elif action == "pipeline":
                result = self._handle_pipeline(task.payload)
            else:
                # Fallback: LLM-powered analysis
                result = await self._handle_llm_analysis(task, context)

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=result,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )

    # ── Action Handlers ───────────────────────────────────────────────

    def _handle_add_product(self, payload: dict) -> dict:
        from molib.agencies.shop.product_manager import Product

        p = Product(
            name=payload.get("name", ""),
            description=payload.get("description", ""),
            price=float(payload.get("price", 0)),
            category=payload.get("category", ""),
            stock=int(payload.get("stock", 0)),
            platform=payload.get("platform", "闲鱼"),
            images=payload.get("images", []),
        )
        self.pm.create(p)
        return {"status": "created", "product": p.to_dict()}

    def _handle_list_products(self, payload: dict) -> dict:
        status = payload.get("status", "")
        products = self.pm.list_all(status)
        return {
            "count": len(products),
            "products": [p.to_dict() for p in products],
        }

    def _handle_generate_listing(self, payload: dict) -> dict:
        product_id = payload.get("product_id", "")
        platform = payload.get("platform", "闲鱼")
        adapter = self.get_adapter(platform)

        p = self.pm.get(product_id)
        if not p:
            return {"error": f"Product {product_id} not found"}

        product_dict = p.to_dict()
        formatted = adapter.format_product(product_dict)
        listing_text = adapter.format_listing(product_dict)
        tips = adapter.listing_tips(product_dict)

        return {
            "platform": platform,
            "product_id": product_id,
            "formatted_product": formatted,
            "listing_text": listing_text,
            "listing_tips": tips,
        }

    def _handle_create_order(self, payload: dict) -> dict:
        from molib.agencies.shop.transaction_engine import Transaction

        product_id = payload.get("product_id", "")
        p = self.pm.get(product_id)

        txn = Transaction(
            product_id=product_id,
            product_name=p.name if p else payload.get("product_name", ""),
            customer=payload.get("customer", ""),
            customer_contact=payload.get("contact", ""),
            amount=float(payload.get("amount") or (p.price if p else 0)),
            quantity=int(payload.get("quantity", 1)),
            platform=payload.get("platform", "闲鱼"),
            notes=payload.get("notes", ""),
        )
        self.te.create(txn)

        # Deduct stock
        if p and p.stock > 0:
            self.pm.adjust_stock(product_id, -txn.quantity)

        return {"status": "created", "transaction": txn.to_dict()}

    def _handle_list_orders(self, payload: dict) -> dict:
        status = payload.get("status", "")
        txns = self.te.list_all(status)
        return {
            "count": len(txns),
            "orders": [t.to_dict() for t in txns],
        }

    def _handle_update_order(self, payload: dict) -> dict:
        txn_id = payload.get("order_id", payload.get("id", ""))
        new_status = payload.get("status", "")

        if new_status == "paid":
            txn = self.te.mark_paid(txn_id)
        elif new_status == "shipped":
            txn = self.te.mark_shipped(
                txn_id,
                carrier=payload.get("carrier", ""),
                tracking=payload.get("tracking", ""),
            )
        elif new_status == "delivered":
            txn = self.te.mark_delivered(txn_id)
        elif new_status in ("cancelled", "canceled"):
            txn = self.te.cancel(txn_id)
        elif new_status == "refunded":
            txn = self.te.refund(txn_id)
        else:
            txn = self.te.update_status(txn_id, new_status)

        if not txn:
            return {"error": f"Failed to update {txn_id} to {new_status}"}
        return {"status": "updated", "transaction": txn.to_dict()}

    def _handle_report(self, payload: dict) -> dict:
        period = payload.get("period", "all")
        tx_report = self.te.get_report(period)
        inv_report = self.pm.get_inventory_report()
        low_stock = self.pm.check_low_stock()

        return {
            "period": period,
            "transactions": tx_report,
            "inventory": inv_report,
            "alerts": {
                "low_stock_count": len(low_stock),
                "low_stock_items": [p.summary for p in low_stock],
            },
            "generated_at": time.time(),
        }

    def _handle_pipeline(self, payload: dict) -> dict:
        """Run the full ecommerce pipeline for a product."""
        platform = payload.get("platform", "闲鱼")
        adapter = self.get_adapter(platform)

        product_id = payload.get("product_id", "")
        p = self.pm.get(product_id)
        if not p:
            return {"error": f"Product {product_id} not found"}

        product_dict = p.to_dict()

        pipeline = OrderPipeline(
            order_id=f"PIPE-{product_id}",
            product_id=product_id,
            platform=platform,
        )

        # Stage 1: Format product
        formatted = adapter.format_product(product_dict)

        # Stage 2: Generate listing
        listing = adapter.format_listing(product_dict)
        tips = adapter.listing_tips(product_dict)
        pipeline.advance("listed", "Listing generated")

        # Stage 3: Ready for order
        pipeline.advance("ordered", "Ready for customer order")

        return {
            "pipeline": pipeline.to_dict(),
            "product": formatted,
            "listing": listing,
            "listing_tips": tips,
            "next_steps": [
                "1. 复制 listing 内容到闲鱼发布",
                "2. 设置价格和库存",
                "3. 上传图片（建议9张）",
                "4. 选择合适的鱼塘/圈子发布",
                "5. 每日擦亮商品",
            ],
        }

    # ── LLM-Powered Analysis ──────────────────────────────────────────

    async def _handle_llm_analysis(self, task: Task, context: dict | None) -> dict:
        """Fallback: LLM-powered ecommerce analysis."""
        products = task.payload.get("products", [])
        platform = task.payload.get("platform", "闲鱼")
        action = task.payload.get("action", "list")
        pending = task.payload.get("pending_orders", 0)
        shipped = task.payload.get("shipped_orders", 0)

        # Get real data from our stores
        all_products = self.pm.list_all()
        all_txns = self.te.list_all()
        low_stock = self.pm.check_low_stock()

        products_summary = json.dumps(
            [p.to_dict() for p in all_products], ensure_ascii=False
        )[:2000] if all_products else "无商品数据"

        txn_summary = json.dumps(
            [t.summary for t in all_txns[:20]], ensure_ascii=False
        ) if all_txns else "无交易数据"

        system_prompt = (
            "你是一位资深的电商运营专家，精通多平台上架策略、订单管理、库存优化。"
            "请根据商品信息和平台特性，给出最优运营方案。"
        )

        prompt = (
            f"请处理以下电商运营请求：\n"
            f"平台：{platform}\n"
            f"操作类型：{action}\n"
            f"待处理订单：{pending}\n"
            f"已发货订单：{shipped}\n"
            f"低库存商品：{len(low_stock)} 款\n"
            f"商品信息：\n{products_summary}\n"
            f"近期交易：\n{txn_summary}\n\n"
            "以JSON格式输出运营方案：\n"
            "{\n"
            '  "platform": "平台名称",\n'
            '  "action": "操作类型",\n'
            '  "products_count": 商品数量,\n'
            '  "low_stock_alerts": 低库存商品数,\n'
            '  "order_summary": {\n'
            '    "total": 总订单数,\n'
            '    "pending": 待处理数,\n'
            '    "shipped": 已发货数,\n'
            '    "delivered": 已交付数,\n'
            '    "total_revenue": 总收入估算\n'
            '  },\n'
            '  "pricing_strategy": "定价策略建议",\n'
            '  "listing_advice": ["上架建议1", "上架建议2"],\n'
            '  "recommendations": ["运营建议1", "运营建议2"],\n'
            '  "status": "listing_plan_ready"\n'
            "}"
        )

        llm_result = await self.llm_chat_json(prompt, system=system_prompt)

        if llm_result and "platform" in llm_result:
            # Merge real data
            txn_report = self.te.get_report("today")
            llm_result["_real_data"] = {
                "products_count": len(all_products),
                "transactions_count": len(all_txns),
                "low_stock_count": len(low_stock),
                "daily_report": txn_report,
            }
            llm_result["source"] = "llm+realtime"
            return llm_result

        # Fallback mock
        return {
            "platform": platform,
            "action": action,
            "products_count": len(all_products),
            "transactions_count": len(all_txns),
            "low_stock_count": len(low_stock),
            "order_summary": {
                "pending": len([t for t in all_txns if t.status == "pending"]),
                "shipped": len([t for t in all_txns if t.status == "shipped"]),
                "delivered": len([t for t in all_txns if t.status == "delivered"]),
            },
            "recommendations": [
                "检查低库存商品并及时补货" if low_stock else "库存状态良好",
                "优化商品标题和描述以提升搜索排名",
            ],
            "status": "report_ready",
            "source": "realtime",
        }
