"""
记忆层访问控制列表 (ACL) 中间件
在 MemoryManager 的 store/retrieve 操作前进行权限校验，
防止低权限子公司读取其他命名空间的敏感数据。

配置文件: config/memory_acl.toml
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

# ACL 配置文件路径
ACL_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "memory_acl.toml"

# 配置缓存
_acl_cache: Optional[Dict[str, Any]] = None
_acl_mtime: float = 0.0


class MemoryACL:
    """记忆层访问控制列表"""

    # CEO 始终拥有全部权限
    SUPERUSER_AGENCIES = {"ceo"}

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or ACL_CONFIG_PATH
        self.config = self._load_config()
        self.enabled = self.config.get("global", {}).get("enabled", False)
        self.default_deny = self.config.get("global", {}).get("default_deny", True)
        self.audit_log = self.config.get("global", {}).get("audit_log", True)

    def _load_config(self) -> Dict[str, Any]:
        """加载 ACL 配置，带 mtime 缓存避免重复磁盘读取"""
        global _acl_cache, _acl_mtime

        if not TOML_AVAILABLE or not self.config_path.exists():
            logger.warning("ACL 配置不可用，将使用宽松模式（允许所有访问）")
            return {"global": {"enabled": False}}

        try:
            current_mtime = self.config_path.stat().st_mtime
            if _acl_cache is not None and _acl_mtime >= current_mtime:
                return _acl_cache

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = toml.load(f)

            _acl_cache = config
            _acl_mtime = current_mtime
            logger.info(f"ACL 配置已加载/刷新，命名空间数量: {len(config.get('namespaces', {}))}")
            return config

        except Exception as e:
            logger.error(f"加载 ACL 配置失败: {e}")
            return _acl_cache or {"global": {"enabled": False}}

    def reload(self):
        """强制重新加载配置"""
        global _acl_cache, _acl_mtime
        _acl_cache = None
        _acl_mtime = 0.0
        self.config = self._load_config()
        self.enabled = self.config.get("global", {}).get("enabled", False)

    def check_access(
        self,
        agency_id: str,
        namespace: str,
        operation: str = "read"
    ) -> bool:
        """
        检查子公司是否有权访问指定命名空间

        Args:
            agency_id: 子公司 ID（如 "finance", "cs"）
            namespace: 目标记忆命名空间（如 "finance", "legal"）
            operation: 操作类型，"read" 或 "write"

        Returns:
            bool: 是否允许访问
        """
        # ACL 未启用，放行所有
        if not self.enabled:
            return True

        # 超级用户直接放行
        if agency_id in self.SUPERUSER_AGENCIES:
            return True

        # 子公司访问自己的命名空间始终允许
        if agency_id == namespace:
            return True

        # 查找命名空间配置
        ns_config = self.config.get("namespaces", {}).get(namespace)
        if ns_config is None:
            # 命名空间未配置
            if self.default_deny:
                self._audit_deny(agency_id, namespace, operation, "namespace_not_configured")
                return False
            return True

        # 检查权限列表
        if operation == "write":
            allowed = ns_config.get("write_access", [])
        else:
            allowed = ns_config.get("read_access", [])

        if agency_id in allowed:
            return True

        # 拒绝访问
        self._audit_deny(agency_id, namespace, operation, "not_in_access_list")
        return False

    def get_accessible_namespaces(
        self,
        agency_id: str,
        operation: str = "read"
    ) -> List[str]:
        """获取子公司可访问的所有命名空间列表"""
        if not self.enabled:
            return list(self.config.get("namespaces", {}).keys())

        if agency_id in self.SUPERUSER_AGENCIES:
            return list(self.config.get("namespaces", {}).keys())

        accessible = []
        for ns_name, ns_config in self.config.get("namespaces", {}).items():
            access_key = "write_access" if operation == "write" else "read_access"
            allowed = ns_config.get(access_key, [])
            if agency_id in allowed or agency_id == ns_name:
                accessible.append(ns_name)

        return accessible

    def _audit_deny(
        self,
        agency_id: str,
        namespace: str,
        operation: str,
        reason: str
    ):
        """记录 ACL 拒绝审计日志"""
        if self.audit_log:
            logger.warning(
                f"[ACL DENY] agency={agency_id} namespace={namespace} "
                f"op={operation} reason={reason}"
            )


# ── 全局单例 ──────────────────────────────────────────

_acl_instance: Optional[MemoryACL] = None


def get_memory_acl() -> MemoryACL:
    """获取全局 ACL 实例（单例）"""
    global _acl_instance
    if _acl_instance is None:
        _acl_instance = MemoryACL()
    return _acl_instance
