"""自主规划引擎 — OKR分解 + 进度追踪
适配自 molin-os-ultra v6.6.0 core/ceo/autonomous_planner.py
适配: loguru→logging, 去掉ModelRouter/CronScheduler耦合
"""
from __future__ import annotations

import json
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


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
    priority: str = "medium"
    status: TaskStatus = TaskStatus.PLANNED
    parent_okr: str = ""
    deadline: float = 0
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OKR:
    okr_id: str
    objective: str
    key_results: List[str]
    tasks: List[PlannedTask] = field(default_factory=list)
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    deadline: float = 0


class ProgressTracker:
    """自主任务生命周期追踪"""
    def __init__(self, stuck_threshold_seconds: int = 3600):
        self._tasks: Dict[str, PlannedTask] = {}
        self._stuck_threshold = stuck_threshold_seconds

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
                t.status = TaskStatus.PLANNED
                logger.info(f"[Tracker] 任务重试: {task_id} ({t.retry_count}/{t.max_retries})")
            else:
                t.status = TaskStatus.FAILED
                logger.error(f"[Tracker] 任务失败: {task_id}, error={error[:100]}")

    def get_stuck_tasks(self) -> List[PlannedTask]:
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


class AutonomousPlanner:
    """自主规划引擎总控"""
    def __init__(self):
        self.tracker = ProgressTracker()
        self._active_okrs: Dict[str, OKR] = {}

    def create_okr(self, objective: str, key_results: List[str]) -> OKR:
        okr_id = f"okr_{int(time.time())}"
        okr = OKR(okr_id=okr_id, objective=objective, key_results=key_results)
        self._active_okrs[okr_id] = okr
        logger.info(f"[Planner] OKR {okr_id}: objective={objective[:40]}...")
        return okr

    def add_task_to_okr(self, okr_id: str, task: PlannedTask):
        if okr_id in self._active_okrs:
            self._active_okrs[okr_id].tasks.append(task)
            self.tracker.register(task)
            logger.info(f"[Planner] 添加任务: {task.title} → {okr_id} ({task.agency})")

    def get_daily_tasks(self) -> List[PlannedTask]:
        today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()
        today_end = today_start + 86400
        tasks = []
        for okr in self._active_okrs.values():
            for task in okr.tasks:
                if today_start <= task.deadline <= today_end:
                    tasks.append(task)
        return sorted(tasks, key=lambda t: t.priority == "high", reverse=True)

    def get_all_tasks(self) -> List[PlannedTask]:
        tasks = []
        for okr in self._active_okrs.values():
            tasks.extend(okr.tasks)
        return tasks

    def get_blocked_summary(self) -> str:
        stuck = self.tracker.get_stuck_tasks()
        if not stuck:
            return ""
        lines = [f"⚠️ {len(stuck)} 个任务异常："]
        for t in stuck[:5]:
            lines.append(f"- [{t.agency}] {t.title[:40]}: {t.status.value}")
        return "\n".join(lines)


_planner: Optional[AutonomousPlanner] = None


def get_autonomous_planner() -> AutonomousPlanner:
    global _planner
    if _planner is None:
        _planner = AutonomousPlanner()
    return _planner
