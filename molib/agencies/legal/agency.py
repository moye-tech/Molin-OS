"""墨律法务子公司 — 合同条款审查、隐私政策生成、版权检测、合规风险预警"""
import json
import time
from pathlib import Path

from molib.agencies.base import BaseAgency, Task, AgencyResult

LEGAL_SYSTEM_PROMPT = """你是墨律法务子公司的法务专家。
根据需求进行合同审查、合规分析或法律文档生成。

输出必须是严格的 JSON 格式：
{
  "legal_type": "contract_review|compliance|ip|document",
  "risk_level": "low|medium|high|critical",
  "summary": "法律分析摘要",
  "key_clauses": ["关键条款1", "关键条款2"],
  "risk_items": [
    {"item": "风险项", "severity": "严重程度", "recommendation": "建议"}
  ],
  "compliance_requirements": ["合规要求1", "合规要求2"],
  "recommended_actions": ["建议动作1", "建议动作2"],
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "contract_reviewer": "contract_reviewer.txt",
    "compliance_advisor": "compliance_advisor.txt",
    "doc_drafter": "doc_drafter.txt",
    "ip_guardian": "ip_guardian.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


class LegalAgency(BaseAgency):
    agency_id = "legal"
    trigger_keywords = ["合同", "协议", "版权", "合规", "法律", "NDA", "授权", "知识产权", "隐私政策", "免责声明"]
    approval_level = "high"
    cost_level = "high"

    def _select_worker(self, desc: str) -> str:
        desc_l = desc.lower()
        if any(k in desc_l for k in ["审查", "审核", "风险条款"]):
            return "contract_reviewer"
        if any(k in desc_l for k in ["合规", "pipl", "广告法", "数据保护"]):
            return "compliance_advisor"
        if any(k in desc_l for k in ["版权", "知识产权", "侵权"]):
            return "ip_guardian"
        return "doc_drafter"

    def _parse_legal_json(self, text: str) -> dict:
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
            "legal_type": "document",
            "risk_level": "medium",
            "summary": text[:300],
            "key_clauses": [],
            "risk_items": [],
            "compliance_requirements": [],
            "recommended_actions": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        system_prompt = WORKER_PROMPTS.get(worker_type, LEGAL_SYSTEM_PROMPT)
        system_prompt += "\n\n" + LEGAL_SYSTEM_PROMPT

        start = time.time()
        res = await self.router.call_async(
            prompt=desc, system=system_prompt,
            task_type="legal", team="legal",
        )
        parsed = self._parse_legal_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "legal_type": parsed.get("legal_type", "document"),
                "risk_level": parsed.get("risk_level", "medium"),
                "summary": parsed.get("summary", ""),
                "key_clauses": parsed.get("key_clauses", []),
                "risk_items": parsed.get("risk_items", []),
                "compliance_requirements": parsed.get("compliance_requirements", []),
                "recommended_actions": parsed.get("recommended_actions", []),
                "worker_type": worker_type,
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
