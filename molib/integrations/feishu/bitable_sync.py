"""
飞书多维表格 — 系统运行监控数据同步（v6.6）

在每次任务执行完成后，将执行记录写入飞书多维表格（Bitable），
供「多维表格仪表盘」小组件在工作台实时展示。

数据流：
  CEO执行链完成 → sync_task_execution() → Bitable API（批量/单条）
  失败降级 → SQLite task_executions 表

表结构（在飞书多维表格中预先创建）：
  - task_id（单行文本，主键）
  - user_input（多行文本）
  - agencies（多行文本，逗号分隔）
  - total_subtasks（数字）
  - success_count（数字）
  - success_rate（数字，百分比）
  - status（单选：completed/failed/partial）
  - latency_seconds（数字）
  - cost_cny（数字）
  - summary（多行文本）
  - created_at（日期）
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from loguru import logger

import httpx

FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BITABLE_APP_TOKEN = os.getenv("FEISHU_BITABLE_APP_TOKEN", "")
# 监控专用表 ID（可与审批表不同）
FEISHU_BITABLE_MONITOR_TABLE = os.getenv("FEISHU_BITABLE_MONITOR_TABLE", "")

# Token 缓存
_monitor_token: Optional[str] = None
_TOKEN_TTL = 7000  # 飞书 tenant_access_token 有效期 ~2h


async def _get_monitor_token() -> Optional[str]:
    """获取多维表格写权限 token（带缓存）"""
    global _monitor_token
    if _monitor_token:
        return _monitor_token
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
                _monitor_token = data.get("tenant_access_token")
                return _monitor_token
            logger.warning(f"Bitable token 获取失败: code={data.get('code')}")
            return None
    except Exception as e:
        logger.error(f"Bitable token 异常: {e}")
        return None


def _truncate(s: str, max_len: int = 800) -> str:
    if s and len(s) > max_len:
        return s[:max_len] + "..."
    return s or ""


def _status_label(status: str) -> str:
    """映射到 Bitable 单选值（需与多维表格字段选项一致）"""
    mapping = {
        "completed": "已完成",
        "failed": "失败",
        "partial": "部分完成",
        "skipped": "跳过",
        "error": "失败",
    }
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
    """
    同步单次任务执行记录到飞书多维表格。

    使用 batch_create 支持同一表写入多条记录（后续优化用）。
    当前用单条 create，失败降级到 SQLite。
    """
    app_token = FEISHU_BITABLE_APP_TOKEN
    table_id = FEISHU_BITABLE_MONITOR_TABLE or FEISHU_BITABLE_APP_TOKEN and None

    # 如果没有独立的监控表，复用主表
    if not table_id:
        table_id = os.getenv("FEISHU_BITABLE_TABLE_ID", "")

    if not app_token or not table_id:
        logger.debug("Bitable 监控表配置缺失，降级到 SQLite")
        await _fallback_to_sqlite(session_id, user_input, agencies,
                                   total_subtasks, success_count, status,
                                   latency_seconds, cost_cny, summary)
        return False

    token = await _get_monitor_token()
    if not token:
        logger.warning("Bitable token 不可用，降级到 SQLite")
        await _fallback_to_sqlite(session_id, user_input, agencies,
                                   total_subtasks, success_count, status,
                                   latency_seconds, cost_cny, summary)
        return False

    rate = round(success_count / max(total_subtasks, 1) * 100, 1) if total_subtasks > 0 else 0

    # Bitable 字段映射（字段名需与多维表格实际字段名一致）
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
        "created_at": int(time.time() * 1000),  # 毫秒时间戳
    }

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
                logger.info(f"Bitable 同步成功: session={session_id[:12]}... "
                            f"agencies={agencies} rate={rate}%")
                return True
            logger.warning(f"Bitable 写入返回非 0: code={data.get('code')}, msg={data.get('msg')}")
            await _fallback_to_sqlite(session_id, user_input, agencies,
                                       total_subtasks, success_count, status,
                                       latency_seconds, cost_cny, summary)
            return False
    except Exception as e:
        logger.error(f"Bitable 同步异常: {e}")
        await _fallback_to_sqlite(session_id, user_input, agencies,
                                   total_subtasks, success_count, status,
                                   latency_seconds, cost_cny, summary)
        return False


async def _fallback_to_sqlite(session_id, user_input, agencies, total_subtasks,
                               success_count, status, latency_seconds, cost_cny, summary):
    """降级写入 SQLite task_executions 表"""
    try:
        from molib.infra.memory.sqlite_client import SQLiteClient
        db = SQLiteClient()
        await db.log_task_execution(
            session_id=session_id,
            user_input=user_input,
            agencies=agencies,
            total_subtasks=total_subtasks,
            success_count=success_count,
            status=status,
            cost_cny=cost_cny,
            latency_seconds=latency_seconds,
            summary=summary[:500] if summary else "",
        )
        logger.debug("数据已降级写入 SQLite task_executions")
    except Exception as e:
        logger.error(f"SQLite 降级也失败: {e}")


# ── 快捷指令 /dashboard 卡片构建 ────────────────────────

def build_dashboard_summary_card(dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
    """构建 /dashboard 指令的飞书交互卡片"""
    total = dashboard_data.get("total_tasks", 0)
    rate = dashboard_data.get("success_rate", 0)
    agencies = dashboard_data.get("agency_participation", [])
    recent = dashboard_data.get("recent_tasks", [])

    # 构建最近任务行
    task_lines = []
    for t in recent[:5]:
        ag = "、".join(json.loads(t.get("agencies", "[]")) or ["-"])
        icon = "✅" if t.get("status") == "completed" else "❌"
        ts = (t.get("created_at", "") or "")[:16].replace("T", " ")
        task_lines.append(f"{icon} {ts} | {ag} | {t.get('success_count',0)}/{t.get('total_subtasks',0)}")

    agency_top = "、".join(
        f"{a[0]}({a[1]})" for a in agencies[:5]
    ) if agencies else "暂无数据"

    elements = [
        {
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**系统运行概览**\n"
                                                   f"总任务数: **{total}**  |  成功率: **{rate}%**  |  活跃子公司: **{len(agencies)}**"},
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"**参与频次 TOP5**: {agency_top}"},
        },
        {"tag": "hr"},
    ]

    if task_lines:
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": "**最近 5 次任务：**\n" + "\n".join(task_lines)},
        })
        elements.append({"tag": "hr"})

    elements.append({
        "tag": "note",
        "elements": [{"tag": "plain_text", "content": "数据来自系统执行链，每任务完成后自动同步"}],
    })

    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": "墨麟AI 运行监控"},
            "template": "blue",
        },
        "elements": elements,
    }
