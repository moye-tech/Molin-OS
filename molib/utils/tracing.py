"""
Request tracing — 为整个调用链提供唯一 request_id。
通过 ContextVar 在 async 调用栈中自动传播，
配合 loguru 的 bind() 实现结构化日志追踪。
"""

import uuid
from contextvars import ContextVar
from typing import Optional

# 当前请求的唯一 ID（在 async 调用栈中自动传播）
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def generate_request_id() -> str:
    """生成唯一请求 ID"""
    return f"req_{uuid.uuid4().hex[:12]}"


def get_request_id() -> str:
    """获取当前请求 ID（可能为空）"""
    return request_id_var.get()


def set_request_id(rid: Optional[str] = None) -> str:
    """设置当前请求 ID，返回设置的值"""
    rid = rid or generate_request_id()
    request_id_var.set(rid)
    return rid
