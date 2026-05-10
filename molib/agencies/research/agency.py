"""墨思研究子公司 — 行业研究、竞品分析、趋势洞察、技术情报"""
import json
import time

from molib.agencies.base import BaseAgency, Task, AgencyResult

RESEARCH_SYSTEM_PROMPT = """你是墨思研究子公司的行业研究员。
根据主题进行深度研究分析，输出结构化的研究报告。

输出必须是严格的 JSON 格式：
{
  "research_type": "market|competitor|trend|technology",
  "executive_summary": "执行摘要",
  "key_findings": ["发现1", "发现2", "发现3"],
  "market_size": "市场规模描述",
  "competitors": [
    {"name": "竞品名", "strengths": ["优势"], "weaknesses": ["劣势"], "market_share": "市场份额"}
  ],
  "trends": ["趋势1", "趋势2"],
  "opportunities": ["机会1", "机会2"],
  "threats": ["威胁1", "威胁2"],
  "recommendations": ["建议1", "建议2"],
  "quality_score": 质量评分(1-10)
}"""


class ResearchAgency(BaseAgency):
    agency_id = "research"
    agency_name = "墨思研究"
    personality = "严谨的研究分析师，擅长从数据中发现洞察，不满足于表面答案"
    trigger_keywords = ["研究", "竞品", "趋势", "情报", "行业", "调研", "分析报", "竞品分析", "市场"]
    approval_level = "low"
    cost_level = "medium"

    def _parse_research_json(self, text: str) -> dict:
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
            "research_type": "market",
            "executive_summary": text[:300],
            "key_findings": [],
            "market_size": "",
            "competitors": [],
            "trends": [],
            "opportunities": [],
            "threats": [],
            "recommendations": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", task.payload.get("topic", ""))
        prompt = f"请研究以下主题并输出结构化研究报告：{desc}"

        # 挂载 Web Browser 工具文档
        tools_doc = ""
        try:
            from molib.integrations.external_tools.web_browser import get_web_browser
            browser = get_web_browser()
            tools_doc = f"\n\n[Available Tools]:\n- {browser.tool_name}: 可用于实时网络搜索和信息获取"
        except ImportError:
            pass

        prompt += tools_doc

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=RESEARCH_SYSTEM_PROMPT,
            task_type="deep_research", team="research",
        )
        parsed = self._parse_research_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "research_type": parsed.get("research_type", "market"),
                "executive_summary": parsed.get("executive_summary", ""),
                "key_findings": parsed.get("key_findings", []),
                "competitors": parsed.get("competitors", []),
                "trends": parsed.get("trends", []),
                "recommendations": parsed.get("recommendations", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
