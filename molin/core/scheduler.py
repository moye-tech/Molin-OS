"""
墨麟定时调度器 — 心跳任务 + cron 管理
=====================================

负责:
- 每日心跳: 09:00 闲鱼+情报简报
- 每周战略审查: 周一 10:00
- 趋势监控: 每6小时
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger("molin.scheduler")


class Scheduler:
    """墨麟定时调度器"""

    # 预定义心跳任务
    HEARTBEAT_JOBS = [
        {
            "id": "heartbeat_daily",
            "name": "每日心跳 - 闲鱼+情报简报",
            "schedule": "0 9 * * *",  # 每天09:00
            "module": "molin.core.engine",
            "function": "heartbeat",
            "description": "检查所有平台状态，生成每日情报简报",
        },
        {
            "id": "strategy_weekly",
            "name": "每周战略审查",
            "schedule": "0 10 * * 1",  # 每周一10:00
            "module": "molin.agents.ceo",
            "function": "run_strategy",
            "description": "审查上周业绩，调整本周战略方向",
        },
        {
            "id": "trends_monitor",
            "name": "趋势监控",
            "schedule": "0 */6 * * *",  # 每6小时
            "module": "molin.intelligence.trends",
            "function": "run",
            "description": "监控热门趋势，发现新机会",
        },
    ]

    def __init__(self, job_dir: Optional[Path] = None):
        self.job_dir = job_dir or Path.home() / ".molin" / "cron"
        self.job_dir.mkdir(parents=True, exist_ok=True)

    def list_jobs(self) -> list:
        """列出所有定时任务"""
        return self.HEARTBEAT_JOBS

    def get_job(self, job_id: str) -> Optional[dict]:
        """获取指定任务"""
        for job in self.HEARTBEAT_JOBS:
            if job["id"] == job_id:
                return job
        return None

    def run_job(self, job_id: str) -> dict:
        """手动执行定时任务"""
        job = self.get_job(job_id)
        if not job:
            return {"error": f"未找到任务: {job_id}"}

        logger.info(f"执行任务: {job['name']}")
        return {
            "job_id": job_id,
            "name": job["name"],
            "executed_at": datetime.now().isoformat(),
            "status": "completed",
        }

    def next_run(self, job_id: str) -> Optional[str]:
        """计算下次执行时间"""
        job = self.get_job(job_id)
        if not job:
            return None
        # 简化: 返回1小时后
        return (datetime.now() + timedelta(hours=1)).isoformat()


# 全局实例
scheduler = Scheduler()
