"""molib.shared — 墨麟OS v2.5 共享能力层

15个子包的统一导出入口。各子包可按需导入：
  from molib.shared.agent import Seed
  from molib.shared.ai import ModelRouter
  from molib.shared.llm import LLMRouter
  from molib.shared.memory_layer import MemoryLayer
  from molib.shared.observability import observe_worker
  from molib.shared.fault_tolerance import FaultTolerantChain
  ...

v2.5 新增:
  - memory_layer: mem0 双层记忆系统 (GAP-01)
  - observability: Langfuse 全链路追踪 (GAP-02)
  - fault_tolerance: Prefect 断点续跑 (GAP-03)
  - llm_router 升级: OpenRouter 免费模型路由 (GAP-06)
"""

from . import agent
from . import ai
from . import analysis
from . import content
from . import finance
from . import gate
from . import gui_eval
from . import knowledge
from . import llm
from . import network
from . import publish
from . import storage
from . import tts

# v2.5 新增模块
try:
    from . import memory_layer
except ImportError:
    pass

try:
    from . import observability
except ImportError:
    pass

try:
    from . import fault_tolerance
except ImportError:
    pass

try:
    from . import env_loader
except ImportError:
    pass

__all__ = [
    "agent", "ai", "analysis", "content", "finance", "gate",
    "gui_eval", "knowledge", "llm", "network", "publish", "storage", "tts",
    "memory_layer", "observability", "fault_tolerance",
]
