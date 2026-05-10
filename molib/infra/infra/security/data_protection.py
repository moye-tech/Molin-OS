"""
数据保护器 - 零泄漏安全策略
提供敏感数据掩码、数据加密、数据保留策略等功能
"""

import re
import json
import hashlib
from typing import Dict, Any, Optional, List, Set, Union
from datetime import datetime, timedelta
from loguru import logger

from .encryption import EncryptionManager


class DataProtector:
    """数据保护器，处理所有数据保护相关操作"""

    def __init__(self, config: Dict[str, Any], encryption_manager: EncryptionManager = None):
        """
        初始化数据保护器

        Args:
            config: 数据保护配置
            encryption_manager: 加密管理器实例
        """
        self.config = config
        self.encryption_manager = encryption_manager

        # 数据掩码配置
        self.masking_config = config.get("data_masking", {})
        self.masking_enabled = self.masking_config.get("enabled", True)
        self.fields_to_mask = set(self.masking_config.get("fields_to_mask", []))
        self.mask_character = self.masking_config.get("mask_character", "*")
        self.unmasked_length = self.masking_config.get("unmasked_length", 4)

        # 数据加密配置
        self.encryption_config = config.get("data_encryption", {})
        self.encryption_enabled = self.encryption_config.get("enabled", True)
        self.encrypt_at_rest = self.encryption_config.get("encrypt_at_rest", True)
        self.encrypt_in_transit = self.encryption_config.get("encrypt_in_transit", True)
        self.fields_to_encrypt = set(self.encryption_config.get("fields_to_encrypt", []))

        # 数据保留配置
        self.retention_config = config.get("data_retention", {})
        self.retention_enabled = self.retention_config.get("enabled", True)
        self.retention_policies = self.retention_config.get("policies", [])

        # 敏感数据模式检测
        self.sensitive_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b(\+?86)?1[3-9]\d{9}\b',  # 中国手机号
            "id_card": r'\b\d{17}[\dXx]\b',  # 身份证号
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            "bank_account": r'\b\d{16,19}\b',  # 银行卡号
        }

        # 编译正则表达式
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in self.sensitive_patterns.items()
        }

        # 统计信息
        self._stats = {
            "data_masked_count": 0,
            "data_encrypted_count": 0,
            "sensitive_data_detected": defaultdict(int),
            "retention_applied_count": 0,
            "errors": 0
        }

        logger.info("数据保护器初始化成功")

    def mask_data(self, data: Union[Dict[str, Any], List, str],
                 context: str = None) -> Union[Dict[str, Any], List, str]:
        """
        掩码敏感数据

        Args:
            data: 要掩码的数据
            context: 数据上下文（用于确定字段映射）

        Returns:
            掩码后的数据
        """
        if not self.masking_enabled:
            return data

        try:
            if isinstance(data, dict):
                return self._mask_dict(data, context)
            elif isinstance(data, list):
                return [self.mask_data(item, context) for item in data]
            elif isinstance(data, str):
                return self._mask_string(data, context)
            else:
                return data

        except Exception as e:
            logger.error(f"掩码数据失败: {e}")
            self._stats["errors"] += 1
            return data

    def _mask_dict(self, data: Dict[str, Any], context: str) -> Dict[str, Any]:
        """掩码字典数据"""
        masked_data = {}

        for key, value in data.items():
            # 确定字段是否应该被掩码
            should_mask = self._should_mask_field(key, value, context)

            if should_mask:
                masked_value = self._apply_masking(value, key)
                masked_data[key] = masked_value
                self._stats["data_masked_count"] += 1
            else:
                # 递归处理嵌套结构
                if isinstance(value, (dict, list)):
                    masked_data[key] = self.mask_data(value, f"{context}.{key}" if context else key)
                else:
                    masked_data[key] = value

        return masked_data

    def _should_mask_field(self, field_name: str, field_value: Any, context: str) -> bool:
        """检查字段是否应该被掩码"""
        # 检查字段名是否在掩码列表中
        field_name_lower = field_name.lower()

        for mask_field in self.fields_to_mask:
            if mask_field.lower() in field_name_lower:
                return True

        # 检查值是否匹配敏感数据模式
        if isinstance(field_value, str):
            for pattern_name, pattern in self.compiled_patterns.items():
                if pattern.search(field_value):
                    self._stats["sensitive_data_detected"][pattern_name] += 1
                    return True

        return False

    def _apply_masking(self, value: Any, field_name: str) -> str:
        """应用数据掩码"""
        if not isinstance(value, str):
            value = str(value)

        # 确定掩码长度
        if len(value) <= self.unmasked_length:
            # 值太短，完全掩码
            return self.mask_character * len(value)
        else:
            # 保留最后几个字符
            visible_part = value[-self.unmasked_length:]
            masked_part = self.mask_character * (len(value) - self.unmasked_length)
            return masked_part + visible_part

    def _mask_string(self, text: str, context: str) -> str:
        """掩码字符串中的敏感数据"""
        if not text:
            return text

        # 检查整个字符串是否应该被掩码
        if self._should_mask_field("text", text, context):
            return self._apply_masking(text, "text")

        # 查找并掩码字符串中的敏感数据
        masked_text = text

        for pattern_name, pattern in self.compiled_patterns.items():
            def mask_match(match):
                matched_text = match.group(0)
                self._stats["sensitive_data_detected"][pattern_name] += 1
                return self._apply_masking(matched_text, pattern_name)

            masked_text = pattern.sub(mask_match, masked_text)

        return masked_text

    def encrypt_data(self, data: Dict[str, Any], context: str = None) -> Dict[str, Any]:
        """
        加密敏感数据

        Args:
            data: 要加密的数据
            context: 数据上下文

        Returns:
            加密后的数据
        """
        if not self.encryption_enabled or not self.encryption_manager:
            return data

        try:
            encrypted_data = {}

            for key, value in data.items():
                # 检查字段是否应该被加密
                should_encrypt = self._should_encrypt_field(key, value, context)

                if should_encrypt and isinstance(value, str):
                    # 加密字符串值
                    encrypted_value = self.encryption_manager.encrypt(value, f"{context}.{key}" if context else key)
                    if encrypted_value:
                        encrypted_data[key] = encrypted_value
                        self._stats["data_encrypted_count"] += 1
                    else:
                        encrypted_data[key] = value  # 加密失败，保留原值
                elif isinstance(value, dict):
                    # 递归处理嵌套字典
                    encrypted_data[key] = self.encrypt_data(value, f"{context}.{key}" if context else key)
                elif isinstance(value, list):
                    # 处理列表
                    encrypted_data[key] = [
                        self.encrypt_data(item, f"{context}.{key}[{i}]") if isinstance(item, dict)
                        else self._encrypt_if_needed(item, f"{context}.{key}[{i}]")
                        for i, item in enumerate(value)
                    ]
                else:
                    # 其他类型
                    encrypted_data[key] = self._encrypt_if_needed(value, f"{context}.{key}" if context else key)

            return encrypted_data

        except Exception as e:
            logger.error(f"加密数据失败: {e}")
            self._stats["errors"] += 1
            return data

    def _should_encrypt_field(self, field_name: str, field_value: Any, context: str) -> bool:
        """检查字段是否应该被加密"""
        # 检查字段名是否在加密列表中
        field_name_lower = field_name.lower()

        for encrypt_field in self.fields_to_encrypt:
            if encrypt_field.lower() in field_name_lower:
                return True

        # 检查值是否包含敏感数据
        if isinstance(field_value, str):
            for pattern_name, pattern in self.compiled_patterns.items():
                if pattern.search(field_value):
                    return True

        return False

    def _encrypt_if_needed(self, value: Any, context: str) -> Any:
        """如果需要则加密值"""
        if isinstance(value, str) and self._should_encrypt_field("value", value, context):
            encrypted = self.encryption_manager.encrypt(value, context)
            return encrypted if encrypted else value
        return value

    def decrypt_data(self, encrypted_data: Dict[str, Any], context: str = None) -> Dict[str, Any]:
        """
        解密数据

        Args:
            encrypted_data: 加密的数据
            context: 数据上下文

        Returns:
            解密后的数据
        """
        if not self.encryption_enabled or not self.encryption_manager:
            return encrypted_data

        try:
            decrypted_data = {}

            for key, value in encrypted_data.items():
                if isinstance(value, str):
                    # 尝试解密（加密数据有特定格式）
                    if self._looks_like_encrypted(value):
                        decrypted_value = self.encryption_manager.decrypt(value, f"{context}.{key}" if context else key)
                        decrypted_data[key] = decrypted_value if decrypted_value is not None else value
                    else:
                        decrypted_data[key] = value
                elif isinstance(value, dict):
                    # 递归处理嵌套字典
                    decrypted_data[key] = self.decrypt_data(value, f"{context}.{key}" if context else key)
                elif isinstance(value, list):
                    # 处理列表
                    decrypted_data[key] = [
                        self.decrypt_data(item, f"{context}.{key}[{i}]") if isinstance(item, dict)
                        else self._decrypt_if_encrypted(item, f"{context}.{key}[{i}]")
                        for i, item in enumerate(value)
                    ]
                else:
                    decrypted_data[key] = value

            return decrypted_data

        except Exception as e:
            logger.error(f"解密数据失败: {e}")
            self._stats["errors"] += 1
            return encrypted_data

    def _looks_like_encrypted(self, value: str) -> bool:
        """检查字符串是否看起来像加密数据"""
        # 加密数据格式：算法|密钥ID|...
        return '|' in value and (value.startswith('AES-GCM|') or value.startswith('Fernet|'))

    def _decrypt_if_encrypted(self, value: Any, context: str) -> Any:
        """如果是加密数据则解密"""
        if isinstance(value, str) and self._looks_like_encrypted(value):
            decrypted = self.encryption_manager.decrypt(value, context)
            return decrypted if decrypted is not None else value
        return value

    def apply_retention_policy(self, data_type: str, data_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        应用数据保留策略

        Args:
            data_type: 数据类型
            data_records: 数据记录列表

        Returns:
            应用保留策略后的数据记录
        """
        if not self.retention_enabled:
            return data_records

        try:
            # 查找适用的保留策略
            policy = None
            for p in self.retention_policies:
                if p.get("data_type") == data_type:
                    policy = p
                    break

            if not policy:
                return data_records

            retention_days = policy.get("retention_days", 30)
            auto_delete = policy.get("auto_delete", False)

            # 计算截止时间
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            cutoff_timestamp = cutoff_date.timestamp()

            # 过滤数据
            filtered_records = []
            deleted_records = []

            for record in data_records:
                # 尝试获取时间戳字段
                timestamp = self._extract_timestamp(record)

                if timestamp and timestamp < cutoff_timestamp:
                    # 记录超过保留期限
                    if auto_delete:
                        deleted_records.append(record)
                        continue
                    else:
                        # 标记为过期但不删除
                        record["_retention_status"] = "expired"
                else:
                    record["_retention_status"] = "active"

                filtered_records.append(record)

            if deleted_records:
                self._stats["retention_applied_count"] += len(deleted_records)
                logger.info(f"数据保留策略删除了 {len(deleted_records)} 条{data_type}记录")

            return filtered_records

        except Exception as e:
            logger.error(f"应用数据保留策略失败: {e}")
            self._stats["errors"] += 1
            return data_records

    def _extract_timestamp(self, record: Dict[str, Any]) -> Optional[float]:
        """从记录中提取时间戳"""
        # 常见的时间戳字段名
        timestamp_fields = ["timestamp", "created_at", "updated_at", "date", "time"]

        for field in timestamp_fields:
            if field in record:
                value = record[field]
                if isinstance(value, (int, float)):
                    return float(value)
                elif isinstance(value, str):
                    # 尝试解析字符串时间戳
                    try:
                        # 尝试ISO格式
                        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        return dt.timestamp()
                    except ValueError:
                        try:
                            # 尝试Unix时间戳字符串
                            return float(value)
                        except ValueError:
                            continue

        return None

    def anonymize_data(self, data: Dict[str, Any], anonymization_level: str = "medium") -> Dict[str, Any]:
        """
        匿名化数据（用于分析等场景）

        Args:
            data: 要匿名化的数据
            anonymization_level: 匿名化级别（low, medium, high）

        Returns:
            匿名化后的数据
        """
        try:
            anonymized_data = data.copy()

            if anonymization_level == "high":
                # 高匿名化：移除所有个人标识信息
                fields_to_remove = ["name", "email", "phone", "address", "ip_address",
                                   "user_id", "device_id", "session_id"]
                for field in fields_to_remove:
                    if field in anonymized_data:
                        del anonymized_data[field]

                # 泛化其他字段
                if "age" in anonymized_data:
                    age = anonymized_data["age"]
                    if isinstance(age, int):
                        # 将年龄分组（如20-29, 30-39）
                        anonymized_data["age_group"] = f"{(age // 10) * 10}-{(age // 10) * 10 + 9}"
                        del anonymized_data["age"]

                if "location" in anonymized_data:
                    # 泛化位置到城市级别
                    location = anonymized_data["location"]
                    if isinstance(location, str) and ',' in location:
                        city = location.split(',')[0].strip()
                        anonymized_data["location_city"] = city
                        del anonymized_data["location"]

            elif anonymization_level == "medium":
                # 中等匿名化：掩码敏感字段
                anonymized_data = self.mask_data(anonymized_data, "anonymization")

            # 低匿名化：不进行额外处理

            # 添加匿名化元数据
            anonymized_data["_anonymization"] = {
                "level": anonymization_level,
                "applied_at": datetime.now().isoformat(),
                "method": "data_protector"
            }

            return anonymized_data

        except Exception as e:
            logger.error(f"匿名化数据失败: {e}")
            return data

    def get_data_classification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取数据分类

        Args:
            data: 要分类的数据

        Returns:
            分类结果
        """
        classification = {
            "sensitive_fields": [],
            "encryption_recommended": [],
            "masking_applied": [],
            "risk_level": "low"
        }

        try:
            # 分析数据字段
            for key, value in data.items():
                if isinstance(value, str):
                    # 检查敏感数据
                    is_sensitive = False

                    for pattern_name, pattern in self.compiled_patterns.items():
                        if pattern.search(value):
                            classification["sensitive_fields"].append({
                                "field": key,
                                "type": pattern_name,
                                "value_sample": self._apply_masking(value, key) if len(value) > 10 else "***"
                            })
                            is_sensitive = True

                    # 检查是否需要加密
                    if self._should_encrypt_field(key, value, None):
                        classification["encryption_recommended"].append(key)

                    # 检查是否被掩码
                    if self._should_mask_field(key, value, None):
                        classification["masking_applied"].append(key)

            # 确定风险级别
            sensitive_count = len(classification["sensitive_fields"])
            if sensitive_count >= 3:
                classification["risk_level"] = "high"
            elif sensitive_count >= 1:
                classification["risk_level"] = "medium"

            return classification

        except Exception as e:
            logger.error(f"数据分类失败: {e}")
            return classification

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "masking_enabled": self.masking_enabled,
            "encryption_enabled": self.encryption_enabled,
            "retention_enabled": self.retention_enabled,
            "sensitive_patterns_count": len(self.sensitive_patterns)
        }

    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            "data_masked_count": 0,
            "data_encrypted_count": 0,
            "sensitive_data_detected": defaultdict(int),
            "retention_applied_count": 0,
            "errors": 0
        }


# 导入collections.defaultdict
from collections import defaultdict