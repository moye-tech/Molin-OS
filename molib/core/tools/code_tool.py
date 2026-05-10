"""代码执行工具 — 迁移自 external/hermes-agent/tools/code_execution_tool.py"""

from __future__ import annotations

import asyncio
import tempfile
import os
from typing import Any
from molib.core.tools.registry import BaseTool, ToolResult


class CodeTool(BaseTool):
    name = "code_tool"
    description = "执行 Python 代码。适用于数据分析、脚本计算等场景。"
    input_schema = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的 Python 代码"},
            "timeout": {"type": "integer", "description": "超时秒数", "default": 60},
        },
        "required": ["code"],
    }

    async def execute(self, code: str, timeout: int = 60, **kwargs) -> ToolResult:
        # 将代码写入临时文件并执行
        fd, path = tempfile.mkstemp(suffix=".py", prefix="molin_code_")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(code)

            proc = await asyncio.create_subprocess_exec(
                "python3", path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            output = stdout.decode("utf-8", errors="replace")
            error = stderr.decode("utf-8", errors="replace")

            return ToolResult(
                success=proc.returncode == 0,
                output=output.strip(),
                error=error.strip(),
                metadata={"returncode": proc.returncode},
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Code execution timed out after {timeout}s")
        finally:
            os.unlink(path)
