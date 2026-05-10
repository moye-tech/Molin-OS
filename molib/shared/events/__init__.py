"""molib.shared.events — 跨子公司事件总线 + Swarm Engine Handoff 桥接

子包：
- event_bus: FileEventBus — 基于文件的事件系统，支持ACL隔离和内存降级
- swarm_bridge: Swarm Engine Handoff 桥接 — 60+角色模板注册 + 自动路由

用法:
    from molib.shared.events import FileEventBus
    bus = FileEventBus()
    await bus.publish("content_published", "content_writer", {"title": "xxx"})
    await bus.subscribe("content_published", my_handler)

    from molib.shared.events import register_swarm_handoff, swarm_dispatch
    register_swarm_handoff()
    result = swarm_dispatch("帮我写一篇小红书文案")
"""

from .event_bus import FileEventBus, MemEventBus, create_event_bus
from .swarm_bridge import (
    register_swarm_handoff,
    swarm_dispatch,
    SWARM_ROLES,
    SwarmRole,
)

__all__ = [
    "FileEventBus",
    "MemEventBus",
    "create_event_bus",
    "register_swarm_handoff",
    "swarm_dispatch",
    "SWARM_ROLES",
    "SwarmRole",
]
