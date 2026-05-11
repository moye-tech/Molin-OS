"""
墨麟OS v2.5 — 通用环境变量加载器 (EnvLoader)

解决 .env 中的 API key 在 Python 子进程中不可见的问题。
在 molib 入口处调用 load_dotenv() 即可。

用法:
    from molib.shared.env_loader import load_dotenv
    load_dotenv()  # 将 ~/.hermes/.env 中的变量注入 os.environ

    # 之后所有模块都能通过 os.environ.get() 获取 API key
    import os
    key = os.environ.get("DASHSCOPE_API_KEY", "")
"""

from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# 缓存：避免重复加载
_loaded: bool = False
_env_cache: Dict[str, str] = {}


def load_dotenv(env_path: str = None, override: bool = False) -> Dict[str, str]:
    """
    加载 .env 文件到 os.environ。

    Args:
        env_path: .env 文件路径（默认 ~/.hermes/.env）
        override: 是否覆盖已存在的环境变量

    Returns:
        加载的键值对字典
    """
    global _loaded, _env_cache

    if _loaded and not override:
        return _env_cache

    path = Path(env_path) if env_path else Path.home() / ".hermes" / ".env"
    if not path.exists():
        logger.debug(f".env 文件不存在: {path}")
        return {}

    loaded = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            # 解析 KEY=VALUE
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if not key:
                continue

            # 注入 os.environ
            if override or key not in os.environ:
                os.environ[key] = value
            loaded[key] = value

        _env_cache = loaded
        _loaded = True
        logger.debug(f"✅ 已加载 {len(loaded)} 个环境变量从 {path}")

    except Exception as e:
        logger.warning(f"加载 .env 失败: {e}")

    return loaded


def get_env(key: str, default: str = "") -> str:
    """
    安全获取环境变量（自动加载 .env）。

    Args:
        key: 环境变量名
        default: 默认值

    Returns:
        环境变量值
    """
    if not _loaded:
        load_dotenv()
    return os.environ.get(key, default)


def check_keys(required: list = None) -> Dict[str, bool]:
    """
    检查关键 API key 是否存在。

    Args:
        required: 要检查的 key 名称列表（默认检查所有已知 key）

    Returns:
        {key: bool} 字典
    """
    keys_to_check = required or [
        "DASHSCOPE_API_KEY",
        "OPENROUTER_API_KEY",
        "FIRECRAWL_API_KEY",
        "DEEPSEEK_API_KEY",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "FISH_AUDIO_API_KEY",
    ]

    if not _loaded:
        load_dotenv()

    return {k: bool(os.environ.get(k, "")) for k in keys_to_check}


# 自动加载（在 import 时执行，确保后续模块可用）
load_dotenv()
