"""
Manager Dispatcher - 管理器调度器
负责管理所有Subsidiary Manager实例，并根据任务路由到合适的Manager。
"""

import importlib
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

# TOML 库兼容
_tomllib = None
_tomllib_is_text = False
try:
    import tomllib  # Python 3.11+
    _tomllib = tomllib
    _tomllib_is_text = False
except ImportError:
    try:
        import tomli as _tomllib
        _tomllib_is_text = False
    except ImportError:
        try:
            import toml as _tomllib
            _tomllib_is_text = True
        except ImportError:
            pass


def _load_toml_file(path: Path) -> Dict[str, Any]:
    """加载 TOML 文件，兼容多种库"""
    if _tomllib is None or not path.exists():
        return {}
    try:
        if _tomllib_is_text:
            with open(path, "r", encoding="utf-8") as f:
                return _tomllib.load(f)
        else:
            with open(path, "rb") as f:
                return _tomllib.load(f)
    except Exception as e:
        logger.error(f"加载 TOML 失败 {path}: {e}")
        return {}

from molib.agencies.base import Task, AgencyResult
from .base_manager import BaseSubsidiaryManager, ManagerResult


class ManagerDispatcher:
    """管理器调度器"""

    def __init__(self):
        self.managers: Dict[str, BaseSubsidiaryManager] = {}
        self.manager_configs: Dict[str, Dict[str, Any]] = {}
        self.initialized = False

    async def initialize(self, config_path: Optional[Path] = None):
        """初始化所有管理器"""
        if self.initialized:
            return

        # 加载管理器配置
        await self._load_manager_configs(config_path)

        # 创建管理器实例
        await self._create_managers()

        # 初始化所有管理器
        for manager_id, manager in self.managers.items():
            try:
                await manager.initialize()
                logger.info(f"Manager {manager_id} initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize manager {manager_id}: {e}")

        self.initialized = True
        logger.info(f"ManagerDispatcher initialized with {len(self.managers)} managers")

    async def _load_manager_configs(self, config_path: Optional[Path] = None):
        """加载管理器配置，并合并 subsidiaries.toml 中的关键词等配置"""
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent.parent / "config" / "managers.toml"

        # 加载 subsidiaries.toml 用于合并
        subsidiaries_path = Path(__file__).resolve().parent.parent.parent / "config" / "subsidiaries.toml"
        subsidiary_map: Dict[str, Dict[str, Any]] = _load_toml_file(subsidiaries_path)
        subsidiary_list = subsidiary_map.get('agencies', [])
        subsidiary_id_map: Dict[str, Dict[str, Any]] = {}
        for agency in subsidiary_list:
            if isinstance(agency, dict) and 'id' in agency:
                subsidiary_id_map[agency['id']] = agency

        if not config_path.exists():
            logger.warning(f"Manager config file not found at {config_path}, using default configs")
            self.manager_configs = self._get_default_configs()
            return

        config = _load_toml_file(config_path)
        if not config:
            logger.warning(f"加载 managers.toml 失败，使用默认配置")
            self.manager_configs = self._get_default_configs()
            return

        manager_configs = config.get('managers', {})
        for manager_id, manager_config in manager_configs.items():
            sub_id = manager_config.get('subsidiary_id', '')
            sub_cfg = subsidiary_id_map.get(sub_id, {})
            if sub_cfg:
                merged = {**manager_config}
                for key in ('trigger_keywords', 'approval_level', 'cost_level',
                            'default_model', 'fallback_model', 'max_concurrent',
                            'timeout_seconds', 'handoff_to', 'escalate_when'):
                    if key in sub_cfg and key not in merged:
                        merged[key] = sub_cfg[key]
                self.manager_configs[manager_id] = merged
            else:
                self.manager_configs[manager_id] = manager_config
            logger.debug(f"Loaded config for manager: {manager_id}")

        logger.info(f"Loaded {len(manager_configs)} manager configs from {config_path}")

    def _get_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取默认管理器配置"""
        return {
            "ai_manager": {
                "subsidiary_id": "ai",
                "worker_types": ["prompt_engineer", "model_optimizer", "code_reviewer"],
                "max_concurrent_tasks": 5,
                "claude_code_enabled": True,
                "enabled": True
            },
            "growth_manager": {
                "subsidiary_id": "growth",
                "worker_types": ["marketing_writer", "ab_test_designer"],
                "max_concurrent_tasks": 3,
                "claude_code_enabled": True,
                "enabled": True
            },
            "dev_manager": {
                "subsidiary_id": "dev",
                "worker_types": ["code_generator", "code_reviewer", "debugger"],
                "max_concurrent_tasks": 4,
                "claude_code_enabled": True,
                "enabled": True
            }
        }

    async def _create_managers(self):
        """创建管理器实例"""
        from .manager_factory import ManagerFactory

        for manager_id, config in self.manager_configs.items():
            if not config.get('enabled', True):
                logger.debug(f"Skipping disabled manager: {manager_id}")
                continue

            try:
                manager = await ManagerFactory.create_manager(manager_id, config)
                if manager:
                    self.managers[manager_id] = manager
                    logger.info(f"Created manager: {manager_id}")
                else:
                    logger.warning(f"Failed to create manager: {manager_id}")

            except Exception as e:
                logger.error(f"Error creating manager {manager_id}: {e}")

    async def dispatch(self, task: Task, use_managers: bool = True) -> Optional[ManagerResult]:
        """分发任务到合适的管理器"""
        if not use_managers or not self.managers:
            logger.debug("No managers available or managers disabled, skipping manager dispatch")
            return None

        # 1. 检查任务类型和关键词，找到合适的管理器
        target_manager_id = self._find_manager_for_task(task)

        if not target_manager_id:
            logger.debug(f"No suitable manager found for task {task.task_id}")
            return None

        # 2. 获取管理器
        manager = self.managers.get(target_manager_id)
        if not manager:
            logger.warning(f"Manager {target_manager_id} not found in active managers")
            return None

        # 3. 检查管理器是否能处理此任务
        if not await manager.can_handle(task):
            logger.debug(f"Manager {target_manager_id} cannot handle task {task.task_id}")
            return None

        # 4. 委派任务
        try:
            logger.info(f"Dispatching task {task.task_id} to manager {target_manager_id}")
            result = await manager.delegate_task(task)
            return result

        except Exception as e:
            logger.error(f"Task delegation failed for {task.task_id} with manager {target_manager_id}: {e}")
            return None

    def _find_manager_for_task(self, task: Task) -> Optional[str]:
        """根据任务找到合适的管理器"""
        # 1. 首先检查任务类型
        task_type = task.task_type.lower()
        task_description = str(task.payload.get('description', '')).lower()

        # 2. 检查所有管理器的触发关键词
        for manager_id, manager in self.managers.items():
            try:
                keywords = manager.get_trigger_keywords()
                if any(keyword.lower() in task_description for keyword in keywords):
                    logger.debug(f"Manager {manager_id} matched by keywords")
                    return manager_id
            except Exception as e:
                logger.warning(f"Error getting keywords from manager {manager_id}: {e}")

        # 3. 根据任务类型映射
        type_mapping = {
            "ai_optimization": "ai_manager",
            "content_creation": "ip_manager",
            "code_development": "dev_manager",
            "data_analysis": "data_manager",
            "growth_marketing": "growth_manager",
            "order_processing": "order_manager",
            "ecommerce": "shop_manager",
            "education": "edu_manager",
            "security": "secure_manager",
            "research": "research_manager",
            "product": "product_manager",
            "advertising": "ads_manager"
        }

        # 检查精确匹配
        if task_type in type_mapping:
            manager_id = type_mapping[task_type]
            if manager_id in self.managers:
                logger.debug(f"Manager {manager_id} matched by task type: {task_type}")
                return manager_id

        # 检查部分匹配
        for type_key, manager_id in type_mapping.items():
            if type_key in task_type and manager_id in self.managers:
                logger.debug(f"Manager {manager_id} matched by partial task type: {type_key}")
                return manager_id

        # 4. 检查描述中的关键词
        keyword_mapping = {
            "ai": "ai_manager",
            "prompt": "ai_manager",
            "model": "ai_manager",
            "growth": "growth_manager",
            "marketing": "growth_manager",
            "code": "dev_manager",
            "development": "dev_manager",
            "data": "data_manager",
            "analysis": "data_manager",
            "content": "ip_manager",
            "creation": "ip_manager",
            "order": "order_manager",
            "price": "order_manager",
            "shop": "shop_manager",
            "ecommerce": "shop_manager",
            "education": "edu_manager",
            "learn": "edu_manager",
            "security": "secure_manager",
            "compliance": "secure_manager",
            "research": "research_manager",
            "market": "research_manager",
            "product": "product_manager",
            "design": "product_manager",
            "ad": "ads_manager",
            "advertising": "ads_manager"
        }

        for keyword, manager_id in keyword_mapping.items():
            if keyword in task_description and manager_id in self.managers:
                logger.debug(f"Manager {manager_id} matched by keyword: {keyword}")
                return manager_id

        return None

    def get_manager(self, manager_id: str) -> Optional[BaseSubsidiaryManager]:
        """获取指定ID的管理器，支持 'edu' → 'edu_manager' 自动映射"""
        if manager_id in self.managers:
            return self.managers[manager_id]
        # 尝试加上 _manager 后缀
        key = f"{manager_id}_manager"
        if key in self.managers:
            return self.managers[key]
        return None

    def list_managers(self) -> Dict[str, Dict[str, Any]]:
        """列出所有管理器及其状态"""
        result = {}
        for manager_id, manager in self.managers.items():
            try:
                metrics = manager.get_metrics()
                result[manager_id] = {
                    "subsidiary_id": manager.subsidiary_id,
                    "enabled": True,
                    "metrics": metrics,
                    "worker_count": len(manager.worker_pool) if hasattr(manager, 'worker_pool') else 0
                }
            except Exception as e:
                logger.warning(f"Error getting metrics for manager {manager_id}: {e}")
                result[manager_id] = {
                    "subsidiary_id": manager.subsidiary_id,
                    "enabled": True,
                    "error": str(e)
                }

        return result

    async def shutdown(self):
        """关闭所有管理器"""
        for manager_id, manager in self.managers.items():
            try:
                # 这里可以添加管理器的清理逻辑
                logger.info(f"Shutting down manager: {manager_id}")
            except Exception as e:
                logger.error(f"Error shutting down manager {manager_id}: {e}")

        self.managers.clear()
        self.initialized = False
        logger.info("ManagerDispatcher shutdown completed")


# 全局调度器实例
_dispatcher_instance: Optional[ManagerDispatcher] = None


async def get_dispatcher() -> ManagerDispatcher:
    """获取全局调度器实例"""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = ManagerDispatcher()
        await _dispatcher_instance.initialize()
    return _dispatcher_instance


async def dispatch_task(task: Task, use_managers: bool = True) -> Optional[ManagerResult]:
    """分发任务（便捷函数）"""
    dispatcher = await get_dispatcher()
    return await dispatcher.dispatch(task, use_managers)


async def dispatch_to_manager(manager_id: str, task: Task) -> AgencyResult:
    """将任务分派给指定管理器"""
    from .base_manager import ManagerResult

    dispatcher = await get_dispatcher()

    # claude_code_enabled 仅影响 Manager 内部是否使用 Claude Code 分析任务，
    # 不再决定是否走 Worker 链路——所有 Manager 都走完整派发流程
    manager = dispatcher.get_manager(manager_id)
    if not manager:
        return AgencyResult(
            task_id=task.task_id,
            agency_id=f"manager:{manager_id}",
            status="error",
            error=f"Manager {manager_id} not found"
        )

    try:
        # 检查管理器是否能处理此任务
        if not await manager.can_handle(task):
            return AgencyResult(
                task_id=task.task_id,
                agency_id=f"manager:{manager_id}",
                status="error",
                error=f"Manager {manager_id} cannot handle this task"
            )

        # 委派任务
        manager_result = await manager.delegate_task(task)

        # 将ManagerResult转换为AgencyResult
        if manager_result.status == "error":
            return AgencyResult(
                task_id=task.task_id,
                agency_id=f"manager:{manager_id}",
                status="error",
                error=manager_result.error,
                output=manager_result.aggregated_output
            )
        else:
            # success 或 partial_success
            return AgencyResult(
                task_id=task.task_id,
                agency_id=f"manager:{manager_id}",
                status="success",
                output=manager_result.aggregated_output,
                cost=manager_result.total_cost,
                latency=manager_result.total_latency
            )

    except Exception as e:
        logger.error(f"Task delegation failed for {task.task_id} with manager {manager_id}: {e}")
        return AgencyResult(
            task_id=task.task_id,
            agency_id=f"manager:{manager_id}",
            status="error",
            error=str(e)
        )