"""墨声客服子公司 — 智能客服应答、投诉处理、满意度追踪、FAQ自动维护"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from molib.agencies.base import BaseAgency, Task, AgencyResult

CS_SYSTEM_PROMPT = """你是墨声客服子公司的智能客服专家。
分析用户反馈，分类问题类型，评估情感倾向，生成回复方案。

输出必须是严格的 JSON 格式：
{
  "category": "complaint|inquiry|refund|feedback|technical",
  "sentiment": "positive|neutral|negative|angry",
  "sentiment_score": -1.0到1.0的数字(-1最负面,1最正面),
  "urgency": "low|medium|high|critical",
  "response": "给用户的回复",
  "resolution_steps": ["步骤1", "步骤2"],
  "escalation_needed": true或false,
  "follow_up_required": true或false,
  "satisfaction_prediction": 预期满意度(1-5),
  "quality_score": 质量评分(1-10)
}"""

PROMPTS_DIR = Path(__file__).parent / "prompts"
WORKER_PROMPTS = {}
for _wt, _wf in {
    "first_responder": "first_responder.txt",
    "complaint_handler": "complaint_handler.txt",
    "satisfaction_tracker": "satisfaction_tracker.txt",
    "faq_maintainer": "faq_maintainer.txt",
}.items():
    _fp = PROMPTS_DIR / _wf
    if _fp.exists():
        WORKER_PROMPTS[_wt] = _fp.read_text(encoding="utf-8")


@dataclass
class TicketRecord:
    id: str
    category: str
    sentiment: str
    urgency: str
    response: str
    escalation_needed: bool = False
    quality_score: float = 5.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "category": self.category, "sentiment": self.sentiment,
            "urgency": self.urgency, "response": self.response,
            "escalation_needed": self.escalation_needed,
            "quality_score": self.quality_score, "created_at": self.created_at,
        }


class CsAgency(BaseAgency):
    agency_id = "cs"
    trigger_keywords = ["客服", "用户反馈", "投诉", "退款", "咨询", "售后", "问题反馈", "不满意", "差评", "纠纷", "投诉问题"]
    approval_level = "low"
    cost_level = "low"

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
        if any(k in desc_l for k in ["投诉", "纠纷", "退款", "差评", "不满"]):
            return "complaint_handler"
        if any(k in desc_l for k in ["满意度", "nps", "csat", "评价"]):
            return "satisfaction_tracker"
        if any(k in desc_l for k in ["faq", "常见问题", "知识库维护"]):
            return "faq_maintainer"
        return "first_responder"

    def _parse_cs_json(self, text: str) -> dict:
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
            "category": "inquiry",
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "urgency": "medium",
            "response": text[:500],
            "resolution_steps": [],
            "escalation_needed": False,
            "follow_up_required": False,
            "satisfaction_prediction": 3,
            "quality_score": 5.0,
        }

    async def execute(self, task: Task) -> AgencyResult:
        self.load_sop()
        sop_prompt = self.get_sop_prompt()
        desc = task.payload.get("description", "")
        worker_type = self._select_worker(desc)

        # 查询历史工单
        history_info = ""
        if self._db:
            try:
                memories = await self._db.retrieve_memory(
                    key="cs_ticket", scenario="transactional", namespace="cs", limit=3
                )
                if memories:
                    history_info = "\n历史工单参考:\n" + "\n".join(
                        f"- {m['data'].get('category', 'unknown')}: {m['data'].get('sentiment', 'unknown')}"
                        for m in memories
                    )
            except Exception:
                pass

        system_prompt = WORKER_PROMPTS.get(worker_type, CS_SYSTEM_PROMPT)
        system_prompt += "\n\n" + CS_SYSTEM_PROMPT
        if sop_prompt:
            system_prompt += f"\n\n请遵循SOP规范：\n{sop_prompt}"
        prompt = f"{desc}{history_info}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=system_prompt,
            task_type="customer_service", team="cs",
        )
        parsed = self._parse_cs_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)

        # 持久化到 SQLite
        if self._db:
            try:
                ticket = TicketRecord(
                    id=f"cs_{int(time.time())}",
                    category=parsed.get("category", "inquiry"),
                    sentiment=parsed.get("sentiment", "neutral"),
                    urgency=parsed.get("urgency", "medium"),
                    response=parsed.get("response", ""),
                    escalation_needed=parsed.get("escalation_needed", False),
                    quality_score=score,
                    created_at=time.time(),
                )
                await self._db.store_memory(
                    key=f"cs_ticket_{ticket.id}",
                    data=ticket.to_dict(),
                    scenario="transactional",
                    namespace="cs"
                )
            except Exception:
                pass

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "category": parsed.get("category", "inquiry"),
                "sentiment": parsed.get("sentiment", "neutral"),
                "sentiment_score": parsed.get("sentiment_score", 0.0),
                "urgency": parsed.get("urgency", "medium"),
                "response": parsed.get("response", ""),
                "resolution_steps": parsed.get("resolution_steps", []),
                "escalation_needed": parsed.get("escalation_needed", False),
                "follow_up_required": parsed.get("follow_up_required", False),
                "satisfaction_prediction": parsed.get("satisfaction_prediction", 3),
                "worker_type": worker_type,
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
