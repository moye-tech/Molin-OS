"""墨智AI子公司 — Prompt工程、RAG架构、Agent设计、模型选型、工作流搭建"""
import json
import time

from molib.agencies.base import BaseAgency, Task, AgencyResult

AI_SYSTEM_PROMPT = """你是墨智AI子公司的AI架构师。
根据需求提供AI系统解决方案，包括模型选型、Prompt设计、RAG架构或Agent工作流。

输出必须是严格的 JSON 格式：
{
  "solution_type": "prompt|rag|agent|workflow|model_selection",
  "architecture": "架构描述",
  "model_recommendations": [
    {"use_case": "用途", "model": "推荐模型", "reason": "选择理由"}
  ],
  "prompt_templates": ["Prompt模板1", "Prompt模板2"],
  "implementation_steps": ["步骤1", "步骤2", "步骤3"],
  "estimated_cost_per_call": 预估每次调用成本(数字),
  "risks": ["风险1", "风险2"],
  "quality_score": 质量评分(1-10)
}"""


class AiAgency(BaseAgency):
    agency_id = "ai"
    trigger_keywords = ["prompt", "rag", "agent", "模型", "工作流", "Embedding", "向量", "微调", "LLM"]
    approval_level = "low"
    cost_level = "medium"

    def _parse_ai_json(self, text: str) -> dict:
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
            "solution_type": "unknown",
            "architecture": text[:300],
            "model_recommendations": [],
            "prompt_templates": [],
            "implementation_steps": [],
            "estimated_cost_per_call": 0.0,
            "risks": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        prompt = f"请为以下AI系统需求给出解决方案：{desc}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=AI_SYSTEM_PROMPT,
            task_type="deep_research", team="ai",
        )
        parsed = self._parse_ai_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "solution_type": parsed.get("solution_type", "unknown"),
                "architecture": parsed.get("architecture", ""),
                "model_recommendations": parsed.get("model_recommendations", []),
                "prompt_templates": parsed.get("prompt_templates", []),
                "implementation_steps": parsed.get("implementation_steps", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
