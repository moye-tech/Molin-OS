#!/usr/bin/env python3
"""
墨麟OS · Langfuse可观测性装饰器
在技能调用函数上加 @trace_skill 即可自动追踪

用法:
  from tracing import trace_skill

  @trace_skill("xiaohongshu-content-engine", "media")
  def my_skill_function(...):
      ...
"""
import os
import functools
from pathlib import Path

try:
    from langfuse import Langfuse
    LANGFUSE_ENABLED = True

    # 尝试从环境变量加载，无配置时也不会报错
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if public_key and secret_key:
        langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        print("✅ Langfuse可观测性已启用")
    else:
        LANGFUSE_ENABLED = False
        langfuse = None
        print("⚠️ Langfuse未配置（设置 LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY）")

except ImportError:
    LANGFUSE_ENABLED = False
    langfuse = None

    def observe(**kw):
        return lambda f: f


def trace_skill(skill_name: str, agent_profile: str = "unknown"):
    """
    技能调用追踪装饰器
    用法: @trace_skill("xiaohongshu-engine", "media")
    """
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not LANGFUSE_ENABLED or not langfuse:
                return await func(*args, **kwargs)

            trace = langfuse.trace(
                name=f"skill:{skill_name}",
                metadata={"agent": agent_profile, "skill": skill_name},
            )
            span = trace.span(name=f"execute:{skill_name}")
            try:
                result = await func(*args, **kwargs)
                span.end(output=str(result)[:500] if result else None)
                trace.update(output={"status": "success"})
                return result
            except Exception as e:
                span.end(output=str(e), level="ERROR")
                trace.update(output={"status": "error", "error": str(e)})
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not LANGFUSE_ENABLED or not langfuse:
                return func(*args, **kwargs)
            trace = langfuse.trace(name=f"skill:{skill_name}")
            try:
                result = func(*args, **kwargs)
                trace.update(output={"status": "success"})
                return result
            except Exception as e:
                trace.update(output={"status": "error"})
                raise

        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


if __name__ == "__main__":
    print(f"Langfuse 状态: {'✅ 已启用' if LANGFUSE_ENABLED else '⚠️ 未启用'}")
    print("使用方法: from tracing import trace_skill")
    print("          @trace_skill('技能名', 'profile名')")
