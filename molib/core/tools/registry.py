"""
墨麟AI智能系统 v6.6 — 统一工具注册表
所有层级的智能体（CEO/Manager/Worker）都通过此注册表获取可用工具。
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type
from loguru import logger


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTool(abc.ABC):
    """所有工具的基类"""

    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}

    @abc.abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具"""
        ...

    async def __call__(self, **kwargs) -> ToolResult:
        try:
            result = await self.execute(**kwargs)
            logger.debug(f"Tool {self.name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} failed: {e}")
            return ToolResult(success=False, error=str(e))


class ToolRegistry:
    """
    统一工具注册表。

    用法：
        ToolRegistry.register("bash", BashTool())
        tool = ToolRegistry.get("bash")
        result = await tool.execute(command="ls -la")
    """

    _tools: Dict[str, BaseTool] = {}
    _agent_tools: Dict[str, List[str]] = {
        "ceo": ["memory_query", "experience_search", "business_analysis",
                "roi_calculator", "subsidiary_lookup", "requirement_analyzer",
                "task_decomposer"],
        "manager": ["memory_query", "task_decomposer", "delegate_tool",
                    "file_tool"],
        "worker": ["bash_executor", "file_tool", "web_tool",
                   "browser_tool", "code_tool", "memory_tool"],
    }

    @classmethod
    def register(cls, name: str, tool: BaseTool) -> None:
        cls._tools[name] = tool
        logger.info(f"Tool registered: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        tool = cls._tools.get(name)
        if tool is None:
            logger.warning(f"Tool not found: {name}")
        return tool

    @classmethod
    def list_for_agent(cls, agent_role: str) -> List[str]:
        """根据智能体角色返回可用工具名称列表"""
        return cls._agent_tools.get(agent_role, [])

    @classmethod
    def get_tools_for_agent(cls, agent_role: str) -> Dict[str, BaseTool]:
        """返回智能体可用的工具实例字典"""
        names = cls.list_for_agent(agent_role)
        return {n: cls._tools[n] for n in names if n in cls._tools}

    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._tools.keys())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._tools.clear()


class _StubTool(BaseTool):
    """占位工具，用于降级不可用的 CEO 工具"""
    def __init__(self, name: str):
        self.name = name
        self.description = f"Stub for {name}"
    async def execute(self, **kwargs):
        return ToolResult(success=False, output=f"Tool {self.name} not available")


def register_default_tools() -> None:
    """注册默认工具集。在系统启动时调用。"""
    from molib.core.tools.bash_tool import BashTool
    from molib.core.tools.file_tool import FileTool
    from molib.core.tools.web_tool import WebTool
    from molib.core.tools.memory_tool import MemoryTool
    from molib.core.tools.code_tool import CodeTool
    from molib.core.tools.browser_tool import BrowserTool

    ToolRegistry.register("bash_executor", BashTool())
    ToolRegistry.register("file_tool", FileTool())
    ToolRegistry.register("web_tool", WebTool())
    ToolRegistry.register("memory_tool", MemoryTool())
    ToolRegistry.register("code_tool", CodeTool())
    ToolRegistry.register("browser_tools", BrowserTool())

    # CEO 专用工具（来自 hermes_fusion.tools.ceo_tools 或内置占位）
    try:
        from hermes_fusion.tools.ceo_tools import CeoTools

        class BusinessAnalysisTool:
            async def execute(self, **kwargs):
                return {"success": True, "output": CeoTools.analyze_roi(**kwargs)}

        class ROICalculatorTool:
            async def execute(self, budget=0, timeline_days=0, expected_revenue=0):
                return {"success": True, "output": CeoTools.analyze_roi(budget, timeline_days, expected_revenue)}

        class SubsidiaryLookupTool:
            async def execute(self, **kwargs):
                return {"success": True, "output": {"subsidiaries": []}}

        ToolRegistry.register("business_analysis", BusinessAnalysisTool())
        ToolRegistry.register("roi_calculator", ROICalculatorTool())
        ToolRegistry.register("subsidiary_lookup", SubsidiaryLookupTool())
    except ImportError:
        logger.warning("hermes_fusion CEO tools not available, using stubs")
        ToolRegistry.register("business_analysis", _StubTool("business_analysis"))
        ToolRegistry.register("roi_calculator", _StubTool("roi_calculator"))
        ToolRegistry.register("subsidiary_lookup", _StubTool("subsidiary_lookup"))

    logger.info(f"Default tools registered: {ToolRegistry.list_all()}")

    # 注册外部工具（通过桥接层将 ExternalToolAdapter 转为 BaseTool）
    from molib.core.tools.external_tools_bridge import register_external_tools
    register_external_tools()
    logger.info(f"All tools (incl. external): {ToolRegistry.list_all()}")
