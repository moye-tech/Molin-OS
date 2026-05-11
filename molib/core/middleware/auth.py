"""API 鉴权中间件 — Bearer Token + API Key 验证"""
import os
from typing import Set
from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
VALID_KEYS: Set[str] = set(k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip())


async def verify_api_key(key: str = Depends(API_KEY_HEADER)):
    """验证 API Key，无 Key 时跳过（兼容内网调用）"""
    if not VALID_KEYS:
        return  # 未配置 Key，开放模式
    if key and key in VALID_KEYS:
        return
    raise HTTPException(status_code=403, detail="Invalid or missing API Key")


def get_auth_dependency():
    """获取鉴权依赖（未配置 Key 时不拦截）"""
    return [Depends(verify_api_key)] if VALID_KEYS else []
