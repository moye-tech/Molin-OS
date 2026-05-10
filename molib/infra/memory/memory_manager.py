"""
墨麟AI智能系统 记忆管理器
整合 SQLite（事务）、Qdrant（向量）、Supermemory（长期语义）和 Redis（缓存）
提供统一的记忆管理接口，根据场景自动选择最佳后端
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from loguru import logger

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    logger.warning("toml库未安装，记忆配置将使用默认值")

# 导入现有记忆客户端
from molib.infra.memory.sqlite_client import SQLiteClient, DB as SQLITE_DB
from molib.infra.memory.qdrant_client import MolinMemory
from molib.infra.memory.memory_acl import get_memory_acl

# 尝试导入Redis，可选
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis库未安装，缓存功能将不可用")

# 尝试导入Supermemory，可选
SUPERMEMORY_AVAILABLE = False
try:
    # 这里假设Supermemory客户端接口
    # 实际实现需要根据外部源文件调整
    SUPERMEMORY_AVAILABLE = os.getenv('SUPERMEMORY_API_KEY') is not None
    if SUPERMEMORY_AVAILABLE:
        logger.info("Supermemory API密钥检测到，Supermemory可用")
except ImportError:
    logger.warning("Supermemory客户端不可用，将使用回退方案")


class MemoryScenario(Enum):
    """记忆使用场景"""
    TRANSACTIONAL = "transactional"  # 事务性数据
    SEMANTIC_SEARCH = "semantic_search"  # 语义搜索
    LONG_TERM = "long_term_memory"  # 长期记忆
    CACHE = "cache"  # 缓存
    REALTIME_ANALYTICS = "realtime_analytics"  # 实时分析


class MemoryManager:
    """统一记忆管理器"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).resolve().parent.parent / "config" / "memory.toml"
        self.config = self._load_config()

        # 初始化客户端
        self.sqlite = SQLiteClient()
        self.qdrant = MolinMemory()
        self.redis_client = None
        self.supermemory_client = None

        self._init_clients()

    def _load_config(self) -> Dict[str, Any]:
        """加载记忆配置"""
        default_config = {
            "providers": {
                "sqlite": {"enabled": True, "priority": 1},
                "qdrant": {"enabled": True, "priority": 2},
                "supermemory": {"enabled": False, "priority": 3, "optional": True},
                "redis": {"enabled": False, "priority": 0}
            },
            "scenarios": {
                "transactional": {"providers": ["sqlite"], "ttl": "permanent"},
                "semantic_search": {"providers": ["qdrant"], "ttl": "30d"},
                "long_term_memory": {"providers": ["supermemory", "sqlite"], "ttl": "1y"},
                "cache": {"providers": ["redis"], "ttl": "1h"},
                "realtime_analytics": {"providers": ["redis", "sqlite"], "ttl": {"redis": "24h", "sqlite": "7d"}}
            }
        }

        if TOML_AVAILABLE and self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    toml_config = toml.load(f)

                # 合并默认配置和TOML配置
                merged_config = default_config.copy()

                # 更新providers
                if 'providers' in toml_config:
                    for provider, config in toml_config['providers'].items():
                        if provider in merged_config['providers']:
                            merged_config['providers'][provider].update(config)
                        else:
                            merged_config['providers'][provider] = config

                # 更新scenarios
                if 'scenarios' in toml_config:
                    merged_config['scenarios'].update(toml_config['scenarios'])

                logger.info(f"Loaded memory config from {self.config_path}")
                return merged_config

            except Exception as e:
                logger.error(f"Failed to load memory TOML config: {e}")
                return default_config
        else:
            logger.info(f"Using default memory config (TOML not available or not found)")
            return default_config

    def _init_clients(self):
        """初始化记忆客户端"""
        # 初始化SQLite
        if self.config['providers']['sqlite']['enabled']:
            logger.info("Initializing SQLite client")
            # 确保数据库目录存在
            db_dir = os.path.dirname(SQLITE_DB)
            try:
                os.makedirs(db_dir, exist_ok=True)
                # 测试目录是否可写
                test_file = os.path.join(db_dir, '.write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logger.info(f"SQLite directory ready: {db_dir}")
            except Exception as e:
                logger.error(f"SQLite directory not writable: {e}")
                logger.warning("Disabling SQLite provider due to initialization failure")
                self.config['providers']['sqlite']['enabled'] = False

        # 初始化Qdrant
        if self.config['providers']['qdrant']['enabled']:
            logger.info("Initializing Qdrant client")
            try:
                self.qdrant.init_collections()
                logger.info("Qdrant client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant client: {e}")
                logger.warning("Disabling Qdrant provider due to initialization failure")
                # 禁用Qdrant提供者
                self.config['providers']['qdrant']['enabled'] = False
                # 将Qdrant客户端设置为None，避免后续操作
                self.qdrant = None

        # 初始化Redis（如果启用且可用）
        redis_enabled = self.config['providers'].get('redis', {}).get('enabled', False)
        if redis_enabled and REDIS_AVAILABLE:
            try:
                redis_host = os.getenv('REDIS_HOST', 'redis')
                redis_port = int(os.getenv('REDIS_PORT', '6379'))
                redis_password = os.getenv('REDIS_PASSWORD', '')

                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password if redis_password else None,
                    decode_responses=True
                )
                logger.info("Redis client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {e}")

        # 初始化Supermemory（如果启用且可用）
        supermemory_enabled = self.config['providers'].get('supermemory', {}).get('enabled', False)
        if supermemory_enabled and SUPERMEMORY_AVAILABLE:
            try:
                # 这里需要根据外部源文件实现Supermemory客户端初始化
                # 暂时使用占位符
                self.supermemory_client = SupermemoryPlaceholder()
                logger.info("Supermemory client initialized (placeholder)")
            except Exception as e:
                logger.error(f"Failed to initialize Supermemory client: {e}")

    def _get_providers_for_scenario(self, scenario: Union[str, MemoryScenario]) -> List[str]:
        """获取场景对应的记忆提供者列表（按优先级排序）"""
        scenario_str = scenario.value if isinstance(scenario, MemoryScenario) else scenario

        if scenario_str not in self.config['scenarios']:
            logger.warning(f"Unknown scenario: {scenario_str}, using default (transactional)")
            scenario_str = 'transactional'

        provider_names = self.config['scenarios'][scenario_str].get('providers', ['sqlite'])

        # 过滤掉未启用的提供者
        enabled_providers = []
        for provider_name in provider_names:
            provider_config = self.config['providers'].get(provider_name, {})
            if provider_config.get('enabled', False):
                enabled_providers.append(provider_name)
            elif not provider_config.get('optional', False):
                logger.warning(f"Required provider {provider_name} is disabled for scenario {scenario_str}")

        # 为semantic_search场景提供回退：如果Qdrant不可用，使用SQLite
        if scenario_str == 'semantic_search' and not enabled_providers:
            sqlite_enabled = self.config['providers'].get('sqlite', {}).get('enabled', False)
            if sqlite_enabled:
                logger.info(f"Using SQLite as fallback for semantic_search scenario (Qdrant disabled)")
                enabled_providers = ['sqlite']

        return enabled_providers

    async def store(self, key: str, data: Any, scenario: Union[str, MemoryScenario],
                   metadata: Optional[Dict[str, Any]] = None,
                   agency_id: Optional[str] = None, namespace: Optional[str] = None) -> bool:
        """存储数据到记忆系统（带 ACL 校验 + namespace 隔离）"""
        scenario_str = scenario.value if isinstance(scenario, MemoryScenario) else scenario
        namespace = namespace or (metadata.get("namespace") if metadata else None) or scenario_str

        # ACL 权限校验
        if agency_id:
            acl = get_memory_acl()
            if not acl.check_access(agency_id, namespace, "write"):
                logger.warning(f"ACL denied write: agency={agency_id} namespace={namespace}")
                return False

        providers = self._get_providers_for_scenario(scenario_str)

        if not providers:
            logger.error(f"No enabled providers for scenario: {scenario_str}")
            return False

        success = False
        metadata = metadata or {}
        metadata["namespace"] = namespace

        for provider_name in providers:
            try:
                if provider_name == 'sqlite':
                    await self._store_sqlite(key, data, metadata, scenario_str, namespace)
                    success = True
                elif provider_name == 'qdrant':
                    await self._store_qdrant(key, data, metadata, scenario_str)
                    success = True
                elif provider_name == 'redis' and self.redis_client:
                    await self._store_redis(key, data, metadata, scenario_str)
                    success = True
                elif provider_name == 'supermemory' and self.supermemory_client:
                    await self._store_supermemory(key, data, metadata, scenario_str)
                    success = True
                else:
                    logger.warning(f"Provider {provider_name} not available or not implemented")
            except Exception as e:
                logger.error(f"Failed to store to {provider_name}: {e}")

        return success

    async def retrieve(self, key: str, scenario: Union[str, MemoryScenario],
                      query: Optional[str] = None, limit: int = 10,
                      agency_id: Optional[str] = None, namespace: Optional[str] = None) -> List[Any]:
        """从记忆系统检索数据（带 ACL 校验 + namespace 隔离）"""
        scenario_str = scenario.value if isinstance(scenario, MemoryScenario) else scenario
        namespace = namespace or scenario_str

        # ACL 权限校验
        if agency_id:
            acl = get_memory_acl()
            if not acl.check_access(agency_id, namespace, "read"):
                logger.warning(f"ACL denied read: agency={agency_id} namespace={namespace}")
                return []

        providers = self._get_providers_for_scenario(scenario_str)

        results = []

        for provider_name in providers:
            try:
                if provider_name == 'sqlite':
                    provider_results = await self._retrieve_sqlite(key, query, limit, scenario_str, namespace)
                    results.extend(provider_results)
                elif provider_name == 'qdrant':
                    provider_results = await self._retrieve_qdrant(key, query, limit, scenario_str)
                    results.extend(provider_results)
                elif provider_name == 'redis' and self.redis_client:
                    provider_results = await self._retrieve_redis(key, query, limit, scenario_str)
                    results.extend(provider_results)
                elif provider_name == 'supermemory' and self.supermemory_client:
                    provider_results = await self._retrieve_supermemory(key, query, limit, scenario_str)
                    results.extend(provider_results)
            except Exception as e:
                logger.error(f"Failed to retrieve from {provider_name}: {e}")

        unique_results = []
        seen_keys = set()
        for result in results:
            result_key = result.get('key') or str(result)
            if result_key not in seen_keys:
                seen_keys.add(result_key)
                unique_results.append(result)

        return unique_results[:limit]

    async def _store_sqlite(self, key: str, data: Any, metadata: Dict[str, Any], scenario: str, namespace: str = "global"):
        """存储到SQLite（带 namespace 隔离 + 重要性评分）"""
        try:
            await self.sqlite.init()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")

        importance = metadata.get("importance_score", 1.0)
        if isinstance(data, dict):
            importance = data.get("roi", data.get("quality_score", data.get("confidence", importance)))
        await self.sqlite.store_memory(key, data, scenario, namespace, importance_score=importance)
        logger.debug(f"Stored to SQLite: {key} (score={importance}, namespace={namespace})")

    async def _store_qdrant(self, key: str, data: Any, metadata: Dict[str, Any], scenario: str):
        """存储到Qdrant"""
        # 如果Qdrant客户端未初始化（例如初始化失败），直接返回
        if self.qdrant is None:
            logger.warning(f"Qdrant client not available, skipping store for key: {key}")
            return

        # Qdrant需要文本进行嵌入，所以将数据转换为文本
        if isinstance(data, dict):
            text = json.dumps(data, ensure_ascii=False)
        else:
            text = str(data)

        # 这里简化处理，实际可能需要根据场景选择不同的集合
        if scenario == 'semantic_search':
            # 使用用户行为集合
            self.qdrant.upsert_user(key, {'text': text, 'metadata': metadata, 'scenario': scenario})
        elif scenario == 'long_term_memory':
            # 使用决策历史集合
            # 这里需要扩展qdrant_client以支持更多集合
            pass

        logger.debug(f"Stored to Qdrant: {key} ({scenario})")

    async def _store_redis(self, key: str, data: Any, metadata: Dict[str, Any], scenario: str):
        """存储到Redis"""
        if not self.redis_client:
            return

        redis_key = f"hermes:memory:{scenario}:{key}"
        value = {
            'data': data,
            'metadata': metadata,
            'timestamp': json.dumps({'stored_at': 'now'})  # 简化
        }

        await self.redis_client.set(redis_key, json.dumps(value))

        # 设置TTL（根据场景配置）
        ttl_config = self.config['scenarios'][scenario].get('ttl', '1h')
        if isinstance(ttl_config, dict):
            ttl = ttl_config.get('redis', 3600)  # 默认1小时
        elif ttl_config == 'permanent':
            ttl = None  # 永不过期
        else:
            # 解析时间字符串如 '1h', '30d'
            ttl = self._parse_ttl(ttl_config)

        if ttl:
            await self.redis_client.expire(redis_key, ttl)

        logger.debug(f"Stored to Redis: {key} ({scenario}), TTL: {ttl}")

    async def _store_supermemory(self, key: str, data: Any, metadata: Dict[str, Any], scenario: str):
        """存储到Supermemory（占位符实现）"""
        logger.info(f"[Supermemory Placeholder] Would store: {key} ({scenario})")
        # 实际实现需要根据外部源文件

    async def _retrieve_sqlite(self, key: str, query: Optional[str], limit: int, scenario: str, namespace: str = "global") -> List[Any]:
        """从SQLite检索（带 namespace 隔离 + 重要性衰减）"""
        results = await self.sqlite.retrieve_memory(key, scenario, namespace, limit)
        if not results:
            logger.debug(f"No results from SQLite: key={key} scenario={scenario} namespace={namespace}")
        return results

    async def _retrieve_qdrant(self, key: str, query: Optional[str], limit: int, scenario: str) -> List[Any]:
        """从Qdrant检索"""
        # 如果Qdrant客户端未初始化（例如初始化失败），直接返回空列表
        if self.qdrant is None:
            logger.warning(f"Qdrant client not available, skipping retrieve for query: {query}")
            return []

        if not query:
            return []

        if scenario == 'semantic_search':
            results = self.qdrant.search_similar_users(query, limit=limit)
            return [{'key': r['user_id'], 'score': r['score'], 'source': 'qdrant'} for r in results]
        else:
            return []

    async def _retrieve_redis(self, key: str, query: Optional[str], limit: int, scenario: str) -> List[Any]:
        """从Redis检索"""
        if not self.redis_client:
            return []

        if key:
            redis_key = f"hermes:memory:{scenario}:{key}"
            value = await self.redis_client.get(redis_key)
            if value:
                try:
                    data = json.loads(value)
                    return [{'key': key, 'data': data, 'source': 'redis'}]
                except json.JSONDecodeError:
                    pass

        return []

    async def _retrieve_supermemory(self, key: str, query: Optional[str], limit: int, scenario: str) -> List[Any]:
        """从Supermemory检索（占位符实现）"""
        logger.info(f"[Supermemory Placeholder] Would retrieve: {key} ({scenario})")
        return []

    def _parse_ttl(self, ttl_str: str) -> int:
        """解析TTL时间字符串"""
        if not ttl_str:
            return 3600  # 默认1小时

        ttl_str = ttl_str.lower()
        if ttl_str.endswith('s'):  # 秒
            return int(ttl_str[:-1])
        elif ttl_str.endswith('m'):  # 分钟
            return int(ttl_str[:-1]) * 60
        elif ttl_str.endswith('h'):  # 小时
            return int(ttl_str[:-1]) * 3600
        elif ttl_str.endswith('d'):  # 天
            return int(ttl_str[:-1]) * 86400
        elif ttl_str.endswith('y'):  # 年
            return int(ttl_str[:-1]) * 31536000
        else:
            try:
                return int(ttl_str)
            except ValueError:
                return 3600  # 默认1小时


class SupermemoryPlaceholder:
    """Supermemory客户端占位符"""
    def __init__(self):
        self.enabled = SUPERMEMORY_AVAILABLE

    async def store(self, key: str, data: Any):
        logger.info(f"[Supermemory Placeholder] Store: {key}")

    async def retrieve(self, query: str, limit: int = 10):
        logger.info(f"[Supermemory Placeholder] Retrieve: {query}")
        return []


# 全局记忆管理器实例
_memory_manager_instance = None

async def get_memory_manager() -> MemoryManager:
    """获取全局记忆管理器实例（单例）"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance


def get_agency_namespace(agency_id: str) -> str:
    """从 subsidiaries.toml 获取子公司的 memory_namespace"""
    subs_path = Path(__file__).resolve().parent.parent.parent / "config" / "subsidiaries.toml"
    if not TOML_AVAILABLE or not subs_path.exists():
        return agency_id  # 回退到 agency_id
    try:
        with open(subs_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        agencies = config.get('agencies', [])
        for agency in agencies:
            if isinstance(agency, dict) and agency.get('id') == agency_id:
                return agency.get('memory_namespace', agency_id)
    except Exception as e:
        logger.warning(f"Failed to load namespace for {agency_id}: {e}")
    return agency_id