"""
XianyuListener v6.6 — 闲鱼接单自动化 Worker
定时轮询 + 消息监听 → CS处理 → BD报价 → 飞书通知
"""

from __future__ import annotations

import os
import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


# ── 消息模型 ──

@dataclass
class XianyuMessage:
    msg_id: str
    from_user: str
    to_user: str
    content: str
    item_id: str = ""
    item_title: str = ""
    timestamp: float = field(default_factory=time.time)
    conversation_id: str = ""


@dataclass
class DealSignal:
    detected: bool
    signal_type: str = ""       # "purchase_intent", "price_confirm", "deal_done"
    confidence: float = 0.0
    suggested_action: str = ""  # "quote", "close_deal", "notify_boss"


# ── 上下文记忆 ──

class ConversationMemory:
    """同一买家多轮对话上下文"""

    def __init__(self, max_history: int = 20):
        self._conversations: Dict[str, List[Dict[str, str]]] = {}
        self._max_history = max_history

    def add_turn(self, conv_id: str, role: str, content: str):
        if conv_id not in self._conversations:
            self._conversations[conv_id] = []
        self._conversations[conv_id].append({"role": role, "content": content, "time": time.time()})
        if len(self._conversations[conv_id]) > self._max_history:
            self._conversations[conv_id] = self._conversations[conv_id][-self._max_history:]

    def get_context(self, conv_id: str, limit: int = 10) -> str:
        turns = self._conversations.get(conv_id, [])[-limit:]
        lines = []
        for t in turns:
            name = "买家" if t["role"] == "buyer" else "系统"
            lines.append(f"{name}: {t['content'][:200]}")
        return "\n".join(lines)

    def is_first_contact(self, conv_id: str) -> bool:
        return conv_id not in self._conversations or len(self._conversations[conv_id]) == 0


# ── 成交信号检测 ──

class DealSignalDetector:
    """检测买家是否发出成交信号"""

    BUY_SIGNALS = [
        "成交", "好的", "怎么交易", "怎么付款", "我要了",
        "多少钱", "最低多少", "便宜点", "包邮吗",
        "发链接", "拍下", "下单", "链接给我",
        "ok", "OK", "好", "行", "可以",
        "how much", "buy", "purchase",
    ]

    REFUND_SIGNALS = [
        "退款", "退钱", "不要了", "退货", "取消",
        "有问题", "不满意", "投诉",
    ]

    def detect(self, message: str, context: str = "") -> DealSignal:
        msg_lower = message.lower()

        # 退款信号优先
        for sig in self.REFUND_SIGNALS:
            if sig in msg_lower:
                return DealSignal(
                    detected=True,
                    signal_type="refund_request",
                    confidence=0.9,
                    suggested_action="escalate_to_approval",
                )

        # 成交信号
        for sig in self.BUY_SIGNALS:
            if sig in msg_lower:
                return DealSignal(
                    detected=True,
                    signal_type="purchase_intent",
                    confidence=0.75,
                    suggested_action="quote_or_close",
                )

        return DealSignal(detected=False)


# ── Worker 主类 ──

class XianyuListener:
    """闲鱼消息监听器 — 定时轮询 + 消息处理流水线"""

    def __init__(self):
        self.memory = ConversationMemory()
        self.detector = DealSignalDetector()
        self._running = False
        self._poll_interval = 30  # 秒

    async def process_message(self, msg: XianyuMessage) -> Dict[str, Any]:
        """处理单条闲鱼消息，返回处理结果"""

        conv_id = msg.conversation_id or f"{msg.from_user}:{msg.item_id}"

        # 1. 上下文记忆
        is_first = self.memory.is_first_contact(conv_id)
        self.memory.add_turn(conv_id, "buyer", msg.content)
        history = self.memory.get_context(conv_id)

        # 2. 成交信号检测
        deal = self.detector.detect(msg.content, history)

        # 3. 高风险检测 → 审批升级
        if deal.signal_type == "refund_request":
            return {
                "action": "escalate",
                "reason": "refund_detected",
                "conversation_id": conv_id,
                "message": msg.content[:200],
                "needs_approval": True,
            }

        # 4. 首问 → 基础回复模板
        if is_first:
            return {
                "action": "first_respond",
                "conversation_id": conv_id,
                "item_id": msg.item_id,
                "suggested_reply": self._first_reply(msg),
            }

        # 5. 成交信号 → 触发报价/成交流程
        if deal.detected:
            return {
                "action": deal.suggested_action,
                "conversation_id": conv_id,
                "deal_signal": deal.signal_type,
                "confidence": deal.confidence,
                "needs_bd_quote": True,
            }

        # 6. 普通跟进
        return {
            "action": "follow_up",
            "conversation_id": conv_id,
            "suggested_reply": self._follow_up_reply(msg, history),
        }

    def _first_reply(self, msg: XianyuMessage) -> str:
        item = msg.item_title or "商品"
        return (
            f"你好，关于「{item[:20]}」有什么可以帮你的？\n"
            f"可以直接告诉我你的需求，我会尽快回复～"
        )

    def _follow_up_reply(self, msg: XianyuMessage, history: str) -> str:
        return f"收到你的消息。关于这个问题，让我帮你确认一下～"

    # ── 轮询循环 ──

    async def start_polling(self, redis_client=None):
        """启动定时轮询（在独立协程中运行）"""
        self._running = True
        logger.info(f"[Xianyu] 开始轮询，间隔 {self._poll_interval}s")

        while self._running:
            try:
                # 从 Redis 读取待处理消息
                if redis_client:
                    raw = await redis_client.lpop("xianyu:incoming_queue")
                    if raw:
                        data = json.loads(raw)
                        msg = XianyuMessage(**data)
                        result = await self.process_message(msg)
                        await redis_client.publish(
                            "xianyu:processed",
                            json.dumps(result, ensure_ascii=False),
                        )
            except Exception as e:
                logger.error(f"[Xianyu] 轮询异常: {e}")

            await asyncio.sleep(self._poll_interval)

    def stop(self):
        self._running = False
        logger.info("[Xianyu] 轮询已停止")


# 全局单例
_listener: Optional[XianyuListener] = None


def get_xianyu_listener() -> XianyuListener:
    global _listener
    if _listener is None:
        _listener = XianyuListener()
    return _listener
