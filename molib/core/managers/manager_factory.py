"""
Manager Factory - 管理器工厂
负责创建和管理所有Subsidiary Manager实例。
"""

import importlib
from typing import Dict, Any, Optional
from loguru import logger

from .base_manager import BaseSubsidiaryManager


class ManagerFactory:
    """管理器工厂类"""

    _manager_registry: Dict[str, type] = {}

    @classmethod
    def register(cls, manager_id: str, manager_class: type):
        """注册管理器类"""
        if not issubclass(manager_class, BaseSubsidiaryManager):
            raise TypeError(f"Manager class {manager_class} must subclass BaseSubsidiaryManager")
        cls._manager_registry[manager_id] = manager_class
        logger.debug(f"Registered manager class: {manager_id} -> {manager_class.__name__}")

    @classmethod
    async def create_manager(cls, manager_id: str, config: Dict[str, Any]) -> Optional[BaseSubsidiaryManager]:
        """创建管理器实例（支持 ConfigDrivenManager 自动降级）"""
        try:
            # 1. 检查是否已注册，如果未注册则尝试动态导入
            manager_class = cls._manager_registry.get(manager_id)
            if not manager_class:
                # 尝试从配置中动态导入
                manager_class_name = config.get('manager_class')
                if manager_class_name:
                    try:
                        # 动态导入管理器类
                        module_path, class_name = manager_class_name.rsplit('.', 1)
                        module = importlib.import_module(module_path)
                        manager_class = getattr(module, class_name)

                        # 验证类
                        if not issubclass(manager_class, BaseSubsidiaryManager):
                            logger.error(f"Manager class {manager_class_name} must subclass BaseSubsidiaryManager")
                            return None

                        # 注册到缓存
                        cls._manager_registry[manager_id] = manager_class
                        logger.info(f"Dynamically registered manager class: {manager_id} -> {manager_class_name}")
                    except Exception as e:
                        logger.warning(
                            f"Failed to import {manager_class_name}: {e}, "
                            f"falling back to ConfigDrivenManager"
                        )
                        # 降级到 ConfigDrivenManager
                        manager_class = cls._get_config_driven_class()
                        if manager_class:
                            cls._manager_registry[manager_id] = manager_class
                        else:
                            return None
                else:
                    # 没有指定 manager_class，使用 ConfigDrivenManager
                    manager_class = cls._get_config_driven_class()
                    if manager_class:
                        logger.info(f"Using ConfigDrivenManager for {manager_id}")
                        cls._manager_registry[manager_id] = manager_class
                    else:
                        logger.warning(f"No manager class available for: {manager_id}")
                        return None

            # 2. 创建实例
            manager = manager_class(config)

            # 3. 初始化
            await manager.initialize()

            logger.info(f"Created manager instance: {manager_id} ({manager_class.__name__})")
            return manager

        except Exception as e:
            logger.error(f"Failed to create manager {manager_id}: {e}")
            return None

    @classmethod
    def _get_config_driven_class(cls) -> Optional[type]:
        """获取 ConfigDrivenManager 类"""
        try:
            from .config_driven_manager import ConfigDrivenManager
            return ConfigDrivenManager
        except ImportError as e:
            logger.error(f"ConfigDrivenManager not available: {e}")
            return None

    @classmethod
    def get_registered_managers(cls) -> Dict[str, str]:
        """获取已注册的管理器列表"""
        return {mid: cls._manager_registry[mid].__name__ for mid in cls._manager_registry}

    @classmethod
    def auto_register_from_config(cls, configs: Dict[str, Dict[str, Any]]):
        """根据配置自动注册管理器"""
        for manager_id, config in configs.items():
            manager_class_name = config.get('manager_class')
            if manager_class_name:
                try:
                    # 动态导入管理器类
                    module_path, class_name = manager_class_name.rsplit('.', 1)
                    module = __import__(module_path, fromlist=[class_name])
                    manager_class = getattr(module, class_name)
                    cls.register(manager_id, manager_class)
                except Exception as e:
                    logger.error(f"Failed to auto-register manager {manager_id}: {e}")


# 默认管理器注册
def register_default_managers():
    """注册默认管理器（空实现，依赖动态导入）"""
    # 现在管理器类通过动态导入从配置中加载
    logger.info("Default manager registration skipped - using dynamic import from config")


# 初始化时注册默认管理器
register_default_managers()