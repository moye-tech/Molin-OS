"""
Redis Pub/Sub 事件总线 — 子公司间直通通信
让子公司可以发布和订阅事件，无需每次通过 CEO 中转。
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Awaitable
from loguru import logger

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


EventCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class EventBus:
    """基于 Redis Pub/Sub 的子公司间事件总线"""

    CHANNEL_PREFIX = "hermes:events:"

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.subscriptions: Dict[str, List[Dict[str, Any]]] = {}
        self._listener_task: Optional[asyncio.Task] = None
        self._pubsub = None
        self.enabled = REDIS_AVAILABLE and self.redis is not None
        self.metrics = {"published": 0, "received": 0, "errors": 0}

    async def publish(self, event_type: str, data: Dict[str, Any], source_agency: str):
        """发布事件到总线"""
        if not self.enabled:
            logger.debug(f"[EventBus] 未启用，跳过发布: {event_type}")
            return

        channel = f"{self.CHANNEL_PREFIX}{event_type}"
        message = json.dumps({
            "event_type": event_type,
            "source_agency": source_agency,
            "data": data,
            "timestamp": __import__("time").time(),
        }, ensure_ascii=False)

        try:
            await self.redis.publish(channel, message)
            self.metrics["published"] += 1
            logger.info(f"[EventBus] PUBLISH {event_type} from {source_agency}")
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"[EventBus] 发布失败 {event_type}: {e}")

    def subscribe(self, event_type: str, callback: EventCallback, subscriber_agency: str):
        """注册事件订阅"""
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append({
            "callback": callback,
            "agency": subscriber_agency,
        })
        logger.info(f"[EventBus] SUBSCRIBE {subscriber_agency} → {event_type}")

    async def start_listener(self):
        """启动后台事件监听协程"""
        if not self.enabled:
            logger.info("[EventBus] Redis 不可用，监听器未启动")
            return

        if not self.subscriptions:
            logger.info("[EventBus] 无订阅，监听器未启动")
            return

        self._pubsub = self.redis.pubsub()
        channels = [f"{self.CHANNEL_PREFIX}{et}" for et in self.subscriptions]
        await self._pubsub.subscribe(*channels)

        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info(f"[EventBus] 监听器已启动，频道数: {len(channels)}")

    async def _listen_loop(self):
        """后台监听循环"""
        try:
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    event_type = data.get("event_type", "")
                    self.metrics["received"] += 1

                    callbacks = self.subscriptions.get(event_type, [])
                    for sub in callbacks:
                        try:
                            await sub["callback"](data)
                        except Exception as e:
                            self.metrics["errors"] += 1
                            logger.error(f"[EventBus] 回调执行失败 {sub['agency']}: {e}")

                except json.JSONDecodeError:
                    logger.warning("[EventBus] 消息解析失败")
        except asyncio.CancelledError:
            logger.info("[EventBus] 监听器已停止")
        except Exception as e:
            logger.error(f"[EventBus] 监听循环异常: {e}")

    async def stop_listener(self):
        """停止监听器"""
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

    def get_metrics(self) -> Dict[str, Any]:
        return {**self.metrics,
                "subscriptions_count": sum(len(v) for v in self.subscriptions.values()),
                "enabled": self.enabled}


# 全局单例
_event_bus_instance: Optional[EventBus] = None

async def get_event_bus(redis_client=None) -> EventBus:
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus(redis_client)
    return _event_bus_instance
