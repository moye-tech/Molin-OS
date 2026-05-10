"""
日报/周报自动生成器（Feature 4）
查询 SQLite 统计数据，调用 LLM 生成专业报告，推送到飞书群聊
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from loguru import logger


def _query_stats(days: int = 1) -> Dict[str, Any]:
    """从 SQLite 查询指定天数的统计数据"""
    from molib.infra.memory.sqlite_client import SQLiteClient
    db_path = os.environ.get(
        "SQLITE_DB_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "infra", "memory", "data", "sqlite", "hermes.db"),
    )
    if not os.path.exists(db_path):
        return {"error": "SQLite db not found"}

    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    result: Dict[str, Any] = {
        "period_days": days,
        "since": since,
        "model_logs": {},
        "events": 0,
        "decisions": {},
        "evolution": {},
    }

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            # Model logs
            cur = conn.execute(
                "SELECT provider, model, team, task_type, SUM(cost) as total_cost, "
                "COUNT(*) as total_calls, SUM(success) as success_count, "
                "SUM(fallback) as fallback_count, AVG(latency) as avg_latency "
                "FROM model_logs WHERE created_at >= ? GROUP BY provider, model",
                (since,),
            )
            logs = [dict(r) for r in cur.fetchall()]
            result["model_logs"]["entries"] = logs
            result["model_logs"]["total_calls"] = sum(e["total_calls"] for e in logs)
            result["model_logs"]["total_cost"] = round(sum(e["total_cost"] or 0 for e in logs), 4)
            result["model_logs"]["success_rate"] = (
                round(sum(e["success_count"] or 0 for e in logs) / max(1, result["model_logs"]["total_calls"]) * 100, 1)
            )

            # Events
            cur = conn.execute("SELECT COUNT(*) as cnt FROM events WHERE created_at >= ?", (since,))
            result["events"] = cur.fetchone()["cnt"]

            # Decisions
            cur = conn.execute(
                "SELECT COUNT(*) as cnt, AVG(roi) as avg_roi, AVG(confidence) as avg_conf "
                "FROM decisions WHERE created_at >= ?", (since,),
            )
            dec = dict(cur.fetchone())
            result["decisions"] = {
                "count": dec["cnt"],
                "avg_roi": round(dec["avg_roi"] or 0, 2),
                "avg_confidence": round(dec["avg_conf"] or 0, 2),
            }

            # Evolution stats
            cur = conn.execute(
                "SELECT outcome, COUNT(*) as cnt FROM evolution_knowledge WHERE created_at >= ? GROUP BY outcome",
                (since,),
            )
            result["evolution"] = {r["outcome"]: r["cnt"] for r in cur.fetchall()}

    except Exception as e:
        result["error"] = str(e)

    return result


async def generate_daily_report() -> Dict[str, Any]:
    """生成日报"""
    stats = _query_stats(days=1)
    return await _generate_report(stats, "日报")


async def generate_weekly_report() -> Dict[str, Any]:
    """生成周报"""
    stats = _query_stats(days=7)
    return await _generate_report(stats, "周报")


async def _generate_report(stats: Dict[str, Any], report_type: str) -> Dict[str, Any]:
    prompt = f"""你是墨麟AI系统的CEO，请生成一份专业的系统运行{report_type}。

## 数据概览
- 统计区间: {stats.get('since', 'N/A')}
- LLM 调用总次数: {stats.get('model_logs', {}).get('total_calls', 0)}
- 总成本: ¥{stats.get('model_logs', {}).get('total_cost', 0)}
- 模型成功率: {stats.get('model_logs', {}).get('success_rate', 0)}%
- 系统事件数: {stats.get('events', 0)}
- 决策数: {stats.get('decisions', {}).get('count', 0)}
- 平均 ROI: {stats.get('decisions', {}).get('avg_roi', 0)}
- 知识卡片新增: {stats.get('evolution', {})}

请用简洁专业的中文生成{report_type}，包含：
1. **执行摘要**（2-3句话总结）
2. **模型使用分析**（调用量、成本、成功率）
3. **业务运行状态**（事件、决策）
4. **进化进展**（知识积累情况）
5. **建议与预警**（下一步优化方向）
"""
    try:
        from molib.core.ceo.model_router import ModelRouter
        router = ModelRouter()
        result = await router.call_async(
            prompt=prompt,
            system="你是墨麟AI系统的CEO，负责生成系统运行报告。用专业、简洁的中文输出。",
            task_type="ceo_decision",
        )
        report_text = result.get("text", "")
        return {
            "status": "success",
            "type": report_type,
            "report": report_text,
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"{report_type}生成失败: {e}")
        return {"status": "error", "type": report_type, "error": str(e), "stats": stats}


async def send_report_to_feishu(report: Dict[str, Any]) -> bool:
    """将报告推送到飞书群聊"""
    if report.get("status") != "success":
        return False
    try:
        chat_id = os.getenv("FEISHU_REPORT_CHAT_ID", "")
        if not chat_id:
            logger.warning("FEISHU_REPORT_CHAT_ID 未配置，报告推送跳过")
            return False

        from molib.integrations.feishu.bridge import _get_feishu_token
        token = await _get_feishu_token()
        if not token:
            return False

        report_text = report.get("report", "")
        report_type = report.get("type", "报告")
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"📊 墨麟AI系统 · {report_type}"},
                "template": "green" if report_type == "日报" else "blue",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": report_text}},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"}]},
            ],
        }
        async with httpx.AsyncClient() as client:
            await client.post(
                "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
                headers={"Authorization": f"Bearer {token}"},
                json={"receive_id": chat_id, "msg_type": "interactive", "content": json.dumps(card)},
                timeout=10,
            )
        logger.info(f"{report_type}已推送到飞书")
        return True
    except Exception as e:
        logger.error(f"飞书报告推送失败: {e}")
        return False
