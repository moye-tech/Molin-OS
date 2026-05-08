"""
墨麟AI智能系统 v6.6 — 知识提取器

从成功任务中提取知识卡片，存入长期记忆。
灵感来源：Claude Code `src/services/extractMemories/`。

Source: core/evolution/knowledge_extractor.py (from molin-os-ultra)
Adapted for Hermes OS: loguru→logging only.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class KnowledgeExtractor:
    """知识提取器"""

    async def extract(self, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从成功任务提取知识卡片"""
        cards = []

        # 1. 提取任务模式
        pattern_card = self._extract_pattern(task_result)
        if pattern_card:
            cards.append(pattern_card)

        # 2. 提取工具使用经验
        tool_card = self._extract_tool_experience(task_result)
        if tool_card:
            cards.append(tool_card)

        # 3. 提取业务洞察
        insight_card = self._extract_business_insight(task_result)
        if insight_card:
            cards.append(insight_card)

        logger.info(f"Extracted {len(cards)} knowledge cards from success task")
        return cards

    async def extract_partial(self, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从部分成功任务提取待验证知识"""
        cards = await self.extract(task_result)
        for card in cards:
            card["verified"] = False
            card["status"] = "pending_verification"
        return cards

    def _extract_pattern(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取任务模式"""
        task_type = task_result.get("task_type", "")
        agency = task_result.get("agency", "")
        output = task_result.get("output", "")

        if not output:
            return {}

        return {
            "type": "task_pattern",
            "task_type": task_type,
            "agency": agency,
            "pattern": output[:500],
            "score": task_result.get("score", 0),
            "timestamp": time.time(),
        }

    def _extract_tool_experience(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取工具使用经验"""
        metadata = task_result.get("metadata", {})
        tools_used = metadata.get("tools_used", [])
        worker_id = metadata.get("worker_id", "")

        if not tools_used:
            return {}

        return {
            "type": "tool_experience",
            "tools": tools_used,
            "worker": worker_id,
            "success": task_result.get("status") == "success",
            "tips": metadata.get("tips", ""),
            "timestamp": time.time(),
        }

    def _extract_business_insight(self, task_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取业务洞察"""
        output = task_result.get("output", "")
        task_type = task_result.get("task_type", "")

        if not output:
            return {}

        return {
            "type": "business_insight",
            "domain": task_type,
            "insight": output[:800],
            "confidence": min(task_result.get("score", 5) / 10.0, 1.0),
            "timestamp": time.time(),
        }
