"""
External Tool Adapter
标准化接口：将不同开源仓库的各种异构方法签名，统一转换为 墨麟Worker 可以识别的字典/JSON格式参数。
"""
from typing import Dict, Any, Callable
from loguru import logger

class ExternalToolAdapter:
    def __init__(self, tool_name: str, executable_path: str = None):
        self.tool_name = tool_name
        self.executable_path = executable_path
        self._commands = {}
        
    def register_command(self, command_name: str, handler: Callable):
        """注册一个外部工具的具体命令处理器"""
        self._commands[command_name] = handler
        logger.debug(f"Registered external tool command: {self.tool_name}.{command_name}")
        
    async def execute(self, command_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """统一执行入口"""
        if command_name not in self._commands:
            return {"status": "error", "message": f"Command {command_name} not found in {self.tool_name}"}
            
        try:
            handler = self._commands[command_name]
            # 执行底层工具
            result = await handler(params)
            return {
                "status": "success",
                "tool": self.tool_name,
                "command": command_name,
                "data": result
            }
        except Exception as e:
            logger.error(f"External tool execution failed: {self.tool_name}.{command_name} - {e}")
            return {"status": "error", "message": str(e)}

    def get_available_commands(self) -> list:
        return list(self._commands.keys())
