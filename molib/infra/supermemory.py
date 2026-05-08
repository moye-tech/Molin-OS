"""
Supermemory 记忆引擎 — Hermes OS 集成层
基于 supermemory.ai 云 API，提供无限容量的持久化记忆。
替代 Hermes memory 工具的静态注入模式，实现按需检索。

用法:
    from molib.infra.supermemory import save_memory, recall_memory, SupermemoryClient

    # 保存记忆
    save_memory("SOP引擎已完成吸收，支持YAML定义流程", tags=["吸收记录", "SOP"])

    # 检索记忆
    results = recall_memory("SOP引擎有哪些组件？")
"""
from __future__ import annotations

import os
import json
import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

API_BASE = "https://api.supermemory.ai/v3"
DEFAULT_API_KEY = "sm_pGfHeyP7gnUUSsjKZNcVsU_Se8B8eN1MzGhtDEENF1r3ob7mgQfFROxkmSV6K9moIUm0IdVHsDS2MALwXHTIAYL"


class SupermemoryClient:
    """Supermemory API 客户端 — 云记忆存储"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get(
            "SUPERMEMORY_API_KEY", DEFAULT_API_KEY
        )
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def save(
        self,
        content: str,
        title: str = "",
        type_: str = "memory",
        tags: Optional[List[str]] = None,
        source: str = "",
    ) -> Optional[str]:
        """
        保存记忆到 supermemory 云。

        Args:
            content: 记忆内容（文本）
            title: 标题（可选）
            type_: 类型，默认 "memory"
            tags: 标签列表
            source: 来源标识（如 "session-20260506"）

        Returns:
            document_id 或 None
        """
        import httpx

        payload: Dict[str, Any] = {
            "content": content,
            "title": title,
            "type": type_,
        }
        if tags:
            payload["tags"] = tags
        if source:
            payload["source"] = source

        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    f"{API_BASE}/documents",
                    headers=self._headers,
                    json=payload,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    doc_id = data.get("id")
                    logger.info(
                        f"[Supermemory] 已保存: {title or content[:40]}... "
                        f"(id={doc_id})"
                    )
                    return doc_id
                else:
                    logger.warning(
                        f"[Supermemory] 保存失败: {resp.status_code} {resp.text[:200]}"
                    )
                    return None
        except Exception as e:
            logger.warning(f"[Supermemory] 保存异常: {e}")
            return None

    def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        语义搜索记忆。

        Args:
            query: 搜索查询
            limit: 最大返回数
            threshold: 相关性阈值 (0-1)

        Returns:
            记忆结果列表，每项含 content, score, title, documentId, createdAt
        """
        import httpx

        try:
            with httpx.Client(timeout=15) as client:
                resp = client.post(
                    f"{API_BASE}/search",
                    headers=self._headers,
                    json={"q": query, "limit": limit},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    logger.info(
                        f"[Supermemory] 搜索 '{query}': "
                        f"找到 {len(results)} 条 (用时 {data.get('timing', '?')}ms)"
                    )
                    return results
                else:
                    logger.warning(
                        f"[Supermemory] 搜索失败: {resp.status_code} {resp.text[:200]}"
                    )
                    return []
        except Exception as e:
            logger.warning(f"[Supermemory] 搜索异常: {e}")
            return []

    def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取单个文档详情"""
        import httpx

        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"{API_BASE}/documents/{document_id}",
                    headers=self._headers,
                )
                if resp.status_code == 200:
                    return resp.json()
                return None
        except Exception:
            return None

    def delete(self, document_id: str) -> bool:
        """删除文档"""
        import httpx

        try:
            with httpx.Client(timeout=15) as client:
                resp = client.delete(
                    f"{API_BASE}/documents/{document_id}",
                    headers=self._headers,
                )
                return resp.status_code in (200, 204)
        except Exception:
            return False


# 单例
_client: Optional[SupermemoryClient] = None


def get_client() -> SupermemoryClient:
    global _client
    if _client is None:
        _client = SupermemoryClient()
    return _client


def save_memory(
    content: str,
    title: str = "",
    tags: Optional[List[str]] = None,
    source: str = "",
) -> Optional[str]:
    """快速保存记忆"""
    return get_client().save(content, title=title, tags=tags, source=source)


def recall_memory(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """快速检索记忆"""
    return get_client().search(query, limit=limit)
