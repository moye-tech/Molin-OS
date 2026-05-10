"""
CredentialVault v6.6 — 凭证保险库
AES-256-GCM 加密存储平台账号凭证，ACL 访问控制，审计日志。
"""

from __future__ import annotations

import os
import json
import time
import hashlib
import base64
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger


# ── 加密层 ──

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography 库不可用，凭证库将使用 base64 编码（不安全，仅开发环境）")


class _Crypto:
    """AES-256-GCM 加解密"""

    def __init__(self, master_key: bytes):
        self._aes = AESGCM(master_key) if CRYPTO_AVAILABLE else None

    def encrypt(self, plaintext: str) -> str:
        if not CRYPTO_AVAILABLE:
            return base64.b64encode(plaintext.encode()).decode()
        nonce = os.urandom(12)
        ciphertext = self._aes.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()

    def decrypt(self, encoded: str) -> str:
        if not CRYPTO_AVAILABLE:
            return base64.b64decode(encoded).decode()
        raw = base64.b64decode(encoded)
        nonce, ciphertext = raw[:12], raw[12:]
        return self._aes.decrypt(nonce, ciphertext, None).decode()


def _derive_master_key() -> bytes:
    """从主密码 + 机器ID 派生加密密钥"""
    machine_id = hashlib.sha256(
        (os.uname().nodename + os.uname().machine).encode()
    ).hexdigest()[:16]

    master_password = os.getenv("CREDENTIAL_MASTER_PASSWORD", "molin-ai-default-key-change-me")
    key_material = f"{master_password}:{machine_id}".encode()
    return hashlib.sha256(key_material).digest()


# ── 数据模型 ──

@dataclass
class CredentialRecord:
    platform: str           # xianyu, xiaohongshu, douyin, feishu, ...
    account_id: str         # 账号标识（用户名/手机号）
    encrypted_secret: str   # 加密后的 cookie/token/密码
    secret_type: str        # "cookie", "token", "password", "api_key"
    expires_at: float = 0   # Unix timestamp, 0=永不过期
    last_verified: float = 0
    tags: List[str] = field(default_factory=list)


# ── ACL 配置 ──

DEFAULT_ACL: Dict[str, List[str]] = {
    "cs": ["xianyu", "feishu"],
    "ip": ["xiaohongshu", "douyin"],
    "bd": ["xianyu", "feishu"],
    "finance": ["payment_api", "xianyu"],
    "ads": ["douyin", "xiaohongshu"],
    "dev": [],
    "research": [],
    "data": [],
    "ceo": ["*"],  # CEO 有全部权限
}


class CredentialVault:
    """凭证保险库 — 独立于其他所有组件"""

    def __init__(self, storage_dir: str = None):
        self._crypto = _Crypto(_derive_master_key())
        self._store: Dict[str, CredentialRecord] = {}
        self._audit_log: List[Dict[str, Any]] = []

        if storage_dir is None:
            storage_dir = "/app/storage/vault" if os.path.isdir("/app/storage") else os.path.join(
                os.path.dirname(os.path.dirname(__file__)) if "__file__" in dir() else "/opt/molin-ai",
                "storage", "vault"
            )
        self._storage_dir = storage_dir
        os.makedirs(self._storage_dir, exist_ok=True)
        self._load()

    # ── CRUD ──

    def store_credential(
        self,
        platform: str,
        account_id: str,
        secret: str,
        secret_type: str = "cookie",
        expires_in_days: int = 0,
        tags: List[str] = None,
    ) -> str:
        """存储加密凭证，返回记录ID"""
        record_id = f"{platform}:{account_id}"
        encrypted = self._crypto.encrypt(secret)
        expires = (time.time() + expires_in_days * 86400) if expires_in_days > 0 else 0

        self._store[record_id] = CredentialRecord(
            platform=platform,
            account_id=account_id,
            encrypted_secret=encrypted,
            secret_type=secret_type,
            expires_at=expires,
            last_verified=time.time(),
            tags=tags or [],
        )
        self._save()
        logger.info(f"[Vault] 凭证已存储: {record_id} (type={secret_type})")
        return record_id

    def get_credential(self, record_id: str, requester_agency: str = "") -> Optional[str]:
        """获取解密后的凭证（需ACL检查）"""
        record = self._store.get(record_id)
        if not record:
            return None

        # ACL 检查
        if not self._check_acl(requester_agency, record.platform):
            self._log_audit(record_id, requester_agency, "DENIED", "ACL拒绝")
            logger.warning(f"[Vault] ACL拒绝: {requester_agency} → {record.platform}")
            return None

        # 过期检查
        if record.expires_at > 0 and time.time() > record.expires_at:
            self._log_audit(record_id, requester_agency, "EXPIRED", "凭证已过期")
            logger.warning(f"[Vault] 凭证已过期: {record_id}")
            return None

        self._log_audit(record_id, requester_agency, "GRANTED", "正常读取")
        return self._crypto.decrypt(record.encrypted_secret)

    def list_credentials(self, platform: str = None) -> List[Dict[str, Any]]:
        """列出凭证（不包含明文）"""
        result = []
        for rid, record in self._store.items():
            if platform and record.platform != platform:
                continue
            result.append({
                "id": rid,
                "platform": record.platform,
                "account_id": record.account_id,
                "secret_type": record.secret_type,
                "expires_at": record.expires_at,
                "is_expired": record.expires_at > 0 and time.time() > record.expires_at,
                "last_verified": record.last_verified,
            })
        return result

    def delete_credential(self, record_id: str) -> bool:
        if record_id in self._store:
            del self._store[record_id]
            self._save()
            return True
        return False

    # ── 过期提醒 ──

    def check_expiring(self, days_before: int = 3) -> List[CredentialRecord]:
        """检查即将过期的凭证"""
        threshold = time.time() + days_before * 86400
        expiring = []
        for record in self._store.values():
            if 0 < record.expires_at <= threshold and record.expires_at > time.time():
                expiring.append(record)
        return expiring

    # ── ACL ──

    def _check_acl(self, agency: str, platform: str) -> bool:
        if not agency:
            return True  # 内部调用
        allowed = DEFAULT_ACL.get(agency, [])
        return "*" in allowed or platform in allowed

    # ── 审计 ──

    def _log_audit(self, record_id: str, requester: str, action: str, detail: str):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "record_id": record_id,
            "requester": requester,
            "action": action,
            "detail": detail,
        }
        self._audit_log.append(entry)
        # 只保留最近 1000 条
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._audit_log[-limit:]

    # ── 持久化 ──

    def _save(self):
        data = {
            rid: {
                "platform": r.platform,
                "account_id": r.account_id,
                "encrypted_secret": r.encrypted_secret,
                "secret_type": r.secret_type,
                "expires_at": r.expires_at,
                "last_verified": r.last_verified,
                "tags": r.tags,
            }
            for rid, r in self._store.items()
        }
        path = os.path.join(self._storage_dir, "vault.json")
        with open(path, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 审计日志单独存储
        audit_path = os.path.join(self._storage_dir, "audit.json")
        with open(audit_path, "w") as f:
            json.dump(self._audit_log[-500:], f, ensure_ascii=False, indent=2)

    def _load(self):
        path = os.path.join(self._storage_dir, "vault.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            for rid, r in data.items():
                self._store[rid] = CredentialRecord(
                    platform=r["platform"],
                    account_id=r["account_id"],
                    encrypted_secret=r["encrypted_secret"],
                    secret_type=r.get("secret_type", "cookie"),
                    expires_at=r.get("expires_at", 0),
                    last_verified=r.get("last_verified", 0),
                    tags=r.get("tags", []),
                )

        audit_path = os.path.join(self._storage_dir, "audit.json")
        if os.path.exists(audit_path):
            with open(audit_path) as f:
                self._audit_log = json.load(f)


# 全局单例
_vault: Optional[CredentialVault] = None


def get_credential_vault() -> CredentialVault:
    global _vault
    if _vault is None:
        _vault = CredentialVault()
    return _vault
