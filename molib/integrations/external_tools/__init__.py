"""
External Tools Registry
集中注册所有外部工具，供 ExternalToolManager 统一调度。
"""
from .cli_hub import get_cli_hub
from .social_hub import get_social_hub
from .web_browser import get_web_browser
from .market_radar import get_market_radar
from .vision_engine import get_vision_engine
from .agent_skills import get_agent_skills
from .video_tool import get_video_tool
from .claw_code_tool import get_claw_code_tool
from .trading_tool import get_trading_tool
from .pm_skills import get_pm_skills

__all__ = [
    "get_cli_hub",
    "get_social_hub",
    "get_web_browser",
    "get_market_radar",
    "get_vision_engine",
    "get_agent_skills",
    "get_video_tool",
    "get_claw_code_tool",
    "get_trading_tool",
    "get_pm_skills",
]
