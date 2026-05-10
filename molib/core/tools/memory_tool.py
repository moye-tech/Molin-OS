"""记忆操作工具 — 桥接 infra/memory/memory_manager.py"""

from __future__ import annotations

from typing import Any, Dict
from molib.core.tools.registry import BaseTool, ToolResult


class MemoryTool(BaseTool):
    name = "memory_tool"
    description = "记忆查询和存储。支持 query（语义搜索）、store（存储）、list（列出所有）三种操作。"
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["query", "store", "list"], "description": "操作类型"},
            "query": {"type": "string", "description": "查询关键词（query 时需要）"},
            "key": {"type": "string", "description": "存储键（store 时需要）"},
            "data": {"type": "object", "description": "存储数据（store 时需要）"},
            "limit": {"type": "integer", "description": "返回条数", "default": 5},
        },
        "required": ["operation"],
    }

    async def execute(self, operation: str, query: str = None, key: str = None,
                      data: Dict = None, limit: int = 5, **kwargs) -> ToolResult:
        try:
            from molib.infra.memory.memory_manager import get_memory_manager, MemoryScenario

            manager = await get_memory_manager()

            if operation == "query":
                if not query:
                    return ToolResult(success=False, error="query is required")
                # 使用 Qdrant 语义搜索
                results = await manager.search(
                    query=query,
                    scenario=MemoryScenario.LONG_TERM,
                    limit=limit,
                )
                output = "\n".join(f"- {r.get('key', 'unknown')}: {r}" for r in (results or []))
                return ToolResult(success=True, output=output or "无相关记忆")

            elif operation == "store":
                if not key or data is None:
                    return ToolResult(success=False, error="key and data are required for store")
                await manager.store(key=key, data=data, scenario=MemoryScenario.LONG_TERM)
                return ToolResult(success=True, output=f"Stored memory: {key}")

            elif operation == "list":
                # 列出所有长期记忆
                results = await manager.search(query="*", scenario=MemoryScenario.LONG_TERM, limit=20)
                output = "\n".join(f"- {r.get('key', 'unknown')}" for r in (results or []))
                return ToolResult(success=True, output=output or "无记忆")

            return ToolResult(success=False, error=f"Unknown operation: {operation}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
