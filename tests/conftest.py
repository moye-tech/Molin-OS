"""全局测试配置 — Mock redis、qdrant 等外部依赖"""
import sys
from unittest.mock import MagicMock

# 在导入任何项目代码之前 mock redis，避免 ModuleNotFoundError
redis_mock = MagicMock()
redis_mock.exceptions = MagicMock()
redis_mock.exceptions.ResponseError = Exception
sys.modules["redis"] = redis_mock
sys.modules["redis.asyncio"] = MagicMock()
sys.modules["redis.exceptions"] = redis_mock.exceptions

# Mock qdrant_client 避免 portalocker.redis 尝试用 MagicMock 做类型注解
sys.modules["qdrant_client"] = MagicMock()
sys.modules["qdrant_client.models"] = MagicMock()

# Mock aiosqlite 如果不可用
try:
    import aiosqlite
except ImportError:
    sys.modules["aiosqlite"] = MagicMock()
