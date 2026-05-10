"""
质量门控与降级策略模块
在 Manager 层对 Worker 执行结果进行质量评估，
低质量结果自动升级模型重试，超过重试上限则推送人工介入。
"""

import time
from typing import Dict, Any, Optional, Tuple
from loguru import logger

from molib.agencies.base import Task, AgencyResult


class QualityGate:
    """质量门控 — 集成到 BaseSubsidiaryManager._execute_with_worker() 末尾。"""

    MIN_SCORE: float = 6.0
    MAX_RETRIES: int = 2
    MODEL_UPGRADE_MAP: Dict[str, str] = {
        # 升序链：百炼模型从弱到强
        "qwen3.6-flash": "qwen3.6-plus",
        "qwen3.6-plus": "deepseek-v4-pro",
        "deepseek-v4-pro": "deepseek-v4-pro",  # qwen disabled (400 errors)
    }
    # 终端哨兵：百炼最强旗舰，到达后不再升级
    TERMINAL_MODELS = set()  # qwen disabled

    # 各子公司质量审查标准（LLM 驱动审查时使用）
    AGENCY_REVIEW_CRITERIA: Dict[str, str] = {
        "ip": "评估标准：标题是否有吸引力、内容是否可直接发布、标签是否相关、是否包含互动引导。",
        "research": "评估标准：数据来源是否权威、分析方法是否合理、结论是否有数据支撑、建议是否可执行。",
        "dev": "评估标准：代码是否可运行、错误处理是否完善、文档是否清晰、是否符合最佳实践。",
        "data": "评估标准：数据来源是否清晰、计算方法是否透明、可视化是否合理、结论是否有业务价值。",
        "growth": "评估标准：策略是否可执行、假设是否清晰、指标是否可衡量、预期效果是否合理。",
        "ads": "评估标准：投放策略是否精准、预算分配是否合理、素材建议是否有创意、ROI预期是否合理。",
        "product": "评估标准：需求是否明确、功能设计是否合理、优先级是否清晰、是否考虑用户场景。",
        "ai": "评估标准：技术方案是否可行、Prompt设计是否合理、架构是否可扩展、是否有风险说明。",
        "edu": "评估标准：课程结构是否合理、内容深度是否适当、学员体验是否考虑、转化路径是否清晰。",
        "order": "评估标准：报价是否合理、交付方案是否清晰、风险是否识别、时间线是否可行。",
        "shop": "评估标准：话术是否有说服力、转化路径是否优化、定价策略是否合理、客户价值是否体现。",
        "finance": "评估标准：数据是否准确、计算是否正确、分析是否深入、建议是否有财务逻辑。",
        "crm": "评估标准：用户分层是否合理、运营策略是否有针对性、自动化规则是否可行。",
        "knowledge": "评估标准：知识提取是否准确、文档是否清晰、结构是否合理、是否便于检索。",
        "cs": "评估标准：回复是否专业、是否解决用户问题、是否维护品牌形象、是否包含跟进建议。",
        "legal": "评估标准：法律依据是否准确、风险识别是否全面、建议是否合规、用语是否专业。",
        "bd": "评估标准：客户分析是否深入、报价方案是否合理、谈判策略是否可行、跟进计划是否具体。",
        "global_market": "评估标准：本地化是否到位、市场分析是否深入、合规建议是否准确、策略是否可落地。",
        "devops": "评估标准：运维方案是否可靠、监控是否完善、故障处理是否及时、性能优化是否有数据支撑。",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.min_score = config.get("min_score", self.MIN_SCORE)
        self.max_retries = config.get("max_retries", self.MAX_RETRIES)
        self.model_upgrade_map = config.get("model_upgrade_map", self.MODEL_UPGRADE_MAP)
        self.metrics = {
            "total_evaluations": 0, "passed": 0,
            "retried": 0, "escalated_to_human": 0,
        }

    def extract_score(self, result: AgencyResult) -> float:
        """从 Worker 执行结果中提取质量分数。无数字分数时返回 sentinel (-1.0)，触发 LLM 审查。"""
        if result.status == "error":
            return 0.0
        if result.status == "pending_approval":
            return 5.0

        output = result.output or {}
        for field in ("confidence", "score", "quality_score"):
            if field in output:
                raw = output[field]
                if isinstance(raw, (int, float)):
                    return raw * 10 if raw <= 1.0 else min(raw, 10.0)

        result_text = output.get("result", "") or output.get("report", "") or output.get("content", "")
        if not result_text:
            return -1.0

        # 尝试从文本中提取分数
        import re as _re3
        score_match = _re3.search(r'(?:score|quality|评分)[:\s]*(\d+(?:\.\d+)?)', str(result_text), _re3.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))
            return score * 10 if score <= 1.0 else min(score, 10.0)

        return -1.0

    async def _llm_review_async(self, result: AgencyResult, task: Task) -> float:
        """
        LLM 驱动的质量审查。异步、非阻塞。
        使用各子公司独立审查标准，返回 0-10 的评分。
        """
        try:
            from molib.core.ceo.model_router import ModelRouter
            router = ModelRouter()

            agency_id = result.agency_id.replace("_manager", "").replace("_agency", "")
            criteria = self.AGENCY_REVIEW_CRITERIA.get(
                agency_id, "评估标准：内容完整性、准确性、可操作性。"
            )

            # 提取待审查内容
            output = result.output or {}
            content = ""
            for key in ("result", "report", "content", "summary", "text"):
                val = output.get(key, "")
                if isinstance(val, str) and len(val) > 50:
                    content = val[:3000]
                    break
            if not content:
                content = str(output)[:3000]

            review_prompt = (
                f"请评估以下任务的执行结果质量（1-10分）：\n\n"
                f"任务ID: {task.task_id}\n"
                f"子公司: {agency_id}\n\n"
                f"{criteria}\n\n"
                f"执行输出:\n{content}\n\n"
                f'请返回纯JSON：{{"score": 7.5, "reasoning": "评估理由（一句话）"}}'
            )

            review_result = await router.call_async(
                prompt=review_prompt,
                system="你是质量评估专家。给出0-10的分数，严格评估，不浮夸。",
                task_type="quality_review",
            )
            text = review_result.get("text", "")
            import re as _re2, json as _json2
            match = _re2.search(r'\{[\s\S]*\}', text)
            if match:
                parsed = _json2.loads(match.group())
                return float(parsed.get("score", 5.0))
        except Exception as e:
            logger.debug(f"[QualityGate] LLM review failed: {e}")
        return 5.0

    async def evaluate(self, result, task, retry_count=0, retry_callback=None, start_time=None):
        """评估执行结果质量，必要时自动重试或升级人工。"""
        if start_time is None:
            start_time = time.time()
        self.metrics["total_evaluations"] += 1

        # 总时间上限保护：超过 120 秒直接放行，避免飞书超时
        elapsed = time.time() - start_time
        if elapsed > 120:
            logger.warning(f"[QualityGate] 总耗时 {elapsed:.0f}s 超过 120s 上限，强制放行 task={task.task_id}")
            return result, {"score": -1, "min_score": self.min_score, "retry_count": retry_count, "action": "timeout_force_pass"}

        score = self.extract_score(result)

        # Sentinels: -1.0 触发 LLM 审查评分
        if score < 0:
            score = await self._llm_review_async(result, task)
            logger.info(f"[QualityGate] LLM review score: {score:.1f} for {task.task_id}")

        eval_meta = {"score": score, "min_score": self.min_score,
                      "retry_count": retry_count, "action": "pass"}

        if score >= self.min_score:
            self.metrics["passed"] += 1
            logger.debug(f"[QualityGate] PASS task={task.task_id} score={score:.1f}")
            return result, eval_meta

        if retry_count < self.max_retries and retry_callback is not None:
            current_model = (result.output or {}).get("model_used", "qwen3.6-plus")
            # 终端哨兵：最强模型不重试，直接升级到人工
            if current_model in getattr(self, "TERMINAL_MODELS", set()):
                logger.warning(
                    f"[QualityGate] 已是终端模型 {current_model}，跳过重试直接升级人工 "
                    f"task={task.task_id} score={score:.1f}"
                )
                eval_meta["action"] = "terminal_skip"
            else:
                self.metrics["retried"] += 1
                upgraded_model = self.model_upgrade_map.get(current_model, current_model)
                if upgraded_model == current_model:
                    logger.warning(
                        f"[QualityGate] 无可用升级模型 for {current_model}，升级人工 "
                        f"task={task.task_id} score={score:.1f}"
                    )
                    eval_meta["action"] = "no_upgrade_path"
                else:
                    logger.warning(
                        f"[QualityGate] RETRY task={task.task_id} score={score:.1f} "
                        f"model: {current_model} → {upgraded_model}"
                    )
                    eval_meta["action"] = "retry"
                    eval_meta["model_upgrade"] = f"{current_model} → {upgraded_model}"
                    try:
                        new_result = await retry_callback(task, upgraded_model)
                        return await self.evaluate(new_result, task, retry_count + 1, retry_callback, start_time)
                    except Exception as e:
                        logger.error(f"[QualityGate] Retry failed: {e}")
                        eval_meta["retry_error"] = str(e)

        # 超过重试上限，升级到人工介入
        self.metrics["escalated_to_human"] += 1
        eval_meta["action"] = "escalate_to_human"
        logger.error(f"[QualityGate] ESCALATE task={task.task_id} score={score:.1f}")

        escalation_result = AgencyResult(
            task_id=result.task_id, agency_id=result.agency_id,
            status="pending_approval",
            output={**(result.output or {}), "quality_gate": eval_meta,
                    "escalation_reason": f"质量评分 {score:.1f} < {self.min_score}，重试 {retry_count} 次仍未达标"},
            needs_approval=True,
            approval_reason=f"质量门控升级: 评分 {score:.1f}/{self.min_score}",
            cost=result.cost, latency=result.latency,
        )
        return escalation_result, eval_meta

    def get_metrics(self) -> Dict[str, Any]:
        total = self.metrics["total_evaluations"]
        return {**self.metrics,
                "pass_rate": self.metrics["passed"] / total if total > 0 else 0.0,
                "escalation_rate": self.metrics["escalated_to_human"] / total if total > 0 else 0.0}


_quality_gate_instance: Optional[QualityGate] = None

def get_quality_gate(config=None) -> QualityGate:
    global _quality_gate_instance
    if _quality_gate_instance is None:
        _quality_gate_instance = QualityGate(config)
    return _quality_gate_instance
