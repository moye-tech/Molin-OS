"""
墨麟AIOS — CacheManager (缓存管理器)
参考 E2B (12K⭐) 文件系统+沙箱存储的持久化缓存方案。
基于JSON文件持久化，支持TTL过期、批量失效、命中率统计。
"""

import os
import json
import time
import fnmatch
import hashlib
import threading
from pathlib import Path
from typing import Any, Optional


class CacheManager:
    """
    缓存管理器 — JSON文件持久化缓存，支持TTL和批量失效。

    参考 E2B 沙箱文件系统存储方案：
    - get(key) → any
    - set(key, value, ttl=None) → bool
    - invalidate(pattern) → int 批量失效
    - stats() → dict 缓存命中率等统计
    """

    def __init__(self, storage_path: str = "~/.hermes/cache/", ttl: int = 3600):
        """
        Args:
            storage_path: 缓存存储路径
            ttl: 默认缓存过期时间（秒），默认3600秒（1小时）
        """
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.default_ttl = ttl
        self._cache_file = self.storage_path / "cache.json"

        # 内存缓存
        self._cache: dict[str, dict] = {}
        self._lock = threading.Lock()  # 线程安全

        # 统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "total_sets": 0,
            "total_invalidations": 0,
            "total_expired_cleared": 0,
            "started_at": time.time(),
        }

        self._load()

    # ───────── 持久化 ─────────

    def _load(self):
        """从JSON文件加载缓存。"""
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache = data
            except (json.JSONDecodeError, OSError):
                self._cache = {}
        else:
            self._cache = {}

    def _save(self):
        """持久化缓存到JSON文件（原子写入）。"""
        tmp_file = self._cache_file.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)
        tmp_file.replace(self._cache_file)

    # ───────── 内部方法 ─────────

    def _make_hash_key(self, key: str) -> str:
        """
        将任意字符串key转为安全的哈希key。
        避免文件系统不支持的特殊字符，同时保持短小。
        """
        if not key:
            raise ValueError("缓存key不能为空")
        # 使用SHA256哈希缩短
        return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]

    def _is_expired(self, entry: dict) -> bool:
        """检查缓存条目是否过期。"""
        expires_at = entry.get("expires_at")
        if expires_at is None:
            return False  # 永不过期
        return time.time() > expires_at

    def _clean_expired(self) -> int:
        """清理所有过期条目。"""
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if v.get("expires_at") is not None and now > v["expires_at"]
        ]
        for k in expired_keys:
            del self._cache[k]

        if expired_keys:
            self._stats["total_expired_cleared"] += len(expired_keys)
            self._save()

        return len(expired_keys)

    # ───────── 公有API ─────────

    def get(self, key: str) -> Any:
        """
        获取缓存值。

        Args:
            key: 缓存键

        Returns:
            any: 缓存的值，如果不存在或已过期返回 None
        """
        hash_key = self._make_hash_key(key)

        with self._lock:
            # 清理过期条目（惰性清理）
            self._clean_expired()

            entry = self._cache.get(hash_key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            # 检查TTL过期
            if self._is_expired(entry):
                del self._cache[hash_key]
                self._stats["misses"] += 1
                self._stats["total_expired_cleared"] += 1
                self._save()
                return None

            # 命中
            self._stats["hits"] += 1
            entry["access_count"] = entry.get("access_count", 0) + 1
            entry["last_access_at"] = time.time()

            return entry.get("value")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值。

        Args:
            key: 缓存键
            value: 缓存值（必须是JSON可序列化的）
            ttl: 过期时间（秒），None表示永不过期，默认使用 self.default_ttl

        Returns:
            bool: 是否成功设置
        """
        hash_key = self._make_hash_key(key)
        ttl = self.default_ttl if ttl is None else ttl

        # 构建条目
        entry = {
            "key": key,  # 保存原始key便于通配匹配
            "value": value,
            "created_at": time.time(),
            "last_access_at": time.time(),
            "access_count": 0,
        }

        if ttl is not None and ttl > 0:
            entry["expires_at"] = time.time() + ttl
        else:
            entry["expires_at"] = None  # 永不过期

        with self._lock:
            self._cache[hash_key] = entry
            self._stats["total_sets"] += 1
            self._save()

        return True

    def invalidate(self, pattern: str) -> int:
        """
        批量失效缓存条目（支持通配符模式）。

        Args:
            pattern: 通配符模式，如 "user:*", "session:*", "data_*"
                     也支持直接匹配完整key

        Returns:
            int: 被失效的缓存条目数量
        """
        with self._lock:
            # 收集匹配的key
            keys_to_delete = []
            for hash_key, entry in list(self._cache.items()):
                original_key = entry.get("key", "")
                # 通配符匹配原始key
                if fnmatch.fnmatch(original_key, pattern):
                    keys_to_delete.append(hash_key)
                # 也支持直接匹配hash_key
                elif fnmatch.fnmatch(hash_key, pattern):
                    keys_to_delete.append(hash_key)

            # 删除
            for k in keys_to_delete:
                del self._cache[k]

            count = len(keys_to_delete)
            if count > 0:
                self._stats["total_invalidations"] += count
                self._save()

            return count

    def stats(self) -> dict:
        """
        获取缓存统计信息。

        Returns:
            dict: 统计信息包含:
                - total_entries: 缓存条目总数
                - active_entries: 未过期的有效条目数
                - expired_entries: 已过期的条目数（将被清理）
                - hits: 命中次数
                - misses: 未命中次数
                - hit_rate: 命中率 (0-1)
                - total_sets: 设置总次数
                - total_invalidations: 失效总次数
                - total_expired_cleared: 自动清理过期总数
                - memory_size_bytes: 内存中缓存大小
                - storage_size_bytes: 持久化文件大小
                - default_ttl: 默认TTL（秒）
                - uptime_seconds: 运行时长
                - storage_path: 存储路径
        """
        with self._lock:
            # 计算统计
            total = len(self._cache)
            now = time.time()

            active = sum(
                1 for v in self._cache.values()
                if v.get("expires_at") is None or now <= v["expires_at"]
            )
            expired = total - active

            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = round(
                self._stats["hits"] / total_requests, 4
            ) if total_requests > 0 else 0.0

            # 内存大小估算
            memory_size = len(json.dumps(self._cache, ensure_ascii=False, default=str))

            # 持久化文件大小
            storage_size = self._cache_file.stat().st_size if self._cache_file.exists() else 0

            # 最热key
            hot_keys = sorted(
                [
                    {"key": v.get("key", k), "access_count": v.get("access_count", 0)}
                    for k, v in self._cache.items()
                ],
                key=lambda x: x["access_count"],
                reverse=True,
            )[:10]

            return {
                "total_entries": total,
                "active_entries": active,
                "expired_entries": expired,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "total_sets": self._stats["total_sets"],
                "total_invalidations": self._stats["total_invalidations"],
                "total_expired_cleared": self._stats["total_expired_cleared"],
                "memory_size_bytes": memory_size,
                "storage_size_bytes": storage_size,
                "default_ttl": self.default_ttl,
                "uptime_seconds": round(time.time() - self._stats["started_at"], 2),
                "hot_keys": hot_keys,
                "storage_path": str(self.storage_path),
            }

    def exists(self, key: str) -> bool:
        """
        检查key是否存在且未过期。

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """
        return self.get(key) is not None

    def delete(self, key: str) -> bool:
        """
        删除单个缓存条目。

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        hash_key = self._make_hash_key(key)
        with self._lock:
            if hash_key in self._cache:
                del self._cache[hash_key]
                self._save()
                return True
            return False

    def clear(self) -> int:
        """
        清空所有缓存。

        Returns:
            int: 被清空的条目数
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._save()
            self._stats["total_invalidations"] += count
            return count

    def get_ttl(self, key: str) -> Optional[int]:
        """
        获取key的剩余存活时间。

        Args:
            key: 缓存键

        Returns:
            int or None: 剩余秒数，None表示永不过期或不存在
        """
        hash_key = self._make_hash_key(key)
        with self._lock:
            entry = self._cache.get(hash_key)
            if entry is None:
                return None
            expires_at = entry.get("expires_at")
            if expires_at is None:
                return None
            remaining = expires_at - time.time()
            return max(0, int(remaining))

    def touch(self, key: str, ttl: Optional[int] = None) -> bool:
        """
        刷新key的过期时间。

        Args:
            key: 缓存键
            ttl: 新的TTL（秒），None使用默认TTL

        Returns:
            bool: 是否成功刷新
        """
        hash_key = self._make_hash_key(key)
        ttl = self.default_ttl if ttl is None else ttl

        with self._lock:
            entry = self._cache.get(hash_key)
            if entry is None:
                return False

            if ttl is not None and ttl > 0:
                entry["expires_at"] = time.time() + ttl
            else:
                entry["expires_at"] = None

            entry["last_access_at"] = time.time()
            self._save()
            return True
