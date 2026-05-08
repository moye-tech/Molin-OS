"""
EventBus v6.6 — 子公司横向事件总线（去Redis版）
标准化事件协议 + 内存 Pub/Sub，可选JSON文件持久化。
让子公司可以横向实时通信，CEO从微观调度中解放。

适配自 molin-os-ultra v6.6.0 infra/data_brain/event_bus.py
适配: 去掉Redis依赖 → 内存Pub/Sub; loguru → logging
"""
from __future__ import annotations

import json
import time
import asyncio
import os
import logging
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# ── 标准化事件协议 ──

@dataclass
class BusEvent:
    """总线事件"""
    event_type: str  # "order.created", "content.published", ...
    source: str  # 发布者 (agency_id)
    payload: Dict[str, Any]  # 事件载荷
    timestamp: float = field(default_factory=time.time)
    task_id: str = ""
    event_id: str = ""

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"evt_{int(self.timestamp)}_{self.source}"

    def to_json(self) -> str:
        return json.dumps(
            {
                "event_type": self.event_type,
                "source": self.source,
                "payload": self.payload,
                "timestamp": self.timestamp,
                "task_id": self.task_id,
                "event_id": self.event_id,
            },
            ensure_ascii=False,
        )

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
    ORDER_CREATED = "order.created"
    ORDER_CONFIRMED = "order.confirmed"
    ORDER_REFUND = "order.refund"
    CUSTOMER_MESSAGE = "customer.message"
    CONTENT_PUBLISHED = "content.published"
    CONTENT_APPROVED = "content.approved"
    CONTENT_REJECTED = "content.rejected"
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_REFUNDED = "payment.refunded"
    DAILY_REPORT = "finance.daily_report"
    QUOTE_GENERATED = "quote.generated"
    QUOTE_ACCEPTED = "quote.accepted"
    CREDENTIAL_EXPIRING = "system.credential_expiring"
    TASK_STUCK = "system.task_stuck"
    AGENCY_ERROR = "system.agency_error"
    AGENCY_HEALTH = "system.agency_health"
    SYSTEM_ALERT = "system.alert"


# ── 订阅声明 ──

AGENCY_SUBSCRIPTIONS: Dict[str, Dict[str, List[str]]] = {
    "cs": {
        "publish": [
            EventType.ORDER_CREATED,
            EventType.ORDER_CONFIRMED,
            EventType.CUSTOMER_MESSAGE,
        ],
        "subscribe": [EventType.QUOTE_ACCEPTED, EventType.CONTENT_PUBLISHED],
    },
    "bd": {
        "publish": [EventType.QUOTE_GENERATED, EventType.QUOTE_ACCEPTED],
        "subscribe": [EventType.ORDER_CREATED, EventType.ORDER_CONFIRMED],
    },
    "ip": {
        "publish": [
            EventType.CONTENT_PUBLISHED,
            EventType.CONTENT_APPROVED,
        ],
        "subscribe": [EventType.ORDER_CREATED],
    },
    "finance": {
        "publish": [EventType.PAYMENT_RECEIVED, EventType.DAILY_REPORT],
        "subscribe": [
            EventType.ORDER_CREATED,
            EventType.ORDER_CONFIRMED,
            EventType.ORDER_REFUND,
        ],
    },
    "data": {
        "publish": [],
        "subscribe": [
            EventType.ORDER_CREATED,
            EventType.CONTENT_PUBLISHED,
            EventType.PAYMENT_RECEIVED,
        ],
    },
    "knowledge": {
        "publish": [],
        "subscribe": [
            EventType.ORDER_CREATED,
            EventType.CONTENT_PUBLISHED,
        ],
    },
    "ops": {
        "publish": [EventType.AGENCY_HEALTH, EventType.SYSTEM_ALERT],
        "subscribe": [EventType.TASK_STUCK, EventType.AGENCY_ERROR],
    },
}


# ── 内存事件总线 ──

class EventBus:
    """子公司横向事件总线 — 内存 Pub/Sub + 可选文件持久化"""

    def __init__(self, persistence_dir: Optional[str] = None):
        self._handlers: Dict[str, List[Callable]] = {}
        self._listening = False
        self._event_log: List[Dict[str, Any]] = []  # 最近100条事件日志
        self._persistence_dir = persistence_dir
        if self._persistence_dir:
            Path(self._persistence_dir).mkdir(parents=True, exist_ok=True)

    # ── 发布 ──

    async def publish(self, event: BusEvent) -> bool:
        """发布事件到总线"""
        logger.debug(f"[EventBus] 发布: {event.event_type} ← {event.source}")
        await self.dispatch(event)

        # 记录事件日志
        self._event_log.append(
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source": event.source,
                "timestamp": event.timestamp,
                "payload_summary": str(event.payload)[:80],
            }
        )
        if len(self._event_log) > 100:
            self._event_log = self._event_log[-100:]

        # 可选文件持久化
        if self._persistence_dir:
            await self._persist_event(event)

        return True

    async def publish_quick(
        self,
        event_type: str,
        source: str,
        payload: Dict[str, Any],
        task_id: str = "",
    ):
        """快捷发布"""
        return await self.publish(
            BusEvent(
                event_type=event_type,
                source=source,
                payload=payload,
                task_id=task_id,
            )
        )

    # ── 订阅 ──

    def subscribe(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"[EventBus] 订阅: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """取消订阅"""
        handlers = self._handlers.get(event_type)
        if not handlers:
            return False
        try:
            handlers.remove(handler)
            return True
        except ValueError:
            return False

    async def dispatch(self, event: BusEvent):
        """分发事件到所有注册的处理器"""
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            return

        tasks = []
        for handler in handlers:
            tasks.append(
                asyncio.create_task(self._safe_call(handler, event))
            )
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_call(self, handler: Callable, event: BusEvent):
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                f"[EventBus] 处理失败: {event.event_type}, {e}"
            )

    # ── 持久化 ──

    async def _persist_event(self, event: BusEvent):
        """将事件持久化到文件"""
        if not self._persistence_dir:
            return
        date_str = time.strftime("%Y%m%d")
        log_dir = Path(self._persistence_dir) / date_str
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{event.event_type.replace('.', '_')}.jsonl"
        try:
            with open(log_file, "a") as f:
                f.write(event.to_json() + "\n")
        except Exception as e:
            logger.warning(f"[EventBus] 持久化失败: {e}")

    # ── 查询 ──

    def get_recent_events(
        self, event_type: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取最近的事件日志"""
        events = self._event_log
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        return events[-limit:]

    def get_handler_count(self) -> Dict[str, int]:
        """获取各事件类型的处理器数量"""
        return {et: len(hs) for et, hs in self._handlers.items()}

    # ── 标准工作流 ──

    def register_standard_workflows(self):
        """注册标准的横向事件流转规则"""

        @self._wrap_handler("ORDER_CREATED")
        async def on_order_created(event: BusEvent):
            logger.info(
                f"[Workflow] 新订单: {event.payload.get('item_title', '?')} "
                f"→ BD跟进 + Finance记账 + Knowledge归档"
            )

        @self._wrap_handler("ORDER_CONFIRMED")
        async def on_order_confirmed(event: BusEvent):
            logger.info(
                f"[Workflow] 订单确认: {event.payload.get('item_title', '?')} "
                f"→ Finance确认收款"
            )

        @self._wrap_handler("PAYMENT_RECEIVED")
        async def on_payment(event: BusEvent):
            amount = event.payload.get("amount", 0)
            logger.info(f"[Workflow] 收款: ¥{amount} → Data更新报表")

        @self._wrap_handler("CONTENT_PUBLISHED")
        async def on_content_published(event: BusEvent):
            logger.info(
                f"[Workflow] 内容发布: {event.payload.get('title', '?')} "
                f"→ Growth跟踪"
            )

        self.subscribe(EventType.ORDER_CREATED, on_order_created)
        self.subscribe(EventType.ORDER_CONFIRMED, on_order_confirmed)
        self.subscribe(EventType.PAYMENT_RECEIVED, on_payment)
        self.subscribe(EventType.CONTENT_PUBLISHED, on_content_published)

    def _wrap_handler(self, name: str):
        """包装处理器名（用于日志）"""
        return lambda f: setattr(f, "_handler_name", name) or f


# 全局单例
_bus: Optional[EventBus] = None


def get_event_bus(persistence_dir: Optional[str] = None) -> EventBus:
    """获取全局事件总线实例（单例）"""
    global _bus
    if _bus is None:
        _bus = EventBus(persistence_dir=persistence_dir)
        _bus.register_standard_workflows()
    return _bus
