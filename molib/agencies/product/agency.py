"""墨品产品子公司 — MVP设计、功能规划、产品标准化、套餐定价"""
import json
import time

from molib.agencies.base import BaseAgency, Task, AgencyResult

PRODUCT_SYSTEM_PROMPT = """你是墨品产品子公司的产品经理。
根据需求设计MVP方案、功能规划或产品套餐。

输出必须是严格的 JSON 格式：
{
  "product_type": "mvp|feature|pricing|roadmap",
  "product_name": "产品名称",
  "target_users": "目标用户描述",
  "core_features": [
    {"name": "功能名", "priority": "P0|P1|P2", "effort_days": 开发天数, "description": "描述"}
  ],
  "mvp_scope": "MVP范围描述",
  "pricing_tiers": [
    {"name": "档位名", "price": 价格(数字), "features": ["权益1", "权益2"]}
  ],
  "timeline_weeks": 开发周期(周),
  "risks": ["风险1", "风险2"],
  "success_metrics": ["成功指标1", "成功指标2"],
  "quality_score": 质量评分(1-10)
}"""


class ProductAgency(BaseAgency):
    agency_id = "product"
    trigger_keywords = ["mvp", "功能规划", "标准化", "套餐", "定价", "版本", "迭代", "roadmap", "产品化"]
    approval_level = "low"
    cost_level = "medium"

    def _parse_product_json(self, text: str) -> dict:
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
            "product_type": "mvp",
            "product_name": "未命名产品",
            "target_users": "",
            "core_features": [],
            "mvp_scope": text[:300],
            "pricing_tiers": [],
            "timeline_weeks": 4,
            "risks": [],
            "success_metrics": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        prompt = f"请为以下产品方向生成MVP方案：{desc}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=PRODUCT_SYSTEM_PROMPT,
            task_type="strategy_generation", team="product",
        )
        parsed = self._parse_product_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "product_type": parsed.get("product_type", "mvp"),
                "product_name": parsed.get("product_name", ""),
                "target_users": parsed.get("target_users", ""),
                "core_features": parsed.get("core_features", []),
                "mvp_scope": parsed.get("mvp_scope", ""),
                "pricing_tiers": parsed.get("pricing_tiers", []),
                "timeline_weeks": parsed.get("timeline_weeks", 4),
                "risks": parsed.get("risks", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
