"""速率限制中间件 — 内存滑动窗口实现（零外部依赖）"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from loguru import logger

# 全局速率限制：每 IP 每分钟最大请求数
MAX_REQUESTS_PER_MINUTE = int(__import__("os").getenv("RATE_LIMIT_RPM", "60"))

# {ip: [(timestamp, ...)]}
_request_log: dict[str, list[float]] = defaultdict(list)


async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - 60

    # 清理过期记录
    _request_log[client_ip] = [t for t in _request_log[client_ip] if t > window_start]

    if len(_request_log[client_ip]) >= MAX_REQUESTS_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

    _request_log[client_ip].append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(
        max(0, MAX_REQUESTS_PER_MINUTE - len(_request_log[client_ip]))
    )
    return response
