"""墨海出海子公司 — 多语言内容本地化、海外平台运营策略、跨境合规"""
import json
import time
from pathlib import Path

from molib.agencies.base import BaseAgency, Task, AgencyResult

GLOBAL_SYSTEM_PROMPT = """你是墨海出海子公司的国际化专家。
根据需求进行内容本地化、海外市场策略、跨境合规分析或平台适配。

输出必须是严格的 JSON 格式：
{
  "global_type": "localization|market_strategy|compliance|platform",
  "target_market": "目标市场",
  "localization_plan": "本地化方案描述",
  "cultural_adaptations": ["文化适配点1", "文化适配点2"],
  "compliance_requirements": ["合规要求1", "合规要求2"],
  "platform_strategy": "平台策略描述",
  "launch_checklist": ["上线检查项1", "上线检查项2"],
  "risks": ["风险1", "风险2"],
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "localizer": "localizer.txt",
    "market_strategist": "market_strategist.txt",
    "compliance_checker": "compliance_checker.txt",
    "platform_adapter": "platform_adapter.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


class Global_marketAgency(BaseAgency):
    agency_id = "global_market"
    trigger_keywords = ["出海", "海外", "英文", "翻译", "台湾", "繁体", "东南亚", "LINE", "Shopee", "TikTok", "国际化", "本地化", "跨境"]
    approval_level = "medium"
    cost_level = "medium"

    def _select_worker(self, desc: str) -> str:
        desc_l = desc.lower()
        if any(k in desc_l for k in ["翻译", "本地化", "繁体", "繁简"]):
            return "localizer"
        if any(k in desc_l for k in ["合规", "跨境", "法规"]):
            return "compliance_checker"
        if any(k in desc_l for k in ["平台", "line", "shopee", "tiktok", "dcard"]):
            return "platform_adapter"
        return "market_strategist"

    def _parse_global_json(self, text: str) -> dict:
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
            "global_type": "market_strategy",
            "target_market": "",
            "localization_plan": text[:300],
            "cultural_adaptations": [],
            "compliance_requirements": [],
            "platform_strategy": "",
            "launch_checklist": [],
            "risks": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        system_prompt = WORKER_PROMPTS.get(worker_type, GLOBAL_SYSTEM_PROMPT)
        system_prompt += "\n\n" + GLOBAL_SYSTEM_PROMPT

        start = time.time()
        res = await self.router.call_async(
            prompt=desc, system=system_prompt,
            task_type="globalization", team="global_market",
        )
        parsed = self._parse_global_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)
        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "global_type": parsed.get("global_type", "market_strategy"),
                "target_market": parsed.get("target_market", ""),
                "localization_plan": parsed.get("localization_plan", ""),
                "cultural_adaptations": parsed.get("cultural_adaptations", []),
                "compliance_requirements": parsed.get("compliance_requirements", []),
                "platform_strategy": parsed.get("platform_strategy", ""),
                "launch_checklist": parsed.get("launch_checklist", []),
                "risks": parsed.get("risks", []),
                "worker_type": worker_type,
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
