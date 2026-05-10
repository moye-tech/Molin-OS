"""墨单订单子公司 — 询盘处理、报价生成、交付管理、订单跟踪"""
import json
import time

from molib.agencies.base import BaseAgency, Task, AgencyResult

ORDER_SYSTEM_PROMPT = """你是墨单订单子公司的订单管理专家。
根据询盘内容生成报价方案、交付计划和订单状态。

输出必须是严格的 JSON 格式：
{
  "inquiry_type": "new|existing|renewal",
  "quoted_items": [
    {"item": "服务项", "price": 价格(数字), "delivery_days": 交付天数}
  ],
  "total_price": 总价(数字),
  "payment_terms": "付款方式",
  "delivery_timeline": "交付时间线",
  "risks": ["风险1", "风险2"],
  "quality_score": 质量评分(1-10)
}"""


class OrderAgency(BaseAgency):
    agency_id = "order"
    trigger_keywords = ["询盘", "报价", "交付", "订单", "支付", "下单", "尾款", "定金"]
    approval_level = "low"
    cost_level = "low"

    def _parse_order_json(self, text: str) -> dict:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if "```json" in text:
                try:
                    start = text.index("```json") + 7
                    end = text.index("```", start)
                    return json.loads(text[start:end].strip())
                except Exception:
                    pass
        return {
            "inquiry_type": "new",
            "quoted_items": [],
            "total_price": 0.0,
            "payment_terms": "面议",
            "delivery_timeline": "",
            "risks": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        prompt = f"请根据以下询盘生成报价方案：{desc}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=ORDER_SYSTEM_PROMPT,
            task_type="pricing", team="order",
        )
        parsed = self._parse_order_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "inquiry_type": parsed.get("inquiry_type", "new"),
                "quoted_items": parsed.get("quoted_items", []),
                "total_price": parsed.get("total_price", 0.0),
                "payment_terms": parsed.get("payment_terms", "面议"),
                "delivery_timeline": parsed.get("delivery_timeline", ""),
                "risks": parsed.get("risks", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
