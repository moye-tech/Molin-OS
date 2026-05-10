"""墨算财务子公司 — 成本核算、ROI分析、预算规划、财务报表自动生成"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from molib.agencies.base import BaseAgency, Task, AgencyResult

FINANCE_SYSTEM_PROMPT = """你是墨算财务子公司的财务专家。
根据任务描述进行财务分析，输出结构化的财务报告。

输出必须是严格的 JSON 格式：
{
  "analysis_type": "cost|roi|budget|report",
  "summary": "财务摘要",
  "key_metrics": {
    "total_cost": 总成本(数字),
    "total_revenue": 总收入(数字),
    "roi_pct": ROI百分比(数字),
    "profit_margin_pct": 利润率百分比(数字)
  },
  "breakdown": [
    {"item": "项目", "amount": 金额(数字), "pct_of_total": 占比(数字)}
  ],
  "alerts": ["预警1", "预警2"],
  "recommendations": ["建议1", "建议2"],
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "cost_analyst": "cost_analyst.txt",
    "roi_calculator": "roi_calculator.txt",
    "report_generator": "report_generator.txt",
    "budget_monitor": "budget_monitor.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


@dataclass
class FinancialReport:
    id: str
    analysis_type: str
    summary: str
    key_metrics: dict = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    quality_score: float = 5.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "analysis_type": self.analysis_type,
            "summary": self.summary, "key_metrics": self.key_metrics,
            "alerts": self.alerts, "quality_score": self.quality_score,
            "created_at": self.created_at,
        }


class FinanceAgency(BaseAgency):
    agency_id = "finance"
    trigger_keywords = ["预算", "成本", "财务", "ROI", "利润", "账单", "报销", "盈亏", "收入", "支出", "ROAS", "CAC", "LTV"]
    approval_level = "high"
    cost_level = "medium"

    def __init__(self):
        super().__init__()
        self._load_sqlite()

    def _load_sqlite(self):
        try:
            from molib.infra.memory.sqlite_client import SQLiteClient
            self._db = SQLiteClient()
        except ImportError:
            self._db = None

    def _select_worker(self, desc: str) -> str:
        desc_l = desc.lower()
        if any(k in desc_l for k in ["roi", "回报", "roas"]):
            return "roi_calculator"
        if any(k in desc_l for k in ["月报", "简报", "报告", "报表"]):
            return "report_generator"
        if any(k in desc_l for k in ["预算", "告警", "预警", "超支"]):
            return "budget_monitor"
        return "cost_analyst"

    def _parse_finance_json(self, text: str) -> dict:
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
            "analysis_type": "unknown",
            "summary": text[:300],
            "key_metrics": {},
            "breakdown": [],
            "alerts": [],
            "recommendations": [],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        self.load_sop()
        sop_prompt = self.get_sop_prompt()
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        # 查询历史财务数据
        history_info = ""
        if self._db:
            try:
                memories = await self._db.retrieve_memory(
                    key="finance_report", scenario="transactional", namespace="finance", limit=3
                )
                if memories:
                    history_info = "\n历史财务参考:\n" + "\n".join(
                        f"- {m['data'].get('summary', 'unknown')[:100]}" for m in memories
                    )
            except Exception:
                pass

        system_prompt = WORKER_PROMPTS.get(worker_type, FINANCE_SYSTEM_PROMPT)
        system_prompt += "\n\n" + FINANCE_SYSTEM_PROMPT
        if sop_prompt:
            system_prompt += f"\n\n请遵循SOP规范：\n{sop_prompt}"
        prompt = f"{desc}{history_info}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=system_prompt,
            task_type="finance", team="finance",
        )
        parsed = self._parse_finance_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)

        # 持久化到 SQLite
        if self._db:
            try:
                report = FinancialReport(
                    id=f"finance_{int(time.time())}",
                    analysis_type=parsed.get("analysis_type", ""),
                    summary=parsed.get("summary", ""),
                    key_metrics=parsed.get("key_metrics", {}),
                    alerts=parsed.get("alerts", []),
                    quality_score=score,
                    created_at=time.time(),
                )
                await self._db.store_memory(
                    key=f"finance_report_{report.id}",
                    data=report.to_dict(),
                    scenario="transactional",
                    namespace="finance"
                )
            except Exception:
                pass

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "analysis_type": parsed.get("analysis_type", "unknown"),
                "summary": parsed.get("summary", ""),
                "key_metrics": parsed.get("key_metrics", {}),
                "breakdown": parsed.get("breakdown", []),
                "alerts": parsed.get("alerts", []),
                "recommendations": parsed.get("recommendations", []),
                "worker_type": worker_type,
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
