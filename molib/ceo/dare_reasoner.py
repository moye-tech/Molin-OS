"""
墨麟OS — DARE 推理层 (DAREReasoningLayer)

在 IntentRouter 之前运行，为 CEO 决策增加情境理解。
从旧关键词匹配升级为 DARE 四步推理模型：
  D — Decompose（解构目标）
  A — Analyze（分析缺口）
  R — Route（智能编排）
  E — Elevate（超预期设计）

用法:
    from molib.ceo.dare_reasoner import DAREReasoningLayer, DAREResult

    dare_layer = DAREReasoningLayer(llm_client)
    result = await dare_layer.analyze(user_input, context)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import logging

logger = logging.getLogger("molin.ceo.dare")


# ═══════════════════════════════════════════════════════════════
# DARE 系统提示词（低成本推理，用 DeepSeek-chat 即可）
# ═══════════════════════════════════════════════════════════════

DARE_SYSTEM_PROMPT = """
你是墨麟AI集团CEO。收到任务时，用DARE框架推理：

D - Decompose: 这个任务成功完成时，结果应该是什么样子？评判标准是什么？
A - Analyze: 达成这个结果，需要哪些信息/能力，现在缺什么？
R - Route: 哪些Worker最适合填补缺口？串行还是并行？为什么这样组合？
E - Elevate: 基础需求之外，加什么能让结果超过预期？

输出格式（严格JSON）：
{
  "decompose": "目标解构（1-2句）",
  "gaps": ["缺口1", "缺口2", ...],
  "worker_plan": [
    {"worker": "Worker名", "reason": "为什么选他", "input": "需要什么输入", "parallel": true}
  ],
  "elevate": "超预期设计（1句）",
  "needs_research_first": false,
  "is_conversational": false
}

关键判断规则：
- is_conversational=true: 纯闲聊/情绪表达/简单确认 → 不需要Worker
- needs_research_first=true: 需要实时数据/市场信息 → 必须先调墨研竞情
- gaps为空且is_conversational=false → 纯内容创作类，可直接调墨笔文创
- 任何涉及金钱/发布/合同的任务 → gaps中必须包含"合规审查"
"""


# ═══════════════════════════════════════════════════════════════
# DARE 结果数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class DAREResult:
    """DARE推理结果"""
    decompose: str = ""
    gaps: list[str] = field(default_factory=list)
    worker_plan: list[dict] = field(default_factory=list)
    elevate: str = ""
    needs_research_first: bool = False
    is_conversational: bool = False

    @classmethod
    def conversational(cls) -> DAREResult:
        """快速创建闲聊结果"""
        return cls(is_conversational=True)

    @classmethod
    def from_json(cls, raw: dict) -> DAREResult:
        """从JSON创建"""
        return cls(
            decompose=raw.get("decompose", ""),
            gaps=raw.get("gaps", []),
            worker_plan=raw.get("worker_plan", []),
            elevate=raw.get("elevate", ""),
            needs_research_first=raw.get("needs_research_first", False),
            is_conversational=raw.get("is_conversational", False),
        )

    def to_dict(self) -> dict:
        return {
            "decompose": self.decompose,
            "gaps": self.gaps,
            "worker_plan": self.worker_plan,
            "elevate": self.elevate,
            "needs_research_first": self.needs_research_first,
            "is_conversational": self.is_conversational,
        }


# ═══════════════════════════════════════════════════════════════
# 闲聊快速判断（避免对简单的"好""谢谢"跑LLM推理）
# ═══════════════════════════════════════════════════════════════

_TRIVIAL_PATTERNS = {
    "好", "好的", "嗯", "行", "可以", "谢谢", "ok", "OK", "嗯嗯",
    "知道了", "明白了", "辛苦了", "哈哈", "不错", "厉害",
}


def is_trivial(user_input: str) -> bool:
    """快速判断输入是否为闲聊/确认类，不需要DARE推理"""
    text = user_input.strip().lower()
    # 超短确认
    if text in _TRIVIAL_PATTERNS or len(text) <= 2:
        return True
    # 纯表情/符号
    if all(c in "，。！？、👍😊😂❤️🙏🔥✅ " for c in text):
        return True
    return False


# ═══════════════════════════════════════════════════════════════
# DARE 推理层
# ═══════════════════════════════════════════════════════════════

class DAREReasoningLayer:
    """
    DARE推理层：在IntentRouter之前运行，为CEO决策增加情境理解。

    工作流程:
      1. 快速判断是否闲聊 → 直接返回 DAREResult(is_conversational=True)
      2. 用低成本模型（deepseek-chat）做DARE推理
      3. 返回结构化的任务理解
    """

    def __init__(self, llm_client):
        """
        Args:
            llm_client: LLMClient 实例
        """
        self.llm = llm_client

    async def analyze(
        self,
        user_input: str,
        context: dict | None = None,
    ) -> DAREResult:
        """
        对用户输入运行DARE推理，返回结构化的任务理解。

        Args:
            user_input: 用户输入文本
            context: 上下文信息

        Returns:
            DAREResult: 包含目标解构、缺口分析、Worker计划
        """
        # ── 快速判断：闲聊不需要DARE推理 ──
        if is_trivial(user_input):
            logger.debug("[DARE] 闲聊输入，跳过推理: %s", user_input[:50])
            return DAREResult.conversational()

        # ── 低成本DARE推理 ──
        try:
            prompt = (
                f"用户输入: {user_input}\n\n"
                f"系统当前能力:\n{self._get_context(context)}"
            )
            raw = await self.llm.chat_json(
                system=DARE_SYSTEM_PROMPT,
                user=prompt,
                model="deepseek-chat",  # 低成本，DARE推理不需要最强模型
            )

            if raw:
                result = DAREResult.from_json(raw)
                logger.info(
                    "[DARE] 推理完成: gaps=%d workers=%d needs_research=%s conversational=%s",
                    len(result.gaps),
                    len(result.worker_plan),
                    result.needs_research_first,
                    result.is_conversational,
                )
                return result
            else:
                logger.warning("[DARE] LLM返回空结果，使用默认")
                return DAREResult()

        except Exception as e:
            logger.error("[DARE] 推理失败: %s，降级到默认路由", e)
            return DAREResult()

    def _get_context(self, ctx: dict | None) -> str:
        """注入系统当前状态（余额、今日已完成的任务、最新数据）"""
        if not ctx:
            return "无最新快照"
        parts = []
        if "balance" in ctx:
            parts.append(f"当前余额: ¥{ctx['balance']}")
        if "today_tasks_completed" in ctx:
            parts.append(f"今日已完成任务: {ctx['today_tasks_completed']}")
        if "relay_status" in ctx:
            parts.append(f"飞轮状态: {ctx['relay_status']}")
        return "\n".join(parts) if parts else "无最新快照"
