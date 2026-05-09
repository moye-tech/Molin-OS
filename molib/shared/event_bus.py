"""
墨麟OS — 轻量事件总线
=========================
蓝图概念代码化（替代Redis Pub/Sub）。

⚠️ 两个 EventBus 并存说明：
   - 本文件 (molib/shared/event_bus.py, 177行): 文件接力总线
     支持 ZeroMQ 和 JSON 文件降级模式，适合跨进程/跨会话事件传递。
   - molib/infra/event_bus.py (320行): 内存 Pub/Sub 总线
     使用内存处理器列表 + 可选文件持久化，适合进程内子公司间横向通信。
   两者不冲突：shared/event_bus.py 用于进程间/文件接力场景，
   infra/event_bus.py 用于进程内实时事件分发。未来可考虑合并。

使用 ZeroMQ（纯Python，无守护进程）实现子公司间实时事件通知。
当 ZeroMQ 不可用时，自动降级为 JSON 文件接力。

用法:
    bus = EventBus()
    await bus.publish("content_published", {"title": "xxx", "url": "..."})
    await bus.subscribe("content_published", handler_func)

无需外部服务，pip install pyzmq 或使用文件降级模式。
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("molin.event_bus")

# ── 降级模式：JSON文件接力 ──────────────────────────────────────────
# 当 ZeroMQ 不可用时，使用 ~/.hermes/events/ 目录进行文件级事件交换

EVENT_DIR = Path.home() / ".hermes" / "events"


class FileEventBus:
    """文件级事件总线（零依赖降级方案）"""

    def __init__(self, base_dir: Path = EVENT_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._subscriptions: dict[str, list[Callable]] = {}
        self._my_id = f"agent-{uuid.uuid4().hex[:8]}"

    async def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> str:
        """发布事件到文件总线"""
        event = {
            "id": f"evt-{uuid.uuid4().hex[:12]}",
            "type": event_type,
            "payload": payload or {},
            "source": self._my_id,
            "timestamp": time.time(),
        }
        # 写入事件文件
        event_file = self.base_dir / f"{event['id']}.json"
        event_file.write_text(json.dumps(event, ensure_ascii=False))
        logger.info("[EventBus] 发布事件: %s (%s)", event_type, event['id'])

        # 同时触发本地订阅者
        for handler in self._subscriptions.get(event_type, []):
            try:
                if callable(handler):
                    await handler(event)
            except Exception as e:
                logger.error("[EventBus] 订阅处理异常: %s", e)

        return event['id']

    async def subscribe(self, event_type: str, handler: Callable):
        """订阅事件类型"""
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(handler)
        logger.info("[EventBus] 订阅: %s (%d handlers)", event_type, len(self._subscriptions[event_type]))

    async def unsubscribe(self, event_type: str, handler: Callable | None = None):
        """取消订阅"""
        if event_type not in self._subscriptions:
            return
        if handler:
            self._subscriptions[event_type] = [
                h for h in self._subscriptions[event_type] if h is not handler
            ]
        else:
            self._subscriptions[event_type] = []

    async def poll(self, event_type: str | None = None, since: float = 0.0) -> list[dict]:
        """轮询新事件（替代Redis Pub/Sub的pull模式）"""
        events = []
        for f in sorted(self.base_dir.glob("*.json")):
            try:
                data = json.loads(f.read_text())
                if data["timestamp"] > since:
                    if event_type is None or data["type"] == event_type:
                        events.append(data)
            except Exception:
                continue
        return events

    async def cleanup(self, older_than: float = 3600):
        """清理过期事件（默认1小时以上）"""
        now = time.time()
        cleaned = 0
        for f in self.base_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                if now - data["timestamp"] > older_than:
                    f.unlink()
                    cleaned += 1
            except Exception:
                f.unlink(missing_ok=True)
                cleaned += 1
        if cleaned > 0:
            logger.info("[EventBus] 清理了 %d 个过期事件", cleaned)
        return cleaned


# ── 自动选择总线实现 ──────────────────────────────────────────────────

EventBusImpl = FileEventBus  # 默认为文件总线

try:
    import zmq
    HAVE_ZMQ = True
except ImportError:
    HAVE_ZMQ = False


class ZMQEventBus:
    """ZeroMQ 事件总线（高性能，需要 pyzmq）"""

    def __init__(self, pub_endpoint: str = "ipc:///tmp/molin_event_bus"):
        self._pub_endpoint = pub_endpoint
        self._context = zmq.Context()
        self._publisher = self._context.socket(zmq.PUB)
        self._publisher.bind(pub_endpoint)
        self._subscriptions: dict[str, list[Callable]] = {}
        self._my_id = f"agent-{uuid.uuid4().hex[:8]}"
        logger.info("[ZMQEventBus] 初始化: %s", pub_endpoint)

    async def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> str:
        event = {
            "id": f"evt-{uuid.uuid4().hex[:12]}",
            "type": event_type,
            "payload": payload or {},
            "source": self._my_id,
            "timestamp": time.time(),
        }
        self._publisher.send_json(event)
        logger.debug("[ZMQEventBus] 发布: %s", event_type)
        return event['id']

    async def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(handler)

    async def unsubscribe(self, event_type: str, handler: Callable | None = None):
        if event_type not in self._subscriptions:
            return
        if handler:
            self._subscriptions[event_type] = [h for h in self._subscriptions[event_type] if h is not handler]
        else:
            self._subscriptions[event_type] = []

    async def poll(self, event_type: str | None = None, since: float = 0.0) -> list[dict]:
        # ZMQ 模式不轮询，使用订阅回调
        return []

    async def cleanup(self, older_than: float = 3600):
        return 0


def create_event_bus() -> FileEventBus | ZMQEventBus:
    """根据环境创建最佳事件总线"""
    if HAVE_ZMQ:
        logger.info("[EventBus] 使用 ZeroMQ 事件总线")
        return ZMQEventBus()
    logger.info("[EventBus] 使用文件事件总线（零依赖）")
    return FileEventBus()
