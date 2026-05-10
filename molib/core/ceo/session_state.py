"""
墨麟AI智能系统 v6.6 — 会话状态机

管理用户与 CEO 的多轮对话状态。
灵感来源：Claude Code `src/query.ts` 的 turn-based 状态流转。

状态流转：
INITIAL → EXPLORING → CLARIFYING → PLANNING → EXECUTING → DELIVERING
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger


class SessionState(Enum):
    INITIAL = "initial"         # 初始接触
    EXPLORING = "exploring"     # 探索用户需求
    CLARIFYING = "clarifying"   # 确认细节
    PLANNING = "planning"       # 拆解任务
    EXECUTING = "executing"     # 任务执行中
    DELIVERING = "delivering"   # 汇总交付


@dataclass
class TurnRecord:
    """单轮对话记录"""
    turn_id: int
    user_input: str
    ceo_output: str
    state_before: SessionState
    state_after: SessionState
    tools_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
    """会话上下文"""
    session_id: str
    state: SessionState = SessionState.INITIAL
    turn_count: int = 0
    user_needs: Dict[str, Any] = field(default_factory=dict)
    confirmed_fields: Dict[str, Any] = field(default_factory=dict)
    pending_questions: List[str] = field(default_factory=list)
    task_plan: Optional[Dict[str, Any]] = None
    history: List[TurnRecord] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_turn(self, user_input: str, ceo_output: str, state_before: SessionState,
                 state_after: SessionState, tools_used: List[str] = None,
                 metadata: Dict[str, Any] = None) -> None:
        """添加一轮对话记录"""
        self.turn_count += 1
        self.updated_at = time.time()
        self.history.append(TurnRecord(
            turn_id=self.turn_count,
            user_input=user_input,
            ceo_output=ceo_output,
            state_before=state_before,
            state_after=state_after,
            tools_used=tools_used or [],
            metadata=metadata or {},
        ))

    def transition(self, new_state: SessionState) -> None:
        """状态迁移"""
        old_state = self.state
        self.state = new_state
        self.updated_at = time.time()
        logger.info(f"Session {self.session_id}: {old_state.value} → {new_state.value}")

    def get_summary(self) -> str:
        """获取会话摘要"""
        parts = [
            f"Session: {self.session_id}",
            f"State: {self.state.value}",
            f"Turns: {self.turn_count}",
        ]
        if self.confirmed_fields:
            parts.append(f"Confirmed: {self.confirmed_fields}")
        if self.pending_questions:
            parts.append(f"Pending questions: {self.pending_questions}")
        return " | ".join(parts)


class SessionStore:
    """会话存储 — 内存缓存 + Redis 持久化，重启不丢"""

    _sessions: Dict[str, SessionContext] = {}
    _redis = None
    _redis_available = False
    _lock = asyncio.Lock()
    TTL_SECONDS = 86400  # 24h
    REDIS_KEY_PREFIX = "session:"

    @classmethod
    async def _ensure_redis(cls):
        if cls._redis is not None:
            return
        try:
            import redis.asyncio as aioredis
            cls._redis = aioredis.from_url(
                f"redis://:{os.getenv('REDIS_PASSWORD', '')}@{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/0",
                socket_connect_timeout=3,
                decode_responses=True,
            )
            await cls._redis.ping()
            cls._redis_available = True
            logger.info("[SessionStore] Redis 持久化已启用")
        except Exception as e:
            logger.warning(f"[SessionStore] Redis 不可用 ({e})，回退到纯内存模式")
            cls._redis = None
            cls._redis_available = False

    @classmethod
    def _serialize(cls, ctx: SessionContext) -> str:
        return json.dumps({
            "session_id": ctx.session_id,
            "state": ctx.state.value,
            "turn_count": ctx.turn_count,
            "user_needs": ctx.user_needs,
            "confirmed_fields": ctx.confirmed_fields,
            "pending_questions": ctx.pending_questions,
            "task_plan": ctx.task_plan,
            "history": [{
                "turn_id": t.turn_id,
                "user_input": t.user_input,
                "ceo_output": t.ceo_output,
                "state_before": t.state_before.value,
                "state_after": t.state_after.value,
                "tools_used": t.tools_used,
                "metadata": t.metadata,
            } for t in ctx.history[-20:]],  # 最多保留20轮
            "created_at": ctx.created_at,
            "updated_at": ctx.updated_at,
        }, ensure_ascii=False)

    @classmethod
    def _deserialize(cls, data: dict) -> SessionContext:
        ctx = SessionContext(session_id=data["session_id"])
        ctx.state = SessionState(data.get("state", "initial"))
        ctx.turn_count = data.get("turn_count", 0)
        ctx.user_needs = data.get("user_needs", {})
        ctx.confirmed_fields = data.get("confirmed_fields", {})
        ctx.pending_questions = data.get("pending_questions", [])
        ctx.task_plan = data.get("task_plan")
        ctx.created_at = data.get("created_at", time.time())
        ctx.updated_at = data.get("updated_at", time.time())
        for t in data.get("history", []):
            ctx.history.append(TurnRecord(
                turn_id=t.get("turn_id", 0),
                user_input=t.get("user_input", ""),
                ceo_output=t.get("ceo_output", ""),
                state_before=SessionState(t.get("state_before", "initial")),
                state_after=SessionState(t.get("state_after", "initial")),
                tools_used=t.get("tools_used", []),
                metadata=t.get("metadata", {}),
            ))
        return ctx

    @classmethod
    async def get_or_create(cls, session_id: str) -> SessionContext:
        # 1. 内存缓存
        if session_id in cls._sessions:
            return cls._sessions[session_id]

        # 2. Redis 持久化
        await cls._ensure_redis()
        if cls._redis_available:
            try:
                raw = await cls._redis.get(f"{cls.REDIS_KEY_PREFIX}{session_id}")
                if raw:
                    ctx = cls._deserialize(json.loads(raw))
                    cls._sessions[session_id] = ctx
                    logger.info(f"[SessionStore] 从 Redis 恢复会话: {session_id} ({ctx.turn_count} 轮)")
                    return ctx
            except Exception as e:
                logger.warning(f"[SessionStore] Redis 读取失败: {e}")

        # 3. 新建
        cls._sessions[session_id] = SessionContext(session_id=session_id)
        logger.info(f"[SessionStore] 新建会话: {session_id}")
        return cls._sessions[session_id]

    @classmethod
    def get(cls, session_id: str) -> Optional[SessionContext]:
        return cls._sessions.get(session_id)

    @classmethod
    async def update(cls, session_id: str, context: SessionContext) -> None:
        async with cls._lock:
            cls._sessions[session_id] = context
        # 持久化到 Redis
        await cls._ensure_redis()
        if cls._redis_available:
            try:
                key = f"{cls.REDIS_KEY_PREFIX}{session_id}"
                await cls._redis.setex(key, cls.TTL_SECONDS, cls._serialize(context))
            except Exception as e:
                logger.debug(f"[SessionStore] Redis 写入失败: {e}")

    @classmethod
    def clear(cls) -> None:
        cls._sessions.clear()
