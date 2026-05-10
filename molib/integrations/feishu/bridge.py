"""
飞书审批卡片推送 + 回调处理（FS-1）
审批幂等性（FS-6）+ 操作人鉴权（FS-8）
"""

import os
import json
import time
from typing import Dict, Any, Optional
from loguru import logger

import httpx

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_APPROVED_OPERATORS = [
    op.strip() for op in os.getenv("FEISHU_APPROVED_OPERATORS", "").split(",") if op.strip()
]

from molib.integrations.feishu.token_manager import get_feishu_token as _get_managed_token


async def _get_feishu_token() -> Optional[str]:
    """获取飞书 tenant_access_token（通过 TokenManager 统一管理，自动刷新）"""
    return await _get_managed_token(FEISHU_APP_ID, FEISHU_APP_SECRET, label="bridge")


async def push_approval_card(
    approval_id: str,
    title: str,
    description: str,
    chat_id: str,
    task_type: str = "",
    agency_id: str = "",
) -> bool:
    """推送审批卡片到飞书群聊 — Feature 2: 优先尝试官方审批 API"""
    # Feature 2: 官方审批 API 模式
    if os.getenv("FEISHU_USE_OFFICIAL_APPROVAL", "false").lower() == "true":
        try:
            from molib.integrations.feishu.official_approval import push_official_approval
            instance_code = await push_official_approval(
                approval_id=approval_id, title=title, description=description,
                task_type=task_type, agency_id=agency_id,
            )
            if instance_code:
                # 更新 SQLite 记录
                try:
                    from molib.infra.memory.sqlite_client import SQLiteClient
                    db = SQLiteClient()
                    await db.update_approval_instance_code(approval_id, instance_code)
                except Exception as db_e:
                    logger.warning(f"审批 instance_code 写入失败: {db_e}")
                logger.info(f"官方审批已创建: {approval_id} → {instance_code}")
                return True
        except Exception as e:
            logger.warning(f"官方审批创建失败，回退到卡片模式: {e}")

    # 回退：自定义卡片模式
    token = await _get_feishu_token()
    if not token:
        logger.warning("飞书 token 不可用，审批卡片推送跳过")
        return False

    event_id = f"approval_{approval_id}_{int(time.time())}"
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"⚡ 待审批：{title}"},
            "template": "blue",
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": description}},
            {"tag": "hr"},
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "✅ 同意"},
                        "type": "primary",
                        "value": {"action": "approve", "approval_id": approval_id, "event_id": event_id},
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "❌ 拒绝"},
                        "type": "danger",
                        "value": {"action": "reject", "approval_id": approval_id, "event_id": event_id},
                    },
                ],
            },
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "interactive",
                    "content": json.dumps(card),
                },
                timeout=10,
            )
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"审批卡片推送成功: {approval_id}")
                return True
            logger.error(f"审批卡片推送失败: {data}")
            return False
    except Exception as e:
        logger.error(f"审批卡片推送异常: {e}")
        return False


def _check_operator(user_id: str) -> bool:
    """FS-8: 验证操作员是否在白名单中"""
    if not FEISHU_APPROVED_OPERATORS:
        return True
    return user_id in FEISHU_APPROVED_OPERATORS


async def handle_callback(payload: Dict[str, Any], user_id: str = "") -> Dict[str, Any]:
    """处理飞书回调（按钮点击）— FS-6 幂等性 + 飞书要求的 toast 响应格式"""
    event = payload.get("event", payload)  # 兼容两种事件结构
    action = event.get("action", {})
    value = action.get("value", {})

    if not isinstance(value, dict):
        return {"toast": {"type": "error", "content": "回调参数格式错误"}}

    action_type = value.get("action")
    approval_id = value.get("approval_id")
    event_id = value.get("event_id")

    if not action_type or not approval_id:
        return {"toast": {"type": "warning", "content": "缺少必要参数"}}

    # FS-8: 操作人鉴权
    operator = event.get("operator", {})
    operator_id = operator.get("open_id", user_id)
    if operator_id and not _check_operator(operator_id):
        logger.warning(f"未授权操作员回调: {operator_id}")
        return {"toast": {"type": "error", "content": "无权限操作"}}

    # FS-6: 幂等性检查（Redis event_id 去重）
    if event_id:
        try:
            import redis
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD", ""),
                decode_responses=True,
            )
            if r.exists(f"feishu_callback:{event_id}"):
                logger.info(f"回调已处理过（幂等去重）: {event_id}")
                return {"toast": {"type": "success", "content": "已处理"}}
            r.setex(f"feishu_callback:{event_id}", 86400, "1")
        except Exception as e:
            logger.warning(f"Redis 幂等检查失败，继续处理: {e}")

    logger.info(f"飞书审批回调: action={action_type}, approval_id={approval_id}")

    # 更新审批状态（写入 SQLite）
    try:
        from molib.infra.memory.sqlite_client import SQLiteClient
        db = SQLiteClient()
        if action_type == "approve":
            await db.approve(approval_id)
        else:
            await db.reject(approval_id)
    except Exception as e:
        logger.error(f"更新审批状态失败: {e}")
        return {"toast": {"type": "error", "content": "审批状态更新失败"}}

    # 返回飞书要求的 toast 响应（3 秒内必须返回）
    if action_type == "approve":
        return {"toast": {"type": "success", "content": f"审批已通过: {approval_id}"}}
    else:
        return {"toast": {"type": "info", "content": f"审批已驳回: {approval_id}"}}


def get_feishu_callback_router():
    """返回 FastAPI APIRouter 用于注册回调端点（FS-5）"""
    from fastapi import APIRouter, Request
    from fastapi.responses import JSONResponse

    router = APIRouter(prefix="/feishu", tags=["feishu"])

    @router.post("/callback")
    async def feishu_callback(request: Request):
        try:
            body = await request.json()
            user_id = request.headers.get("X-Feishu-User-Id", "")
            result = handle_callback(body, user_id)
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"飞书卡片回调异常: {e}")
            # 即使异常也要返回 200，避免飞书反复重试
            return JSONResponse(content={"toast": {"type": "error", "content": "处理失败，请稍后重试"}})

    return router
