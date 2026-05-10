"""
EventBus v6.6 — 子公司横向事件总线
标准化事件协议 + Pub/Sub，让子公司可以横向通信，CEO从微观调度中解放。
"""

from __future__ import annotations

import json
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from loguru import logger


# ── 标准化事件协议 ──

@dataclass
class BusEvent:
    event_type: str          # "order.created", "content.published", ...
    source: str              # 发布者 (agency_id)
    payload: Dict[str, Any]  # 事件载荷
    timestamp: float = field(default_factory=time.time)
    task_id: str = ""
    event_id: str = ""

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"evt_{int(self.timestamp)}_{self.source}"

    def to_json(self) -> str:
        return json.dumps({
            "event_type": self.event_type,
            "source": self.source,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "task_id": self.task_id,
            "event_id": self.event_id,
        }, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "BusEvent":
        d = json.loads(data)
        return cls(
            event_type=d["event_type"],
            source=d["source"],
            payload=d.get("payload", {}),
            timestamp=d.get("timestamp", time.time()),
            task_id=d.get("task_id", ""),
            event_id=d.get("event_id", ""),
        )


# ── 事件类型定义 ──

class EventType:
    """标准化事件类型常量"""
    # CS (客服)
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_REFUND = "order.refund"
    CUSTOMER_MESSAGE = "customer.message"

    # IP (内容)
    CONTENT_PUBLISHED = "content.published"
    CONTENT_APPROVED = "content.approved"
    CONTENT_REJECTED = "content.rejected"

    # Finance
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_REFUNDED = "payment.refunded"
    DAILY_REPORT = "finance.daily_report"

    # BD
    QUOTE_GENERATED = "quote.generated"
    QUOTE_ACCEPTED = "quote.accepted"

    # System
    CREDENTIAL_EXPIRING = "system.credential_expiring"
    TASK_STUCK = "system.task_stuck"
    AGENCY_ERROR = "system.agency_error"


# ── 订阅声明 ──

AGENCY_SUBSCRIPTIONS: Dict[str, Dict[str, List[str]]] = {
    "cs": {
        "publish": [EventType.ORDER_CREATED, EventType.ORDER_CONFIRMED, EventType.CUSTOMER_MESSAGE],
        "subscribe": [EventType.QUOTE_ACCEPTED, EventType.CONTENT_PUBLISHED],
    },
    "bd": {
        "publish": [EventType.QUOTE_GENERATED, EventType.QUOTE_ACCEPTED],
        "subscribe": [EventType.ORDER_CREATED, EventType.ORDER_CONFIRMED],
    },
    "ip": {
        "publish": [EventType.CONTENT_PUBLISHED, EventType.CONTENT_APPROVED],
        "subscribe": [EventType.ORDER_CREATED],
    },
    "finance": {
        "publish": [EventType.PAYMENT_RECEIVED, EventType.DAILY_REPORT],
        "subscribe": [EventType.ORDER_CREATED, EventType.ORDER_CONFIRMED, EventType.ORDER_REFUND],
    },
    "data": {
        "publish": [],
        "subscribe": [
            EventType.ORDER_CREATED, EventType.CONTENT_PUBLISHED,
            EventType.PAYMENT_RECEIVED,
        ],
    },
    "knowledge": {
        "publish": [],
        "subscribe": [EventType.ORDER_CREATED, EventType.CONTENT_PUBLISHED],
    },
    "growth": {
        "publish": [],
        "subscribe": [EventType.CONTENT_PUBLISHED, EventType.ORDER_CREATED],
    },
}


# ── 事件总线 ──

class EventBus:
    """子公司横向事件总线 — 基于 Redis Pub/Sub"""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._handlers: Dict[str, List[Callable]] = {}
        self._listening = False

    async def connect(self, redis_client):
        self._redis = redis_client
        logger.info("[EventBus] 已连接 Redis")

    # ── 发布 ──

    async def publish(self, event: BusEvent) -> bool:
        """发布事件到总线"""
        if not self._redis:
            logger.warning("[EventBus] Redis 未连接，无法发布")
            return False

        channel = f"bus:{event.event_type}"
        message = event.to_json()

        try:
            await self._redis.publish(channel, message)
            logger.debug(f"[EventBus] 发布: {event.event_type} ← {event.source}")
            return True
        except Exception as e:
            logger.error(f"[EventBus] 发布失败: {e}")
            return False

    async def publish_quick(
        self, event_type: str, source: str, payload: Dict[str, Any], task_id: str = ""
    ):
        """快捷发布"""
        return await self.publish(BusEvent(
            event_type=event_type, source=source, payload=payload, task_id=task_id,
        ))

    # ── 订阅 ──

    def subscribe(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"[EventBus] 订阅: {event_type}")

    async def dispatch(self, event: BusEvent):
        """分发事件到所有注册的处理器"""
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            return

        tasks = []
        for handler in handlers:
            tasks.append(asyncio.create_task(self._safe_call(handler, event)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(self, handler: Callable, event: BusEvent):
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"[EventBus] 处理失败: {event.event_type}, {e}")

    # ── 监听 ──

    async def listen(self):
        """启动事件监听（阻塞循环）"""
        if not self._redis:
            return
        self._listening = True
        logger.info("[EventBus] 开始监听")

        pubsub = self._redis.pubsub()
        channels = [f"bus:{et}" for et in self._handlers.keys()]
        if channels:
            await pubsub.subscribe(*channels)

        while self._listening:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                try:
                    event = BusEvent.from_json(message["data"])
                    await self.dispatch(event)
                except Exception as e:
                    logger.error(f"[EventBus] 消息解析失败: {e}")

    def stop(self):
        self._listening = False

    # ── 典型流转示例 ──

    def register_standard_workflows(self):
        """注册标准的横向事件流转规则"""

        # CS 完成接单 → BD 建立客户 + Finance 记账 + Knowledge 提取
        async def on_order_created(event: BusEvent):
            logger.info(
                f"[Workflow] 新订单: {event.payload.get('item_title', '?')} "
                f"→ BD跟进 + Finance记账 + Knowledge归档"
            )

        self.subscribe(EventType.ORDER_CREATED, on_order_created)
        self.subscribe(EventType.ORDER_CONFIRMED, on_order_created)

        # Finance 收款 → Data 更新报表
        async def on_payment(event: BusEvent):
            amount = event.payload.get("amount", 0)
            logger.info(f"[Workflow] 收款: ¥{amount} → Data更新报表")

        self.subscribe(EventType.PAYMENT_RECEIVED, on_payment)

        # 内容发布 → Growth 跟踪
        async def on_content_published(event: BusEvent):
            logger.info(
                f"[Workflow] 内容发布: {event.payload.get('title', '?')} → Growth跟踪"
            )

        self.subscribe(EventType.CONTENT_PUBLISHED, on_content_published)


# 全局单例
_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
        _bus.register_standard_workflows()
    return _bus
