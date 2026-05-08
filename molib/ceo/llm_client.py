"""
墨麟OS — LLM Client 包装器（统一代理层）
=========================================
已统一为 shared/ai/llm_client.py 的代理层。
所有 CEO 层调用自动路由到共享层的 LLMClient（含 BudgetGuard, fallback, 成本记录）。

模型路由规则：
- 复杂任务（推理/分析/评估）→ deepseek-v4-pro (deepseek-chat)
- 简单任务（分类/摘要/翻译）→ deepseek-v4-flash (deepseek-chat)
- 深度推理（复杂代码/长文档）→ deepseek-reasoner
- 视频/图片 → 百炼 qwen-vl-plus / qwen-image-2.0-pro

API Key 来源：~/.hermes/.env (DEEPSEEK_API_KEY) / ~/.hermes/config.yaml (providers)
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
    # 百炼模型
    "qwen-vl-plus": "qwen-vl-plus",
    "qwen-image": "qwen-image-2.0-pro",
    "qwen-plus": "qwen-plus",
}

SUPPORTED_MODELS = list(MODEL_MAP.keys())

# 模型层级（任务难度 → 自动选择）
MODEL_TIERS = {
    "flash": "deepseek-v4-flash",     # 简单：分类、摘要、翻译
    "pro": "deepseek-v4-pro",         # 标准：分析、评估、生成
    "reasoner": "deepseek-reasoner",  # 深度：复杂推理、长文档
    "vision": "qwen-vl-plus",         # 视觉：图片分析
    "image": "qwen-image",            # 生图：文生图
    "default": "deepseek-v4-flash",   # 默认兜底
}


def get_model_for_task(task_type: str = "default") -> str:
    """根据任务类型自动选择合适的模型层级"""
    return MODEL_TIERS.get(task_type, MODEL_TIERS["default"])


def get_upgrade_chain() -> list[str]:
    """降级链路：pro → flash（从不更贵的降级到更便宜的）"""
    return [
        "deepseek-v4-pro",
        "deepseek-v4-flash",
    ]


def _load_api_key() -> str:
    """加载 DeepSeek API Key"""
    # 优先从环境变量读取
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key
    # 从 .env 文件读取
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    logger.warning("⚠️ DEEPSEEK_API_KEY 未配置")
    return ""


class LLMClient:
    """CEO 层 LLM 客户端 — 统一代理到 shared/ai/llm_client.py
    
    提供与旧版本兼容的接口，内部路由到共享层的 LLMClient。
    """
    
    def __init__(self, provider: str = "deepseek", config: Optional[dict] = None):
        self._shared_client = None
        self._provider = provider
        self._config = config or {}
        self._api_key = _load_api_key()
        self._last_model = None
    
    def _get_shared(self):
        """懒加载共享层 LLMClient"""
        if self._shared_client is None:
            try:
                from molib.shared.ai.llm_client import LLMClient as SharedLLMClient
                self._shared_client = SharedLLMClient(
                    provider=self._provider,
                    config=self._config,
                )
            except ImportError:
                logger.warning("shared/ai/llm_client 不可用，使用内置 fallback")
                self._shared_client = None
        return self._shared_client
    
    async def chat(self, messages: list[dict], model: Optional[str] = None) -> str:
        """同步 chat 兼容方法 — 内部转异步调用"""
        return await self._do_chat(messages, model)
    
    async def _do_chat(self, messages: list[dict], model: Optional[str] = None) -> str:
        """核心 LLM 调用"""
        if not model:
            model = MODEL_TIERS["default"]
        
        actual_model = MODEL_MAP.get(model, model)
        self._last_model = actual_model
        
        logger.info("[LLM] 请求: model=%s -> %s", model, actual_model)
        
        # 尝试共享层
        shared = self._get_shared()
        if shared:
            try:
                result = shared.chat(messages, model=actual_model)
                return result
            except Exception as e:
                logger.warning("[LLM] 共享层调用失败: %s, 回退内置调用", e)
        
        # 内置 fallback：直接 HTTP 调用
        import httpx
        
        api_key = self._api_key
        if not api_key:
            return "【错误】DEEPSEEK_API_KEY 未配置"
        
        base_url = self._config.get("base_url", "https://api.deepseek.com/v1")
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": actual_model,
                        "messages": messages,
                        "temperature": 0.3,
                        "max_tokens": 4096,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                logger.info("[LLM] ✅ 请求成功: model=%s tokens=%s",
                           actual_model, data.get("usage", {}))
                return content
        except Exception as e:
            logger.error("[LLM] ❌ 请求失败: %s", e, exc_info=True)
            return f"【LLM错误】{e}"
    
    async def chat_with_fallback(
        self, messages: list[dict], preferred_model: str = None
    ) -> str:
        """带降级链的调用：pro → flash"""
        if not preferred_model:
            preferred_model = MODEL_TIERS["pro"]
        
        chain = [preferred_model]
        if preferred_model != MODEL_TIERS["flash"]:
            chain.append(MODEL_TIERS["flash"])
        
        for model in chain:
            result = await self._do_chat(messages, model)
            if result and not result.startswith("【LLM错误】"):
                return result
        
        return "【LLM错误】所有模型调用失败"
    
    # ── 批量调用 ──────────────────────────────────────────────────
    
    async def batch_chat(self, prompts: list[list[dict]], model: Optional[str] = None) -> list[str]:
        """批量并行调用"""
        import asyncio
        tasks = [self._do_chat(p, model) for p in prompts]
        return await asyncio.gather(*tasks)
    
    # ── 成本估算 ──────────────────────────────────────────────────
    
    @staticmethod
    def estimate_cost(model: str, prompt_tokens: int = 0, completion_tokens: int = 0) -> float:
        """估算调用成本（元）"""
        rates = {
            "deepseek-chat": (1.0, 2.0),         # 输入/输出 ¥/M token
            "deepseek-reasoner": (4.0, 16.0),
            "qwen-vl-plus": (0.003, 0.003),      # ¥/1K image
            "qwen-image-2.0-pro": (0.14, 0.14),  # ¥/张
        }
        in_rate, out_rate = rates.get(model, (1.0, 2.0))
        return (prompt_tokens * in_rate + completion_tokens * out_rate) / 1_000_000
    
    @property
    def last_model(self) -> str:
        return self._last_model or "?"


# ── 兼容导出 ──────────────────────────────────────────────────────
# 提供与旧版相同的顶层函数，用于向后兼容
async def chat(messages, model=None):
    client = LLMClient()
    return await client.chat(messages, model)


async def chat_with_fallback(messages, preferred_model=None):
    client = LLMClient()
    return await client.chat_with_fallback(messages, preferred_model)


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
    return await client.chat(messages, model=model)


async def deep_chat(prompt: str, system: str = "") -> str:
    """复杂推理任务"""
    return await simple_chat(prompt, system, model="deepseek-v4-pro")


async def vision_chat(prompt: str, image_url: str) -> str:
    """图片分析任务（百炼 qwen-vl-plus）"""
    client = create_client()
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ]
    return await client.chat(messages, model="qwen-vl-plus")

