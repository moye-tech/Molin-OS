"""墨商销售转化子公司 — 销售话术、意向分析、成交转化、报价策略"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from molib.agencies.base import BaseAgency, Task, AgencyResult

SALES_STAGES = ["lead", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
PRODUCT_TIERS = [
    {"name": "AI副业入门班", "price": 999, "level": "entry"},
    {"name": "AI自动化进阶包", "price": 2999, "level": "mid"},
    {"name": "全套定制服务", "price": 5999, "level": "premium"},
]

@dataclass
class SalesRecord:
    id: str
    stage: str
    customer_msg: str
    intent_score: float = 0.0
    recommended_product: str = ""
    response: str = ""
    quality_score: float = 5.0
    created_at: float = 0.0

    def to_dict(self) -> dict:
        return {
            "id": self.id, "stage": self.stage,
            "intent_score": self.intent_score,
            "recommended_product": self.recommended_product,
            "response": self.response,
            "quality_score": self.quality_score,
            "created_at": self.created_at,
        }


SALES_SYSTEM_PROMPT = """你是墨商销售转化子公司的AI销售顾问。
分析用户意图，判断销售阶段，推荐产品档位，生成回复话术。

输出必须是严格的 JSON 格式：
{
  "stage": "lead|qualified|proposal|negotiation|closed_won|closed_lost",
  "intent": "用户意图简述",
  "intent_score": 0.0-1.0的数字,
  "recommended_product": "推荐产品名",
  "recommended_tier": "entry|mid|premium",
  "talking_points": ["话术要点1", "话术要点2"],
  "response": "给用户的回复话术",
  "follow_up_action": "下一步动作",
  "quality_score": 质量评分(1-10)
}"""


class ShopAgency(BaseAgency):
    agency_id = "shop"
    trigger_keywords = ["报价", "收费", "合作", "咨询", "成交", "私信", "怎么买", "价格", "感兴趣", "报名", "多少钱", "靠谱吗"]
    approval_level = "low"
    cost_level = "low"

    def __init__(self):
        super().__init__()
        self._load_prompt()
        self._load_sqlite()

    def _load_sqlite(self):
        try:
            from molib.infra.memory.sqlite_client import SQLiteClient
            self._db = SQLiteClient()
        except ImportError:
            self._db = None

    def _load_prompt(self):
        prompt_path = Path(__file__).parent / "prompts" / "sales.txt"
        if prompt_path.exists():
            self._prompt_text = prompt_path.read_text(encoding="utf-8")
        else:
            self._prompt_text = ""

    def _parse_sales_json(self, text: str) -> dict:
        """解析销售 JSON 输出，失败时提供默认值"""
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
        # 默认回退
        return {
            "stage": "lead",
            "intent": text[:100],
            "intent_score": 0.3,
            "recommended_product": "AI副业入门班",
            "recommended_tier": "entry",
            "talking_points": ["了解需求", "介绍产品"],
            "response": text[:500],
            "follow_up_action": "继续沟通",
            "quality_score": 5.0,
        }

    def _detect_intent_level(self, message: str) -> str:
        """基于关键词快速检测用户意向层级"""
        msg = message.lower()
        high = ["报名", "付款", "买", "下单", "怎么支付", "确定"]
        mid = ["价格", "收费", "多少钱", "报价", "收费", "贵不贵"]
        low = ["了解", "咨询", "看看", "感兴趣"]
        if any(k in msg for k in high):
            return "high"
        if any(k in msg for k in mid):
            return "mid"
        if any(k in msg for k in low):
            return "low"
        return "unknown"

    async def execute(self, task: Task) -> AgencyResult:
        self.load_sop()
        sop_prompt = self.get_sop_prompt()
        user_msg = task.payload.get("message", task.payload.get("description", ""))
        history = task.payload.get("history", [])
        intent_level = self._detect_intent_level(user_msg)

        # 查询历史销售记录
        history_info = ""
        if self._db:
            try:
                memories = await self._db.retrieve_memory(
                    key="shop_sale", scenario="transactional", namespace="shop", limit=3
                )
                if memories:
                    history_info = "\n历史销售参考:\n" + "\n".join(
                        f"- {m['data'].get('recommended_product', 'unknown')}" for m in memories
                    )
            except Exception:
                pass

        history_text = ""
        if history:
            history_text = "\n".join(
                f"{h['role']}: {h['content']}" for h in history[-5:]
            )

        prompt = (
            f"用户消息：{user_msg}\n"
            f"用户意向层级：{intent_level}\n"
            f"历史对话（最近5条）：\n{history_text or '（无）'}"
            f"{history_info}"
        )
        if self._prompt_text:
            prompt = f"{self._prompt_text}\n\n{prompt}"
        if sop_prompt:
            prompt = f"请遵循以下SOP规范：\n{sop_prompt}\n\n{prompt}"

        start = time.time()
        res = await self.router.call_async(
            prompt=prompt, system=SALES_SYSTEM_PROMPT,
            task_type="sales", team="shop",
        )
        parsed = self._parse_sales_json(res.get("text", ""))

        score = parsed.get("quality_score", 5.0)

        # 持久化到 SQLite
        if self._db:
            try:
                sale = SalesRecord(
                    id=f"shop_{int(time.time())}",
                    stage=parsed.get("stage", "lead"),
                    customer_msg=user_msg[:200],
                    intent_score=parsed.get("intent_score", 0.3),
                    recommended_product=parsed.get("recommended_product", ""),
                    response=parsed.get("response", ""),
                    quality_score=score,
                    created_at=time.time(),
                )
                await self._db.store_memory(
                    key=f"shop_sale_{sale.id}",
                    data=sale.to_dict(),
                    scenario="transactional",
                    namespace="shop"
                )
            except Exception:
                pass

        return AgencyResult(
            task_id=task.task_id, agency_id=self.agency_id, status="success",
            output={
                "stage": parsed.get("stage", "lead"),
                "intent_score": parsed.get("intent_score", 0.3),
                "recommended_product": parsed.get("recommended_product", ""),
                "recommended_tier": parsed.get("recommended_tier", "entry"),
                "response": parsed.get("response", ""),
                "talking_points": parsed.get("talking_points", []),
                "follow_up_action": parsed.get("follow_up_action", ""),
                "quality_score": score,
                "model_used": res.get("model", "unknown"),
            },
            cost=res.get("cost", 0.0),
            latency=round(time.time() - start, 2),
        )
