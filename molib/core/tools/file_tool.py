"""文件操作工具 — 迁移自 external/hermes-agent/tools/file_operations.py"""

from __future__ import annotations

import os
from typing import Any
from molib.core.tools.registry import BaseTool, ToolResult


class FileTool(BaseTool):
    name = "file_tool"
    description = "文件读写和编辑操作。支持 read、write、append 三种模式。"
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {"type": "string", "enum": ["read", "write", "append"], "description": "操作类型"},
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "写入内容（write/append 时需要）"},
        },
        "required": ["operation", "path"],
    }

    async def execute(self, operation: str, path: str, content: str = None, **kwargs) -> ToolResult:
        try:
            if operation == "read":
                if not os.path.exists(path):
                    return ToolResult(success=False, error=f"File not found: {path}")
                with open(path, "r", encoding="utf-8") as f:
                    return ToolResult(success=True, output=f.read())
            elif operation == "write":
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content or "")
                return ToolResult(success=True, output=f"Written {len(content or '')} chars to {path}")
            elif operation == "append":
                os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content or "")
                return ToolResult(success=True, output=f"Appended {len(content or '')} chars to {path}")
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
