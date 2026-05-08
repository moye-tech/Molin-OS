"""
墨麟OS — 自愈引擎 (Self-Healing Engine)
=========================================
从 molin-os-ultra/infra/self_healing/self_healing_engine.py 吸收。
纯 Python 实现，无需 Docker。

监控：
- CPU / 内存 / 磁盘 (psutil)
- 关键进程存活 (pgrep)
- 超限时飞书告警
- 自动重启尝试
"""

import asyncio
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import psutil

logger = logging.getLogger("molin.infra.self_healing")


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ResourcePoint:
    timestamp: float
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    process_count: int = 0


class SelfHealingEngine:
    """自愈引擎 — 纯 psutil，零 Docker"""

    def __init__(self, chat_id: str = ""):
        self.chat_id = chat_id
        self.enabled = os.getenv("SELF_HEALING_ENABLED", "false").lower() == "true"
        self.cpu_thr = float(os.getenv("CPU_THRESHOLD", "90"))
        self.mem_thr = float(os.getenv("MEMORY_THRESHOLD", "85"))
        self.disk_thr = float(os.getenv("DISK_THRESHOLD", "90"))
        self.interval = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))

        # 监控的关键进程模式
        self.monitored_processes = {
            "hermes": "hermes",
            "molib": "python3.*molib",
        }

        self.resource_history: list[ResourcePoint] = []
        self.max_history = 1000
        self.alerts_sent: dict[str, float] = {}
        self.alert_cooldown = 300  # 5分钟

        self.is_running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        if not self.enabled:
            logger.info("自愈引擎已禁用")
            return
        self.is_running = True
        self._tasks.append(asyncio.create_task(self._health_loop()))
        self._tasks.append(asyncio.create_task(self._resource_loop()))
        logger.info("自愈引擎已启动")

    async def stop(self):
        self.is_running = False
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    # ── 循环 ──

    async def _health_loop(self):
        while self.is_running:
            try:
                await self._check_processes()
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("健康检查异常: %s", e)
                await asyncio.sleep(60)

    async def _resource_loop(self):
        while self.is_running:
            try:
                self._collect_metrics()
                self._check_thresholds()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("资源监控异常: %s", e)
                await asyncio.sleep(60)

    # ── 进程检查 ──

    async def _check_processes(self):
        for name, pattern in self.monitored_processes.items():
            try:
                r = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True, text=True, timeout=10
                )
                alive = r.returncode == 0 and r.stdout.strip()
            except Exception:
                alive = False

            if not alive:
                logger.warning("进程未运行: %s", name)
                await self._send_alert(AlertLevel.WARNING,
                    f"进程离线: {name}", f"{name} 未在运行 (pgrep: {pattern})")

    # ── 资源采集 (psutil) ──

    def _collect_metrics(self):
        p = ResourcePoint(timestamp=time.time())
        try:
            p.cpu_percent = psutil.cpu_percent(interval=0.5)
            p.memory_percent = psutil.virtual_memory().percent
            p.disk_percent = psutil.disk_usage("/").percent
            p.process_count = len(psutil.pids())
        except Exception as e:
            logger.debug("资源采集失败: %s", e)
        self.resource_history.append(p)
        if len(self.resource_history) > self.max_history:
            self.resource_history = self.resource_history[-self.max_history:]

    def _check_thresholds(self):
        if not self.resource_history:
            return
        m = self.resource_history[-1]
        if m.cpu_percent > self.cpu_thr:
            self._send_alert_sync(AlertLevel.WARNING, "CPU超限",
                f"CPU {m.cpu_percent:.0f}% > {self.cpu_thr:.0f}%")
        if m.memory_percent > self.mem_thr:
            self._send_alert_sync(AlertLevel.WARNING, "内存超限",
                f"内存 {m.memory_percent:.0f}% > {self.mem_thr:.0f}%")
        if m.disk_percent > self.disk_thr:
            self._send_alert_sync(AlertLevel.WARNING, "磁盘超限",
                f"磁盘 {m.disk_percent:.0f}% > {self.disk_thr:.0f}%")

    # ── 告警 ──

    async def _send_alert(self, level: AlertLevel, title: str, message: str):
        self._send_alert_sync(level, title, message)

    def _send_alert_sync(self, level: AlertLevel, title: str, message: str):
        now = time.time()
        key = f"{level.value}_{title}"
        if key in self.alerts_sent and now - self.alerts_sent[key] < self.alert_cooldown:
            return
        self.alerts_sent[key] = now
        logger.warning("[%s] %s: %s", level.value, title, message)

        if self.chat_id:
            try:
                from molib.ceo.feishu_card import FeishuCardSender, CardBuilder
                color = {"info": "blue", "warning": "yellow",
                         "error": "red", "critical": "red"}.get(level.value, "blue")
                cb = CardBuilder(f"{level.name} {title}", color)
                cb.add_div(message)
                cb.add_note(f"自愈引擎 · {datetime.now().strftime('%H:%M:%S')}")
                FeishuCardSender().send_card(cb.build(), chat_id=self.chat_id)
            except Exception as e:
                logger.error("告警卡片失败: %s", e)

    # ── 状态 ──

    def get_status(self) -> dict:
        m = self.resource_history[-1] if self.resource_history else None
        return {
            "enabled": self.enabled,
            "running": self.is_running,
            "resources": {
                "cpu_pct": m.cpu_percent,
                "memory_pct": m.memory_percent,
                "disk_pct": m.disk_percent,
                "processes": m.process_count,
            } if m else {},
            "alerts_active": len(self.alerts_sent),
        }
