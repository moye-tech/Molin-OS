"""墨链电商 Worker — 订单管理、交易、电商平台

所属: VP运营
技能: molin-order
"""
import json
from .base import SubsidiaryWorker, Task, WorkerResult

class Ecommerce(SubsidiaryWorker):
    worker_id = "ecommerce"
    worker_name = "墨链电商"
    description = "订单管理、交易、电商平台"
    oneliner = "订单管理、交易、电商平台"

    @staticmethod
    def get_capabilities() -> list[str]:
        return [
            "多平台商品上架管理",
            "订单状态追踪与更新",
            "交易记录与对账",
            "电商平台API集成",
        ]

    @staticmethod
    def get_metadata() -> dict:
        return {
            "name": "墨链电商",
            "vp": "运营",
            "description": "订单管理、交易、电商平台",
        }

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            products = task.payload.get("products", [])
            platform = task.payload.get("platform", "闲鱼")
            action = task.payload.get("action", "list")
            pending_orders = task.payload.get("pending_orders", 0)
            shipped_orders = task.payload.get("shipped_orders", 0)

            # ── LLM 注入：电商运营智能分析 ──
            system_prompt = (
                "你是一位资深的电商运营专家，精通多平台上架策略、订单管理、库存优化。"
                "请根据商品信息和平台特性，给出最优运营方案。"
            )

            products_summary = json.dumps(products, ensure_ascii=False)[:2000] if products else "无商品数据"

            prompt = (
                f"请处理以下电商运营请求：\n"
                f"平台：{platform}\n"
                f"操作类型：{action}\n"
                f"待处理订单：{pending_orders}\n"
                f"已发货订单：{shipped_orders}\n"
                f"商品信息：\n{products_summary}\n\n"
                "以JSON格式输出运营方案：\n"
                "{\n"
                '  "platform": "平台名称",\n'
                '  "action": "操作类型",\n'
                '  "products": [\n'
                '    {\n'
                '      "title": "商品标题",\n'
                '      "price": 价格,\n'
                '      "category": "分类",\n'
                '      "status": "draft_ready/listed/sold",\n'
                '      "optimization_suggestion": "上架优化建议"\n'
                '    }\n'
                '  ],\n'
                '  "order_stats": {\n'
                '    "pending": 待处理数,\n'
                '    "shipped": 已发货数,\n'
                '    "total_revenue": 总收入估算,\n'
                '    "avg_order_value": 平均客单价\n'
                '  },\n'
                '  "pricing_strategy": "定价策略建议",\n'
                '  "listing_advice": ["上架建议1", "上架建议2"],\n'
                '  "status": "listing_plan_ready"\n'
                "}"
            )

            llm_result = await self.llm_chat_json(prompt, system=system_prompt)

            if llm_result and "platform" in llm_result:
                output = llm_result
                output["source"] = "llm"
            else:
                # ── fallback：原有 mock ──
                output = {
                    "platform": platform,
                    "action": action,
                    "products": [{
                        "title": p.get("title", "未命名"),
                        "price": p.get("price", 0),
                        "status": "draft_ready",
                    } for p in products],
                    "order_stats": {
                        "pending": pending_orders,
                        "shipped": shipped_orders,
                    },
                    "pricing_strategy": "",
                    "listing_advice": [],
                    "status": "listing_plan_ready",
                    "source": "mock",
                }

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=output,
            )
        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={},
                error=str(e),
            )
