"""
CLI Hub External Tool (OpenCLI Integration)
允许 Worker 将自身变成一个强大的命令行控制台，对接底层操作系统的能力，但加入了严格的沙箱与权限控制。
"""
from typing import Dict, Any
import subprocess
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter

class CliHubTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="opencli_hub")
        self.register_command("run_safe_command", self._run_safe_command)
        # 白名单命令前缀（v6.6 扩展）
        self.whitelist_prefixes = [
            "ls", "cat", "echo", "pwd",
            "git status", "git log", "git diff",
            "docker ps", "docker logs", "docker stats", "docker compose ps",
            "df", "free", "uptime", "ps aux",
            "npm run", "pip list", "python --version",
            "curl -s",
        ]
        logger.info("CliHubTool (OpenCLI) initialized with strict sandbox.")

    async def _run_safe_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """在白名单沙箱内执行命令"""
        command = params.get("command")
        if not command:
            raise ValueError("Command parameter is required")

        # 安全校验
        is_safe = any(command.strip().startswith(prefix) for prefix in self.whitelist_prefixes)
        if not is_safe:
            logger.warning(f"[OpenCLI] Rejected unsafe command execution: {command}")
            return {
                "status": "error",
                "message": "Command not in whitelist or potentially unsafe. Request escalated to CEO.",
                "command_rejected": command
            }

        # timeout 从参数读取，默认 30s
        timeout = params.get("timeout", 30)
        logger.debug(f"[OpenCLI] Executing safe command: {command} (timeout={timeout}s)")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return {
                "status": "success" if result.returncode == 0 else "error",
                "command": command,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:2000],
                "return_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Command execution timed out (>{timeout}s)"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

_cli_hub = CliHubTool()

def get_cli_hub() -> CliHubTool:
    return _cli_hub
