"""飞书多维表格 — 任务执行记录同步
适配自 molin-os-ultra v6.6.0 integrations/feishu/bitable_sync.py
适配: loguru→logging, 环境变量前缀统一 -> .hermes/.env
"""
from __future__ import annotations

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional

import httpx

logger = logging.getLogger(__name__)

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
BITABLE_BASE_TOKEN = os.getenv("BITABLE_BASE_TOKEN", "")
BITABLE_TABLE_ID = os.getenv("BITABLE_TABLE_ID", "")

_token: Optional[str] = None


async def _get_bitable_token() -> Optional[str]:
    global _token
    if _token:
        return _token
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        return None
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
            )
            data = resp.json()
            if data.get("code") == 0:
                _token = data.get("tenant_access_token")
                return _token
            logger.warning(f"Bitable token 获取失败: code={data.get('code')}")
    except Exception as e:
        logger.error(f"Bitable token 异常: {e}")
    return None


def _truncate(s: str, max_len: int = 800) -> str:
    return (s[:max_len] + "...") if s and len(s) > max_len else (s or "")


def _status_label(status: str) -> str:
    mapping = {"completed": "已完成", "failed": "失败", "partial": "部分完成",
               "skipped": "跳过", "error": "失败"}
    return mapping.get(status, status)


async def sync_task_execution(
    session_id: str,
    user_input: str,
    agencies: List[str],
    total_subtasks: int,
    success_count: int,
    status: str,
    latency_seconds: float,
    cost_cny: float = 0.0,
    summary: str = "",
) -> bool:
    """同步单次任务执行记录到飞书多维表格。失败时静默跳过。"""
    if not BITABLE_BASE_TOKEN or not BITABLE_TABLE_ID:
        logger.debug("Bitable 配置缺失，跳过")
        return False

    token = await _get_bitable_token()
    if not token:
        return False

    rate = round(success_count / max(total_subtasks, 1) * 100, 1) if total_subtasks > 0 else 0
    fields = {
        "task_id": session_id,
        "user_input": _truncate(user_input),
        "agencies": "、".join(agencies) if agencies else "",
        "total_subtasks": total_subtasks,
        "success_count": success_count,
        "success_rate": rate,
        "status": _status_label(status),
        "latency_seconds": round(latency_seconds, 1),
        "cost_cny": round(cost_cny, 4),
        "summary": _truncate(summary, 500),
        "created_at": int(time.time() * 1000),
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_BASE_TOKEN}/tables/{BITABLE_TABLE_ID}/records",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"fields": fields},
                timeout=15,
            )
            data = resp.json()
            if data.get("code") == 0:
                logger.info(f"Bitable 同步成功: session={session_id[:12]}...")
                return True
            logger.warning(f"Bitable 写入失败: code={data.get('code')}")
    except Exception as e:
        logger.error(f"Bitable 同步异常: {e}")
    return False


def build_dashboard_summary_card(dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
    """构建 /dashboard 指令的飞书交互卡片"""
    total = dashboard_data.get("total_tasks", 0)
    rate = dashboard_data.get("success_rate", 0)
    agencies = dashboard_data.get("agency_participation", [])
    recent = dashboard_data.get("recent_tasks", [])

    task_lines = []
    for t in recent[:5]:
        ag = "、".join(json.loads(t.get("agencies", "[]")) or ["-"]) if isinstance(t.get("agencies"), str) else str(t.get("agencies", "-"))
        icon = "✅" if t.get("status") == "completed" else "❌"
        ts = (t.get("created_at", "") or "")[:16].replace("T", " ")
        task_lines.append(f"{icon} {ts} | {ag} | {t.get('success_count',0)}/{t.get('total_subtasks',0)}")

    agency_top = "、".join(f"{a[0]}({a[1]})" for a in agencies[:5]) if agencies else "暂无数据"

    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": f"**系统运行概览**\n总任务数: **{total}**  |  成功率: **{rate}%**  |  活跃子公司: **{len(agencies)}**"}},
        {"tag": "hr"},
        {"tag": "div", "text": {"tag": "lark_md", "content": f"**参与频次 TOP5**: {agency_top}"}},
        {"tag": "hr"},
    ]
    if task_lines:
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "**最近 5 次任务：**\n" + "\n".join(task_lines)}})
        elements.append({"tag": "hr"})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "数据来自系统执行链，每任务完成后自动同步"}]})

    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "墨麟AI 运行监控"}, "template": "blue"},
        "elements": elements,
    }
