"""
访问控制器 - 零泄漏安全策略
提供访问控制、速率限制、输入验证、漏洞防护功能
"""

import time
import ipaddress
from typing import Dict, Any, Optional, List, Set, Tuple
from collections import defaultdict
from loguru import logger


class AccessController:
    """访问控制器，管理所有访问控制相关功能"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化访问控制器

        Args:
            config: 访问控制配置
        """
        self.config = config

        # API访问控制
        self.api_config = config.get("api", {})
        self.rate_limit_config = self.api_config.get("rate_limit", {})
        self.ip_whitelist_config = self.api_config.get("ip_whitelist", {})
        self.auth_config = self.api_config.get("authentication", {})

        # 数据库访问控制
        self.db_config = config.get("database", {})

        # 速率限制状态
        self._rate_limit_buckets: Dict[str, List[float]] = defaultdict(list)
        self._blocked_ips: Dict[str, float] = {}  # IP -> 解封时间

        # 认证状态
        self._valid_api_keys: Set[str] = set()
        self._valid_tokens: Set[str] = set()

        # 统计信息
        self._stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "failed_auth": 0,
            "rate_limit_hits": 0,
            "sql_injection_attempts": 0,
            "xss_attempts": 0,
        }

        self._init_access_control()

    def _init_access_control(self):
        """初始化访问控制"""
        try:
            # 初始化API密钥（从环境变量或配置加载）
            self._load_api_keys()

            # 初始化IP白名单
            if self.ip_whitelist_config.get("enabled", False):
                logger.info("IP白名单已启用")

            # 初始化速率限制
            if self.rate_limit_config.get("enabled", True):
                logger.info(f"速率限制已启用: {self.rate_limit_config.get('requests_per_minute', 60)} 请求/分钟")

            logger.info("访问控制器初始化成功")

        except Exception as e:
            logger.error(f"初始化访问控制器失败: {e}")

    def _load_api_keys(self):
        """加载API密钥"""
        # 从环境变量加载API密钥
        api_key_env = self.auth_config.get("api_key_env", "API_KEYS")
        api_keys_str = os.getenv(api_key_env, "")

        if api_keys_str:
            api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
            self._valid_api_keys.update(api_keys)
            logger.info(f"加载了 {len(api_keys)} 个API密钥")

        # 如果没有配置API密钥，生成一个默认的（仅用于开发）
        if not self._valid_api_keys and os.getenv("ENVIRONMENT") != "production":
            default_key = "dev_api_key_" + hashlib.sha256(b"hermes_fusion_dev").hexdigest()[:32]
            self._valid_api_keys.add(default_key)
            logger.warning(f"生成开发环境API密钥: {default_key}")

    def check_permission(self, resource: str, action: str, user_context: Dict[str, Any]) -> bool:
        """
        检查用户对资源的访问权限

        Args:
            resource: 资源标识符
            action: 操作类型（read, write, execute等）
            user_context: 用户上下文，包含用户ID、角色、权限等

        Returns:
            bool: 是否允许访问
        """
        self._stats["total_requests"] += 1

        try:
            # 1. 检查IP白名单
            ip_address = user_context.get("ip_address")
            if ip_address and not self._check_ip_whitelist(ip_address):
                logger.warning(f"IP不在白名单中: {ip_address}")
                self._stats["blocked_requests"] += 1
                return False

            # 2. 检查速率限制
            client_id = user_context.get("client_id", ip_address or "unknown")
            if not self._check_rate_limit(client_id, resource):
                logger.warning(f"速率限制触发: {client_id} -> {resource}")
                self._stats["rate_limit_hits"] += 1
                return False

            # 3. 检查认证
            if self.auth_config.get("required", True):
                if not self._check_authentication(user_context):
                    logger.warning(f"认证失败: {user_context.get('user_id', 'unknown')}")
                    self._stats["failed_auth"] += 1
                    return False

            # 4. 检查授权（基于角色的访问控制）
            user_roles = user_context.get("roles", [])
            user_permissions = user_context.get("permissions", [])

            required_permission = f"{resource}:{action}"
            if required_permission not in user_permissions:
                # 检查角色是否包含权限
                if not self._check_role_permissions(user_roles, required_permission):
                    logger.warning(f"权限不足: {user_context.get('user_id', 'unknown')} -> {required_permission}")
                    self._stats["blocked_requests"] += 1
                    return False

            return True

        except Exception as e:
            logger.error(f"检查权限时出错: {e}")
            return False

    def _check_ip_whitelist(self, ip_address: str) -> bool:
        """检查IP是否在白名单中"""
        if not self.ip_whitelist_config.get("enabled", False):
            return True

        try:
            allowed_ips = self.ip_whitelist_config.get("allowed_ips", [])
            if not allowed_ips:
                return True

            # 检查IP是否在白名单中
            ip_obj = ipaddress.ip_address(ip_address)

            for allowed_ip in allowed_ips:
                try:
                    # 处理CIDR表示法
                    if '/' in allowed_ip:
                        network = ipaddress.ip_network(allowed_ip, strict=False)
                        if ip_obj in network:
                            return True
                    else:
                        # 单个IP地址
                        allowed_ip_obj = ipaddress.ip_address(allowed_ip)
                        if ip_obj == allowed_ip_obj:
                            return True
                except ValueError:
                    continue

            return False

        except Exception as e:
            logger.error(f"检查IP白名单时出错: {e}")
            # 出错时默认拒绝访问
            return False

    def _check_rate_limit(self, client_id: str, resource: str) -> bool:
        """检查速率限制"""
        if not self.rate_limit_config.get("enabled", True):
            return True

        requests_per_minute = self.rate_limit_config.get("requests_per_minute", 60)
        burst_size = self.rate_limit_config.get("burst_size", 10)

        current_time = time.time()
        bucket_key = f"{client_id}:{resource}"

        # 清理旧的时间戳（超过1分钟）
        window_start = current_time - 60
        self._rate_limit_buckets[bucket_key] = [
            ts for ts in self._rate_limit_buckets[bucket_key]
            if ts > window_start
        ]

        # 检查是否超过限制
        if len(self._rate_limit_buckets[bucket_key]) >= requests_per_minute + burst_size:
            # 超过突发限制，直接拒绝
            return False
        elif len(self._rate_limit_buckets[bucket_key]) >= requests_per_minute:
            # 超过正常限制，检查是否在突发范围内
            pass  # 暂时允许，但记录

        # 添加当前请求时间戳
        self._rate_limit_buckets[bucket_key].append(current_time)

        # 保持桶大小合理
        if len(self._rate_limit_buckets[bucket_key]) > requests_per_minute * 2:
            self._rate_limit_buckets[bucket_key] = self._rate_limit_buckets[bucket_key][-requests_per_minute:]

        return True

    def _check_authentication(self, user_context: Dict[str, Any]) -> bool:
        """检查认证"""
        auth_methods = self.auth_config.get("methods", ["api_key", "jwt"])

        # 检查API密钥
        if "api_key" in auth_methods:
            api_key = user_context.get("api_key")
            api_key_header = self.auth_config.get("api_key_header", "X-API-Key")

            # 从header中获取（如果未在上下文中提供）
            if not api_key and "headers" in user_context:
                headers = user_context["headers"]
                api_key = headers.get(api_key_header)

            if api_key and api_key in self._valid_api_keys:
                return True

        # 检查JWT令牌
        if "jwt" in auth_methods:
            jwt_token = user_context.get("jwt_token")
            jwt_header = self.auth_config.get("jwt_header", "Authorization")

            # 从header中获取（如果未在上下文中提供）
            if not jwt_token and "headers" in user_context:
                headers = user_context["headers"]
                auth_header = headers.get(jwt_header)
                if auth_header and auth_header.startswith("Bearer "):
                    jwt_token = auth_header[7:]

            if jwt_token and self._validate_jwt(jwt_token):
                return True

        return False

    def _validate_jwt(self, jwt_token: str) -> bool:
        """验证JWT令牌（简化实现）"""
        try:
            # TODO: 实际JWT验证逻辑
            # 这里只是一个简单的示例
            import jwt
            # 在实际应用中，需要配置JWT密钥和验证算法
            # decoded = jwt.decode(jwt_token, "secret", algorithms=["HS256"])
            return True
        except Exception:
            return False

    def _check_role_permissions(self, user_roles: List[str], required_permission: str) -> bool:
        """检查角色权限"""
        # 角色到权限的映射（应从配置或数据库加载）
        role_permissions = {
            "admin": ["*:*"],  # 管理员有所有权限
            "user": ["read:*", "write:own"],
            "viewer": ["read:*"],
        }

        for role in user_roles:
            permissions = role_permissions.get(role, [])
            for perm in permissions:
                # 支持通配符权限
                if perm == "*:*" or perm == required_permission:
                    return True

                # 检查通配符匹配
                if '*' in perm:
                    perm_parts = perm.split(':')
                    req_parts = required_permission.split(':')

                    if len(perm_parts) != len(req_parts):
                        continue

                    matches = True
                    for perm_part, req_part in zip(perm_parts, req_parts):
                        if perm_part != '*' and perm_part != req_part:
                            matches = False
                            break

                    if matches:
                        return True

        return False

    def validate_input(self, input_data: Any, input_type: str = "generic",
                      vulnerability_config: Dict[str, Any] = None) -> bool:
        """验证输入数据，防止安全漏洞"""
        if vulnerability_config is None:
            vulnerability_config = {}

        try:
            if isinstance(input_data, str):
                return self._validate_string_input(input_data, input_type, vulnerability_config)
            elif isinstance(input_data, dict):
                return all(
                    self.validate_input(value, f"{input_type}.{key}", vulnerability_config)
                    for key, value in input_data.items()
                )
            elif isinstance(input_data, list):
                return all(
                    self.validate_input(item, input_type, vulnerability_config)
                    for item in input_data
                )
            else:
                # 其他类型（数字、布尔值等）通常安全
                return True

        except Exception as e:
            logger.error(f"验证输入数据时出错: {e}")
            return False

    def _validate_string_input(self, input_str: str, input_type: str,
                             vulnerability_config: Dict[str, Any]) -> bool:
        """验证字符串输入"""
        # SQL注入检测
        sql_injection_config = vulnerability_config.get("sql_injection", {})
        if sql_injection_config.get("enabled", True):
            if self._detect_sql_injection(input_str):
                logger.warning(f"检测到SQL注入尝试: {input_type}")
                self._stats["sql_injection_attempts"] += 1

                if sql_injection_config.get("detection_mode", "block") == "block":
                    return False

        # XSS检测
        xss_config = vulnerability_config.get("xss", {})
        if xss_config.get("enabled", True):
            if self._detect_xss(input_str):
                logger.warning(f"检测到XSS尝试: {input_type}")
                self._stats["xss_attempts"] += 1

                if xss_config.get("detection_mode", "block") == "block":
                    return False

        # 命令注入检测
        if self._detect_command_injection(input_str):
            logger.warning(f"检测到命令注入尝试: {input_type}")
            return False

        # 路径遍历检测
        if self._detect_path_traversal(input_str):
            logger.warning(f"检测到路径遍历尝试: {input_type}")
            return False

        return True

    def _detect_sql_injection(self, input_str: str) -> bool:
        """检测SQL注入尝试"""
        sql_keywords = [
            "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
            "UNION", "JOIN", "WHERE", "OR", "AND", "EXEC", "EXECUTE", "TRUNCATE",
            "--", "/*", "*/", ";", "'", '"'
        ]

        input_upper = input_str.upper()
        for keyword in sql_keywords:
            if keyword in input_upper:
                # 检查是否可能是合法的使用
                if keyword == "--" and input_str.strip().startswith("--"):
                    # 注释，可能是合法的
                    continue
                if keyword in ["OR", "AND"]:
                    # 这些词可能出现在正常文本中
                    continue
                return True

        return False

    def _detect_xss(self, input_str: str) -> bool:
        """检测XSS尝试"""
        xss_patterns = [
            "<script", "</script>", "javascript:", "onload=", "onerror=",
            "onclick=", "eval(", "alert(", "document.cookie", "window.location",
            "<iframe", "<img", "<svg", "<object"
        ]

        input_lower = input_str.lower()
        for pattern in xss_patterns:
            if pattern in input_lower:
                return True

        return False

    def _detect_command_injection(self, input_str: str) -> bool:
        """检测命令注入尝试"""
        command_patterns = [
            ";", "&&", "||", "|", "&", "$(", "`", ">>", ">", "<",
            "rm ", "cat ", "ls ", "chmod ", "wget ", "curl "
        ]

        for pattern in command_patterns:
            if pattern in input_str:
                return True

        return False

    def _detect_path_traversal(self, input_str: str) -> bool:
        """检测路径遍历尝试"""
        traversal_patterns = [
            "../", "..\\", "/etc/", "/bin/", "/usr/", "C:\\", "..",
            "~/.ssh", "/root", "/home", "\\.."
        ]

        for pattern in traversal_patterns:
            if pattern in input_str:
                return True

        return False

    def block_ip(self, ip_address: str, duration_seconds: int = 3600):
        """阻塞IP地址"""
        self._blocked_ips[ip_address] = time.time() + duration_seconds
        logger.warning(f"IP地址已阻塞: {ip_address} ({duration_seconds}秒)")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """检查IP是否被阻塞"""
        if ip_address in self._blocked_ips:
            block_until = self._blocked_ips[ip_address]
            if time.time() < block_until:
                return True
            else:
                # 阻塞已过期
                del self._blocked_ips[ip_address]

        return False

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "current_rate_limit_buckets": len(self._rate_limit_buckets),
            "blocked_ips_count": len(self._blocked_ips),
            "valid_api_keys_count": len(self._valid_api_keys),
            "valid_tokens_count": len(self._valid_tokens)
        }

    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "failed_auth": 0,
            "rate_limit_hits": 0,
            "sql_injection_attempts": 0,
            "xss_attempts": 0,
        }


# 导入所需的模块
import os
import hashlib