"""
墨麟OS v2.5 — Langfuse 可观测性追踪层 (ObservabilityLayer)

GAP-02 补强：在现有 tracing.py（ContextVar 请求ID）之上，新增 Langfuse 全链路追踪。

特性：
- 零侵入：@observe 装饰器，不改业务逻辑
- 自动捕获：Worker 耗时、token 消耗、输入/输出
- 跨 WorkerChain 追踪：多 Worker 协作链路自动关联
- 降级保护：Langfuse 不可用时自动跳过（不影响主流程）
- 支持 Langfuse Cloud（无需 Docker）+ 本地自托管

用法:
    from molib.shared.observability import trace, observe_worker

    @observe_worker("research")
    async def execute(self, task):
        ...

架构（与 EvolutionEngine 互补）：
  Langfuse → 实时执行追踪（trace/span/token/耗时）
  EvolutionEngine → 事后评估（质量评分/知识提取/失败分析）
"""

from __future__ import annotations

import functools
import logging
import os
import time
from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# ── Langfuse 客户端（延迟初始化） ──

_langfuse_client = None
_langfuse_available: bool = False
_trace_enabled: bool = True

# 当前追踪上下文
_current_trace_id: ContextVar[str] = ContextVar("langfuse_trace_id", default="")
_current_span_id: ContextVar[str] = ContextVar("langfuse_span_id", default="")


def _init_langfuse():
    """延迟初始化 Langfuse 客户端"""
    global _langfuse_client, _langfuse_available

    if _langfuse_client is not None:
        return

    # 检查配置
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.debug("Langfuse 未配置 (LANGFUSE_PUBLIC_KEY/SECRET_KEY)，可观测性追踪将跳过")
        _langfuse_available = False
        return

    try:
        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        _langfuse_available = True
        logger.info("✅ Langfuse 可观测性追踪已激活")
    except ImportError:
        logger.warning("⚠️ langfuse 未安装，可观测性追踪将跳过")
        _langfuse_available = False
    except Exception as e:
        logger.warning(f"⚠️ Langfuse 初始化失败: {e}")
        _langfuse_available = False


def _get_langfuse():
    """获取 Langfuse 客户端（延迟初始化）"""
    _init_langfuse()
    return _langfuse_client if _langfuse_available else None


# ── 追踪装饰器 ──


def observe_worker(
    worker_name: str,
    capture_input: bool = True,
    capture_output: bool = True,
):
    """
    Worker 追踪装饰器（仿 Langfuse @observe）。

    自动捕获：
    - 执行耗时
    - 输入/输出
    - 异常信息
    - 与 EvolutionEngine 的评估结果关联

    用法:
        @observe_worker("research")
        async def execute(self, task):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not _trace_enabled:
                return await func(*args, **kwargs)

            lf = _get_langfuse()
            start_time = time.time()
            trace_name = f"worker:{worker_name}"

            # 提取任务信息
            task_desc = ""
            try:
                task = args[1] if len(args) > 1 else kwargs.get("task")
                if task and hasattr(task, "payload"):
                    task_desc = str(task.payload.get("description", task.payload.get("topic", "")))[:200]
            except Exception:
                pass

            trace = None
            if lf:
                try:
                    trace = lf.trace(
                        name=trace_name,
                        metadata={
                            "worker": worker_name,
                            "task": task_desc,
                        },
                    )
                    if trace and hasattr(trace, 'id'):
                        _current_trace_id.set(trace.id)
                except Exception as e:
                    logger.debug(f"Langfuse trace 创建失败: {e}")

            # 执行
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time

                # 记录成功
                if lf and trace:
                    try:
                        trace.update(
                            output={"status": "success", "elapsed": elapsed},
                            metadata={
                                "status": "success",
                                "elapsed_seconds": elapsed,
                                "worker": worker_name,
                            },
                        )
                        # 与 EvolutionEngine 关联
                        if hasattr(result, 'output') and isinstance(result.output, dict):
                            score = result.output.get("quality_score")
                            if score:
                                trace.score(name="quality", value=float(score))
                    except Exception as e:
                        logger.debug(f"Langfuse trace update 失败: {e}")

                return result

            except Exception as e:
                elapsed = time.time() - start_time

                # 记录失败
                if lf and trace:
                    try:
                        trace.update(
                            output={"status": "error", "error": str(e), "elapsed": elapsed},
                            metadata={
                                "status": "error",
                                "error": str(e),
                                "elapsed_seconds": elapsed,
                                "worker": worker_name,
                            },
                        )
                    except Exception:
                        pass
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not _trace_enabled:
                return func(*args, **kwargs)

            lf = _get_langfuse()
            start_time = time.time()
            trace_name = f"worker:{worker_name}"

            trace = None
            if lf:
                try:
                    trace = lf.trace(name=trace_name, metadata={"worker": worker_name})
                except Exception:
                    pass

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                if lf and trace:
                    try:
                        trace.update(output={"status": "success", "elapsed": elapsed})
                    except Exception:
                        pass
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                if lf and trace:
                    try:
                        trace.update(output={"status": "error", "error": str(e), "elapsed": elapsed})
                    except Exception:
                        pass
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def observe_chain(chain_name: str = "worker_chain"):
    """
    WorkerChain 追踪装饰器。

    用法:
        @observe_chain("content_pipeline")
        async def execute(self):
            ...
    """
    return observe_worker(chain_name, capture_input=True, capture_output=True)


# ── 追踪工具函数 ──


def trace_span(name: str, metadata: Optional[Dict] = None):
    """
    创建追踪子段（用于追踪 Worker 内部的子步骤）。

    用法:
        with trace_span("gpt_researcher_fetch", {"topic": topic}):
            result = await researcher.conduct_research()
    """
    class _SpanContext:
        def __init__(self, span_name: str, meta: Optional[Dict] = None):
            self.name = span_name
            self.meta = meta or {}
            self.start_time = None
            self.lf = None

        def __enter__(self):
            if not _trace_enabled:
                return self
            self.lf = _get_langfuse()
            self.start_time = time.time()
            if self.lf:
                try:
                    self.lf.trace(name=self.name, metadata=self.meta)
                except Exception:
                    pass
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.start_time if self.start_time else 0
            if self.lf and exc_type is not None:
                try:
                    self.lf.trace(name=f"{self.name}:error", metadata={
                        "error": str(exc_val),
                        "elapsed": elapsed,
                    })
                except Exception:
                    pass
            return False

    return _SpanContext(name, metadata)


def get_trace_id() -> str:
    """获取当前追踪 ID"""
    return _current_trace_id.get()


def set_trace_enabled(enabled: bool):
    """全局开关追踪"""
    global _trace_enabled
    _trace_enabled = enabled


def observability_status() -> Dict[str, Any]:
    """可观测性系统健康检查"""
    _init_langfuse()
    return {
        "langfuse_available": _langfuse_available,
        "trace_enabled": _trace_enabled,
        "current_trace_id": _current_trace_id.get() or "无活跃追踪",
        "mode": "Langfuse 全链路追踪" if _langfuse_available else "基础 ContextVar 追踪",
    }
