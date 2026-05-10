"""墨增增长子公司 — 增长实验、投放策略、裂变玩法、A/B测试"""
import json
import time
from dataclasses import dataclass, field
from typing import List, Optional

from molib.agencies.base import BaseAgency, Task, AgencyResult

GROWTH_SYSTEM_PROMPT = """你是墨增增长子公司的增长策略师。
根据需求设计增长实验方案，包含渠道策略、裂变玩法、A/B测试设计。

输出必须是严格的 JSON 格式：
{
  "experiment_name": "实验名称",
  "hypothesis": "增长假设",
  "channels": [
    {"name": "渠道名", "budget_pct": 预算占比(数字), "expected_cac": 预期获客成本}
  ],
  "viral_mechanics": "裂变机制描述",
  "ab_test": {
    "variant_a": "A组方案",
    "variant_b": "B组方案",
    "success_metric": "成功指标",
    "sample_size": "样本量"
  },
  "timeline_days": 实验周期(天),
  "expected_uplift_pct": 预期提升百分比(数字),
  "risks": ["风险1", "风险2"],
  "quality_score": 质量评分(1-10)
}"""


@dataclass
class GrowthExperiment:
    id: str
    name: str
    hypothesis: str
    channels: List[dict] = field(default_factory=list)
    expected_uplift_pct: float = 0.0
    quality_score: float = 5.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "hypothesis": self.hypothesis,
            "channels": self.channels, "expected_uplift_pct": self.expected_uplift_pct,
            "quality_score": self.quality_score, "created_at": self.created_at,
        }


class GrowthAgency(BaseAgency):
    agency_id = "growth"
    trigger_keywords = ["增长", "投放", "裂变", "获客", "实验", "A/B", "转化优化", "渠道", "ROI优化"]
    approval_level = "low"
    cost_level = "medium"

    def _parse_growth_json(self, text: str) -> dict:
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
            "experiment_name": "增长方案",
            "hypothesis": text[:200],
            "channels": [],
            "viral_mechanics": "",
            "ab_test": {},
            "timeline_days": 14,
            "expected_uplift_pct": 0.0,
            "risks": ["执行风险"],
            "quality_score": 5.0,
        }

    def __init__(self):
        super().__init__()
        self._load_sqlite()

    def _load_sqlite(self):
        try:
            from molib.infra.memory.sqlite_client import SQLiteClient
            self._db = SQLiteClient()
        except ImportError:
            self._db = None

    async def execute(self, task: Task) -> AgencyResult:
        self.load_sop()
        sop_prompt = self.get_sop_prompt()
        desc = task.payload.get("description", task.payload.get("topic", ""))

        # 尝试加载外部工具文档
        tools_doc = ""
        try:
            from molib.integrations.external_tools.social_hub import get_social_hub
            from molib.integrations.external_tools.market_radar import get_market_radar
            social = get_social_hub()
            radar = get_market_radar()
            tools_doc = (
                f"\n[Available Tools]:\n"
                f"- {social.tool_name}: {social.get_available_commands()}\n"
                f"- {radar.tool_name}: {radar.get_available_commands()}"
            )
        except ImportError:
            pass

        # 查询历史增长实验
        history_info = ""
        if self._db:
            try:
                memories = await self._db.retrieve_memory(
                    key="growth_exp", scenario="transactional", namespace="growth", limit=3
                )
                if memories:
                    history_info = "\n历史实验参考:\n" + "\n".join(
                        f"- {m['data'].get('name', 'unknown')}: uplift {m['data'].get('expected_uplift_pct', 0)}%"
                        for m in memories
                    )
            except Exception:
                pass

        prompt = f"请设计增长实验方案：{desc}{tools_doc}{history_info}"
        if sop_prompt:
            prompt = f"请遵循以下SOP规范：\n{sop_prompt}\n\n{prompt}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=GROWTH_SYSTEM_PROMPT,
            task_type="strategy_generation", team="growth",
        )
        parsed = self._parse_growth_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)

        # 持久化到 SQLite
        if self._db:
            try:
                exp = GrowthExperiment(
                    id=f"growth_{int(time.time())}",
                    name=parsed.get("experiment_name", ""),
                    hypothesis=parsed.get("hypothesis", ""),
                    channels=parsed.get("channels", []),
                    expected_uplift_pct=parsed.get("expected_uplift_pct", 0.0),
                    quality_score=score,
                    created_at=time.time(),
                )
                await self._db.store_memory(
                    key=f"growth_exp_{exp.id}",
                    data=exp.to_dict(),
                    scenario="transactional",
                    namespace="growth"
                )
            except Exception:
                pass

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "experiment_name": parsed.get("experiment_name", ""),
                "hypothesis": parsed.get("hypothesis", ""),
                "channels": parsed.get("channels", []),
                "viral_mechanics": parsed.get("viral_mechanics", ""),
                "ab_test": parsed.get("ab_test", {}),
                "timeline_days": parsed.get("timeline_days", 14),
                "expected_uplift_pct": parsed.get("expected_uplift_pct", 0.0),
                "risks": parsed.get("risks", []),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
