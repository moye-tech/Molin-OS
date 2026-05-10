"""
ClawCode Tool Integrator (ultraworkers/claw-code)
专为 ClawTeam 生态设计的代码执行引擎，支持沙箱执行、代码审查、自动化重构。
"""
from typing import Dict, Any
import os
import subprocess
import asyncio
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter


class ClawCodeTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="claw_code_tool")
        self.sandbox_enabled = os.getenv("CLAW_CODE_SANDBOX", "true").lower() == "true"
        self.register_command("run_code_review", self._run_code_review)
        self.register_command("run_refactor", self._run_refactor)
        logger.info(f"ClawCodeTool initialized (sandbox={'on' if self.sandbox_enabled else 'off'})")

    async def _run_code_review(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target_path = params.get("target_path", ".")
        depth = params.get("depth", "medium")

        cmd = ["claw-code", "review", "--path", target_path, "--depth", depth]
        if self.sandbox_enabled:
            cmd.insert(0, "claw-sandbox")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(stderr.decode().strip())

        return {
            "status": "success",
            "review_depth": depth,
            "target": target_path,
            "output": stdout.decode()[:2000],
        }

    async def _run_refactor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        target_path = params.get("target_path")
        strategy = params.get("strategy", "extract_method")
        if not target_path:
            raise ValueError("target_path parameter is required for refactoring.")

        cmd = ["claw-code", "refactor", "--path", target_path, "--strategy", strategy]
        if self.sandbox_enabled:
            cmd.insert(0, "claw-sandbox")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(stderr.decode().strip())

        return {
            "status": "success",
            "strategy": strategy,
            "target": target_path,
            "output": stdout.decode()[:2000],
        }


_claw_code_tool = ClawCodeTool()

def get_claw_code_tool() -> ClawCodeTool:
    return _claw_code_tool
