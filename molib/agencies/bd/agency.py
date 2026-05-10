"""墨商BD子公司 — 商务拓展、合作方筛查、报价生成、谈判策略制定"""
import json
import time
from pathlib import Path

from molib.agencies.base import BaseAgency, Task, AgencyResult

BD_SYSTEM_PROMPT = """你是墨商BD子公司的商务拓展专家。
根据需求进行客户分析、报价生成、谈判策略制定或跟进管理。

输出必须是严格的 JSON 格式：
{
  "bd_type": "client_analysis|quotation|negotiation|followup",
  "client_profile": "客户画像描述",
  "opportunity_assessment": "商机评估",
  "recommended_approach": "推荐策略",
  "quotation_items": [
    {"service": "服务项目", "price": 价格(数字), "terms": "条款"}
  ],
  "negotiation_points": ["谈判要点1", "谈判要点2"],
  "next_steps": ["下一步动作1", "下一步动作2"],
  "deal_probability": 成单概率(0-1),
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "client_analyst": "client_analyst.txt",
    "quotation_specialist": "quotation_specialist.txt",
    "negotiation_advisor": "negotiation_advisor.txt",
    "followup_manager": "followup_manager.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


class BdAgency(BaseAgency):
    agency_id = "bd"
    trigger_keywords = ["合作", "报价", "谈判", "BD", "外包", "客户", "签约", "商务", "洽谈", "接单", "询价"]
    approval_level = "high"
    cost_level = "medium"

    def _select_worker(self, desc: str) -> str:
        desc_l = desc.lower()
        if any(k in desc_l for k in ["报价", "定价", "费用"]):
            return "quotation_specialist"
        if any(k in desc_l for k in ["谈判", "压价", "还价", "策略"]):
            return "negotiation_advisor"
        if any(k in desc_l for k in ["跟进", "回访", "催单"]):
            return "followup_manager"
        return "client_analyst"

    def _parse_bd_json(self, text: str) -> dict:
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
            "bd_type": "client_analysis",
            "client_profile": text[:200],
            "opportunity_assessment": "",
            "recommended_approach": "",
            "quotation_items": [],
            "negotiation_points": [],
            "next_steps": [],
            "deal_probability": 0.5,
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        system_prompt = WORKER_PROMPTS.get(worker_type, BD_SYSTEM_PROMPT)
        system_prompt += "\n\n" + BD_SYSTEM_PROMPT

        start = time.time()
        res = await self.router.call_async(
            prompt=desc, system=system_prompt,
            task_type="business_development", team="bd",
        )
        parsed = self._parse_bd_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "bd_type": parsed.get("bd_type", "client_analysis"),
                "client_profile": parsed.get("client_profile", ""),
                "opportunity_assessment": parsed.get("opportunity_assessment", ""),
                "quotation_items": parsed.get("quotation_items", []),
                "negotiation_points": parsed.get("negotiation_points", []),
                "next_steps": parsed.get("next_steps", []),
                "deal_probability": parsed.get("deal_probability", 0.5),
                "worker_type": worker_type,
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
