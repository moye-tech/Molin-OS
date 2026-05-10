"""墨数数据子公司 — 数据分析、报表生成、归因分析、漏斗分析、可视化"""
import json
import time

from molib.agencies.base import BaseAgency, Task, AgencyResult

DATA_SYSTEM_PROMPT = """你是墨数数据子公司的数据分析师。
根据需求提供数据分析方案、报表设计或归因分析。

输出必须是严格的 JSON 格式：
{
  "analysis_type": "report|attribution|funnel|cohort|dashboard",
  "data_requirements": "数据需求描述",
  "key_metrics": ["指标1", "指标2"],
  "analysis_steps": ["步骤1", "步骤2"],
  "expected_insights": "预期洞察",
  "visualization_recommendations": ["可视化建议1", "可视化建议2"],
  "quality_score": 质量评分(1-10)
}"""


class DataAgency(BaseAgency):
    agency_id = "data"
    trigger_keywords = ["报表", "数据", "归因", "漏斗", "指标", "可视化", "大盘", "统计", "数据报表"]
    approval_level = "low"
    cost_level = "low"

    def _parse_data_json(self, text: str) -> dict:
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
            "analysis_type": "report",
            "data_requirements": text[:300],
            "key_metrics": [],
            "analysis_steps": [],
            "expected_insights": "",
            "visualization_recommendations": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        prompt = f"请分析以下数据需求并输出方案：{desc}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=DATA_SYSTEM_PROMPT,
            task_type="data_analysis", team="data",
        )
        parsed = self._parse_data_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "analysis_type": parsed.get("analysis_type", "report"),
                "data_requirements": parsed.get("data_requirements", ""),
                "key_metrics": parsed.get("key_metrics", []),
                "analysis_steps": parsed.get("analysis_steps", []),
                "expected_insights": parsed.get("expected_insights", ""),
                "visualization_recommendations": parsed.get("visualization_recommendations", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
