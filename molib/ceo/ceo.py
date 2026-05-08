"""
Hermes OS — CEO 决策核心
========================
【弃用】此文件依赖 ceo_reasoning.py（已废弃标记）。
保留此文件作为兼容层，但内部直接使用 IntentRouter 四层路由。

ceo_reasoning.py 已标记为 DEPRECATED — 多轮对话LLM推理已被
IntentRouter 的四层架构替代。

除非需要 ceo_reasoning 的对话session管理功能，否则应该直接使用：
    from molib.ceo.intent_router import IntentRouter, IntentResult
"""

import os
import tomllib
from pathlib import Path
from typing import Optional

from .intent_router import IntentRouter, SUBSIDIARY_PROFILES

HERMES_ROOT = Path(os.path.expanduser("~/.hermes"))


class CEO:
    """
    CEO 决策核心 — 基于 IntentRouter 四层路由。

    使用示例：
        ceo = CEO()
        result = await ceo.analyze("帮我写一篇小红书文案")
        # result is IntentResult with intent_type, target_vps, target_subsidiaries, etc.
    """

    def __init__(self):
        self.company_config = self._load_config()
        self._router = IntentRouter()

    def _load_config(self):
        """加载 company.toml 作为唯一配置源"""
        config_path = Path(os.getcwd()) / "config" / "company.toml"
        if not config_path.exists():
            config_path = HERMES_ROOT / "company.toml"
        if config_path.exists():
            with open(config_path, "rb") as f:
                return tomllib.load(f)
        return {"company": []}

    def inject_llm_client(self, llm_client):
        """注入 LLM 客户端（用于 Layer 2 语义路由）"""
        self._router.set_llm_client(llm_client)

    async def analyze(self, user_input: str):
        """
        CEO 分析入口 — 委托 IntentRouter.analyze()。

        Args:
            user_input: 用户输入

        Returns:
            IntentResult
        """
        return await self._router.analyze(user_input)

    def list_capabilities(self) -> dict:
        """列出所有子公司能力（供展示/调试）"""
        return dict(SUBSIDIARY_PROFILES)
