"""
墨麟AI智能系统 6.0 - Subsidiary Manager 模块
提供子公司管理层的实现，实现 CEO → Subsidiary Manager → Worker Agents 的三层架构。
"""

from .base_manager import BaseSubsidiaryManager
from .manager_dispatcher import ManagerDispatcher
from .manager_factory import ManagerFactory

__all__ = [
    'BaseSubsidiaryManager',
    'ManagerDispatcher',
    'ManagerFactory',
]

__version__ = '6.6.0'