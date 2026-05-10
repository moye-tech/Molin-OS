"""
安全引擎 - 零泄漏安全策略核心
提供统一的安全接口，协调加密、访问控制、审计、数据保护等模块
"""

import os
import yaml
from typing import Dict, Any, Optional
from loguru import logger

from .encryption import EncryptionManager
from .access_control import AccessController
from .audit_logger import AuditLogger
from .data_protection import DataProtector


class SecurityEngine:
    """安全引擎主类，协调所有安全组件"""

    def __init__(self, config_path: str = None):
        """
        初始化安全引擎

        Args:
            config_path: 安全配置文件路径，默认为 security/config/security_config.yaml
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "security", "config", "security_config.yaml"
        )
        self.config: Dict[str, Any] = {}
        self.enabled: bool = False

        # 安全组件
        self.encryption: Optional[EncryptionManager] = None
        self.access_control: Optional[AccessController] = None
        self.audit_logger: Optional[AuditLogger] = None
        self.data_protector: Optional[DataProtector] = None

        self._load_config()
        self._init_components()

    def _load_config(self):
        """加载安全配置文件"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"安全配置文件不存在: {self.config_path}")
                self.config = {}
                self.enabled = os.getenv("SECURITY_ENABLED", "true").lower() == "true"
                return

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_content = f.read()

            # 替换环境变量
            config_content = self._replace_env_vars(config_content)

            # 解析YAML
            self.config = yaml.safe_load(config_content)
            self.enabled = self.config.get("enabled", True)

            logger.info(f"安全配置加载成功: {self.config_path}")

        except Exception as e:
            logger.error(f"加载安全配置失败: {e}")
            self.config = {}
            self.enabled = False

    def _replace_env_vars(self, content: str) -> str:
        """替换配置文件中的环境变量"""
        import re

        def replace_match(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""

            # 处理默认值中的类型转换
            if default_value.startswith("true"):
                default_value = True
            elif default_value.startswith("false"):
                default_value = False
            elif default_value.isdigit():
                default_value = int(default_value)
            elif default_value.replace('.', '', 1).isdigit():
                default_value = float(default_value)

            env_value = os.getenv(var_name)
            if env_value is not None:
                # 尝试类型转换
                if isinstance(default_value, bool):
                    return str(env_value.lower() == "true")
                elif isinstance(default_value, int):
                    try:
                        return str(int(env_value))
                    except ValueError:
                        return str(default_value)
                elif isinstance(default_value, float):
                    try:
                        return str(float(env_value))
                    except ValueError:
                        return str(default_value)
                else:
                    return env_value
            else:
                return str(default_value)

        # 匹配 ${VAR_NAME:-default_value} 格式
        pattern = r'\$\{([A-Za-z0-9_]+)(?::-(.*?))?\}'
        return re.sub(pattern, replace_match, content)

    def _init_components(self):
        """初始化安全组件"""
        if not self.enabled:
            logger.info("安全功能已禁用")
            return

        try:
            # 初始化加密管理器
            encryption_config = self.config.get("encryption", {})
            self.encryption = EncryptionManager(encryption_config)
            logger.info("加密管理器初始化成功")

            # 初始化访问控制器
            access_control_config = self.config.get("access_control", {})
            self.access_control = AccessController(access_control_config)
            logger.info("访问控制器初始化成功")

            # 初始化审计日志器
            audit_logging_config = self.config.get("audit_logging", {})
            self.audit_logger = AuditLogger(audit_logging_config)
            logger.info("审计日志器初始化成功")

            # 初始化数据保护器
            data_protection_config = self.config.get("data_protection", {})
            self.data_protector = DataProtector(data_protection_config, self.encryption)
            logger.info("数据保护器初始化成功")

            logger.info("安全引擎初始化完成")

        except Exception as e:
            logger.error(f"初始化安全组件失败: {e}")
            self.enabled = False

    def is_enabled(self) -> bool:
        """检查安全引擎是否启用"""
        return self.enabled

    def get_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.config.copy()

    def log_security_event(self, event_type: str, event_data: Dict[str, Any],
                          user_id: str = None, ip_address: str = None):
        """记录安全事件"""
        if not self.enabled or not self.audit_logger:
            return

        try:
            self.audit_logger.log_event(
                event_type=event_type,
                event_data=event_data,
                user_id=user_id,
                ip_address=ip_address
            )
        except Exception as e:
            logger.warning(f"记录安全事件失败: {e}")

    def check_access(self, resource: str, action: str, user_context: Dict[str, Any]) -> bool:
        """检查访问权限"""
        if not self.enabled or not self.access_control:
            return True  # 安全禁用时默认允许

        try:
            return self.access_control.check_permission(resource, action, user_context)
        except Exception as e:
            logger.error(f"检查访问权限失败: {e}")
            return False

    def encrypt_data(self, data: str, data_type: str = "generic") -> Optional[str]:
        """加密数据"""
        if not self.enabled or not self.encryption:
            return data  # 安全禁用时返回原数据

        try:
            return self.encryption.encrypt(data, data_type)
        except Exception as e:
            logger.error(f"加密数据失败: {e}")
            return None

    def decrypt_data(self, encrypted_data: str, data_type: str = "generic") -> Optional[str]:
        """解密数据"""
        if not self.enabled or not self.encryption:
            return encrypted_data  # 安全禁用时返回原数据

        try:
            return self.encryption.decrypt(encrypted_data, data_type)
        except Exception as e:
            logger.error(f"解密数据失败: {e}")
            return None

    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """掩码敏感数据"""
        if not self.enabled or not self.data_protector:
            return data  # 安全禁用时返回原数据

        try:
            return self.data_protector.mask_data(data)
        except Exception as e:
            logger.error(f"掩码敏感数据失败: {e}")
            return data

    def validate_input(self, input_data: Any, input_type: str = "generic") -> bool:
        """验证输入数据（防止注入攻击等）"""
        if not self.enabled or not self.access_control:
            return True  # 安全禁用时默认通过

        try:
            vulnerability_config = self.config.get("vulnerability_protection", {})
            return self.access_control.validate_input(input_data, input_type, vulnerability_config)
        except Exception as e:
            logger.error(f"验证输入数据失败: {e}")
            return False

    def rotate_encryption_keys(self) -> bool:
        """轮换加密密钥"""
        if not self.enabled or not self.encryption:
            return False

        try:
            return self.encryption.rotate_keys()
        except Exception as e:
            logger.error(f"轮换加密密钥失败: {e}")
            return False

    def get_security_metrics(self) -> Dict[str, Any]:
        """获取安全指标"""
        metrics = {
            "enabled": self.enabled,
            "components_initialized": {
                "encryption": self.encryption is not None,
                "access_control": self.access_control is not None,
                "audit_logger": self.audit_logger is not None,
                "data_protector": self.data_protector is not None
            }
        }

        if self.audit_logger:
            metrics["audit_stats"] = self.audit_logger.get_stats()

        if self.access_control:
            metrics["access_control_stats"] = self.access_control.get_stats()

        return metrics


# 全局单例实例
_security_engine = None


def get_security_engine() -> SecurityEngine:
    """获取安全引擎单例"""
    global _security_engine
    if _security_engine is None:
        _security_engine = SecurityEngine()
    return _security_engine


def initialize_security() -> SecurityEngine:
    """初始化安全引擎（显式调用）"""
    return get_security_engine()