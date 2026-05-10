"""
SOP 反馈管道 — 任务执行结果自动反哺 SOP 和知识库
作为 CEO/Manager 层的 post_task_hook 运行。
"""

import time
from typing import Dict, Any, Optional, List
from loguru import logger


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

    async def post_task_hook(self, task_result: Dict[str, Any], task_meta: Dict[str, Any]):
        """
        CEO/Manager 层任务完成后的自动反馈钩子。

        Args:
            task_result: 任务执行结果（含 score, output 等）
            task_meta: 任务元数据（含 task_type, sop_id 等）
        """
        self.metrics["tasks_evaluated"] += 1

        score = self._extract_score(task_result)
        if score is None:
            return

        feedback_entry = {
            "timestamp": time.time(),
            "task_type": task_meta.get("task_type", "unknown"),
            "score": score,
            "actions": [],
        }

        # 高分任务：提炼知识卡片
        if score >= self.SCORE_THRESHOLD:
            knowledge_card = await self._extract_knowledge(task_result, task_meta)
            if knowledge_card:
                self.metrics["knowledge_extracted"] += 1
                feedback_entry["actions"].append("knowledge_extracted")
                feedback_entry["knowledge_card_id"] = knowledge_card.get("id")

            # 如果是 SOP 覆盖的任务，检查执行偏差
            sop_id = task_meta.get("sop_id")
            if sop_id:
                deviation = await self._compare_with_sop(task_result, task_meta, sop_id)
                feedback_entry["sop_deviation"] = deviation

                if deviation > self.DEVIATION_THRESHOLD:
                    proposal = await self._propose_sop_update(task_result, task_meta, sop_id, deviation)
                    if proposal:
                        self.metrics["sop_updates_proposed"] += 1
                        feedback_entry["actions"].append("sop_update_proposed")
                        feedback_entry["sop_proposal"] = proposal

        self.feedback_log.append(feedback_entry)
        logger.info(
            f"[SOPFeedback] task={task_meta.get('task_type')} "
            f"score={score:.1f} actions={feedback_entry['actions']}"
        )

    def _extract_score(self, task_result: Dict[str, Any]) -> Optional[float]:
        """从任务结果中提取评分"""
        # 直接评分
        score = task_result.get("score")
        if isinstance(score, dict):
            return score.get("composite", 0.0)
        if isinstance(score, (int, float)):
            return float(score)

        # 从 execution_result 中提取
        exec_result = task_result.get("execution_result", {})
        if isinstance(exec_result, dict):
            agg = exec_result.get("aggregated_output", {})
            success_rate = agg.get("success_rate", 0)
            if success_rate > 0:
                return success_rate * 10.0

        return None

    async def _extract_knowledge(
        self, task_result: Dict[str, Any], task_meta: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """从高分任务中提炼知识卡片"""
        knowledge_card = {
            "id": f"KC-{int(time.time())}",
            "source_task_type": task_meta.get("task_type", "unknown"),
            "score": self._extract_score(task_result),
            "situation": task_meta.get("description", "")[:200],
            "core_insight": "",
            "created_at": time.time(),
            "confidence": "high" if (self._extract_score(task_result) or 0) >= 8.0 else "medium",
        }

        # 提取核心输出作为知识
        exec_result = task_result.get("execution_result", {})
        if isinstance(exec_result, dict):
            agg = exec_result.get("aggregated_output", {})
            knowledge_card["core_insight"] = agg.get("summary", "")[:300]

        # 存储到知识库（通过 MemoryManager，带重试和 SQLite 兜底）
        stored = await self._store_with_retry(knowledge_card["id"], knowledge_card)
        if stored:
            logger.info(f"[SOPFeedback] 知识卡片已沉淀: {knowledge_card['id']}")
        return knowledge_card

    async def _store_with_retry(self, key: str, data: Dict, max_retries: int = 3) -> bool:
        """带指数退避的重试存储，失败后写入 SQLite 待重试队列"""
        from infra.memory.memory_manager import get_memory_manager, MemoryScenario

        for attempt in range(max_retries):
            try:
                mm = await get_memory_manager()
                await mm.store(
                    key=key,
                    data=data,
                    scenario=MemoryScenario.LONG_TERM,
                    metadata={"type": "knowledge_card", "auto_extracted": True},
                )
                self._reset_failure_count(key)
                return True
            except Exception as e:
                wait = 0.5 * (2 ** attempt)
                logger.warning(
                    f"[SOPFeedback] 知识沉淀失败 (attempt {attempt+1}/{max_retries}): {e}，{wait}s 后重试"
                )
                if attempt < max_retries - 1:
                    import asyncio
                    await asyncio.sleep(wait)

        # 所有重试均失败，写入 SQLite 队列等待下次启动时重试
        try:
            from infra.memory.sqlite_client import SQLiteClient
            db = SQLiteClient()
            await db.insert_pending_op(
                op_type="knowledge_persist",
                payload={"key": key, "data": data},
            )
            logger.info(f"[SOPFeedback] 知识沉淀失败，已入队 SQLite 待重试: {key}")
        except Exception as sqlite_e:
            logger.error(f"[SOPFeedback] SQLite 兜底也失败: {sqlite_e}")

        await self._check_failure_threshold(key)
        return False

    async def _check_failure_threshold(self, key: str) -> None:
        """连续失败超过阈值时告警。"""
        self.failure_counts[key] = self.failure_counts.get(key, 0) + 1
        count = self.failure_counts[key]
        if count >= self.ALERT_THRESHOLD:
            logger.error(
                f"[SOPFeedback] ALERT: 知识沉淀 key=`{key}` 已连续失败 {count} 次"
                f"（阈值={self.ALERT_THRESHOLD}），请检查 Qdrant/SQLite 连接状态"
            )

    def _reset_failure_count(self, key: str) -> None:
        """成功后重置该 key 的失败计数。"""
        self.failure_counts.pop(key, None)

    async def _compare_with_sop(
        self, task_result: Dict[str, Any], task_meta: Dict[str, Any], sop_id: str
    ) -> float:
        """对比任务执行结果与 SOP 定义，计算偏差度"""
        try:
            from sop.engine import get_sop_engine
            engine = get_sop_engine()
            sop_def = engine.get_definition(sop_id)
            if not sop_def:
                return 0.0

            expected_steps = len(sop_def.get("steps", []))
            actual_steps = len(task_result.get("steps_history", []))

            step_deviation = abs(expected_steps - actual_steps) / max(expected_steps, 1)

            exec_result = task_result.get("execution_result", {})
            if isinstance(exec_result, dict):
                agg = exec_result.get("aggregated_output", {})
                success_rate = agg.get("success_rate", 1.0)
                quality_deviation = 1.0 - success_rate
            else:
                quality_deviation = 0.0

            return (step_deviation + quality_deviation) / 2.0

        except ImportError as e:
            logger.warning(f"[SOPFeedback] SOP 引擎不可用: {e}，跳过对比")
            return 0.0
        except Exception as e:
            logger.error(f"[SOPFeedback] SOP 对比异常: {e}")
            return 0.0

    async def _propose_sop_update(
        self, task_result: Dict[str, Any], task_meta: Dict[str, Any],
        sop_id: str, deviation: float,
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
        logger.info(f"[SOPFeedback] SOP 更新提议: {sop_id} (偏差 {deviation:.1%})")
        return proposal

    def get_metrics(self) -> Dict[str, Any]:
        return {**self.metrics, "feedback_log_size": len(self.feedback_log)}


# 全局单例
_feedback_instance: Optional[SOPFeedbackPipeline] = None

def get_sop_feedback() -> SOPFeedbackPipeline:
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = SOPFeedbackPipeline()
    return _feedback_instance
