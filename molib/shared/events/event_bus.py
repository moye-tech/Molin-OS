"""
跨子公司事件总线 — FileEventBus + MemEventBus
=============================================

基于文件的轻量事件系统，支持：
- 发布/订阅模式：publish() / subscribe() / unsubscribe()
- ACL 隔离：事件只对授权子公司可见
- 内存降级：无文件系统权限时自动切换到内存模式
- 查询：get_events(event_type, since) 按时间和类型查询
- 清理：cleanup() 清理过期事件

存储位置：~/.hermes/events/

用法:
    from molib.shared.events import FileEventBus

    bus = FileEventBus()
    await bus.publish("task_completed", "content_writer", {"task_id": "xxx"})
    events = bus.get_events("task_completed", since=0.0)
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("molin.events")

# ── 事件存储目录 ──────────────────────────────────────────────────
EVENT_DIR = Path.home() / ".hermes" / "events"

# ── ACL: 子公司可见性映射 ─────────────────────────────────────────
# key = 子公司ID，value = 对其可见的子公司ID集合
# 空集合 = 对所有子公司可见（公开事件）
DEFAULT_ACL: dict[str, set[str]] = {
    # VP营销 彼此可见
    "content_writer": {"ip_manager", "designer", "short_video", "voice_actor", "ceo"},
    "ip_manager": {"content_writer", "designer", "short_video", "voice_actor", "ceo"},
    "designer": {"content_writer", "ip_manager", "short_video", "ceo"},
    "short_video": {"content_writer", "ip_manager", "voice_actor", "ceo"},
    "voice_actor": {"content_writer", "short_video", "ceo"},
    # VP运营
    "crm": {"ecommerce", "customer_service", "data_analyst", "ceo"},
    "customer_service": {"crm", "ecommerce", "ceo"},
    "ecommerce": {"crm", "customer_service", "ceo"},
    "education": {"knowledge", "content_writer", "ceo"},
    # VP技术
    "developer": {"ops", "security", "auto_dream", "ceo"},
    "ops": {"developer", "security", "ceo"},
    "security": {"developer", "ops", "ceo"},
    "auto_dream": {"developer", "ceo"},
    # VP财务
    "finance": {"ceo", "trading"},
    "trading": {"finance", "research", "ceo"},
    # VP战略
    "bd": {"research", "global_marketing", "ceo"},
    "global_marketing": {"bd", "research", "content_writer", "ceo"},
    "research": {"bd", "global_marketing", "knowledge", "ceo"},
    # 共同服务
    "legal": {"ceo"},
    "knowledge": {"education", "research", "ceo"},
    "data_analyst": {"crm", "ecommerce", "research", "ceo"},
    # CEO 可见全部
    "ceo": {"*"},
}


@dataclass
class EventEnvelope:
    """事件信封 — 统一的事件数据结构"""
    id: str = ""
    type: str = ""
    source: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    acl_visible_to: list[str] = field(default_factory=list)
    ttl_seconds: float = 3600.0  # 默认1小时过期

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EventEnvelope":
        return cls(**{k: data.get(k, cls.__dataclass_fields__[k].default)
                       for k in cls.__dataclass_fields__})


class FileEventBus:
    """基于文件的事件总线（零依赖，跨进程）

    特性：
    - 事件写入 ~/.hermes/events/ 下的JSON文件
    - ACL隔离：订阅者只能看到被授权的事件
    - 支持异步发布/订阅
    - 内存回调 + 文件持久化双轨
    """

    def __init__(self, base_dir: Path = EVENT_DIR):
        self.base_dir = base_dir
        self._subscriptions: dict[str, list[Callable]] = {}
        self._my_id = f"agent-{uuid.uuid4().hex[:8]}"
        self._my_source: str = "ceo"  # 发布时的默认源身份
        self._in_memory_events: list[dict] = []  # 内存降级备份
        self._use_fs: bool = True
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            # 验证可写
            test_file = self.base_dir / ".hermes_write_test"
            test_file.write_text("ok")
            test_file.unlink()
        except (OSError, PermissionError):
            logger.warning("[FileEventBus] 文件系统不可写，降级为内存模式")
            self._use_fs = False

    # ── 身份设置 ──────────────────────────────────────────────────
    def set_source(self, source: str) -> None:
        """设置发布事件的源身份（子公司ID）"""
        self._my_source = source

    # ── ACL 辅助 ───────────────────────────────────────────────────
    def _resolve_acl_visible(self, source: str) -> list[str]:
        """从ACL映射中解析对哪些子公司可见"""
        return _resolve_acl_for_source(source)

    def _can_see(self, subscriber_source: str, event_visible: list[str]) -> bool:
        """检查订阅者是否有权看到事件"""
        if "*" in event_visible:
            return True
        if not event_visible:
            return True  # 无ACL = 公开
        return subscriber_source in event_visible

    # ── 发布 ───────────────────────────────────────────────────────
    def publish(self, event_type: str, source: str | None = None,
                payload: dict[str, Any] | None = None,
                ttl_seconds: float = 3600.0) -> str:
        """
        发布事件到文件总线。

        Args:
            event_type: 事件类型（如 "task_completed"）
            source: 事件源子公司ID（默认使用初始化时设置的身份）
            payload: 事件载荷
            ttl_seconds: 事件存活时间

        Returns:
            事件ID
        """
        source = source or self._my_source
        event = {
            "id": f"evt-{uuid.uuid4().hex[:12]}",
            "type": event_type,
            "source": source,
            "payload": payload or {},
            "timestamp": time.time(),
            "acl_visible_to": self._resolve_acl_visible(source),
            "ttl_seconds": ttl_seconds,
        }

        # 持久化到文件（如果可以）
        if self._use_fs:
            try:
                event_file = self.base_dir / f"{event['id']}.json"
                event_file.write_text(
                    json.dumps(event, ensure_ascii=False, indent=2))
                logger.debug("[FileEventBus] 发布事件: %s (%s) → %s",
                             event_type, event['id'], event_file)
            except OSError as e:
                logger.error("[FileEventBus] 文件写入失败，存入内存: %s", e)
                self._in_memory_events.append(event)
        else:
            self._in_memory_events.append(event)

        # 触发本地订阅回调
        self._notify_subscribers(event)

        return event["id"]

    async def publish_async(self, event_type: str, source: str | None = None,
                            payload: dict[str, Any] | None = None,
                            ttl_seconds: float = 3600.0) -> str:
        """异步发布（兼容 async 调用约定）"""
        return self.publish(event_type, source, payload, ttl_seconds)

    # ── 订阅 ───────────────────────────────────────────────────────
    def subscribe(self, event_type: str,
                  callback: Callable[[dict], Any],
                  subscriber_source: str = "ceo") -> None:
        """
        订阅指定类型的事件。

        Args:
            event_type: 事件类型（如 "task_completed"）
            callback: 回调函数 fn(event_dict)
            subscriber_source: 订阅者的子公司ID（用于ACL过滤）
        """
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []

        # 包装回调以添加ACL过滤
        original_cb = callback

        def acl_wrapper(evt: dict) -> None:
            visible = evt.get("acl_visible_to", [])
            if self._can_see(subscriber_source, visible):
                original_cb(evt)
            else:
                logger.debug("[FileEventBus] ACL 过滤: %s 不可见事件 %s",
                             subscriber_source, evt.get("id"))

        acl_wrapper._original = original_cb  # 用于取消订阅时匹配
        self._subscriptions[event_type].append(acl_wrapper)
        logger.info("[FileEventBus] 订阅: %s (handlers: %d)",
                     event_type, len(self._subscriptions[event_type]))

    async def subscribe_async(self, event_type: str,
                              callback: Callable[[dict], Any],
                              subscriber_source: str = "ceo") -> None:
        """异步订阅（兼容 async 调用约定）"""
        self.subscribe(event_type, callback, subscriber_source)

    def unsubscribe(self, event_type: str,
                    callback: Callable[[dict], Any] | None = None) -> None:
        """取消订阅"""
        if event_type not in self._subscriptions:
            return
        if callback is None:
            self._subscriptions[event_type] = []
        else:
            self._subscriptions[event_type] = [
                h for h in self._subscriptions[event_type]
                if getattr(h, '_original', h) is not callback
            ]

    async def unsubscribe_async(self, event_type: str,
                                callback: Callable[[dict], Any] | None = None) -> None:
        """异步取消订阅"""
        self.unsubscribe(event_type, callback)

    # ── 回调触发 ──────────────────────────────────────────────────
    def _notify_subscribers(self, event: dict) -> None:
        """通知所有匹配的订阅者"""
        event_type = event["type"]
        handlers = self._subscriptions.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("[FileEventBus] 回调异常: %s", e)

    # ── 查询 ───────────────────────────────────────────────────────
    def get_events(self, event_type: str | None = None,
                   since: float = 0.0,
                   source: str | None = None,
                   subscriber_source: str = "ceo",
                   limit: int = 100) -> list[dict]:
        """
        查询事件。

        Args:
            event_type: 事件类型过滤（None = 全部）
            since: 起始时间戳
            source: 事件源过滤（None = 全部）
            subscriber_source: 查询者的子公司ID（用于ACL过滤）
            limit: 最大返回数

        Returns:
            事件列表（按时间倒序）
        """
        events: list[dict] = []

        # 从文件读取
        if self._use_fs:
            try:
                for f in sorted(self.base_dir.glob("*.json"),
                                key=lambda p: p.stat().st_mtime,
                                reverse=True):
                    if f.name == ".hermes_write_test":
                        continue
                    try:
                        data = json.loads(f.read_text())
                    except Exception:
                        continue

                    # ACL 过滤
                    visible = data.get("acl_visible_to", [])
                    if not self._can_see(subscriber_source, visible):
                        continue

                    # 时间过滤
                    if data.get("timestamp", 0) <= since:
                        continue

                    # 类型过滤
                    if event_type is not None and data.get("type") != event_type:
                        continue

                    # 源过滤
                    if source is not None and data.get("source") != source:
                        continue

                    events.append(data)
                    if len(events) >= limit:
                        break
            except OSError:
                pass

        # 从内存读取
        for evt in self._in_memory_events:
            if evt.get("timestamp", 0) <= since:
                continue
            if event_type is not None and evt.get("type") != event_type:
                continue
            if source is not None and evt.get("source") != source:
                continue
            visible = evt.get("acl_visible_to", [])
            if not self._can_see(subscriber_source, visible):
                continue
            events.append(evt)

        events.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
        return events[:limit]

    def poll(self, event_type: str | None = None,
             since: float = 0.0) -> list[dict]:
        """轮询新事件（向后兼容别名）"""
        return self.get_events(event_type=event_type, since=since)

    async def poll_async(self, event_type: str | None = None,
                         since: float = 0.0) -> list[dict]:
        """异步轮询"""
        return self.poll(event_type, since)

    # ── 清理 ───────────────────────────────────────────────────────
    def cleanup(self, older_than: float = 3600.0) -> int:
        """
        清理过期事件。

        Args:
            older_than: 超过多少秒（默认1小时）

        Returns:
            清理的事件数
        """
        cleaned = 0
        now = time.time()

        # 文件清理
        if self._use_fs:
            try:
                for f in self.base_dir.glob("*.json"):
                    if f.name == ".hermes_write_test":
                        continue
                    try:
                        data = json.loads(f.read_text())
                        if now - data.get("timestamp", 0) > older_than:
                            f.unlink()
                            cleaned += 1
                    except Exception:
                        f.unlink(missing_ok=True)
                        cleaned += 1
            except OSError:
                pass

        # 内存清理
        before = len(self._in_memory_events)
        self._in_memory_events = [
            e for e in self._in_memory_events
            if now - e.get("timestamp", 0) <= older_than
        ]
        cleaned += before - len(self._in_memory_events)

        if cleaned > 0:
            logger.info("[FileEventBus] 清理了 %d 个过期事件", cleaned)
        return cleaned

    async def cleanup_async(self, older_than: float = 3600.0) -> int:
        """异步清理"""
        return self.cleanup(older_than)

    # ── 统计 ───────────────────────────────────────────────────────
    def stats(self) -> dict:
        """返回事件总线统计"""
        file_count = 0
        if self._use_fs:
            try:
                file_count = len(list(
                    f for f in self.base_dir.glob("*.json")
                    if f.name != ".hermes_write_test"
                ))
            except OSError:
                pass
        return {
            "mode": "file" if self._use_fs else "memory",
            "event_dir": str(self.base_dir),
            "file_events": file_count,
            "memory_events": len(self._in_memory_events),
            "subscriptions": sum(len(v) for v in self._subscriptions.values()),
            "acls_configured": len(DEFAULT_ACL),
        }


# ── 纯内存事件总线（降级/测试用）────────────────────────────────

class MemEventBus:
    """纯内存事件总线 — 当文件系统不可用时的完全降级方案

    特点：
    - 所有事件仅在内存中，进程重启即丢失
    - 不依赖任何文件系统
    - 适合单元测试和临时场景
    """

    def __init__(self):
        self._subscriptions: dict[str, list[Callable]] = {}
        self._events: list[dict] = []
        self._my_id = f"agent-{uuid.uuid4().hex[:8]}"
        self._my_source = "ceo"

    def set_source(self, source: str) -> None:
        self._my_source = source

    def publish(self, event_type: str, source: str | None = None,
                payload: dict[str, Any] | None = None,
                ttl_seconds: float = 3600.0) -> str:
        source = source or self._my_source
        event = {
            "id": f"evt-{uuid.uuid4().hex[:12]}",
            "type": event_type,
            "source": source,
            "payload": payload or {},
            "timestamp": time.time(),
            "acl_visible_to": _resolve_acl_for_source(source),
            "ttl_seconds": ttl_seconds,
        }
        self._events.append(event)
        # 触发回调
        for handler in self._subscriptions.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error("[MemEventBus] 回调异常: %s", e)
        return event["id"]

    def subscribe(self, event_type: str,
                  callback: Callable[[dict], Any],
                  subscriber_source: str = "ceo") -> None:
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(callback)

    def unsubscribe(self, event_type: str,
                    callback: Callable[[dict], Any] | None = None) -> None:
        if event_type not in self._subscriptions:
            return
        if callback is None:
            self._subscriptions[event_type] = []
        else:
            self._subscriptions[event_type] = [
                h for h in self._subscriptions[event_type] if h is not callback
            ]

    def get_events(self, event_type: str | None = None,
                   since: float = 0.0,
                   source: str | None = None,
                   limit: int = 100) -> list[dict]:
        results = []
        for e in reversed(self._events):
            if e.get("timestamp", 0) <= since:
                continue
            if event_type is not None and e.get("type") != event_type:
                continue
            if source is not None and e.get("source") != source:
                continue
            results.append(e)
            if len(results) >= limit:
                break
        return results

    def cleanup(self, older_than: float = 3600.0) -> int:
        now = time.time()
        before = len(self._events)
        self._events = [e for e in self._events
                        if now - e.get("timestamp", 0) <= older_than]
        return before - len(self._events)

    def stats(self) -> dict:
        return {
            "mode": "memory",
            "events": len(self._events),
            "subscriptions": sum(len(v) for v in self._subscriptions.values()),
        }


# ── 工厂函数 ───────────────────────────────────────────────────────


def _resolve_acl_for_source(source: str) -> list[str]:
    """模块级 ACL 解析函数"""
    visible = DEFAULT_ACL.get(source, set())
    if "*" in visible:
        return ["*"]
    return sorted(visible)


def create_event_bus(prefer_file: bool = True) -> FileEventBus | MemEventBus:
    """根据环境创建最佳事件总线

    Args:
        prefer_file: True=优先文件模式，False=强制内存模式

    Returns:
        FileEventBus 或 MemEventBus
    """
    if prefer_file:
        bus = FileEventBus()
        if bus._use_fs:
            logger.info("[Events] 使用 FileEventBus (~/.hermes/events/)")
            return bus
        logger.info("[Events] FileEventBus 降级为内存模式")
        return bus  # FileEventBus 已自动降级

    logger.info("[Events] 使用 MemEventBus（纯内存）")
    return MemEventBus()


__all__ = [
    "FileEventBus",
    "MemEventBus",
    "create_event_bus",
    "EventEnvelope",
    "EVENT_DIR",
    "DEFAULT_ACL",
]
