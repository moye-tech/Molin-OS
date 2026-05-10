"""
审计日志器 - 零泄漏安全策略
记录所有安全相关事件和用户操作
"""

import os
import json
import sqlite3
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger


class AuditLogger:
    """审计日志器，记录所有安全相关事件"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化审计日志器

        Args:
            config: 审计日志配置
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.level = config.get("level", "info").lower()
        self.events_to_log = set(config.get("events_to_log", []))
        self.storage_config = config.get("storage", {})

        # 日志存储
        self.storage_type = self.storage_config.get("type", "sqlite")
        self.table_name = self.storage_config.get("table_name", "security_audit_logs")
        self.retention_days = self.storage_config.get("retention_days", 90)

        # 内存缓存（用于批量写入）
        self._log_buffer: List[Dict[str, Any]] = []
        self._buffer_max_size = 100
        self._last_flush_time = time.time()

        # 统计信息
        self._stats = {
            "total_events_logged": 0,
            "events_by_type": defaultdict(int),
            "events_by_level": defaultdict(int),
            "storage_errors": 0,
            "last_flush_time": None,
            "buffer_size": 0
        }

        if self.enabled:
            self._initialize_storage()
            logger.info(f"审计日志器初始化成功，存储类型: {self.storage_type}")
        else:
            logger.info("审计日志器已禁用")

    def _initialize_storage(self):
        """初始化日志存储"""
        try:
            if self.storage_type == "sqlite":
                self._init_sqlite_storage()
            elif self.storage_type == "file":
                self._init_file_storage()
            elif self.storage_type == "memory":
                self._init_memory_storage()
            else:
                logger.warning(f"不支持的存储类型: {self.storage_type}，使用内存存储")
                self._init_memory_storage()

        except Exception as e:
            logger.error(f"初始化审计日志存储失败: {e}")
            self.enabled = False

    def _init_sqlite_storage(self):
        """初始化SQLite存储"""
        try:
            # 获取数据库路径
            db_path_env = os.getenv("SQLITE_DB_PATH", "/app/data/hermes.db")
            db_path = Path(db_path_env)

            # 确保目录存在
            db_path.parent.mkdir(parents=True, exist_ok=True)

            self.db_path = str(db_path)
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row

            # 创建审计日志表
            cursor = self.connection.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    event_level TEXT NOT NULL,
                    user_id TEXT,
                    ip_address TEXT,
                    resource TEXT,
                    action TEXT,
                    status TEXT,
                    details TEXT,
                    metadata TEXT
                )
            """)

            # 创建索引以提高查询性能
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_timestamp ON {self.table_name}(timestamp)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_event_type ON {self.table_name}(event_type)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_user_id ON {self.table_name}(user_id)")

            self.connection.commit()
            logger.info(f"SQLite审计日志表已初始化: {self.table_name}")

        except Exception as e:
            logger.error(f"初始化SQLite存储失败: {e}")
            raise

    def _init_file_storage(self):
        """初始化文件存储"""
        try:
            log_dir = Path(self.storage_config.get("directory", "/app/logs/audit"))
            log_dir.mkdir(parents=True, exist_ok=True)

            self.log_file_path = log_dir / "audit.log"
            logger.info(f"审计日志文件: {self.log_file_path}")

        except Exception as e:
            logger.error(f"初始化文件存储失败: {e}")
            raise

    def _init_memory_storage(self):
        """初始化内存存储"""
        self.memory_logs: List[Dict[str, Any]] = []
        logger.info("审计日志使用内存存储（重启后数据将丢失）")

    def log_event(self, event_type: str, event_data: Dict[str, Any],
                  user_id: str = None, ip_address: str = None,
                  resource: str = None, action: str = None,
                  status: str = "success", level: str = None):
        """
        记录审计事件

        Args:
            event_type: 事件类型
            event_data: 事件数据
            user_id: 用户ID
            ip_address: IP地址
            resource: 资源标识符
            action: 操作类型
            status: 操作状态（success, failure, warning）
            level: 日志级别（info, warning, error）
        """
        if not self.enabled:
            return

        # 检查是否应该记录此事件类型
        if self.events_to_log and event_type not in self.events_to_log:
            return

        # 确定日志级别
        if level is None:
            level = self._determine_level(event_type, status)

        # 检查日志级别过滤
        if not self._should_log_level(level):
            return

        try:
            # 构建日志条目
            log_entry = {
                "timestamp": time.time(),
                "event_type": event_type,
                "event_level": level,
                "user_id": user_id,
                "ip_address": ip_address,
                "resource": resource,
                "action": action,
                "status": status,
                "details": json.dumps(event_data, ensure_ascii=False),
                "metadata": json.dumps({
                    "source": "audit_logger",
                    "app_version": os.getenv("APP_VERSION", "v6.6"),
                    "environment": os.getenv("ENVIRONMENT", "development")
                }, ensure_ascii=False)
            }

            # 添加到缓冲区
            self._log_buffer.append(log_entry)
            self._stats["buffer_size"] = len(self._log_buffer)

            # 更新统计信息
            self._stats["total_events_logged"] += 1
            self._stats["events_by_type"][event_type] += 1
            self._stats["events_by_level"][level] += 1

            # 检查是否需要刷新缓冲区
            if (len(self._log_buffer) >= self._buffer_max_size or
                time.time() - self._last_flush_time > 30):  # 每30秒强制刷新
                self._flush_buffer()

            logger.debug(f"审计事件已记录: {event_type} ({level})")

        except Exception as e:
            logger.error(f"记录审计事件失败: {e}")
            self._stats["storage_errors"] += 1

    def _determine_level(self, event_type: str, status: str) -> str:
        """根据事件类型和状态确定日志级别"""
        # 定义事件级别映射
        level_mapping = {
            "user_login": "info",
            "user_logout": "info",
            "data_access": "info",
            "configuration_change": "warning",
            "security_event": "error",
            "failed_login": "warning",
            "permission_denied": "warning",
            "rate_limit_exceeded": "warning",
            "sql_injection_attempt": "error",
            "xss_attempt": "error",
        }

        # 从映射中获取级别，或使用默认值
        level = level_mapping.get(event_type, "info")

        # 根据状态调整级别
        if status == "failure" and level == "info":
            level = "warning"
        elif status == "failure" and level == "warning":
            level = "error"

        return level

    def _should_log_level(self, level: str) -> bool:
        """检查是否应该记录此级别"""
        level_priority = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }

        current_priority = level_priority.get(self.level, 1)
        event_priority = level_priority.get(level, 0)

        return event_priority >= current_priority

    def _flush_buffer(self):
        """刷新缓冲区，将日志写入存储"""
        if not self._log_buffer:
            return

        try:
            if self.storage_type == "sqlite":
                self._flush_to_sqlite()
            elif self.storage_type == "file":
                self._flush_to_file()
            elif self.storage_type == "memory":
                self._flush_to_memory()

            self._last_flush_time = time.time()
            self._stats["last_flush_time"] = datetime.now().isoformat()
            self._log_buffer.clear()
            self._stats["buffer_size"] = 0

            # 执行清理任务（定期）
            if self._stats["total_events_logged"] % 1000 == 0:
                self._cleanup_old_logs()

        except Exception as e:
            logger.error(f"刷新审计日志缓冲区失败: {e}")
            self._stats["storage_errors"] += 1

    def _flush_to_sqlite(self):
        """将缓冲区写入SQLite"""
        try:
            cursor = self.connection.cursor()

            for log_entry in self._log_buffer:
                cursor.execute(f"""
                    INSERT INTO {self.table_name}
                    (timestamp, event_type, event_level, user_id, ip_address,
                     resource, action, status, details, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_entry["timestamp"],
                    log_entry["event_type"],
                    log_entry["event_level"],
                    log_entry["user_id"],
                    log_entry["ip_address"],
                    log_entry["resource"],
                    log_entry["action"],
                    log_entry["status"],
                    log_entry["details"],
                    log_entry["metadata"]
                ))

            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            raise

    def _flush_to_file(self):
        """将缓冲区写入文件"""
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                for log_entry in self._log_buffer:
                    log_line = json.dumps(log_entry, ensure_ascii=False)
                    f.write(log_line + '\n')
        except Exception as e:
            raise

    def _flush_to_memory(self):
        """将缓冲区写入内存"""
        self.memory_logs.extend(self._log_buffer)

    def _cleanup_old_logs(self):
        """清理旧日志"""
        try:
            if self.storage_type == "sqlite":
                cutoff_time = time.time() - (self.retention_days * 86400)
                cursor = self.connection.cursor()
                cursor.execute(f"DELETE FROM {self.table_name} WHERE timestamp < ?", (cutoff_time,))
                deleted_count = cursor.rowcount
                self.connection.commit()

                if deleted_count > 0:
                    logger.info(f"清理了 {deleted_count} 条旧审计日志")

            # 对于文件存储，需要定期手动清理
            # 对于内存存储，自动清理

        except Exception as e:
            logger.error(f"清理旧审计日志失败: {e}")

    def query_logs(self, start_time: float = None, end_time: float = None,
                   event_type: str = None, user_id: str = None,
                   level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """查询审计日志"""
        if not self.enabled:
            return []

        try:
            # 先刷新缓冲区以确保查询最新数据
            self._flush_buffer()

            if self.storage_type == "sqlite":
                return self._query_sqlite_logs(start_time, end_time, event_type, user_id, level, limit)
            elif self.storage_type == "file":
                return self._query_file_logs(start_time, end_time, event_type, user_id, level, limit)
            elif self.storage_type == "memory":
                return self._query_memory_logs(start_time, end_time, event_type, user_id, level, limit)
            else:
                return []

        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return []

    def _query_sqlite_logs(self, start_time, end_time, event_type, user_id, level, limit):
        """查询SQLite日志"""
        query = f"SELECT * FROM {self.table_name} WHERE 1=1"
        params = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if level:
            query += " AND event_level = ?"
            params.append(level)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = self.connection.cursor()
        cursor.execute(query, params)

        logs = []
        for row in cursor.fetchall():
            log_dict = dict(row)
            # 解析JSON字段
            if log_dict.get("details"):
                log_dict["details"] = json.loads(log_dict["details"])
            if log_dict.get("metadata"):
                log_dict["metadata"] = json.loads(log_dict["metadata"])

            logs.append(log_dict)

        return logs

    def _query_file_logs(self, start_time, end_time, event_type, user_id, level, limit):
        """查询文件日志"""
        logs = []
        try:
            if not os.path.exists(self.log_file_path):
                return []

            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        # 应用过滤器
                        if start_time and log_entry.get("timestamp", 0) < start_time:
                            continue
                        if end_time and log_entry.get("timestamp", 0) > end_time:
                            continue
                        if event_type and log_entry.get("event_type") != event_type:
                            continue
                        if user_id and log_entry.get("user_id") != user_id:
                            continue
                        if level and log_entry.get("event_level") != level:
                            continue

                        logs.append(log_entry)

                        if len(logs) >= limit:
                            break

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"读取文件日志失败: {e}")

        return logs

    def _query_memory_logs(self, start_time, end_time, event_type, user_id, level, limit):
        """查询内存日志"""
        logs = []
        for log_entry in reversed(self.memory_logs):  # 反向遍历以获取最新日志
            # 应用过滤器
            if start_time and log_entry.get("timestamp", 0) < start_time:
                continue
            if end_time and log_entry.get("timestamp", 0) > end_time:
                continue
            if event_type and log_entry.get("event_type") != event_type:
                continue
            if user_id and log_entry.get("user_id") != user_id:
                continue
            if level and log_entry.get("event_level") != level:
                continue

            logs.append(log_entry)

            if len(logs) >= limit:
                break

        return logs

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "enabled": self.enabled,
            "storage_type": self.storage_type,
            "retention_days": self.retention_days,
            "events_to_log_count": len(self.events_to_log)
        }

    def export_logs(self, output_path: str, format: str = "json"):
        """导出审计日志"""
        try:
            # 获取所有日志
            all_logs = self.query_logs(limit=10000)

            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(all_logs, f, ensure_ascii=False, indent=2)
            elif format == "csv":
                import csv
                if all_logs:
                    fieldnames = all_logs[0].keys()
                    with open(output_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(all_logs)

            logger.info(f"审计日志已导出到: {output_path} ({len(all_logs)} 条记录)")
            return True

        except Exception as e:
            logger.error(f"导出审计日志失败: {e}")
            return False

    def close(self):
        """关闭审计日志器"""
        try:
            # 刷新剩余缓冲区
            self._flush_buffer()

            if self.storage_type == "sqlite" and hasattr(self, 'connection'):
                self.connection.close()
                logger.info("审计日志SQLite连接已关闭")

        except Exception as e:
            logger.error(f"关闭审计日志器失败: {e}")


# 导入collections.defaultdict
from collections import defaultdict