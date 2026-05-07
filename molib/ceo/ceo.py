"""
Hermes OS — CEO 决策核心
基于 LLM 推理的多轮对话引擎，废弃关键词兜底。

用户 → CEO（LLM推理） → clarify（追问细节）→ 用户回复 → CEO（再用LLM推理）
                       → dispatch（确定子公司+交付物规格）→ 执行
                       → chat（纯聊天无需调度）
"""

import os
import tomllib
from pathlib import Path
from typing import Optional

from .ceo_reasoning import (
    CEOReasoningSession, CEOAction, SUBSIDIARY_CAPABILITIES,
    get_or_create_session,
)

HERMES_ROOT = Path(os.path.expanduser("~/.hermes"))


class CEO:
    """
    CEO 决策核心 — 基于 LLM 推理的多轮对话。

    使用示例：
        ceo = CEO()
        ceo.inject_llm_client(llm_client)
        action = await ceo.reason("帮我做个东西")
        # action.action_type == "clarify"  → 追问用户
        # action.action_type == "dispatch" → 确定子公司
    """

    def __init__(self):
        self.company_config = self._load_config()

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
        """注入 LLM 客户端"""
        self._llm = llm_client

    async def reason(self, user_input: str, session: CEOReasoningSession = None) -> CEOAction:
        """
        CEO 多轮推理入口。

        Args:
            user_input: 用户输入
            session: 已有会话（多轮对话用），None 则自动创建

        Returns:
            CEOAction — clarify/dispatch/chat/refuse
        """
        if session is None:
            session = get_or_create_session(llm_client=self._llm)
        else:
            session.set_llm_client(self._llm)

        return await session.reason(user_input)

    def get_session(self, session_id: str) -> Optional[CEOReasoningSession]:
        """获取已有会话"""
        return get_or_create_session(session_id, self._llm)

    def list_capabilities(self) -> dict:
        """列出所有子公司能力（供展示/调试）"""
        return dict(SUBSIDIARY_CAPABILITIES)
