"""会话状态机 — 管理多轮对话状态
适配自 molin-os-ultra v6.6.0 core/ceo/session_state.py
适配: loguru→logging, 去掉Redis依赖(纯内存模式)
"""
from __future__ import annotations

import asyncio
import json
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionState(Enum):
    INITIAL = "initial"
    EXPLORING = "exploring"
    CLARIFYING = "clarifying"
    PLANNING = "planning"
    EXECUTING = "executing"
    DELIVERING = "delivering"


@dataclass
class TurnRecord:
    turn_id: int
    user_input: str
    ceo_output: str
    state_before: SessionState
    state_after: SessionState
    tools_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
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
        old_state = self.state
        self.state = new_state
        self.updated_at = time.time()
        logger.info(f"Session {self.session_id}: {old_state.value} → {new_state.value}")

    def get_summary(self) -> str:
        parts = [f"Session: {self.session_id}", f"State: {self.state.value}", f"Turns: {self.turn_count}"]
        if self.confirmed_fields:
            parts.append(f"Confirmed: {self.confirmed_fields}")
        if self.pending_questions:
            parts.append(f"Pending questions: {self.pending_questions}")
        return " | ".join(parts)


class SessionStore:
    """会话存储 — 纯内存模式"""
    _sessions: Dict[str, SessionContext] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_or_create(cls, session_id: str) -> SessionContext:
        if session_id in cls._sessions:
            return cls._sessions[session_id]
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

    @classmethod
    def clear(cls) -> None:
        cls._sessions.clear()

    @classmethod
    def get_stats(cls) -> Dict[str, int]:
        return {"total_sessions": len(cls._sessions)}
