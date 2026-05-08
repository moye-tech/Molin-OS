"""
molib.shared.agent — Agent 核心抽象层

提供不可变 Seed 规范模式 与 SeedContract 运行时解释层。
零外部依赖，仅使用 Python 标准库。
"""

from .spec import Seed, SeedContract

__all__ = ["Seed", "SeedContract"]
