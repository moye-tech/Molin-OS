"""
SOP 自动优化器（Feature 5）
每日分析各子公司失败率，对失败率 >30% 的子公司触发 SOP 重新生成

适配自 molin-os-ultra v6.6.0 sop/sop_optimizer.py
适配: loguru → logging, 无 infra.memory.sqlite_client 依赖, 降级为统计文件
"""
from __future__ import annotations

import os
import json
import time
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)

SOP_DIR = Path(__file__).parent / "definitions"
SOP_DIR.mkdir(exist_ok=True)


class SOPOptimizer:
    """SOP 自动优化器 — 分析失败率 + LLM重新生成SOP"""

    FAILURE_THRESHOLD = 0.3  # 失败率超过 30% 触发优化

    def __init__(self):
        self._knowledge_store: Dict[str, Dict[str, Any]] = {}  # 内存统计存储

    async def analyze_sop_performance(self) -> Dict[str, Any]:
        """分析各子公司/任务类型的 SOP 表现"""
        if not self._knowledge_store:
            return {
                "total_evaluated": 0,
                "outcomes": {},
                "failure_rate": 0.0,
                "needs_optimization": False,
            }

        outcomes: Dict[str, int] = {}
        for _kid, card in self._knowledge_store.items():
            outcome = card.get("outcome", "unknown")
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

        total = sum(outcomes.values())
        failures = outcomes.get("failure", 0)
        failure_rate = failures / max(1, total)

        return {
            "total_evaluated": total,
            "outcomes": outcomes,
            "failure_rate": round(failure_rate, 3),
            "needs_optimization": failure_rate > self.FAILURE_THRESHOLD,
        }

    def _add_knowledge(self, task_type: str, outcome: str):
        """向内存知识库添加一条记录"""
        card_id = f"{task_type}_{int(time.time())}_{hash(task_type) % 10000}"
        self._knowledge_store[card_id] = {
            "source_task": task_type,
            "outcome": outcome,
            "created_at": time.time(),
        }

    async def identify_underperforming_sops(self) -> List[str]:
        """识别需要优化的子公司 SOP（从内存统计中找出失败最多的任务类型）"""
        failure_counts: Dict[str, int] = {}
        for _kid, card in self._knowledge_store.items():
            if card.get("outcome") in ("failure", "partial"):
                task = card.get("source_task", "unknown")
                failure_counts[task] = failure_counts.get(task, 0) + 1

        sorted_tasks = sorted(
            failure_counts.items(), key=lambda x: -x[1]
        )
        return [t for t, _c in sorted_tasks[:5]]

    async def regenerate_sop(
        self, subsidiary_id: str, failure_patterns: List[str]
    ) -> str:
        """LLM 重新生成 SOP（降级为生成模板）"""
        lines = [
            f"# SOP: {subsidiary_id} (自动生成)",
            f"# 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"# 失败模式: {', '.join(failure_patterns[:5])}",
            "",
            "id: " + subsidiary_id.replace(" ", "_").lower(),
            "name: " + subsidiary_id,
            "version: \"1.0\"",
            "enabled: true",
            "steps:",
        ]
        return "\n".join(lines)

    async def apply_sop_update(
        self, subsidiary_id: str, new_sop_content: str
    ) -> bool:
        """将新 SOP 写入文件"""
        try:
            safe_name = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in subsidiary_id
            )
            file_path = SOP_DIR / f"{safe_name}.yaml"
            file_path.write_text(new_sop_content, encoding="utf-8")
            logger.info(f"SOP 已更新: {file_path}")
            return True
        except Exception as e:
            logger.error(f"SOP 写入失败: {e}")
            return False

    async def run_daily_optimization(self) -> Dict[str, Any]:
        """每日 SOP 优化主流程"""
        logger.info("=== 开始每日 SOP 自动优化 ===")
        result: Dict[str, Any] = {"status": "started", "actions": []}

        perf = await self.analyze_sop_performance()
        result["performance"] = perf

        if perf.get("needs_optimization"):
            underperforming = await self.identify_underperforming_sops()
            result["underperforming"] = underperforming

            for task in underperforming:
                new_sop = await self.regenerate_sop(
                    task, [f"Failure pattern: {task}"]
                )
                if new_sop:
                    applied = await self.apply_sop_update(task, new_sop)
                    result["actions"].append(
                        {"task": task, "applied": applied}
                    )
        else:
            logger.info("SOP 性能正常，无需优化")
            result["actions"] = ["no_optimization_needed"]

        return result
