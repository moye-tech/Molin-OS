"""
飞书多维表格（Bitable）KPI 同步（FS-2）
写入失败降级到 SQLite（FS-7）
"""

import os
import time
from typing import Dict, Any, Optional
from loguru import logger

import httpx

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BITABLE_APP_TOKEN = os.getenv("FEISHU_BITABLE_APP_TOKEN", "")
FEISHU_BITABLE_TABLE_ID = os.getenv("FEISHU_BITABLE_TABLE_ID", "")

from molib.integrations.feishu.token_manager import get_feishu_token as _get_managed_token


async def _get_bitable_token() -> Optional[str]:
    """获取飞书 tenant_access_token（通过 TokenManager 统一管理，自动刷新）"""
    return await _get_managed_token(FEISHU_APP_ID, FEISHU_APP_SECRET, label="bitable")


async def sync_kpi_to_bitable(kpi_data: Dict[str, Any]) -> bool:
    """
    将 KPI 数据同步到飞书 Bitable
    FS-7: 失败时自动降级到 SQLite
    """
    app_token = FEISHU_BITABLE_APP_TOKEN
    table_id = FEISHU_BITABLE_TABLE_ID

    if not app_token or not table_id:
        logger.warning("Bitable 配置缺失，降级到 SQLite")
        await _fallback_to_sqlite(kpi_data)
        return False

    token = await _get_bitable_token()
    if not token:
        logger.warning("Bitable token 不可用，降级到 SQLite")
        await _fallback_to_sqlite(kpi_data)
        return False

    fields = {k: str(v) for k, v in kpi_data.items()}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"fields": fields},
                timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"KPI 同步到 Bitable 成功: {list(kpi_data.keys())}")
                return True
            logger.error(f"Bitable 写入失败: {data}")
            await _fallback_to_sqlite(kpi_data)
            return False
    except Exception as e:
        logger.error(f"Bitable 写入异常，降级到 SQLite: {e}")
        await _fallback_to_sqlite(kpi_data)
        return False


async def _fallback_to_sqlite(data: Dict[str, Any]):
    """FS-7: Bitable 写入失败降级到 SQLite"""
    try:
        from molib.infra.memory.sqlite_client import SQLiteClient
        db = SQLiteClient()
        await db.log_decision(
            action="bitable_fallback",
            roi=0, confidence=0,
            input_summary="bitable_task_fallback",
            output_json={"data": data, "timestamp": time.time()},
        )
        logger.info("数据已降级写入 SQLite")
    except Exception as e:
        logger.error(f"SQLite 降级也失败: {e}")


async def sync_task_to_bitable(task_data: Dict[str, Any]) -> bool:
    """
    将任务执行/审批结果同步到飞书 Bitable
    task_data 字段: approval_id, agency, status, output_summary, user_id, timestamp
    """
    app_token = os.getenv("FEISHU_BITABLE_APP_TOKEN", "")
    table_id = os.getenv("FEISHU_BITABLE_TABLE_ID", "")

    if not app_token or not table_id:
        logger.warning("Bitable 配置缺失，降级到 SQLite")
        await _fallback_to_sqlite(task_data)
        return False

    token = await _get_bitable_token()
    if not token:
        logger.warning("Bitable token 不可用，降级到 SQLite")
        await _fallback_to_sqlite(task_data)
        return False

    fields = {k: str(v)[:500] for k, v in task_data.items()}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"fields": fields},
                timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"任务同步到 Bitable 成功: {task_data.get('approval_id')}")
                return True
            logger.error(f"Bitable 写入失败: {data}")
            await _fallback_to_sqlite(task_data)
            return False
    except Exception as e:
        logger.error(f"Bitable 写入异常，降级到 SQLite: {e}")
        await _fallback_to_sqlite(task_data)
        return False

def build_dashboard_summary_card(data: dict) -> dict:
    total = data.get("total_revenue", 0)
    orders = data.get("total_orders", 0)
    roi = data.get("roi", 0)
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "墨麟科技 数据看板"}, "template": "blue"},
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": f"**总收入**: ¥{total:.2f}\n**订单数**: {orders}\n**ROI**: {roi:.2f}"}},
            {"tag": "hr"},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": "数据更新时间: 实时"}]},
        ],
    }
