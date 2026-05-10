"""
飞书官方审批 API 封装（Feature 2）
使用飞书开放平台官方审批接口替代自定义卡片审批
"""

import os
import json
import time
import httpx
from typing import Dict, Any, Optional, List
from loguru import logger

from molib.integrations.feishu.bridge import _get_feishu_token

BASE_URL = "https://open.feishu.cn/open-apis"


async def _api_request(method: str, path: str, json_data: Optional[dict] = None) -> Optional[dict]:
    token = await _get_feishu_token()
    if not token:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{BASE_URL}{path}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=json_data,
                timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data")
            logger.error(f"飞书审批 API 错误: {data}")
    except Exception as e:
        logger.error(f"飞书审批请求异常: {e}")
    return None


async def get_approval_definition_list() -> List[dict]:
    """获取审批定义列表"""
    data = await _api_request("GET", "/approval/v4/definitions")
    if not data:
        return []
    return data.get("items", [])


async def create_approval_instance(
    title: str,
    description: str,
    approval_code: str = "",
    user_id: str = "",
    task_type: str = "",
    agency_id: str = "",
) -> Optional[dict]:
    """
    创建审批实例
    Args:
        approval_code: 审批定义编码（从审批定义列表获取）
        user_id: 发起人 user_id
    Returns:
        {"instance_code": "xxx", "status": "APPROVED/PENDING/REJECTED"}
    """
    # 如果没有指定 approval_code，使用通用审批
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

    payload = {
        "approval_code": approval_code,
        "user_id": user_id,
        "form": form_values,
    }

    data = await _api_request("POST", "/approval/v4/instances", payload)
    if data:
        logger.info(f"飞书审批实例已创建: {data.get('instance_code')}")
    return data


async def get_approval_status(instance_code: str) -> Optional[dict]:
    """查询审批实例状态"""
    if not instance_code:
        return None
    data = await _api_request(
        "POST", "/approval/v4/instances/detail",
        {"instance_code": instance_code}
    )
    return data


async def approve_instance(instance_code: str, comment: str = "") -> bool:
    """通过审批"""
    if not instance_code:
        return False
    payload = {
        "instance_code": instance_code,
        "remark": comment or "已批准",
    }
    data = await _api_request("POST", "/approval/v4/instances/approve", payload)
    return data is not None


async def reject_instance(instance_code: str, comment: str = "") -> bool:
    """驳回审批"""
    if not instance_code:
        return False
    payload = {
        "instance_code": instance_code,
        "remark": comment or "已驳回",
    }
    data = await _api_request("POST", "/approval/v4/instances/reject", payload)
    return data is not None


async def push_official_approval(
    approval_id: str,
    title: str,
    description: str,
    task_type: str = "",
    agency_id: str = "",
) -> Optional[str]:
    """
    创建官方审批实例并返回 instance_code
    如果官方 API 不可用，返回 None 表示回退到卡片模式
    """
    if not os.getenv("FEISHU_USE_OFFICIAL_APPROVAL", "false").lower() == "true":
        return None

    result = await create_approval_instance(
        title=title,
        description=description,
        task_type=task_type,
        agency_id=agency_id,
    )
    if result:
        return result.get("instance_code", "")
    return None
