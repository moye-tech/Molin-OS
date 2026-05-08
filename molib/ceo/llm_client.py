"""
墨域OS — LLM Client 包装器
============================
对接 DeepSeek API（直接 HTTP 调用），供 PhaseExecutor 和 QualityGate 使用。

从 ~/.hermes/.env 读取 DEEPSEEK_API_KEY，不需要额外配置。
支持 Flash / Pro / Reasoner 三种模型映射。
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger("molin.ceo.llm_client")

# ── 模型映射 ──────────────────────────────────────────────────────

MODEL_MAP = {
    "deepseek-v4-flash": "deepseek-chat",
    "deepseek-v4-pro": "deepseek-chat",
    "deepseek-reasoner": "deepseek-reasoner",
}

SUPPORTED_MODELS = list(MODEL_MAP.keys())


def _load_api_key() -> str:
    """
    从 ~/.hermes/.env 加载 DEEPSEEK_API_KEY。

    优先读取 env 文件而非环境变量，因为 Hermes 的 API key
    在 Python 进程内不可用（通过 RPC 传递）。
    """
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        content = env_path.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY"):
                # 处理 export DEEPSEEK_API_KEY="xxx" 和 DEEPSEEK_API_KEY=xxx 两种格式
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val

    # 回退到环境变量
    val = os.environ.get("DEEPSEEK_API_KEY", "")
    if val:
        return val

    logger.warning("DEEPSEEK_API_KEY 未找到，LLM调用将返回模拟结果")
    return ""


_API_KEY = _load_api_key()
_BASE_URL = "https://api.deepseek.com/v1"


class LLMClient:
    """
    LLM Client — 异步包装 DeepSeek API。

    用法:
        client = LLMClient()
        response = await client.chat([
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
        ], model="deepseek-v4-pro")
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or _API_KEY
        self.base_url = _BASE_URL
        self._httpx = None  # 懒加载 httpx

    def _get_httpx(self):
        """懒加载 httpx.AsyncClient"""
        if self._httpx is None:
            import httpx
            # 继承系统代理（mihomo 7890）
            proxy_url = os.environ.get("https_proxy") or os.environ.get("http_proxy") or ""
            client_kwargs = {
                "base_url": self.base_url,
                "timeout": 120.0,
                "headers": {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            }
            if proxy_url:
                client_kwargs["proxies"] = proxy_url
            self._httpx = httpx.AsyncClient(**client_kwargs)
        return self._httpx

    def _map_model(self, model: str) -> str:
        """将内部模型名称映射到 DeepSeek API 的模型名称"""
        mapped = MODEL_MAP.get(model)
        if mapped is None:
            logger.warning("未知模型 %s，使用默认 deepseek-chat", model)
            return "deepseek-chat"
        return mapped

    async def chat(
        self,
        messages: list[dict],
        model: str = "deepseek-v4-pro",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """
        调用 DeepSeek Chat Completions API。

        Args:
            messages: 消息列表 [{"role": "...", "content": "..."}, ...]
            model: 模型名称（支持 flash / pro / reasoner 映射）
            max_tokens: 最大输出 token
            temperature: 采样温度

        Returns:
            模型的文本回复。网络错误或 API 错误时返回错误说明。
        """
        if not self.api_key:
            # 无 API Key，返回模拟回复
            return "[LLMClient 模拟回复 — 未配置 DEEPSEEK_API_KEY]"

        api_model = self._map_model(model)

        # Reasoner 模型的特殊参数
        kwargs = {}
        if model == "deepseek-reasoner":
            kwargs["max_tokens"] = max_tokens * 2

        request_body = {
            "model": api_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }

        try:
            client = self._get_httpx()
            response = await client.post("/chat/completions", json=request_body)
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            logger.info(
                "LLM %s: %d tokens in / %d tokens out (prompt=%d+%d)",
                model,
                data["usage"]["prompt_tokens"],
                data["usage"]["completion_tokens"],
                0, 0,
            )
            return content

        except Exception as e:
            logger.error("LLM 调用失败 (%s): %s", model, e, exc_info=True)
            return f"[LLMClient 调用异常: {e}]"

    async def chat_with_fallback(
        self,
        messages: list[dict],
        models: list[str] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> tuple[str, str]:
        """
        带降级的多模型调用 — 从最好模型开始依次降级。

        Args:
            messages: 消息列表
            models: 模型优先级列表（默认 [reasoner, pro, flash]）
            max_tokens: 最大 token
            temperature: 采样温度

        Returns:
            (content, model_used)
        """
        if models is None:
            models = ["deepseek-reasoner", "deepseek-v4-pro", "deepseek-v4-flash"]

        last_error = ""
        for model in models:
            try:
                content = await self.chat(messages, model=model, max_tokens=max_tokens, temperature=temperature)
                if content and not content.startswith("[LLMClient"):
                    return content, model
                last_error = content
            except Exception as e:
                last_error = str(e)
                continue

        logger.warning("所有模型降级失败: %s", last_error)
        return last_error, "none"

    async def close(self):
        """关闭 HTTP 连接"""
        if self._httpx:
            await self._httpx.aclose()
            self._httpx = None

    def __del__(self):
        """析构时确保连接关闭（安全关闭，不产生警告）"""
        if self._httpx is not None:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
            except (RuntimeError, ImportError):
                pass


# ── 便捷函数 ──────────────────────────────────────────────────────


def create_client() -> LLMClient:
    """创建默认 LLMClient（使用环境配置的 API Key）"""
    return LLMClient()


async def simple_chat(prompt: str, system: str = "", model: str = "deepseek-v4-flash") -> str:
    """
    单次对话的便捷函数。

    用法:
        result = await simple_chat("写一篇小红书文案", system="你是一个文案专家")
    """
    client = create_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        return await client.chat(messages, model=model)
    finally:
        await client.close()
