"""墨盾安全子公司 — 安全审计、权限管理、合规检查、风险评估"""
import json
import time

from molib.agencies.base import BaseAgency, Task, AgencyResult

SECURE_SYSTEM_PROMPT = """你是墨盾安全子公司的安全审计专家。
根据需求进行安全审查、风险评估和合规检查。

输出必须是严格的 JSON 格式：
{
  "audit_type": "security|compliance|access_control|risk_assessment",
  "risk_level": "low|medium|high|critical",
  "vulnerabilities": [
    {"type": "漏洞类型", "severity": "严重级别", "description": "描述", "recommendation": "修复建议"}
  ],
  "compliance_status": {"framework": "合规框架", "status": "pass|fail|partial"},
  "recommendations": ["建议1", "建议2"],
  "urgency": "处理紧急度(low/medium/high/critical)",
  "quality_score": 质量评分(1-10)
}"""


class SecureAgency(BaseAgency):
    agency_id = "secure"
    trigger_keywords = ["安全", "权限", "合规", "风控", "审计", "漏洞", "加密", "攻击", "隐私"]
    approval_level = "medium"
    cost_level = "low"

    def _parse_secure_json(self, text: str) -> dict:
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
            "audit_type": "security",
            "risk_level": "medium",
            "vulnerabilities": [],
            "compliance_status": {},
            "recommendations": ["建议进行全面安全审查"],
            "urgency": "medium",
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        prompt = f"请审查以下需求的安全风险并给出建议：{desc}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=SECURE_SYSTEM_PROMPT,
            task_type="compliance_check", team="secure",
        )
        parsed = self._parse_secure_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "audit_type": parsed.get("audit_type", "security"),
                "risk_level": parsed.get("risk_level", "medium"),
                "vulnerabilities": parsed.get("vulnerabilities", []),
                "compliance_status": parsed.get("compliance_status", {}),
                "recommendations": parsed.get("recommendations", []),
                "urgency": parsed.get("urgency", "medium"),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
