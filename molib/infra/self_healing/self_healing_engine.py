"""
自愈引擎 - 零停机自动恢复系统
监控系统健康状态，自动重启失败服务，管理资源使用
"""

import os
import time
import asyncio
import subprocess
import psutil
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from molib.utils.alerts import send_alert


class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    RESTARTING = "restarting"
    STOPPED = "stopped"
    UNKNOWN = "unknown"


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ServiceHealth:
    """服务健康状态"""
    name: str
    status: ServiceStatus
    uptime: float  # 秒
    restart_count: int
    last_restart_time: Optional[datetime]
    error_message: Optional[str] = None


@dataclass
class ResourceMetrics:
    """资源指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_counters: Optional[Dict[str, Any]] = None
    process_count: Optional[int] = None


class SelfHealingEngine:
    """自愈引擎主类"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化自愈引擎

        Args:
            config: 配置字典，可以从环境变量加载
        """
        self.config = config or self._load_config_from_env()
        self.enabled = self.config.get("enabled", True)
        self.health_check_interval = self.config.get("health_check_interval_seconds", 300)
        self.auto_restart_threshold = self.config.get("auto_restart_threshold", 3)
        self.auto_restart_window = self.config.get("auto_restart_window_minutes", 60)
        self.resource_monitoring_enabled = self.config.get("resource_monitoring_enabled", True)

        # 资源阈值
        self.cpu_threshold = self.config.get("cpu_threshold_percent", 80)
        self.memory_threshold = self.config.get("memory_threshold_percent", 85)
        self.disk_threshold = self.config.get("disk_threshold_percent", 90)
        self.alert_escalation_minutes = self.config.get("alert_escalation_minutes", 30)

        # 服务状态跟踪
        self.service_health: Dict[str, ServiceHealth] = {}
        self.service_restart_history: Dict[str, List[datetime]] = {}
        self.failure_counters: Dict[str, int] = {}

        # 资源监控
        self.resource_metrics_history: List[ResourceMetrics] = []
        self.max_history_size = 1000

        # 告警状态
        self.alerts_sent: Dict[str, datetime] = {}
        self.alert_cooldown = timedelta(minutes=5)

        # 业务指标监控（v6.6 新增）
        self.business_metrics: Dict[str, Any] = {
            "fallback_rate": 0.0,
            "worker_success_rate": 0.0,
            "worker_import_fallbacks": 0,
            "llm_fallbacks": 0,
            "worker_executions": 0,
            "worker_successes": 0,
        }
        self.fallback_rate_threshold = self.config.get("fallback_rate_threshold", 0.3)
        self.worker_success_rate_threshold = self.config.get("worker_success_rate_threshold", 0.8)

        # 运行状态
        self.is_running = False
        self.health_check_task: Optional[asyncio.Task] = None
        self.resource_monitor_task: Optional[asyncio.Task] = None

        # 裸机部署：服务监控列表（默认 redis/qdrant 为 Docker 容器，molin 为 systemd）
        self.monitored_services = self.config.get("monitored_services", ["redis", "qdrant", "molin"])

        if self.enabled:
            logger.info("自愈引擎初始化成功")
            logger.info(f"健康检查间隔: {self.health_check_interval}秒")
            logger.info(f"自动重启阈值: {self.auto_restart_threshold}次/{self.auto_restart_window}分钟")
        else:
            logger.info("自愈引擎已禁用")

    def _load_config_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        return {
            "enabled": os.getenv("SELF_HEALING_ENABLED", "true").lower() == "true",
            "health_check_interval_seconds": int(os.getenv("HEALTH_CHECK_INTERVAL_SECONDS", "300")),
            "auto_restart_threshold": int(os.getenv("AUTO_RESTART_THRESHOLD", "3")),
            "auto_restart_window_minutes": int(os.getenv("AUTO_RESTART_WINDOW_MINUTES", "60")),
            "resource_monitoring_enabled": os.getenv("RESOURCE_MONITORING_ENABLED", "true").lower() == "true",
            "cpu_threshold_percent": float(os.getenv("CPU_THRESHOLD_PERCENT", "80")),
            "memory_threshold_percent": float(os.getenv("MEMORY_THRESHOLD_PERCENT", "85")),
            "disk_threshold_percent": float(os.getenv("DISK_THRESHOLD_PERCENT", "90")),
            "alert_escalation_minutes": int(os.getenv("ALERT_ESCALATION_MINUTES", "30")),
            "monitored_services": self._parse_monitored_services()
        }

    def _parse_monitored_services(self) -> List[str]:
        """解析要监控的服务列表（裸机部署兼容）"""
        services_env = os.getenv("MONITORED_SERVICES", "")
        if services_env:
            return [s.strip() for s in services_env.split(",") if s.strip()]
        # 裸机默认: redis/qdrant (Docker 容器), molin (systemd)
        return ["redis", "qdrant", "molin"]

    async def start(self):
        """启动自愈引擎"""
        if not self.enabled:
            logger.info("自愈引擎已禁用，不启动")
            return

        self.is_running = True

        # 启动健康检查任务
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("健康检查循环已启动")

        # 启动资源监控任务
        if self.resource_monitoring_enabled:
            self.resource_monitor_task = asyncio.create_task(self._resource_monitor_loop())
            logger.info("资源监控循环已启动")

        logger.info("自愈引擎已启动")

    async def stop(self):
        """停止自愈引擎"""
        self.is_running = False

        # 取消任务
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        if self.resource_monitor_task:
            self.resource_monitor_task.cancel()
            try:
                await self.resource_monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("自愈引擎已停止")

    async def _health_check_loop(self):
        """健康检查循环"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟

    async def _resource_monitor_loop(self):
        """资源监控循环"""
        check_interval = 60  # 资源检查间隔60秒

        while self.is_running:
            try:
                await self._collect_resource_metrics()
                await self._check_resource_thresholds()
                await asyncio.sleep(check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"资源监控循环出错: {e}")
                await asyncio.sleep(60)

    async def _perform_health_checks(self):
        """执行健康检查"""
        logger.debug("执行健康检查...")

        # 检查Docker服务
        if self.monitored_services:
            await self._check_docker_services()
        else:
            # 如果没有指定服务，进行基本的系统健康检查
            await self._check_system_health()

        # 清理旧的历史记录
        self._cleanup_old_history()

        # 检查业务指标（v6.6 新增）
        await self._check_business_metrics()

    async def _check_docker_services(self):
        """检查服务健康状态（裸机部署：Docker容器 + systemd）"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode != 0:
                logger.error(f"获取Docker容器列表失败: {result.stderr}")
                return
            docker_services = set(result.stdout.strip().split("\n")) if result.stdout.strip() else set()

            for service_name in self.monitored_services:
                if service_name in ("redis", "qdrant"):
                    if service_name in docker_services:
                        await self._check_single_service(service_name)
                    else:
                        logger.warning(f"Docker 容器 {service_name} 未运行")
                elif service_name == "molin":
                    # 裸机: 通过 HTTP health 检查
                    try:
                        import httpx
                        async with httpx.AsyncClient() as client:
                            resp = await client.get("http://localhost:8000/health", timeout=10)
                            if resp.status_code == 200:
                                logger.debug("molin 健康检查通过")
                            else:
                                logger.warning(f"molin 健康检查异常: HTTP {resp.status_code}")
                    except Exception as e:
                        logger.warning(f"molin 健康检查失败: {e}")

        except subprocess.TimeoutExpired:
            logger.error("检查服务超时")
        except Exception as e:
            logger.error(f"检查服务时出错: {e}")

    async def _check_single_service(self, service_name: str):
        """检查单个 Docker 容器状态"""
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Status}}", service_name],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                status = ServiceStatus.UNKNOWN
                error_msg = result.stderr[:100] if result.stderr else "未知错误"
            else:
                state = result.stdout.strip().lower()
                if state == "running":
                    status = ServiceStatus.HEALTHY
                elif "restart" in state:
                    status = ServiceStatus.RESTARTING
                else:
                    status = ServiceStatus.STOPPED

                error_msg = None

            # 更新服务健康状态
            current_time = datetime.now()

            if service_name not in self.service_health:
                self.service_health[service_name] = ServiceHealth(
                    name=service_name,
                    status=status,
                    uptime=0,
                    restart_count=0,
                    last_restart_time=None
                )

            health = self.service_health[service_name]

            # 检查状态变化
            if health.status != status:
                logger.info(f"服务 {service_name} 状态变化: {health.status.value} -> {status.value}")

                # 处理故障
                if status in [ServiceStatus.UNHEALTHY, ServiceStatus.STOPPED, ServiceStatus.UNKNOWN]:
                    await self._handle_service_failure(service_name, status, error_msg)

                # 更新状态
                health.status = status
                health.error_message = error_msg

            # 记录日志
            if status != ServiceStatus.HEALTHY:
                logger.warning(f"服务 {service_name} 状态异常: {status.value}")

        except Exception as e:
            logger.error(f"检查服务 {service_name} 时出错: {e}")

    async def _handle_service_failure(self, service_name: str, status: ServiceStatus, error_msg: str = None):
        """处理服务故障"""
        current_time = datetime.now()

        # 更新故障计数器
        if service_name not in self.failure_counters:
            self.failure_counters[service_name] = 0
        self.failure_counters[service_name] += 1

        # 更新重启历史
        if service_name not in self.service_restart_history:
            self.service_restart_history[service_name] = []

        # 发送告警
        alert_key = f"service_failure_{service_name}"
        await self._send_alert(
            level=AlertLevel.ERROR,
            title=f"服务故障: {service_name}",
            message=f"服务 {service_name} 状态异常: {status.value}\n错误: {error_msg or '未知'}",
            alert_key=alert_key
        )

        # 检查是否需要自动重启
        restart_history = self.service_restart_history[service_name]

        # 清理超过时间窗口的历史记录
        window_start = current_time - timedelta(minutes=self.auto_restart_window)
        recent_restarts = [rt for rt in restart_history if rt > window_start]

        if len(recent_restarts) >= self.auto_restart_threshold:
            logger.warning(f"服务 {service_name} 在 {self.auto_restart_window} 分钟内重启了 {len(recent_restarts)} 次，超过阈值 {self.auto_restart_threshold}")
            await self._send_alert(
                level=AlertLevel.CRITICAL,
                title=f"服务频繁重启: {service_name}",
                message=f"服务 {service_name} 在 {self.auto_restart_window} 分钟内重启了 {len(recent_restarts)} 次，需要人工干预",
                alert_key=f"frequent_restart_{service_name}"
            )
        else:
            # 尝试自动重启
            logger.info(f"尝试自动重启服务: {service_name}")
            await self._restart_service(service_name)

            # 记录重启时间
            self.service_restart_history[service_name].append(current_time)

    async def _restart_service(self, service_name: str) -> bool:
        """重启服务（裸机部署：Docker容器 / systemd）"""
        try:
            logger.info(f"正在重启服务: {service_name}")

            if service_name in ("redis", "qdrant"):
                cmd = ["docker", "restart", service_name]
            elif service_name == "molin":
                cmd = ["sudo", "systemctl", "restart", "molin"]
            else:
                cmd = ["docker", "restart", service_name]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                logger.info(f"服务 {service_name} 重启成功")
                await self._send_alert(
                    level=AlertLevel.INFO,
                    title=f"服务已重启: {service_name}",
                    message=f"服务 {service_name} 已自动重启成功",
                    alert_key=f"service_restarted_{service_name}"
                )
                return True
            else:
                logger.error(f"服务 {service_name} 重启失败: {result.stderr}")
                await self._send_alert(
                    level=AlertLevel.ERROR,
                    title=f"服务重启失败: {service_name}",
                    message=f"服务 {service_name} 自动重启失败:\n{result.stderr[:200]}",
                    alert_key=f"restart_failed_{service_name}"
                )
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"服务 {service_name} 重启超时")
            await self._send_alert(
                level=AlertLevel.ERROR,
                title=f"服务重启超时: {service_name}",
                message=f"服务 {service_name} 重启操作超时",
                alert_key=f"restart_timeout_{service_name}"
            )
            return False
        except Exception as e:
            logger.error(f"重启服务 {service_name} 时出错: {e}")
            return False

    async def _check_system_health(self):
        """检查系统健康状态（基本检查）"""
        try:
            # 检查磁盘空间
            disk_usage = psutil.disk_usage('/')
            if disk_usage.percent > self.disk_threshold:
                await self._send_alert(
                    level=AlertLevel.WARNING,
                    title="磁盘空间不足",
                    message=f"磁盘使用率: {disk_usage.percent}% (阈值: {self.disk_threshold}%)",
                    alert_key="disk_usage_high"
                )

            # 检查内存使用
            memory = psutil.virtual_memory()
            if memory.percent > self.memory_threshold:
                await self._send_alert(
                    level=AlertLevel.WARNING,
                    title="内存使用率高",
                    message=f"内存使用率: {memory.percent}% (阈值: {self.memory_threshold}%)",
                    alert_key="memory_usage_high"
                )

        except Exception as e:
            logger.error(f"检查系统健康状态时出错: {e}")

    async def _collect_resource_metrics(self):
        """收集资源指标"""
        try:
            timestamp = datetime.now()

            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # 网络IO
            net_io = psutil.net_io_counters()
            network_io_counters = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }

            # 进程数量
            process_count = len(psutil.pids())

            metrics = ResourceMetrics(
                timestamp=timestamp,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io_counters=network_io_counters,
                process_count=process_count
            )

            # 保存到历史
            self.resource_metrics_history.append(metrics)

            # 限制历史记录大小
            if len(self.resource_metrics_history) > self.max_history_size:
                self.resource_metrics_history = self.resource_metrics_history[-self.max_history_size:]

            logger.debug(f"资源指标收集完成: CPU={cpu_percent}%, Memory={memory_percent}%, Disk={disk_percent}%")

        except Exception as e:
            logger.error(f"收集资源指标时出错: {e}")

    async def _check_resource_thresholds(self):
        """检查资源阈值"""
        if not self.resource_metrics_history:
            return

        latest_metrics = self.resource_metrics_history[-1]

        # 检查CPU阈值
        if latest_metrics.cpu_percent > self.cpu_threshold:
            await self._send_alert(
                level=AlertLevel.WARNING,
                title="CPU使用率高",
                message=f"CPU使用率: {latest_metrics.cpu_percent:.1f}% (阈值: {self.cpu_threshold}%)",
                alert_key="cpu_usage_high"
            )

        # 检查内存阈值
        if latest_metrics.memory_percent > self.memory_threshold:
            await self._send_alert(
                level=AlertLevel.WARNING,
                title="内存使用率高",
                message=f"内存使用率: {latest_metrics.memory_percent:.1f}% (阈值: {self.memory_threshold}%)",
                alert_key="memory_usage_high"
            )

        # 检查磁盘阈值
        if latest_metrics.disk_percent > self.disk_threshold:
            await self._send_alert(
                level=AlertLevel.WARNING,
                title="磁盘使用率高",
                message=f"磁盘使用率: {latest_metrics.disk_percent:.1f}% (阈值: {self.disk_threshold}%)",
                alert_key="disk_usage_high"
            )

    async def _send_alert(self, level: AlertLevel, title: str, message: str, alert_key: str = None):
        """发送告警"""
        if not alert_key:
            alert_key = f"{level.value}_{hash(title)}"

        current_time = datetime.now()

        # 检查告警冷却时间
        if alert_key in self.alerts_sent:
            last_sent = self.alerts_sent[alert_key]
            if current_time - last_sent < self.alert_cooldown:
                return  # 还在冷却时间内

        try:
            # 使用现有的告警系统
            await send_alert(
                title=title,
                message=message,
                level=level.value
            )

            # 记录告警发送时间
            self.alerts_sent[alert_key] = current_time

            logger.info(f"告警已发送: {title} ({level.value})")

        except Exception as e:
            logger.error(f"发送告警失败: {e}")

    def _cleanup_old_history(self):
        """清理旧的历史记录"""
        current_time = datetime.now()
        cleanup_threshold = current_time - timedelta(hours=24)

        # 清理重启历史
        for service_name, restart_times in list(self.service_restart_history.items()):
            recent_restarts = [rt for rt in restart_times if rt > cleanup_threshold]
            if recent_restarts:
                self.service_restart_history[service_name] = recent_restarts
            else:
                del self.service_restart_history[service_name]

        # 清理旧告警
        old_alerts = [key for key, sent_time in self.alerts_sent.items() if sent_time < cleanup_threshold]
        for key in old_alerts:
            del self.alerts_sent[key]

    def get_service_health(self, service_name: str = None) -> Dict[str, Any]:
        """获取服务健康状态"""
        if service_name:
            if service_name in self.service_health:
                health = self.service_health[service_name]
                return {
                    "name": health.name,
                    "status": health.status.value,
                    "uptime": health.uptime,
                    "restart_count": health.restart_count,
                    "last_restart_time": health.last_restart_time.isoformat() if health.last_restart_time else None,
                    "error_message": health.error_message
                }
            else:
                return {"error": f"服务 {service_name} 未找到"}

        # 返回所有服务状态
        return {
            service_name: {
                "status": health.status.value,
                "uptime": health.uptime,
                "restart_count": health.restart_count,
                "last_restart_time": health.last_restart_time.isoformat() if health.last_restart_time else None
            }
            for service_name, health in self.service_health.items()
        }

    def get_resource_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取资源指标历史"""
        metrics_list = self.resource_metrics_history[-limit:] if self.resource_metrics_history else []

        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "disk_percent": m.disk_percent,
                "process_count": m.process_count
            }
            for m in metrics_list
        ]

    def update_business_metrics(self, manager_metrics: Dict[str, Any]) -> None:
        """更新业务指标（由 Manager 定期上报）"""
        self.business_metrics.update(manager_metrics)
        worker_executions = self.business_metrics.get("worker_executions", 0)
        worker_successes = self.business_metrics.get("worker_successes", 0)
        self.business_metrics["worker_success_rate"] = (
            round(worker_successes / worker_executions, 4) if worker_executions > 0 else 0
        )
        total_tasks = self.business_metrics.get("total_tasks", 0)
        llm_fallbacks = self.business_metrics.get("llm_fallbacks", 0)
        self.business_metrics["fallback_rate"] = (
            round(llm_fallbacks / total_tasks, 4) if total_tasks > 0 else 0
        )

    async def _check_business_metrics(self) -> None:
        """检查业务指标阈值，超标则告警"""
        fallback_rate = self.business_metrics.get("fallback_rate", 0)
        if fallback_rate > self.fallback_rate_threshold:
            await self._send_alert(
                level=AlertLevel.WARNING,
                title="Manager Fallback 率过高",
                message=f"当前 fallback_rate={fallback_rate:.1%} (阈值: {self.fallback_rate_threshold:.0%})，大量任务退化为 LLM 直接执行",
                alert_key="high_fallback_rate"
            )

        worker_success_rate = self.business_metrics.get("worker_success_rate", 0)
        if worker_success_rate > 0 and worker_success_rate < self.worker_success_rate_threshold:
            await self._send_alert(
                level=AlertLevel.WARNING,
                title="Worker 执行成功率过低",
                message=f"当前 worker_success_rate={worker_success_rate:.1%} (阈值: {self.worker_success_rate_threshold:.0%})",
                alert_key="low_worker_success_rate"
            )

    def get_business_metrics(self) -> Dict[str, Any]:
        """获取业务指标"""
        return {
            **self.business_metrics,
            "fallback_rate_threshold": self.fallback_rate_threshold,
            "worker_success_rate_threshold": self.worker_success_rate_threshold,
        }

    def get_engine_status(self) -> Dict[str, Any]:
        """获取引擎状态"""
        return {
            "enabled": self.enabled,
            "is_running": self.is_running,
            "health_check_interval": self.health_check_interval,
            "monitored_services_count": len(self.monitored_services),
            "service_health_count": len(self.service_health),
            "resource_metrics_count": len(self.resource_metrics_history),
            "active_alerts_count": len(self.alerts_sent),
            "failure_counters": self.failure_counters
        }

    def manual_restart_service(self, service_name: str) -> Dict[str, Any]:
        """手动重启服务"""
        if not self.enabled:
            return {"success": False, "error": "自愈引擎已禁用"}

        try:
            # 使用同步方式调用异步方法
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self._restart_service(service_name))
            loop.close()

            return {"success": success, "service": service_name}
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局单例实例
_self_healing_engine = None


async def get_self_healing_engine() -> SelfHealingEngine:
    """获取自愈引擎单例"""
    global _self_healing_engine
    if _self_healing_engine is None:
        _self_healing_engine = SelfHealingEngine()
        await _self_healing_engine.start()
    return _self_healing_engine


def initialize_self_healing() -> SelfHealingEngine:
    """初始化自愈引擎（同步版本）"""
    import asyncio
    engine = SelfHealingEngine()

    # 启动引擎
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(engine.start())

    return engine