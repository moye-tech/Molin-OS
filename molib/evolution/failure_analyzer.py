"""
墨麟AI智能系统 v6.6 — 失败分析器

分析失败任务，提取失败模式和改进建议。

Source: core/evolution/failure_analyzer.py (from molin-os-ultra)
Adapted for Hermes OS: loguru→logging only.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class FailureAnalyzer:
    """失败分析器"""

    async def analyze(self, task_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析失败原因，返回失败模式列表"""
        patterns = []

        error = task_result.get("error", "")
        status = task_result.get("status", "error")

        # 1. 错误类型分类
        error_type = self._classify_error(error)
        patterns.append({
            "error_type": error_type,
            "raw_error": error[:500],
            "task_type": task_result.get("task_type", ""),
            "timestamp": time.time(),
        })

        # 2. 工具可用性检查
        metadata = task_result.get("metadata", {})
        tools_used = metadata.get("tools_used", [])
        for tool in tools_used:
            if self._is_tool_failure(tool, error):
                patterns.append({
                    "error_type": f"tool_failure:{tool}",
                    "detail": f"工具 {tool} 执行失败",
                    "timestamp": time.time(),
                })

        # 3. 任务复杂度分析
        task_desc = task_result.get("description", "")
        if len(task_desc) > 500:
            patterns.append({
                "error_type": "task_too_complex",
                "detail": "任务描述过长，可能需要进一步拆解",
                "description_length": len(task_desc),
                "timestamp": time.time(),
            })

        logger.info(f"Analyzed failure, found {len(patterns)} patterns")
        return patterns

    @staticmethod
    def _classify_error(error: str) -> str:
        """错误分类"""
        error_lower = error.lower()
        if "timeout" in error_lower or "timed out" in error_lower:
            return "timeout"
        elif "connection" in error_lower or "network" in error_lower:
            return "network_error"
        elif "permission" in error_lower or "denied" in error_lower:
            return "permission_error"
        elif "parse" in error_lower or "json" in error_lower or "decode" in error_lower:
            return "parse_error"
        elif "tool" in error_lower or "not found" in error_lower:
            return "tool_not_found"
        elif "memory" in error_lower:
            return "memory_error"
        else:
            return "unknown_error"

    @staticmethod
    def _is_tool_failure(tool_name: str, error: str) -> bool:
        """判断工具是否执行失败"""
        return tool_name.lower() in error.lower() or "error" in error.lower()
