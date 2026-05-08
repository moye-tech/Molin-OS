"""飞书官方审批 API 封装
适配自 molin-os-ultra v6.6.0 integrations/feishu/official_approval.py
"""
from __future__ import annotations

import os
import time
import logging
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")

_token: Optional[str] = None
BASE_URL = "https://open.feishu.cn/open-apis"


async def _get_approval_token() -> Optional[str]:
    global _token
    if _token:
        return _token
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/auth/v3/tenant_access_token/internal",
                json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
            )
            data = resp.json()
            if data.get("code") == 0:
                _token = data.get("tenant_access_token")
                return _token
    except Exception as e:
        logger.error(f"审批 token 异常: {e}")
    return None


async def _api_request(method: str, path: str, json_data: Optional[dict] = None) -> Optional[dict]:
    token = await _get_approval_token()
    if not token:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method, f"{BASE_URL}{path}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=json_data, timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data")
            logger.error(f"飞书审批 API 错误: {data}")
    except Exception as e:
        logger.error(f"飞书审批请求异常: {e}")
    return None


async def get_approval_definition_list() -> list:
    """获取审批定义列表"""
    data = await _api_request("GET", "/approval/v4/definitions")
    return data.get("items", []) if data else []


async def create_approval_instance(
    title: str, description: str, approval_code: str = "",
    user_id: str = "", task_type: str = "", agency_id: str = "",
) -> Optional[dict]:
    """创建审批实例"""
    if not approval_code:
        approval_code = os.getenv("FEISHU_DEFAULT_APPROVAL_CODE", "")
    form_values = [
        {"id": "title", "value": title},
        {"id": "description", "value": description},
    ]
    if task_type:
        form_values.append({"id": "task_type", "value": task_type})
    if agency_id:
        form_values.append({"id": "agency_id", "value": agency_id})

    payload = {"approval_code": approval_code, "user_id": user_id, "form": form_values}
    data = await _api_request("POST", "/approval/v4/instances", payload)
    if data:
        logger.info(f"飞书审批实例已创建: {data.get('instance_code')}")
    return data


async def get_approval_status(instance_code: str) -> Optional[dict]:
    if not instance_code:
        return None
    return await _api_request("POST", "/approval/v4/instances/detail", {"instance_code": instance_code})


async def approve_instance(instance_code: str, comment: str = "") -> bool:
    if not instance_code:
        return False
    data = await _api_request("POST", "/approval/v4/instances/approve",
                              {"instance_code": instance_code, "remark": comment or "已批准"})
    return data is not None


async def reject_instance(instance_code: str, comment: str = "") -> bool:
    if not instance_code:
        return False
    data = await _api_request("POST", "/approval/v4/instances/reject",
                              {"instance_code": instance_code, "remark": comment or "已驳回"})
    return data is not None


async def push_official_approval(
    approval_id: str, title: str, description: str,
    task_type: str = "", agency_id: str = "",
) -> Optional[str]:
    """创建官方审批实例。如果不可用返回 None（回退卡片模式）"""
    if os.getenv("FEISHU_USE_OFFICIAL_APPROVAL", "false").lower() != "true":
        return None
    result = await create_approval_instance(title=title, description=description,
                                            task_type=task_type, agency_id=agency_id)
    return result.get("instance_code", "") if result else None
