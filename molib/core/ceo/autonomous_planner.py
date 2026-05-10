"""
AutonomousPlanner v6.6 — 自主规划引擎
OKR分解 + Cron调度 + 进度追踪，让系统从被动响应升级为主动干活
"""

from __future__ import annotations

import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from loguru import logger


# ── 任务生命周期 ──

class TaskStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"


@dataclass
class PlannedTask:
    task_id: str
    title: str
    agency: str
    priority: str          # "high", "medium", "low"
    status: TaskStatus = TaskStatus.PLANNED
    parent_okr: str = ""   # 所属 OKR ID
    deadline: float = 0    # Unix timestamp
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OKR:
    okr_id: str
    objective: str        # 月度目标
    key_results: List[str]  # 关键结果
    tasks: List[PlannedTask] = field(default_factory=list)
    progress: float = 0.0  # 0.0 - 1.0
    created_at: float = field(default_factory=time.time)
    deadline: float = 0


# ── OKR 分解器 ──

class OKRDecomposer:
    """月度目标 → 每日任务树"""

    def decompose(self, objective: str, key_results: List[str], month_days: int = 30) -> OKR:
        """将月度 OKR 拆解为每日子任务"""
        okr_id = f"okr_{int(time.time())}"
        okr = OKR(okr_id=okr_id, objective=objective, key_results=key_results)

        # 按子公司分配
        agency_map = {
            "接单": "cs",
            "内容": "ip",
            "发布": "ip",
            "分析": "data",
            "报价": "bd",
            "增长": "growth",
            "收入": "finance",
            "客服": "cs",
            "闲鱼": "cs",
            "小红书": "ip",
            "抖音": "ip",
            "广告": "ads",
            "合规": "legal",
        }

        task_idx = 0
        for kr in key_results:
            # 确定负责的子公司
            agency = "research"  # 默认
            for keyword, ag in agency_map.items():
                if keyword in kr:
                    agency = ag
                    break

            # 每日拆解
            daily_target = max(1, month_days // 30)
            for day in range(0, month_days, daily_target):
                task_idx += 1
                deadline = time.time() + (day + daily_target) * 86400
                task = PlannedTask(
                    task_id=f"{okr_id}_task_{task_idx}",
                    title=f"[{kr[:30]}] Day {day + 1}-{min(day + daily_target, month_days)}",
                    agency=agency,
                    priority="high" if task_idx <= 3 else "medium",
                    parent_okr=okr_id,
                    deadline=deadline,
                )
                okr.tasks.append(task)

        logger.info(f"[Planner] OKR {okr_id}: {len(okr.tasks)} tasks, {len(key_results)} KRs")
        return okr


# ── Cron 调度引擎 ──

class CronScheduler:
    """增强的定时任务调度器"""

    JOBS = [
        {
            "id": "ip_daily_content",
            "cron": "0 9 * * *",  # 每天 9:00
            "description": "IP 子公司生成当日内容草稿",
            "agency": "ip",
            "action": "generate_daily_content",
        },
        {
            "id": "content_publish",
            "cron": "0 10 * * *",  # 每天 10:00
            "description": "ContentScheduler 发布到各平台",
            "agency": "ip",
            "action": "publish_scheduled_content",
        },
        {
            "id": "xianyu_patrol",
            "cron": "*/30 * * * *",  # 每 30 分钟
            "description": "CS 巡检闲鱼未回复消息",
            "agency": "cs",
            "action": "patrol_xianyu_messages",
        },
        {
            "id": "finance_daily_report",
            "cron": "0 22 * * *",  # 每天 22:00
            "description": "Finance 生成日收支报告 → 飞书推送",
            "agency": "finance",
            "action": "generate_daily_report",
        },
        {
            "id": "ceo_daily_review",
            "cron": "0 23 * * *",  # 每天 23:00
            "description": "CEO 日复盘 (已有 daily-loop)",
            "agency": "ceo",
            "action": "daily_loop",
        },
        {
            "id": "vault_expiry_check",
            "cron": "0 8 * * *",  # 每天 8:00
            "description": "检查凭证过期，飞书通知刷新",
            "agency": "ceo",
            "action": "check_credential_expiry",
        },
    ]

    def get_due_jobs(self) -> List[Dict[str, Any]]:
        """返回所有已注册的定时任务定义"""
        return self.JOBS

    def add_job(self, job_id: str, cron: str, description: str, agency: str, action: str):
        self.JOBS.append({
            "id": job_id, "cron": cron, "description": description,
            "agency": agency, "action": action,
        })


# ── 进度追踪器 ──

class ProgressTracker:
    """自主任务生命周期追踪"""

    def __init__(self, stuck_threshold_seconds: int = 3600):
        self._tasks: Dict[str, PlannedTask] = {}
        self._stuck_threshold = stuck_threshold_seconds  # 1小时默认

    def register(self, task: PlannedTask):
        self._tasks[task.task_id] = task

    def start(self, task_id: str):
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.IN_PROGRESS
            self._tasks[task_id].started_at = time.time()

    def block(self, task_id: str, reason: str = ""):
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.BLOCKED
            self._tasks[task_id].metadata["block_reason"] = reason

    def complete(self, task_id: str):
        if task_id in self._tasks:
            self._tasks[task_id].status = TaskStatus.DONE
            self._tasks[task_id].completed_at = time.time()

    def fail(self, task_id: str, error: str = ""):
        if task_id in self._tasks:
            t = self._tasks[task_id]
            if t.retry_count < t.max_retries:
                t.retry_count += 1
                t.status = TaskStatus.PLANNED  # 回退重试
                logger.info(f"[Tracker] 任务重试: {task_id} ({t.retry_count}/{t.max_retries})")
            else:
                t.status = TaskStatus.FAILED
                logger.error(f"[Tracker] 任务失败: {task_id}, error={error[:100]}")

    def get_stuck_tasks(self) -> List[PlannedTask]:
        """检测卡住的任务（超过阈值）"""
        stuck = []
        now = time.time()
        for task in self._tasks.values():
            if task.status == TaskStatus.IN_PROGRESS and task.started_at > 0:
                if now - task.started_at > self._stuck_threshold:
                    stuck.append(task)
            elif task.status == TaskStatus.BLOCKED:
                stuck.append(task)
        return stuck

    def get_stats(self) -> Dict[str, int]:
        stats = {"total": 0, "planned": 0, "in_progress": 0, "blocked": 0, "done": 0, "failed": 0}
        for t in self._tasks.values():
            stats["total"] += 1
            stats[t.status.value] = stats.get(t.status.value, 0) + 1
        return stats


# ── 主 Planner ──

class AutonomousPlanner:
    """自主规划引擎总控"""

    def __init__(self):
        self.decomposer = OKRDecomposer()
        self.scheduler = CronScheduler()
        self.tracker = ProgressTracker()
        self._active_okrs: Dict[str, OKR] = {}

    def create_okr(self, objective: str, key_results: List[str]) -> OKR:
        okr = self.decomposer.decompose(objective, key_results)
        self._active_okrs[okr.okr_id] = okr
        for task in okr.tasks:
            self.tracker.register(task)
        return okr

    def get_daily_tasks(self) -> List[PlannedTask]:
        """获得今日应执行的任务"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()
        today_end = today_start + 86400
        tasks = []
        for okr in self._active_okrs.values():
            for task in okr.tasks:
                if today_start <= task.deadline <= today_end:
                    tasks.append(task)
        return sorted(tasks, key=lambda t: t.priority == "high", reverse=True)

    def get_blocked_summary(self) -> str:
        """生成卡住任务的飞书通知摘要"""
        stuck = self.tracker.get_stuck_tasks()
        if not stuck:
            return ""
        lines = [f"⚠️ {len(stuck)} 个任务异常："]
        for t in stuck[:5]:
            lines.append(f"- [{t.agency}] {t.title[:40]}: {t.status.value}")
        return "\n".join(lines)


# 全局单例
_planner: Optional[AutonomousPlanner] = None


def get_autonomous_planner() -> AutonomousPlanner:
    global _planner
    if _planner is None:
        _planner = AutonomousPlanner()
    return _planner
