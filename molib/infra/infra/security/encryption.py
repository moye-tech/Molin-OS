"""
加密管理器 - 零泄漏安全策略
提供数据加密、解密、密钥管理功能
"""

import os
import base64
import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import padding
from loguru import logger


class EncryptionManager:
    """加密管理器，处理所有加密相关操作"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化加密管理器

        Args:
            config: 加密配置
        """
        self.config = config
        self.algorithm = config.get("algorithm", "AES-256-GCM")
        self.key_rotation_days = config.get("key_rotation_days", 30)
        self.key_storage = config.get("key_storage", "env")
        self.env_key_name = config.get("env_key_name", "ENCRYPTION_KEY")

        # 密钥缓存
        self._current_key: Optional[bytes] = None
        self._current_key_id: Optional[str] = None
        self._key_generated_at: Optional[datetime] = None
        self._key_history: Dict[str, Tuple[bytes, datetime]] = {}

        self._init_encryption_key()

    def _init_encryption_key(self):
        """初始化加密密钥"""
        try:
            if self.key_storage == "env":
                # 从环境变量获取密钥
                env_key = os.getenv(self.env_key_name)
                if not env_key:
                    logger.warning(f"环境变量 {self.env_key_name} 未设置，生成临时密钥")
                    # 生成临时密钥（仅用于开发环境）
                    env_key = self._generate_key()
                    # 警告但不设置环境变量
                    logger.warning("请设置 ENCRYPTION_KEY 环境变量以确保安全")

                self._current_key = self._derive_key(env_key.encode('utf-8'))
                self._current_key_id = self._generate_key_id(self._current_key)
                self._key_generated_at = datetime.now()

                logger.info(f"加密密钥初始化成功，算法: {self.algorithm}")

            elif self.key_storage == "kms":
                # KMS集成（TODO: 未来扩展）
                logger.warning("KMS密钥存储暂未实现，使用环境变量回退")
                self._init_encryption_key()  # 回退到环境变量
            else:
                logger.error(f"不支持的密钥存储类型: {self.key_storage}")
                raise ValueError(f"Unsupported key storage: {self.key_storage}")

        except Exception as e:
            logger.error(f"初始化加密密钥失败: {e}")
            # 生成临时密钥作为最后手段
            temp_key = self._generate_key()
            self._current_key = self._derive_key(temp_key)
            self._current_key_id = self._generate_key_id(self._current_key)
            self._key_generated_at = datetime.now()
            logger.warning("使用临时加密密钥（不安全，仅用于测试）")

    def _generate_key(self) -> str:
        """生成随机密钥"""
        import secrets
        return secrets.token_hex(32)  # 64字符十六进制字符串

    def _derive_key(self, input_key: bytes, salt: bytes = None) -> bytes:
        """从输入密钥派生出适合算法的密钥"""
        if salt is None:
            # 使用固定的盐（在实际应用中应该随机生成并存储）
            salt = b"hermes_fusion_pro_salt_2026"

        if self.algorithm.startswith("AES-256"):
            # 对于AES-256，需要32字节密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return kdf.derive(input_key)
        elif self.algorithm == "Fernet":
            # Fernet使用32字节密钥，base64编码
            return base64.urlsafe_b64encode(input_key[:32])
        else:
            # 默认使用SHA256哈希
            return hashlib.sha256(input_key).digest()

    def _generate_key_id(self, key: bytes) -> str:
        """生成密钥ID（用于标识密钥）"""
        return hashlib.sha256(key).hexdigest()[:16]

    def encrypt(self, plaintext: str, data_type: str = "generic") -> Optional[str]:
        """
        加密数据

        Args:
            plaintext: 明文数据
            data_type: 数据类型，用于密钥派生

        Returns:
            str: 加密后的base64字符串，包含算法、密钥ID和密文
        """
        if not self._current_key:
            logger.error("加密密钥未初始化")
            return None

        try:
            # 检查是否需要轮换密钥
            self._check_key_rotation()

            # 根据算法选择加密方式
            if self.algorithm == "AES-256-GCM":
                return self._encrypt_aes_gcm(plaintext, data_type)
            elif self.algorithm == "Fernet":
                return self._encrypt_fernet(plaintext, data_type)
            else:
                logger.warning(f"未知算法 {self.algorithm}，使用AES-256-GCM回退")
                return self._encrypt_aes_gcm(plaintext, data_type)

        except Exception as e:
            logger.error(f"加密数据失败: {e}")
            return None

    def _encrypt_aes_gcm(self, plaintext: str, data_type: str) -> str:
        """使用AES-256-GCM加密"""
        import secrets

        # 生成随机nonce（12字节，GCM推荐）
        nonce = secrets.token_bytes(12)

        # 创建加密器
        cipher = Cipher(
            algorithms.AES(self._current_key),
            modes.GCM(nonce)
        )
        encryptor = cipher.encryptor()

        # 添加关联数据（可选，用于验证）
        associated_data = data_type.encode('utf-8')
        encryptor.authenticate_additional_data(associated_data)

        # 加密数据
        ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()

        # 获取认证标签
        auth_tag = encryptor.tag

        # 组合结果：算法|密钥ID|nonce|auth_tag|ciphertext
        result = f"AES-GCM|{self._current_key_id}|{base64.b64encode(nonce).decode()}|" \
                 f"{base64.b64encode(auth_tag).decode()}|{base64.b64encode(ciphertext).decode()}"

        return result

    def _encrypt_fernet(self, plaintext: str, data_type: str) -> str:
        """使用Fernet加密"""
        f = Fernet(self._current_key)
        ciphertext = f.encrypt(plaintext.encode('utf-8'))

        # 组合结果：算法|密钥ID|ciphertext
        result = f"Fernet|{self._current_key_id}|{base64.b64encode(ciphertext).decode()}"
        return result

    def decrypt(self, encrypted_data: str, data_type: str = "generic") -> Optional[str]:
        """
        解密数据

        Args:
            encrypted_data: 加密数据字符串
            data_type: 数据类型，用于验证

        Returns:
            str: 解密后的明文
        """
        if not encrypted_data:
            return None

        try:
            # 解析加密数据格式
            parts = encrypted_data.split('|')
            if len(parts) < 3:
                logger.error(f"无效的加密数据格式: {encrypted_data}")
                return None

            algorithm = parts[0]
            key_id = parts[1]

            # 查找对应密钥
            decryption_key = self._get_key_by_id(key_id)
            if decryption_key is None:
                logger.error(f"找不到密钥ID: {key_id}")
                return None

            if algorithm == "AES-GCM":
                if len(parts) != 5:
                    logger.error(f"无效的AES-GCM数据格式: {encrypted_data}")
                    return None

                nonce = base64.b64decode(parts[2])
                auth_tag = base64.b64decode(parts[3])
                ciphertext = base64.b64decode(parts[4])

                # 创建解密器
                cipher = Cipher(
                    algorithms.AES(decryption_key),
                    modes.GCM(nonce, auth_tag)
                )
                decryptor = cipher.decryptor()

                # 验证关联数据
                associated_data = data_type.encode('utf-8')
                decryptor.authenticate_additional_data(associated_data)

                # 解密数据
                plaintext = decryptor.update(ciphertext) + decryptor.finalize()
                return plaintext.decode('utf-8')

            elif algorithm == "Fernet":
                ciphertext = base64.b64decode(parts[2])
                f = Fernet(decryption_key)
                plaintext = f.decrypt(ciphertext)
                return plaintext.decode('utf-8')

            else:
                logger.error(f"不支持的加密算法: {algorithm}")
                return None

        except Exception as e:
            logger.error(f"解密数据失败: {e}")
            return None

    def _get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """根据密钥ID获取密钥"""
        # 首先检查当前密钥
        if self._current_key_id == key_id:
            return self._current_key

        # 检查历史密钥
        for hist_key_id, (hist_key, _) in self._key_history.items():
            if hist_key_id == key_id:
                return hist_key

        return None

    def _check_key_rotation(self):
        """检查并执行密钥轮换"""
        if not self._key_generated_at:
            return

        # 计算密钥年龄
        key_age = datetime.now() - self._key_generated_at

        if key_age.days >= self.key_rotation_days:
            logger.info(f"密钥已使用 {key_age.days} 天，执行轮换")
            self.rotate_keys()

    def rotate_keys(self) -> bool:
        """轮换加密密钥"""
        try:
            # 保存当前密钥到历史
            if self._current_key and self._current_key_id:
                self._key_history[self._current_key_id] = (self._current_key, self._key_generated_at)

                # 清理旧的历史密钥（保留最近3个）
                if len(self._key_history) > 3:
                    oldest_key_id = sorted(self._key_history.items(),
                                          key=lambda x: x[1][1])[0][0]
                    del self._key_history[oldest_key_id]

            # 生成新密钥
            if self.key_storage == "env":
                env_key = os.getenv(self.env_key_name)
                if not env_key:
                    logger.warning("无法轮换密钥：环境变量未设置")
                    return False

                # 生成新密钥（使用不同的派生参数）
                import secrets
                salt = secrets.token_bytes(16)
                new_key = self._derive_key(env_key.encode('utf-8'), salt)

                self._current_key = new_key
                self._current_key_id = self._generate_key_id(new_key)
                self._key_generated_at = datetime.now()

                logger.info(f"密钥轮换成功，新密钥ID: {self._current_key_id}")
                return True

            else:
                logger.warning(f"密钥轮换暂不支持 {self.key_storage} 存储类型")
                return False

        except Exception as e:
            logger.error(f"密钥轮换失败: {e}")
            return False

    def get_key_info(self) -> Dict[str, Any]:
        """获取密钥信息"""
        return {
            "algorithm": self.algorithm,
            "key_storage": self.key_storage,
            "current_key_id": self._current_key_id,
            "key_generated_at": self._key_generated_at.isoformat() if self._key_generated_at else None,
            "key_age_days": (datetime.now() - self._key_generated_at).days if self._key_generated_at else 0,
            "key_rotation_days": self.key_rotation_days,
            "historical_keys_count": len(self._key_history)
        }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "encryption_available": self._current_key is not None,
            "algorithm": self.algorithm,
            "key_initialized": bool(self._current_key),
            "key_age_days": (datetime.now() - self._key_generated_at).days if self._key_generated_at else 0,
            "rotation_needed": (datetime.now() - self._key_generated_at).days >= self.key_rotation_days
                               if self._key_generated_at else False
        }