"""
墨麟OS v2.5 — 双层记忆系统 (MemoryLayer)

GAP-01 补强：在 ExperienceVault（任务级经验）之上，新增 mem0 用户级长期记忆。

架构：
  ┌─────────────────────────────────────────┐
  │         会话开始                          │
  │  mem0.search(user_id) → 用户画像/偏好     │
  │  ExperienceVault.recall(task_type) → 任务经验 │
  └──────────────┬──────────────────────────┘
                 ↓
  ┌─────────────────────────────────────────┐
  │         Worker 执行                       │
  │  使用两重记忆上下文增强任务执行             │
  └──────────────┬──────────────────────────┘
                 ↓
  ┌─────────────────────────────────────────┐
  │         会话结束                          │
  │  mem0.add(新事实) → 用户级记忆持久化       │
  │  ExperienceVault.store(执行模式) → 任务经验  │
  └─────────────────────────────────────────┘

用法:
    from molib.shared.memory_layer import MemoryLayer

    memory = MemoryLayer(user_id="moye")
    context = await memory.recall("content_creation")  # 召回所有相关记忆
    await memory.remember("用户偏好小红书写实风格")     # 持久化新事实
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MemoryLayer:
    """
    双层记忆系统：mem0（用户级）+ ExperienceVault（任务级）。

    特性：
    - 自动检测 mem0 可用性，不可用时降级到纯 ExperienceVault
    - 记忆冲突自动合并（mem0 的 self-edit 特性）
    - 支持语义搜索 + 关键词搜索双模式
    """

    def __init__(
        self,
        user_id: str = "moye",
        use_mem0: bool = True,
        mem0_config: Optional[Dict] = None,
    ):
        self.user_id = user_id
        self._mem0_client = None
        self._mem0_available = False

        if use_mem0:
            self._init_mem0(mem0_config)

    def _init_mem0(self, config: Optional[Dict] = None):
        """延迟初始化 mem0 客户端，使用 DeepSeek/OpenRouter 作为 embedding provider"""
        try:
            from mem0 import Memory
            import os

            # 自动探测可用的 embedding provider
            deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
            openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

            if deepseek_key:
                # 使用 DeepSeek 兼容 OpenAI API 做 embedding
                cfg = config or {
                    "embedder": {
                        "provider": "openai",
                        "config": {
                            "api_key": deepseek_key,
                            "model": "deepseek-chat",  # DeepSeek 兼容接口
                            "embedding_dims": 1536,
                        },
                    },
                    "llm": {
                        "provider": "openai",
                        "config": {
                            "api_key": deepseek_key,
                            "model": "deepseek-chat",
                        },
                    },
                    "history_db_path": os.path.expanduser("~/.hermes/memory/mem0_history.db"),
                }
                logger.info("✅ mem0 使用 DeepSeek API 作为 embedding provider")
            elif openrouter_key:
                cfg = config or {
                    "embedder": {
                        "provider": "openai",
                        "config": {
                            "api_key": openrouter_key,
                            "model": "openai/text-embedding-3-small",
                            "api_base": "https://openrouter.ai/api/v1",
                        },
                    },
                    "llm": {
                        "provider": "openai",
                        "config": {
                            "api_key": openrouter_key,
                            "model": "openai/gpt-4o-mini",
                            "api_base": "https://openrouter.ai/api/v1",
                        },
                    },
                    "history_db_path": os.path.expanduser("~/.hermes/memory/mem0_history.db"),
                }
                logger.info("✅ mem0 使用 OpenRouter API 作为 embedding provider")
            else:
                cfg = config or {
                    "history_db_path": os.path.expanduser("~/.hermes/memory/mem0_history.db"),
                }

            self._mem0_client = Memory.from_config(cfg)
            self._mem0_available = True
            logger.info(f"✅ mem0 用户记忆层已激活 (user={self.user_id})")
        except ImportError:
            logger.warning("⚠️ mem0ai 未安装，降级到纯 ExperienceVault 模式")
            self._mem0_available = False
        except Exception as e:
            logger.warning(f"⚠️ mem0 初始化失败: {e}，降级到纯 ExperienceVault 模式")
            self._mem0_available = False

    async def recall(
        self,
        task_type: str = "",
        query: str = "",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        召回所有相关记忆（双层）。

        Args:
            task_type: 任务类型（用于匹配任务级经验）
            query: 语义搜索查询（可选）
            limit: 最大返回条目数

        Returns:
            {
                "user_memories": [...],      # mem0 用户级记忆
                "task_experiences": [...],   # ExperienceVault 任务级经验
                "combined_context": "..."    # 合并后的上下文文本
            }
        """
        result = {
            "user_memories": [],
            "task_experiences": [],
            "combined_context": "",
        }

        # 第一层：mem0 用户级记忆
        if self._mem0_available and self._mem0_client:
            try:
                search_query = query or task_type or f"用户 {self.user_id} 的偏好和背景"
                memories = self._mem0_client.search(
                    search_query,
                    user_id=self.user_id,
                    limit=limit,
                )
                result["user_memories"] = [
                    {"memory": m.get("memory", ""), "metadata": m.get("metadata", {})}
                    for m in (memories or [])
                ]
            except Exception as e:
                logger.warning(f"mem0 recall 失败: {e}")

        # 第二层：ExperienceVault 任务级经验
        try:
            from molib.shared.experience.vault import ExperienceVault
            vault = ExperienceVault()
            experiences = await vault.recall(task_type=task_type, limit=limit)
            result["task_experiences"] = experiences or []
        except ImportError:
            logger.debug("ExperienceVault 不可用")
        except Exception as e:
            logger.warning(f"ExperienceVault recall 失败: {e}")

        # 合并为上下文文本
        context_parts = []
        if result["user_memories"]:
            context_parts.append("📌 用户长期记忆:")
            for m in result["user_memories"]:
                context_parts.append(f"  • {m['memory']}")
        if result["task_experiences"]:
            context_parts.append("📋 历史任务经验:")
            for e in result["task_experiences"]:
                if isinstance(e, dict):
                    context_parts.append(f"  • {e.get('summary', str(e)[:200])}")
                else:
                    context_parts.append(f"  • {str(e)[:200]}")

        result["combined_context"] = "\n".join(context_parts)
        return result

    async def remember(
        self,
        content: str,
        memory_type: str = "user_fact",
        metadata: Optional[Dict] = None,
    ):
        """
        持久化新记忆。

        Args:
            content: 记忆内容
            memory_type: "user_fact"(用户事实) / "user_preference"(偏好) / "task_lesson"(任务教训)
            metadata: 附加元数据
        """
        meta = metadata or {}
        meta["memory_type"] = memory_type
        meta["source"] = "molin_memory_layer"

        # mem0 用户级
        if self._mem0_available and self._mem0_client:
            try:
                self._mem0_client.add(
                    content,
                    user_id=self.user_id,
                    metadata=meta,
                )
                logger.debug(f"✅ mem0 记忆已保存: {content[:80]}...")
            except Exception as e:
                logger.warning(f"mem0 add 失败: {e}")

        # ExperienceVault 任务级（仅任务教训类）
        if memory_type == "task_lesson":
            try:
                from molib.shared.experience.vault import ExperienceVault
                vault = ExperienceVault()
                await vault.store({
                    "summary": content,
                    "type": memory_type,
                    "metadata": meta,
                })
            except Exception as e:
                logger.warning(f"ExperienceVault store 失败: {e}")

    async def get_user_profile(self) -> Dict[str, Any]:
        """
        获取用户完整画像（从 mem0 聚合）。

        Returns:
            {
                "preferences": [...],
                "facts": [...],
                "recent_topics": [...],
            }
        """
        if not self._mem0_available or not self._mem0_client:
            return {"preferences": [], "facts": [], "recent_topics": []}

        try:
            # 获取全部用户记忆
            all_memories = self._mem0_client.get_all(user_id=self.user_id) or []

            preferences = []
            facts = []
            recent_topics = []

            for m in all_memories:
                memory_text = m.get("memory", "") if isinstance(m, dict) else str(m)
                meta = m.get("metadata", {}) if isinstance(m, dict) else {}
                mem_type = meta.get("memory_type", "user_fact")

                if mem_type == "user_preference":
                    preferences.append(memory_text)
                elif mem_type == "user_fact":
                    facts.append(memory_text)
                else:
                    recent_topics.append(memory_text)

            return {
                "preferences": preferences[-20:],
                "facts": facts[-20:],
                "recent_topics": recent_topics[-10:],
            }
        except Exception as e:
            logger.warning(f"mem0 get_user_profile 失败: {e}")
            return {"preferences": [], "facts": [], "recent_topics": []}

    @property
    def mem0_available(self) -> bool:
        return self._mem0_available

    @property
    def status(self) -> Dict[str, Any]:
        """系统健康状态"""
        return {
            "user_id": self.user_id,
            "mem0_available": self._mem0_available,
            "experience_vault_available": self._check_experience_vault(),
            "mode": "双层记忆 (mem0 + ExperienceVault)" if self._mem0_available else "单层 (仅 ExperienceVault)",
        }

    def _check_experience_vault(self) -> bool:
        try:
            from molib.shared.experience.vault import ExperienceVault
            return True
        except ImportError:
            return False


# ── 全局单例 ──

_default_memory: Optional[MemoryLayer] = None


def get_memory_layer(user_id: str = "moye") -> MemoryLayer:
    """获取全局 MemoryLayer 单例"""
    global _default_memory
    if _default_memory is None:
        _default_memory = MemoryLayer(user_id=user_id)
    return _default_memory
