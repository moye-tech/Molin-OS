"""墨域私域子公司 — 用户生命周期管理、复购激活、流失预警、RFM分层运营"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from molib.agencies.base import BaseAgency, Task, AgencyResult

CRM_SYSTEM_PROMPT = """你是墨域私域子公司的CRM专家。
根据任务描述分析用户需求，输出结构化的CRM策略方案。

输出必须是严格的 JSON 格式：
{
  "analysis_type": "rfm_segment|churn_risk|lifecycle_stage|campaign_plan",
  "user_segment": "用户分群标签",
  "key_findings": ["发现1", "发现2"],
  "recommended_actions": [
    {"action": "动作描述", "channel": "触达渠道", "priority": "high|medium|low"}
  ],
  "expected_impact": "预期效果描述",
  "metrics_to_track": ["指标1", "指标2"],
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "user_analyst": "user_analyst.txt",
    "lifecycle_manager": "lifecycle_manager.txt",
    "churn_predictor": "churn_predictor.txt",
    "campaign_designer": "campaign_designer.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


@dataclass
class CustomerRecord:
    id: str
    segment: str
    analysis_type: str
    key_findings: List[str] = field(default_factory=list)
    actions: List[dict] = field(default_factory=list)
    quality_score: float = 5.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "segment": self.segment,
            "analysis_type": self.analysis_type,
            "key_findings": self.key_findings,
            "actions": self.actions,
            "quality_score": self.quality_score,
            "created_at": self.created_at,
        }


class CrmAgency(BaseAgency):
    agency_id = "crm"
    trigger_keywords = ["私域", "会员", "复购", "流失", "激活", "用户分层", "RFM", "M0", "M1", "M2", "转化率", "留存"]
    approval_level = "medium"
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
        if any(k in desc_l for k in ["流失", "预警", "churn"]):
            return "churn_predictor"
        if any(k in desc_l for k in ["活动", "策划", "裂变", "促销"]):
            return "campaign_designer"
        if any(k in desc_l for k in ["生命周期", "m0", "m1", "m2", "转化"]):
            return "lifecycle_manager"
        return "user_analyst"

    def _parse_crm_json(self, text: str) -> dict:
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
            "user_segment": "未分类",
            "key_findings": [text[:200]],
            "recommended_actions": [],
            "expected_impact": "",
            "metrics_to_track": ["转化率"],
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        self.load_sop()
        sop_prompt = self.get_sop_prompt()
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        # 查询用户分层历史
        history_info = ""
        if self._db:
            try:
                memories = await self._db.retrieve_memory(
                    key="crm_segment", scenario="transactional", namespace="crm", limit=3
                )
                if memories:
                    history_info = "\n历史分层参考:\n" + "\n".join(
                        f"- {m['data'].get('segment', 'unknown')}" for m in memories
                    )
            except Exception:
                pass

        system_prompt = WORKER_PROMPTS.get(worker_type, CRM_SYSTEM_PROMPT)
        system_prompt += "\n\n" + CRM_SYSTEM_PROMPT
        if sop_prompt:
            system_prompt += f"\n\n请遵循SOP规范：\n{sop_prompt}"
        prompt = f"{desc}{history_info}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=system_prompt,
            task_type="crm", team="crm",
        )
        parsed = self._parse_crm_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)

        # 持久化到 SQLite
        if self._db:
            try:
                record = CustomerRecord(
                    id=f"crm_{int(time.time())}",
                    segment=parsed.get("user_segment", ""),
                    analysis_type=parsed.get("analysis_type", ""),
                    key_findings=parsed.get("key_findings", []),
                    actions=parsed.get("recommended_actions", []),
                    quality_score=score,
                    created_at=time.time(),
                )
                await self._db.store_memory(
                    key=f"crm_segment_{record.id}",
                    data=record.to_dict(),
                    scenario="transactional",
                    namespace="crm"
                )
            except Exception:
                pass

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "analysis_type": parsed.get("analysis_type", "unknown"),
                "user_segment": parsed.get("user_segment", ""),
                "key_findings": parsed.get("key_findings", []),
                "recommended_actions": parsed.get("recommended_actions", []),
                "expected_impact": parsed.get("expected_impact", ""),
                "metrics_to_track": parsed.get("metrics_to_track", []),
                "worker_type": worker_type,
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
