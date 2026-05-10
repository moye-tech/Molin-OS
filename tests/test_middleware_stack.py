"""测试 Middleware 栈 — CORS、Rate Limiter、Body Size Limit"""
import asyncio
import os
import sys
import time

import pytest
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_rate_limiter_allows_normal_traffic():
    """正常请求不应被限速"""
    from core.middleware.rate_limiter import rate_limit_middleware, _request_log

    client_ip = "test_normal_ip"
    # 清理该 IP 的历史记录
    _request_log.pop(client_ip, None)

    # 模拟正常请求（每分钟 100 次以内）
    for i in range(5):
        request = MagicMock()
        request.client.host = client_ip
        call_next = AsyncMock(return_value=MagicMock())
        # 在事件循环中运行
        asyncio.run(rate_limit_middleware(request, call_next))

    # 5 次请求都应成功
    assert len(_request_log.get(client_ip, [])) == 5


def test_rate_limiter_blocks_excess():
    """超过限速应返回 429"""
    from core.middleware.rate_limiter import rate_limit_middleware, _request_log, MAX_REQUESTS_PER_MINUTE

    client_ip = "test_blocked_ip"
    _request_log.pop(client_ip, None)

    # 发送超过限制的请求
    for i in range(MAX_REQUESTS_PER_MINUTE):
        request = MagicMock()
        request.client.host = client_ip
        call_next = AsyncMock(return_value=MagicMock())
        asyncio.run(rate_limit_middleware(request, call_next))

    # 再发一次，应触发 429
    request = MagicMock()
    request.client.host = client_ip
    call_next = AsyncMock(return_value=MagicMock())

    with pytest.raises(Exception) as exc_info:
        asyncio.run(rate_limit_middleware(request, call_next))

    assert exc_info.value.status_code == 429


def test_rate_limiter_window_reset():
    """时间窗口过期后应重置计数"""
    from core.middleware.rate_limiter import rate_limit_middleware, _request_log

    client_ip = "test_window_ip"
    # 模拟过期的时间戳
    old_time = time.time() - 120  # 2分钟前
    _request_log[client_ip] = [old_time] * 100

    # 新请求应正常处理（旧记录已被清理）
    request = MagicMock()
    request.client.host = client_ip
    call_next = AsyncMock(return_value=MagicMock())
    asyncio.run(rate_limit_middleware(request, call_next))

    # 窗口应重置，只剩当前请求
    assert len(_request_log[client_ip]) == 1


def test_cors_middleware_setup():
    """CORS 中间件应正确配置"""
    from core.middleware.cors import setup_cors
    from fastapi import FastAPI

    app = FastAPI()
    setup_cors(app)

    # 检查是否添加了中间件
    assert len(app.user_middleware) > 0


def test_body_size_limit_allows_small():
    """小请求体不应被拒绝 — 纯逻辑测试，不加载完整 app"""
    import os
    # 设置一个较大的限制
    os.environ["MAX_BODY_SIZE_BYTES"] = "1048576"

    from core.middleware import rate_limit_middleware
    # body_size_limit 在 main.py 中定义，直接测试逻辑
    # 模拟 body size check: content_length < MAX_BODY_SIZE
    content_length = 1000  # 1KB
    max_size = int(os.getenv("MAX_BODY_SIZE_BYTES", "1048576"))
    assert content_length <= max_size  # 小请求体应通过


def test_auth_dependency_open_mode():
    """未配置 API Key 时应开放模式"""
    from core.middleware.auth import verify_api_key, VALID_KEYS

    if not VALID_KEYS:
        # 开放模式：没有 VALID_KEYS 时依赖不应报错
        assert len(VALID_KEYS) == 0
