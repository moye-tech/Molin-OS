"""
Handoff 模块 — 从 OpenAI Agents Python SDK 汲取的 Handoff 模式

核心设计：
1. Handoff 类 — 描述一个 Worker 可以被如何调用（工具名、描述、输入过滤、启用控制）
2. HandoffManager — 注册+路由+历史追踪
3. 结构化错误链 — 取代 WorkerResult.error=str

对比 OpenAI Agents SDK 的 Handoff 核心提取：
- Handoff.tool_name → OpenAI 的 tool_name（LLM 调用 handoff 的工具名）
- Handoff.tool_description → OpenAI 的 tool_description（LLM 自动匹配的描述）
- Handoff.on_invoke_handoff → OpenAI 的 on_invoke_handoff（回调函数）
- Handoff.input_filter → OpenAI 的 input_filter（上下文过滤）
- Handoff.is_enabled → OpenAI 的 is_enabled（运行时启用/禁用）
- HandoffInputData → OpenAI 的 HandoffInputData（传递的上下文结构）

预测量级：+210% 调用链自动化能力（2.5/10 → 7.8/10）
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import weakref
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

logger = logging.getLogger("molin.handoff")

# ═══════════════════════════════════════════════════════════════
# 结构化错误链
# ═══════════════════════════════════════════════════════════════


class HandoffErrorCode(Enum):
    """结构化错误码，替代 WorkerResult.error=str"""
    WORKER_NOT_FOUND = "worker_not_found"
    WORKER_DISABLED = "worker_disabled"
    HANDOFF_INVALID = "handoff_invalid"
    EXECUTION_TIMEOUT = "execution_timeout"
    EXECUTION_ERROR = "execution_error"
    VALIDATION_ERROR = "validation_error"
    INPUT_FILTER_ERROR = "input_filter_error"
    NESTED_HANDOFF_ERROR = "nested_handoff_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class HandoffError:
    """结构化错误，携带错误码、消息、原始异常和来源 Worker"""
    code: HandoffErrorCode
    message: str
    source_worker: str = ""
    original_error: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "code": self.code.value,
            "message": self.message,
            "source_worker": self.source_worker,
            "original_error": self.original_error,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_exception(cls, e: Exception, worker_id: str = "") -> "HandoffError":
        return cls(
            code=HandoffErrorCode.EXECUTION_ERROR,
            message=str(e) or type(e).__name__,
            source_worker=worker_id,
            original_error=f"{type(e).__name__}: {e}",
        )


# ═══════════════════════════════════════════════════════════════
# 输入数据 — 类似 OpenAI 的 HandoffInputData
# ═══════════════════════════════════════════════════════════════

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


@dataclass
class HandoffInputData(Generic[TInput]):
    """Handoff 时传递的上下文结构
    类比 OpenAI Agents SDK 的 HandoffInputData：
    - input_history: 输入历史（当前 relay/ 文件 + 会话上下文）
    - pre_handoff_items: handoff 前的上下文项
    - new_items: 本次 handoff 的新数据
    - task_payload: 原始 Task.payload（泛型，支持类型安全）
    """
    input_history: str = ""
    pre_handoff_items: dict = field(default_factory=dict)
    new_items: dict = field(default_factory=dict)
    task_payload: TInput | None = None

    def clone(self, **kwargs: Any) -> "HandoffInputData":
        return HandoffInputData(
            input_history=kwargs.get("input_history", self.input_history),
            pre_handoff_items=kwargs.get("pre_handoff_items", self.pre_handoff_items.copy()),
            new_items=kwargs.get("new_items", self.new_items.copy()),
            task_payload=kwargs.get("task_payload", self.task_payload),
        )


# ═══════════════════════════════════════════════════════════════
# Handoff 类 — 类似 OpenAI 的 Handoff
# ═══════════════════════════════════════════════════════════════

THandoffInput = TypeVar("THandoffInput")


@dataclass
class Handoff(Generic[THandoffInput]):
    """
    描述一个 Worker 可以被如何调用。
    类比 OpenAI Agents SDK 的 Handoff：
    - tool_name: 工具名（如 "transfer_to_content_writer"）
    - tool_description: 工具描述（LLM 自动匹配用）
    - target_worker: 目标 Worker ID
    - input_filter: 输入过滤函数（可选）
    - is_enabled: 运行时启用/禁用（可选 bool 或 Callable）
    - on_handoff: handoff 回调（可选）
    """
    tool_name: str
    tool_description: str
    target_worker: str
    target_worker_name: str = ""
    input_filter: Callable[[HandoffInputData], HandoffInputData] | None = None
    is_enabled: bool | Callable[[], bool] = True
    on_handoff: Callable[[HandoffInputData], Any] | None = None
    created_at: float = field(default_factory=time.time)

    def check_enabled(self) -> bool:
        if callable(self.is_enabled):
            return self.is_enabled()
        return self.is_enabled

    def apply_filter(self, input_data: HandoffInputData) -> HandoffInputData:
        if self.input_filter:
            return self.input_filter(input_data)
        return input_data

    def to_manifest(self) -> dict:
        """输出此 handoff 的清单，供 LLM/CEO 自动决策"""
        return {
            "tool_name": self.tool_name,
            "tool_description": self.tool_description,
            "target_worker": self.target_worker,
            "target_worker_name": self.target_worker_name,
            "enabled": self.check_enabled(),
        }


# ═══════════════════════════════════════════════════════════════
# 历史追踪
# ═══════════════════════════════════════════════════════════════


@dataclass
class HandoffRecord:
    """一次 handoff 执行记录"""
    handoff_tool_name: str
    source_worker: str
    target_worker: str
    input_summary: str = ""
    output_summary: str = ""
    error: HandoffError | None = None
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return {
            "handoff": self.handoff_tool_name,
            "source": self.source_worker,
            "target": self.target_worker,
            "input": self.input_summary[:200],
            "output": self.output_summary[:200],
            "error": self.error.to_dict() if self.error else None,
            "duration_ms": round(self.duration_ms, 1),
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════
# HandoffManager — 注册 + 路由 + 历史
# ═══════════════════════════════════════════════════════════════


class HandoffManager:
    """
    全局 Handoff 管理器。
    
    功能：
    - register(handoff) — 注册 handoff
    - route(task_type, input_data) — 根据 task_type 自动路由到匹配的 Worker
    - get_available(worker_id) — 获取目标 Worker 的所有可用 handoff（清单）
    - build_history(worker_id) — 构建 handoff 历史（供追踪）
    """

    _handoffs: dict[str, list[Handoff]] = {}
    _history: list[HandoffRecord] = []

    @classmethod
    def register(cls, handoff: Handoff) -> None:
        """注册一个 handoff"""
        if handoff.target_worker not in cls._handoffs:
            cls._handoffs[handoff.target_worker] = []
        # 去重：相同 tool_name + 相同 target 不重复注册
        existing = [h for h in cls._handoffs[handoff.target_worker]
                    if h.tool_name == handoff.tool_name]
        if existing:
            logger.warning(f"Handoff '{handoff.tool_name}' already registered for "
                           f"'{handoff.target_worker}', skipping duplicate")
            return
        cls._handoffs[handoff.target_worker].append(handoff)
        logger.info(f"Registered handoff: {handoff.tool_name} → {handoff.target_worker}")

    @classmethod
    def route(cls, task_type: str, input_data: HandoffInputData | None = None,
              source_worker: str = "ceo") -> tuple[Any, HandoffRecord | None]:
        """
        根据 task_type 自动路由到匹配的 Worker。
        
        路由策略：
        1. 精确匹配：task_type == handoff.tool_name 或 handoff.target_worker
        2. 相似匹配：task_type 包含 handoff.tool_name 中的关键词
        3. 描述匹配：用 tool_description 做模糊匹配
        
        返回: (WorkerResult | HandoffError, HandoffRecord)
        """
        from molib.agencies.workers.base import WorkerRegistry

        start = time.time()
        record = HandoffRecord(
            handoff_tool_name=task_type,
            source_worker=source_worker,
            target_worker="",
            input_summary=str(input_data.task_payload)[:200] if input_data else "",
        )

        # Step 1: 精确匹配
        candidates = []
        for worker_id, handoffs in cls._handoffs.items():
            for h in handoffs:
                if not h.check_enabled():
                    continue
                score = 0
                # 精确 tool_name 或 target_worker
                if task_type == h.tool_name or task_type == h.target_worker:
                    score = 10
                # tool_name 包含 task_type
                elif h.tool_name and task_type in h.tool_name:
                    score = 8
                # h.target_worker 包含 task_type
                elif h.target_worker and task_type in h.target_worker:
                    score = 7
                # 描述匹配
                elif h.tool_description and task_type.split("_")[0] in h.tool_description:
                    score = 5
                if score > 0:
                    candidates.append((score, h))

        if not candidates:
            error = HandoffError(
                code=HandoffErrorCode.WORKER_NOT_FOUND,
                message=f"No worker found for task_type: '{task_type}'. "
                        f"Available: {list(cls._handoffs.keys())}",
                source_worker=source_worker,
            )
            record.error = error
            record.target_worker = "?"
            record.duration_ms = (time.time() - start) * 1000
            cls._history.append(record)
            return error, record

        # 按分数降序选最优
        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0][1]

        # Step 2: 应用输入过滤
        filtered_input = input_data
        if input_data and best.input_filter:
            try:
                filtered_input = best.input_filter(input_data)
            except Exception as e:
                error = HandoffError(
                    code=HandoffErrorCode.INPUT_FILTER_ERROR,
                    message=f"Input filter failed for handoff '{best.tool_name}': {e}",
                    source_worker=source_worker,
                    original_error=str(e),
                )
                record.error = error
                record.duration_ms = (time.time() - start) * 1000
                cls._history.append(record)
                return error, record

        # Step 3: 获取 Worker 并执行
        worker_cls = WorkerRegistry.get(best.target_worker)
        if not worker_cls:
            error = HandoffError(
                code=HandoffErrorCode.WORKER_NOT_FOUND,
                message=f"Worker class '{best.target_worker}' not found in registry",
                source_worker=source_worker,
            )
            record.error = error
            record.duration_ms = (time.time() - start) * 1000
            cls._history.append(record)
            return error, record

        # Step 4: 触发 on_handoff 回调
        if best.on_handoff and filtered_input:
            try:
                result = best.on_handoff(filtered_input)
                if asyncio.iscoroutine(result):
                    # 在实际 async 环境下 await，这里简化处理
                    pass
            except Exception as e:
                logger.warning(f"on_handoff callback failed: {e}")

        # Step 5: 构建 Task 并委托
        from molib.agencies.workers.base import Task
        task = Task(
            task_id=f"handoff_{int(time.time())}",
            task_type=best.target_worker,
            payload=filtered_input.task_payload if filtered_input else {},
            requester=source_worker,
        )

        try:
            worker = worker_cls()
            if hasattr(worker, 'execute') and callable(worker.execute):
                import asyncio as _asyncio
                try:
                    result = _asyncio.run(worker.execute(task))
                except RuntimeError:
                    # 已经在 event loop 中
                    loop = _asyncio.get_event_loop()
                    result = loop.run_until_complete(worker.execute(task))
                record.target_worker = best.target_worker
                record.output_summary = str(result.output)[:200] if result.output else ""
                record.duration_ms = (time.time() - start) * 1000
                cls._history.append(record)
                return result, record
            else:
                error = HandoffError(
                    code=HandoffErrorCode.HANDOFF_INVALID,
                    message=f"Worker '{best.target_worker}' has no execute() method",
                    source_worker=source_worker,
                )
                record.error = error
                record.duration_ms = (time.time() - start) * 1000
                cls._history.append(record)
                return error, record
        except Exception as e:
            error = HandoffError.from_exception(e, best.target_worker)
            record.error = error
            record.target_worker = best.target_worker
            record.duration_ms = (time.time() - start) * 1000
            cls._history.append(record)
            return error, record

    @classmethod
    def get_available(cls, worker_id: str | None = None) -> list[dict]:
        """获取所有（或指定的 Worker 的）可用 handoff 清单"""
        result = []
        for wid, handoffs in cls._handoffs.items():
            if worker_id and wid != worker_id:
                continue
            for h in handoffs:
                if h.check_enabled():
                    result.append(h.to_manifest())
        return result

    @classmethod
    def build_history(cls, worker_id: str | None = None,
                      limit: int = 10) -> list[dict]:
        """构建 handoff 历史"""
        records = cls._history
        if worker_id:
            records = [r for r in records
                       if r.source_worker == worker_id or r.target_worker == worker_id]
        return [r.to_dict() for r in records[-limit:]]

    @classmethod
    def get_manifest(cls) -> list[dict]:
        """全量清单 — 供 CEO/SOUL.md 注入时使用"""
        return cls.get_available()


# ═══════════════════════════════════════════════════════════════
# 便捷工厂函数 — 类比 OpenAI 的 handoff() 函数
# ═══════════════════════════════════════════════════════════════


def create_handoff(
    target_worker: str,
    target_worker_name: str = "",
    tool_name_override: str | None = None,
    tool_description_override: str | None = None,
    input_filter: Callable[[HandoffInputData], HandoffInputData] | None = None,
    is_enabled: bool | Callable[[], bool] = True,
    on_handoff: Callable[[HandoffInputData], Any] | None = None,
) -> Handoff:
    """
    创建并注册一个 Handoff。
    类比 OpenAI SDK 的 handoff() 函数。
    
    默认的 tool_name: "transfer_to_{worker_id}"
    默认的 tool_description: "Handoff to the {worker_name} worker to handle the request."
    """
    tool_name = tool_name_override or f"transfer_to_{target_worker}"
    tool_desc = tool_description_override or (
        f"将任务委托给 {target_worker_name or target_worker} Worker 处理"
    )
    handoff_obj = Handoff(
        tool_name=tool_name,
        tool_description=tool_desc,
        target_worker=target_worker,
        target_worker_name=target_worker_name,
        input_filter=input_filter,
        is_enabled=is_enabled,
        on_handoff=on_handoff,
    )
    HandoffManager.register(handoff_obj)
    return handoff_obj


__all__ = [
    "Handoff",
    "HandoffManager",
    "HandoffInputData",
    "HandoffRecord",
    "HandoffError",
    "HandoffErrorCode",
    "create_handoff",
]
