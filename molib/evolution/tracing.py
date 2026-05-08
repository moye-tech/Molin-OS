"""请求追踪 — ContextVar全链路追踪ID
适配自 molin-os-ultra v6.6.0 utils/tracing.py
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import Optional

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def generate_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"


def get_request_id() -> str:
    return request_id_var.get()


def set_request_id(rid: Optional[str] = None) -> str:
    rid = rid or generate_request_id()
    request_id_var.set(rid)
    return rid
