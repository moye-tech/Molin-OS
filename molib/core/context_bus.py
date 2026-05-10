"""
TaskContextBus — 跨 Worker 轻量级上下文共享总线。

设计原则：
- 仅存储摘要，不存储完整输出（最大 500 字符/条目）
- 按 task_id 隔离命名空间
- 内存级访问，零延迟
- 自动 TTL 清理（任务完成后清除）
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from loguru import logger


class TaskContextBus:
    """跨 Worker/Manager 的轻量级上下文总线。"""

    MAX_ENTRY_LENGTH = 500
    _instance: Optional[TaskContextBus] = None

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}

    @classmethod
    def get_instance(cls) -> TaskContextBus:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def write(self, task_id: str, key: str, value: Any) -> None:
        """写入上下文条目，自动截断到 MAX_ENTRY_LENGTH。"""
        if task_id not in self._store:
            self._store[task_id] = {}
            self._timestamps[task_id] = time.time()
        if isinstance(value, str) and len(value) > self.MAX_ENTRY_LENGTH:
            value = value[:self.MAX_ENTRY_LENGTH] + "..."
        self._store[task_id][key] = value
        logger.debug(f"[ContextBus] write {task_id}.{key} ({len(str(value))} chars)")

    def read(self, task_id: str, key: str) -> Optional[Any]:
        """读取指定 key 的上下文。"""
        return self._store.get(task_id, {}).get(key)

    def get_relevant_context(self, task_id: str) -> Dict[str, Any]:
        """获取指定任务的所有上下文条目。"""
        return self._store.get(task_id, {}).copy()

    def get_all_context(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活跃任务的上下文。"""
        return {k: v.copy() for k, v in self._store.items()}

    def clear(self, task_id: str) -> None:
        """任务完成后清除上下文。"""
        self._store.pop(task_id, None)
        self._timestamps.pop(task_id, None)

    def clear_expired(self, max_age_seconds: int = 3600) -> int:
        """清除超过最大存活时间的上下文条目，返回清除数量。"""
        now = time.time()
        expired = [
            tid for tid, ts in self._timestamps.items()
            if now - ts > max_age_seconds
        ]
        for tid in expired:
            self.clear(tid)
        if expired:
            logger.info(f"[ContextBus] Cleared {len(expired)} expired contexts")
        return len(expired)


def get_context_bus() -> TaskContextBus:
    return TaskContextBus.get_instance()
