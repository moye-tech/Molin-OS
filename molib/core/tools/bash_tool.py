"""Bash 命令行工具 — 迁移自 external/hermes-agent/tools/terminal_tool.py"""

from __future__ import annotations

import asyncio
from typing import Any, Dict
from molib.core.tools.registry import BaseTool, ToolResult


class BashTool(BaseTool):
    name = "bash_executor"
    description = "执行 shell 命令。适用于文件操作、系统命令、脚本执行等。"
    input_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的 shell 命令"},
            "timeout": {"type": "integer", "description": "超时秒数", "default": 120},
            "cwd": {"type": "string", "description": "工作目录", "default": None},
        },
        "required": ["command"],
    }

    async def execute(self, command: str, timeout: int = 120, cwd: str = None, **kwargs) -> ToolResult:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")

        output = stdout.decode("utf-8", errors="replace")
        error = stderr.decode("utf-8", errors="replace")

        return ToolResult(
            success=proc.returncode == 0,
            output=output.strip(),
            error=error.strip(),
            metadata={"returncode": proc.returncode},
        )
