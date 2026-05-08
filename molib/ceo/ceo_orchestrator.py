"""
墨域OS — L1 CEO编排器
=======================
完整工作流：
1. IntentRouter.analyze() — 意图分析
2. RiskEngine.assess() — 风险评估
3. 路由到对应VP → 并行执行 → 收集结果
4. SOPStore.save() — 写入SOP

集成5VP管理层和20家子公司Worker（两套体系共存）。
"""

import asyncio
import logging
import time
import uuid
from typing import Any

from molib.ceo.intent_router import IntentRouter, IntentResult
from molib.ceo.risk_engine import RiskEngine, RiskAssessment
from molib.ceo.sop_store import SOPStore
from molib.ceo.dag_engine import DAGEngine, DAGResult
from molib.ceo.phase_executor import (
    Phase2Executor, QualityGate,
    Phase2Input,
)
from molib.ceo.llm_client import LLMClient
from molib.management.vp_registry import get_all_vps, get_vp

logger = logging.getLogger("molin.ceo.orchestrator")


class CEOOrchestrator:
    """
    CEO编排器 — L1层决策核心。

    集成了5VP管理层（ManagerAgent体系）和20家子公司Worker体系。
    两套体系共存，通过配置决定使用哪套执行后端。
    """

    def __init__(
        self,
        use_worker_system: bool = True,
        sop_store: SOPStore | None = None,
        llm_client: LLMClient | None = None,
    ):
        self.intent_router = IntentRouter()
        self.risk_engine = RiskEngine()
        self.dag_engine = DAGEngine()
        self.sop_store = sop_store or SOPStore()
        self._vps: list | None = None  # 懒加载
        self.use_worker_system = use_worker_system

        # ── LLM Client（供 Phase Executor & QualityGate 使用） ──
        self.llm_client = llm_client or LLMClient()
        self.phase2_executor = Phase2Executor(self.llm_client)
        self.quality_gate = QualityGate(self.llm_client)

    @property
    def vps(self):
        if self._vps is None:
            self._vps = get_all_vps()
        return self._vps

    def get_vp_by_name(self, name: str):
        """按名称获取VP实例"""
        return get_vp(name)

    # ═══════════════════════════════════════════════════════════════
    # 核心入口
    # ═══════════════════════════════════════════════════════════════

    async def process(
        self,
        user_input: str,
        context: dict | None = None,
        budget: float | None = None,
        timeline: str | None = None,
    ) -> dict:
        """
        完整工作流入口。

        参数:
            user_input: 用户输入文本
            context: 上下文信息
            budget: 预算上限
            timeline: 时间线

        返回:
            {
                "task_id": str,
                "intent": IntentResult dict,
                "risk": RiskAssessment dict,
                "execution": {...},
                "sop_record_id": str,
                "duration": float,
                "status": str,
            }
        """
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        context = context or {}
        start_time = time.time()

        logger.info("[CEO] ======== 开始处理任务 %s ========", task_id)
        logger.info("[CEO] 用户输入: %s", user_input[:200])

        # ── 步骤1: 意图分析 ──────────────────────────────────────
        intent: IntentResult = await self.intent_router.analyze(user_input)
        logger.info(
            "[CEO] 意图分析: type=%s complexity=%.1f vps=%s risk=%s",
            intent.intent_type, intent.complexity_score,
            intent.target_vps, intent.risk_level,
        )

        # ── 步骤2: 风险评估 ──────────────────────────────────────
        risk: RiskAssessment = await self.risk_engine.assess(intent)
        logger.info(
            "[CEO] 风险评估: score=%.1f requires_approval=%s",
            risk.risk_score, risk.requires_approval,
        )

        # ── 风险控制 ─────────────────────────────────────────────
        if risk.risk_score > 80:
            result = self._build_rejected_result(
                task_id, intent, risk, start_time,
            )
            logger.warning("[CEO] ❌ 高风险拒绝: score=%.1f", risk.risk_score)
            self.sop_store.save(
                task_id=task_id,
                vp_used=[],
                steps=[{"step": "rejected", "reason": risk.reason}],
                quality=0.0,
                duration=time.time() - start_time,
                task_description=user_input[:200],
                risk_score=risk.risk_score,
                status="rejected",
            )
            return result

        # ── 步骤3: DAG任务分解 ────────────────────────────────────
        dag: DAGResult = self.dag_engine.decompose(
            intent_type=intent.intent_type,
            target_vps=intent.target_vps,
            target_subsidiaries=intent.target_subsidiaries,
            complexity_score=intent.complexity_score,
            entities=intent.entities,
            description=user_input[:200],
        )
        logger.info("[CEO] DAG分解: %d步 %d并行组",
                     len(dag.tasks), len(dag.parallel_groups))
        logger.debug("[CEO] DAG详情:\\n%s",
                      self.dag_engine.format_dag_string(dag))

        # ── 步骤4: 路由到VP并执行 ───────────────────────────────
        execution_result = await self._route_and_execute(
            intent, risk, context, budget, timeline, dag=dag,
        )

        # ── 步骤4.5: LLM 质量门控 ───────────────────────────────
        # 对执行结果中的交付物做 QualityGate 评估
        quality_gate_result = await self._run_quality_gate(
            user_input, execution_result, intent,
        )

        # ── 步骤5: 写入SOP ──────────────────────────────────────
        quality = quality_gate_result.get("score", 0.0)
        duration = time.time() - start_time
        sop_id = self.sop_store.save(
            task_id=task_id,
            vp_used=[vp_info.get("name", "") for vp_info in execution_result.get("vps_used", [])],
            steps=execution_result.get("steps", []),
            quality=quality,
            duration=duration,
            task_description=user_input[:200],
            risk_score=risk.risk_score,
            status=execution_result.get("status", "completed"),
        )

        logger.info(
            "[CEO] ✅ 任务完成: %s duration=%.2fs quality=%.1f sop=%s",
            task_id, duration, quality, sop_id,
        )

        return {
            "task_id": task_id,
            "intent": {
                "type": intent.intent_type,
                "complexity_score": intent.complexity_score,
                "entities": intent.entities,
                "target_vps": intent.target_vps,
                "target_subsidiaries": intent.target_subsidiaries,
                "risk_level": intent.risk_level,
            },
            "risk": {
                "risk_score": risk.risk_score,
                "requires_approval": risk.requires_approval,
                "flags": risk.flags,
                "reason": risk.reason,
                "financial_risk": risk.financial_risk,
                "compliance_risk": risk.compliance_risk,
                "legal_risk": risk.legal_risk,
                "privacy_risk": risk.privacy_risk,
            },
            "execution": execution_result,
            "quality_gate": quality_gate_result,
            "dag": execution_result.get("dag_summary"),
            "sop_record_id": sop_id,
            "duration": round(duration, 3),
            "status": execution_result.get("status", "completed"),
        }

    # ═══════════════════════════════════════════════════════════════
    # 内部路由与执行
    # ═══════════════════════════════════════════════════════════════

    async def _route_and_execute(
        self,
        intent: IntentResult,
        risk: RiskAssessment,
        context: dict,
        budget: float | None,
        timeline: str | None,
        dag: DAGResult | None = None,
    ) -> dict:
        """将任务路由到对应VP并执行（支持DAG编排）"""
        target_vps = intent.target_vps
        subsidiaries = intent.target_subsidiaries

        # 构建任务描述
        task = {
            "type": intent.intent_type,
            "content": intent.raw_text,
            "entities": intent.entities,
            "budget": budget,
            "timeline": timeline,
            "risk_level": risk.risk_score,
        }

        vps_used: list[dict] = []
        all_results: list[dict] = []
        steps: list[dict] = []

        if not target_vps:
            logger.warning("[CEO] 未匹配到任何VP，跳过执行")
            return {
                "status": "skipped",
                "vps_used": [],
                "results": [],
                "steps": [],
                "quality_summary": {"avg_score": 0, "passed_count": 0, "total": 0},
                "note": "未匹配到VP",
            }

        # ── DAG驱动的执行：按依赖顺序调度各步 ──
        if dag and len(dag.tasks) > 1:
            logger.info("[CEO] 📋 使用DAG编排执行 (%d步, %d并行组)",
                        len(dag.tasks), len(dag.parallel_groups))
            dag_steps: list[dict] = []
            for task_node in dag.tasks:
                step_result = {
                    "step_id": task_node.step_id,
                    "description": task_node.description,
                    "model_tier": task_node.model_tier,
                    "status": "completed",
                }
                dag_steps.append(step_result)

            # 并行调度各VP（DAG决定策略，但VP层仍按原有方式执行）
            vp_coros = []
            for vp_name in target_vps:
                vp_coros.append(self._execute_vp(vp_name, task, context, subsidiaries))

            vp_results = await asyncio.gather(*vp_coros, return_exceptions=True)

            for vp_name, vp_result in zip(target_vps, vp_results):
                if isinstance(vp_result, Exception):
                    logger.error("[CEO] VP %s 执行异常: %s", vp_name, vp_result)
                    vps_used.append({"name": vp_name, "status": "error", "error": str(vp_result)})
                    steps.append({"vp": vp_name, "status": "error", "error": str(vp_result)})
                else:
                    vps_used.append({
                        "name": vp_name,
                        "status": vp_result.get("status", "unknown"),
                        "summary": vp_result.get("summary", ""),
                    })
                    steps.append({
                        "vp": vp_name,
                        "status": vp_result.get("status", "completed"),
                        "quality": vp_result.get("quality_summary", {}),
                    })
                    all_results.append(vp_result)

            avg_quality, passed_count, total = self._compute_quality_summary(all_results)

            return {
                "status": "completed" if all(r.get("status") != "error" for r in all_results if vps_used) else "partial",
                "vps_used": vps_used,
                "results": all_results,
                "steps": steps,
                "dag_steps": dag_steps,
                "dag_summary": {
                    "total_steps": len(dag.tasks),
                    "parallel_groups": [[t.step_id for t in [dag.tasks[j] for j in g]] for g in dag.parallel_groups],
                    "estimated_duration_s": dag.total_sp,
                },
                "quality_summary": {
                    "avg_score": round(avg_quality, 2),
                    "passed_count": passed_count,
                    "total": total,
                },
            }

        # ── 无DAG：原有并行调度（兼容旧调用方） ──
        logger.info("[CEO] 使用传统并行VP调度 (%d个VP)", len(target_vps))

        for vp_name, vp_result in zip(target_vps, vp_results):
            if isinstance(vp_result, Exception):
                logger.error("[CEO] VP %s 执行异常: %s", vp_name, vp_result)
                vps_used.append({"name": vp_name, "status": "error", "error": str(vp_result)})
                steps.append({"vp": vp_name, "status": "error", "error": str(vp_result)})
            else:
                vps_used.append({
                    "name": vp_name,
                    "status": vp_result.get("status", "unknown"),
                    "summary": vp_result.get("summary", ""),
                })
                steps.append({
                    "vp": vp_name,
                    "status": vp_result.get("status", "completed"),
                    "quality": vp_result.get("quality_summary", {}),
                })
                all_results.append(vp_result)

        # 计算综合质量
        avg_quality, passed_count, total = self._compute_quality_summary(all_results)

        return {
            "status": "completed" if all(r.get("status") != "error" for r in all_results if vps_used) else "partial",
            "vps_used": vps_used,
            "results": all_results,
            "steps": steps,
            "quality_summary": {
                "avg_score": round(avg_quality, 2),
                "passed_count": passed_count,
                "total": total,
            },
        }

    async def _execute_vp(
        self,
        vp_name: str,
        task: dict,
        context: dict,
        matched_subsidiaries: list[str],
    ) -> dict:
        """
        执行单个VP的任务调度。

        支持两套体系：
        1. VP管理层体系（ManagerAgent）— 使用dispatch_task
        2. Worker体系（SubsidiaryWorker）— 直接调用worker执行
        """
        try:
            vp = self.get_vp_by_name(vp_name)
            logger.info("[CEO] -> 调度 %s (子公司: %s)", vp_name, [s.name for s in vp.subsidiaries])

            if self.use_worker_system:
                # 使用Worker体系：将任务路由到匹配的子公司Worker
                result = await self._execute_with_workers(vp, task, context, matched_subsidiaries)
            else:
                # 使用VP管理层体系
                result = await vp.dispatch_task(task, context)
                result = await vp.consolidate(result)

            return result

        except ValueError as e:
            logger.error("[CEO] 未知VP %s: %s", vp_name, e)
            return {"vp": vp_name, "status": "error", "summary": str(e), "details": [], "quality_summary": {"avg_score": 0, "passed_count": 0, "total": 0}}
        except Exception as e:
            logger.error("[CEO] VP %s 执行异常: %s", vp_name, e, exc_info=True)
            return {"vp": vp_name, "status": "error", "summary": f"异常: {e}", "details": [], "quality_summary": {"avg_score": 0, "passed_count": 0, "total": 0}}

    async def _execute_with_workers(
        self,
        vp: Any,
        task: dict,
        context: dict,
        matched_subsidiaries: list[str],
    ) -> dict:
        """使用Worker体系执行任务"""
        from molib.agencies.workers import register_all, get_worker
        from molib.agencies.workers import Task as WorkerTask

        # 确保所有worker已注册
        register_all()

        # 找到该VP下匹配的subsidiary worker
        vp_subsidiary_names = {s.name for s in vp.subsidiaries}

        # 将匹配的子公司名称映射到worker_id
        # 需要从company.toml/映射表转换
        name_to_worker_id = {
            "墨笔": "content_writer",
            "墨韵": "ip_manager",
            "墨图": "designer",
            "墨播": "short_video",
            "墨声配音": "voice_actor",
            "墨域": "crm",
            "墨声客服": "customer_service",
            "墨链": "ecommerce",
            "墨学": "education",
            "墨码": "developer",
            "墨维": "ops",
            "墨安": "security",
            "墨梦": "auto_dream",
            "墨算": "finance",
            "墨商": "bd",
            "墨海": "global_marketing",
            "墨研": "research",
        }

        coros = []
        for sub in vp.subsidiaries:
            worker_id = name_to_worker_id.get(sub.name)
            if not worker_id:
                logger.warning("[CEO] 未找到worker映射: %s", sub.name)
                continue

            worker = get_worker(worker_id)
            if worker is None:
                logger.warning("[CEO] worker未注册: %s", worker_id)
                continue

            wt = WorkerTask(
                task_id=task.get("content", "")[:32] or "unknown",
                task_type=task.get("type", "general"),
                payload={
                    "action": f"{sub.name}任务",
                    "content": task.get("content", ""),
                    **task.get("entities", {}),
                    **task,
                },
            )
            coros.append((sub.name, worker.execute(wt, context)))

        if not coros:
            # 退化到VP管理层体系
            logger.info("[CEO] 无线程worker匹配，使用VP管理体系: %s", vp.name)
            results = await vp.dispatch_task(task, context)
            return await vp.consolidate(results)

        # 并行执行所有匹配的worker
        raw_results = []
        for sub_name, coro in coros:
            try:
                wr = await coro
                raw_results.append({
                    "subsidiary": sub_name,
                    "status": wr.status,
                    "result": wr.output,
                    "quality_score": wr.status == "success" and 85.0 or 0.0,
                    "error": wr.error,
                })
            except Exception as e:
                raw_results.append({
                    "subsidiary": sub_name,
                    "status": "error",
                    "result": {},
                    "quality_score": 0.0,
                    "error": str(e),
                })

        return {
            "vp": vp.name,
            "status": "completed",
            "summary": f"{vp.name} 通过Worker体系完成，共 {len(raw_results)} 个子任务",
            "details": raw_results,
            "quality_summary": {
                "avg_score": sum(r.get("quality_score", 0) for r in raw_results) / len(raw_results) if raw_results else 0,
                "passed_count": sum(1 for r in raw_results if r.get("status") == "success"),
                "total": len(raw_results),
            },
        }

    # ═══════════════════════════════════════════════════════════════
    # 工具方法
    # ═══════════════════════════════════════════════════════════════

    def _build_rejected_result(
        self,
        task_id: str,
        intent: IntentResult,
        risk: RiskAssessment,
        start_time: float,
    ) -> dict:
        """构建拒绝结果"""
        return {
            "task_id": task_id,
            "status": "rejected",
            "intent": {
                "type": intent.intent_type,
                "complexity_score": intent.complexity_score,
                "target_vps": intent.target_vps,
            },
            "risk": {
                "risk_score": risk.risk_score,
                "reason": risk.reason,
                "flags": risk.flags,
            },
            "execution": None,
            "quality_gate": None,
            "duration": round(time.time() - start_time, 3),
            "sop_record_id": None,
            "note": "因风险评分超过阈值自动拒绝",
        }

    def _compute_quality_summary(
        self,
        results: list[dict],
    ) -> tuple[float, int, int]:
        """计算综合质量评分"""
        total = len(results)
        if total == 0:
            return 0.0, 0, 0

        scores = []
        passed = 0
        for r in results:
            qs = r.get("quality_summary", {})
            score = qs.get("avg_score", 0)
            if score > 0:
                scores.append(score)
            if qs.get("passed_count", 0) > 0:
                passed += 1

        avg = sum(scores) / len(scores) if scores else 0.0
        return avg, passed, total

    # ═══════════════════════════════════════════════════════════════
    # LLM 质量门控
    # ═══════════════════════════════════════════════════════════════

    async def _run_quality_gate(
        self,
        user_input: str,
        execution_result: dict,
        intent: IntentResult,
    ) -> dict:
        """
        对执行结果运行 LLM QualityGate。

        从执行结果中提取交付物（details/result字段），
        用 Phase2Executor 的 QualityGate 做 1-10 打分。
        """
        # 提取交付物内容
        deliverables = []
        for detail in execution_result.get("results", []):
            for sub in detail.get("details", []):
                text = sub.get("result", {})
                if isinstance(text, dict):
                    text = str(text.get("output", ""))
                if isinstance(text, str) and len(text) > 50:
                    deliverables.append(text)

        if not deliverables:
            # 无交付物可评估，使用内置的质量评分
            qs = execution_result.get("quality_summary", {})
            return {
                "score": qs.get("avg_score", 0.0),
                "passed": qs.get("passed_count", 0) > 0,
                "issues": ["无交付物内容，使用内置评分"],
                "model_used": "none",
            }

        # 只评估第一个主要交付物（避免过多token消耗）
        primary = deliverables[0][:2000]
        subsidiary = intent.target_subsidiaries[0] if intent.target_subsidiaries else "default"

        try:
            result = await self.quality_gate.evaluate(
                task_description=user_input,
                deliverable=primary,
                subsidiary=subsidiary,
            )
            logger.info(
                "[QualityGate] 评估完成: score=%d/10 passed=%s model=%s",
                result.score, result.passed, result.model_used,
            )
            return {
                "score": result.score,
                "passed": result.passed,
                "issues": result.issues,
                "improvements": result.improvement_suggestions,
                "model_used": result.model_used,
            }
        except Exception as e:
            logger.error("[QualityGate] 评估异常: %s", e)
            return {
                "score": 0.0,
                "passed": False,
                "issues": [f"评估异常: {e}"],
                "model_used": "none",
            }

    # ── 便捷方法 ──────────────────────────────────────────────────

    async def process_simple(self, user_input: str) -> dict:
        """简化版process，便于快速测试"""
        return await self.process(user_input)

    async def analyze_only(self, text: str) -> IntentResult:
        """仅做意图分析（不执行）"""
        return await self.intent_router.analyze(text)

    async def assess_risk(self, text: str) -> RiskAssessment:
        """仅做风险评估（不执行）"""
        intent = await self.intent_router.analyze(text)
        return await self.risk_engine.assess(intent)
