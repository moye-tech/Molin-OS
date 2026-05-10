"""
外部工具桥接层 — 将 integrations/external_tools/ 中的 ExternalToolAdapter
包装为 ToolRegistry 可识别的 BaseTool 格式。
"""

from __future__ import annotations

from typing import Any
from molib.core.tools.registry import BaseTool, ToolResult


class ExternalToolBridge(BaseTool):
    """桥接外部工具到统一注册表"""

    def __init__(self, adapter_instance, command_name: str):
        self._adapter = adapter_instance
        self._command = command_name
        self.name = f"{adapter_instance.tool_name}_{command_name}"
        self.description = f"External tool: {adapter_instance.tool_name} - {command_name}"
        self.input_schema = {
            "type": "object",
            "properties": {
                "params": {"type": "object", "description": "工具参数"}
            },
        }

    async def execute(self, params: dict = None, **kwargs) -> ToolResult:
        result = await self._adapter.execute(self._command, params or kwargs)
        if result.get("status") == "success":
            return ToolResult(
                success=True,
                output=str(result.get("data", "")),
                metadata={"tool": result.get("tool", ""), "command": result.get("command", "")},
            )
        return ToolResult(success=False, error=result.get("message", "Unknown error"))


def register_external_tools() -> None:
    """注册所有外部工具到 ToolRegistry"""
    try:
        from molib.integrations.external_tools import (
            get_cli_hub, get_social_hub, get_web_browser, get_market_radar,
            get_vision_engine, get_agent_skills, get_video_tool,
            get_claw_code_tool, get_trading_tool, get_pm_skills,
        )
        from molib.core.tools.registry import ToolRegistry

        tool_getters = [
            get_cli_hub, get_social_hub, get_web_browser, get_market_radar,
            get_vision_engine, get_agent_skills, get_video_tool,
            get_claw_code_tool, get_trading_tool, get_pm_skills,
        ]

        count = 0
        for getter in tool_getters:
            try:
                adapter = getter()
                for cmd in adapter.get_available_commands():
                    bridge = ExternalToolBridge(adapter, cmd)
                    ToolRegistry.register(bridge.name, bridge)
                    count += 1
            except Exception as e:
                import traceback
                traceback.print_exc()

        if count > 0:
            from loguru import logger
            logger.info(f"External tools bridge: registered {count} tools from external adapters")
    except ImportError as e:
        from loguru import logger
        logger.warning(f"External tools not available: {e}")
