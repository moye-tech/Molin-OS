"""
SOP 反馈管道 — 任务执行结果自动反哺 SOP 和知识库
作为 CEO/Manager 层的 post_task_hook 运行。

适配自 molin-os-ultra v6.6.0 sop/sop_feedback.py
适配: loguru → logging, 无 infra.memory.sqlite_client 依赖, 降级为内存存储
"""
from __future__ import annotations

import time
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class SOPFeedbackPipeline:
    """执行结果 → SOP/知识库 的自动反馈管道"""

    SCORE_THRESHOLD = 7.0
    DEVIATION_THRESHOLD = 0.3
    ALERT_THRESHOLD = 5

    def __init__(self):
        self.feedback_log: List[Dict[str, Any]] = []
        self.metrics = {
            "tasks_evaluated": 0,
            "knowledge_extracted": 0,
            "sop_updates_proposed": 0,
        }
        self.failure_counts: Dict[str, int] = {}
        self._knowledge_store: Dict[str, Dict[str, Any]] = {}  # 内存知识库

    async def post_task_hook(
        self,
        task_result: Dict[str, Any],
        task_meta: Dict[str, Any],
    ):
        """CEO/Manager 层任务完成后的自动反馈钩子"""
        self.metrics["tasks_evaluated"] += 1

        score = self._extract_score(task_result)
        if score is None:
            return

        feedback_entry: Dict[str, Any] = {
            "timestamp": time.time(),
            "task_type": task_meta.get("task_type", "unknown"),
            "score": score,
            "actions": [],
        }

        # 高分任务：提炼知识卡片
        if score >= self.SCORE_THRESHOLD:
            knowledge_card = await self._extract_knowledge(
                task_result, task_meta
            )
            if knowledge_card:
                self.metrics["knowledge_extracted"] += 1
                feedback_entry["actions"].append("knowledge_extracted")
                feedback_entry["knowledge_card_id"] = knowledge_card.get(
                    "id"
                )

            # 如果是 SOP 覆盖的任务，检查执行偏差
            sop_id = task_meta.get("sop_id")
            if sop_id:
                deviation = await self._compare_with_sop(
                    task_result, task_meta, sop_id
                )
                feedback_entry["sop_deviation"] = deviation

                if deviation > self.DEVIATION_THRESHOLD:
                    proposal = await self._propose_sop_update(
                        task_result, task_meta, sop_id, deviation
                    )
                    if proposal:
                        self.metrics["sop_updates_proposed"] += 1
                        feedback_entry["actions"].append(
                            "sop_update_proposed"
                        )
                        feedback_entry["sop_proposal"] = proposal

        self.feedback_log.append(feedback_entry)
        logger.info(
            f"[SOPFeedback] task={task_meta.get('task_type')} "
            f"score={score:.1f} actions={feedback_entry['actions']}"
        )

    def _extract_score(
        self, task_result: Dict[str, Any]
    ) -> Optional[float]:
        """从任务结果中提取评分"""
        score = task_result.get("score")
        if isinstance(score, dict):
            return float(score.get("composite", 0.0))
        if isinstance(score, (int, float)):
            return float(score)

        exec_result = task_result.get("execution_result", {})
        if isinstance(exec_result, dict):
            agg = exec_result.get("aggregated_output", {})
            success_rate = agg.get("success_rate", 0)
            if success_rate > 0:
                return success_rate * 10.0

        return None

    async def _extract_knowledge(
        self,
        task_result: Dict[str, Any],
        task_meta: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """从高分任务中提炼知识卡片"""
        score = self._extract_score(task_result) or 0
        knowledge_card = {
            "id": f"KC-{int(time.time())}",
            "source_task_type": task_meta.get("task_type", "unknown"),
            "score": score,
            "situation": (task_meta.get("description", "") or "")[:200],
            "core_insight": "",
            "created_at": time.time(),
            "confidence": "high" if score >= 8.0 else "medium",
        }

        exec_result = task_result.get("execution_result", {})
        if isinstance(exec_result, dict):
            agg = exec_result.get("aggregated_output", {})
            knowledge_card["core_insight"] = (
                agg.get("summary", "") or ""
            )[:300]

        # 内存存储
        self._knowledge_store[knowledge_card["id"]] = knowledge_card
        self._reset_failure_count(knowledge_card["id"])
        logger.info(
            f"[SOPFeedback] 知识卡片已沉淀: {knowledge_card['id']}"
        )
        return knowledge_card

    def _reset_failure_count(self, key: str) -> None:
        self.failure_counts.pop(key, None)

    async def _compare_with_sop(
        self,
        task_result: Dict[str, Any],
        task_meta: Dict[str, Any],
        sop_id: str,
    ) -> float:
        """对比任务执行结果与 SOP 定义，计算偏差度"""
        try:
            from molib.sop.engine import get_sop_engine

            engine = get_sop_engine()
            sop_def = engine.get_definition(sop_id)
            if not sop_def:
                return 0.0

            expected_steps = len(sop_def.get("steps", []))
            actual_steps = len(task_result.get("steps_history", []))

            step_deviation = abs(expected_steps - actual_steps) / max(
                expected_steps, 1
            )

            exec_result = task_result.get("execution_result", {})
            if isinstance(exec_result, dict):
                agg = exec_result.get("aggregated_output", {})
                success_rate = agg.get("success_rate", 1.0)
                quality_deviation = 1.0 - success_rate
            else:
                quality_deviation = 0.0

            return (step_deviation + quality_deviation) / 2.0

        except ImportError:
            return 0.0
        except Exception:
            return 0.0

    async def _propose_sop_update(
        self,
        task_result: Dict[str, Any],
        task_meta: Dict[str, Any],
        sop_id: str,
        deviation: float,
    ) -> Optional[Dict[str, Any]]:
        """提议 SOP 更新"""
        proposal = {
            "sop_id": sop_id,
            "proposed_at": time.time(),
            "deviation": deviation,
            "task_type": task_meta.get("task_type"),
            "suggestion": f"SOP '{sop_id}' 执行偏差 {deviation:.1%}，建议审查并更新",
            "status": "pending_review",
        }
        logger.info(
            f"[SOPFeedback] SOP 更新提议: {sop_id} (偏差 {deviation:.1%})"
        )
        return proposal

    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "feedback_log_size": len(self.feedback_log),
            "knowledge_store_size": len(self._knowledge_store),
        }


# 全局单例
_feedback_instance: Optional[SOPFeedbackPipeline] = None


def get_sop_feedback() -> SOPFeedbackPipeline:
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = SOPFeedbackPipeline()
    return _feedback_instance
