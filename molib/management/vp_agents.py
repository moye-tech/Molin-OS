"""
墨麟OS — 5位VP管理层实现
=========================
每个VP是一个 ManagerAgent 类，负责：
1. 接收CEO分配的任务
2. 分解任务给旗下子公司
3. 质量门控（不合格自动升级模型重试）
4. 结果整合汇报

使用异步模式，允许后续独立扩展每个VP的逻辑。

增强: v1.4 加入Agent评估引擎 (OpenHarness) + 多Agent编排引擎 (OpenMAIC)
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger("molin.vp")


# ---------------------------------------------------------------------------
# 通用质量门控 & 子公司包装
# ---------------------------------------------------------------------------

class QualityGateResult:
    """质量门控检查结果"""

    def __init__(self, score: float, passed: bool, details: str = ""):
        self.score = score
        self.passed = passed
        self.details = details

    def __repr__(self) -> str:
        return (
            f"QualityGateResult(score={self.score:.1f}, "
            f"passed={self.passed}, details={self.details!r})"
        )


class SubsidiaryAgent:
    """
    子公司代理封装。
    实际场景中，subsidiary 可以是另一个 Agent 实例、LLM 调用、API 客户端等。
    这里提供默认实现，子类可覆盖 `execute` 以实现具体逻辑。
    """

    def __init__(self, name: str, model: str = "default", **kwargs):
        self.name = name
        self.model = model
        self.extra = kwargs

    async def execute(self, task: dict, context: dict) -> dict:
        """
        执行子公司任务。
        默认实现为模拟执行（生产环境应替换为真实调用）。
        """
        logger.info("[%s] 执行任务: %s", self.name, task.get("action", "unknown"))
        await asyncio.sleep(0.1)  # 模拟IO
        return {
            "subsidiary": self.name,
            "status": "completed",
            "result": f"{self.name} 完成: {task.get('action', 'unknown')}",
            "quality_score": random.uniform(60, 100),
        }

    def __repr__(self) -> str:
        return f"SubsidiaryAgent({self.name}, model={self.model})"


# ---------------------------------------------------------------------------
# 基类 ManagerAgent
# ---------------------------------------------------------------------------

class ManagerAgent(ABC):
    """
    VP / 管理层基类。

    每个 VP 管理若干子公司，并实现：
      - dispatch_task   : 分解并分派任务
      - quality_check   : 质量门控
      - consolidate     : 结果整合
    """

    def __init__(
        self,
        name: str,
        subsidiary_configs: list[dict],
        quality_gate: float = 70.0,
        escalation_model: str = "deepseek-v4-pro",
    ):
        self.name = name
        self.quality_gate = quality_gate
        self.escalation_model = escalation_model
        self.subsidiaries: list[SubsidiaryAgent] = []
        for cfg in subsidiary_configs:
            if isinstance(cfg, SubsidiaryAgent):
                self.subsidiaries.append(cfg)
            elif isinstance(cfg, dict):
                self.subsidiaries.append(SubsidiaryAgent(**cfg))
            else:
                raise TypeError(f"Unsupported subsidiary config type: {type(cfg)}")

    @abstractmethod
    async def dispatch_task(self, task: dict, context: dict) -> list[dict]:
        """
        将CEO下发的 task 分解为子任务列表并分派给子公司。
        返回每个子公司的执行结果列表。
        """
        ...

    @abstractmethod
    async def quality_check(self, result: dict) -> QualityGateResult:
        """
        对单个子公司产出进行质量评分 (0-100)。
        返回 QualityGateResult，其中 passed=False 表示不合格。
        """
        ...

    @abstractmethod
    async def consolidate(self, results: list[dict]) -> dict:
        """
        整合所有子公司的产出，形成统一汇报结果。
        """
        ...

    # ── 默认实现：质量评分低于阈值时升级模型重试 ──────────────────────

    async def _execute_with_escalation(
        self,
        subsidiary: SubsidiaryAgent,
        sub_task: dict,
        context: dict,
        max_retries: int = 2,
    ) -> dict:
        """
        执行子公司任务，并做质量门控。
        若质量不合格，升级模型（改为 escalation_model）重试最多 max_retries 次。
        记录每次升级的原因用于后续优化。
        """
        original_model = subsidiary.model
        escalation_log: list[dict] = []
        last_quality = 0.0
        passed = False

        for attempt in range(1 + max_retries):
            if attempt > 0:
                logger.warning(
                    "[%s] 质量不合格，升级模型重试 (attempt %d/%d) "
                    "subsidiary=%s, model=%s, last_score=%.1f",
                    self.name, attempt, max_retries,
                    subsidiary.name, self.escalation_model, last_quality,
                )
                subsidiary.model = self.escalation_model

            raw_result = await subsidiary.execute(sub_task, context)
            quality = await self.quality_check(raw_result)
            last_quality = quality.score
            passed = quality.passed

            raw_result["quality"] = {
                "score": quality.score,
                "passed": quality.passed,
                "details": quality.details,
                "attempt": attempt,
                "model_used": subsidiary.model,
            }

            # 记录升级日志
            if attempt > 0:
                escalation_log.append({
                    "attempt": attempt,
                    "subsidiary": subsidiary.name,
                    "model": subsidiary.model,
                    "score": quality.score,
                    "passed": quality.passed,
                    "reason": quality.details,
                })

            if quality.passed:
                logger.info(
                    "[%s] ✅ 子公司 %s 质量通过 score=%.1f attempt=%d model=%s",
                    self.name, subsidiary.name, quality.score, attempt, subsidiary.model,
                )
                break
        else:
            # 所有重试都失败
            logger.error(
                "[%s] ❌ 子公司 %s 质量门控最终失败，"
                "score=%.1f after %d retries. Escalating to CEO.",
                self.name, subsidiary.name, quality.score, max_retries,
            )
            # 标记为需要CEO关注
            raw_result["needs_ceo_attention"] = True
            raw_result["ceo_message"] = (
                f"子公司 {subsidiary.name} ({self.name}) 质量门控失败: "
                f"最终评分 {quality.score:.1f}（阈值 {self.quality_gate}）"
                f"，已重试 {max_retries} 次。请CEO决策。"
            )

        # 恢复原始模型
        subsidiary.model = original_model

        # 附加升级日志
        raw_result["escalation_log"] = escalation_log
        raw_result["total_attempts"] = attempt + 1
        raw_result["final_passed"] = passed
        return raw_result

    async def _run_all_subsidiaries(
        self, sub_tasks: list[tuple[SubsidiaryAgent, dict]], context: dict
    ) -> list[dict]:
        """并行执行所有子任务并做质量门控"""
        coros = [
            self._execute_with_escalation(subsidiary, task, context)
            for subsidiary, task in sub_tasks
        ]
        return await asyncio.gather(*coros)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name={self.name!r}, "
            f"subsidiaries={[s.name for s in self.subsidiaries]}, "
            f"quality_gate={self.quality_gate})"
        )


# ===========================================================================
# 5位 VP 具体实现
# ===========================================================================

class VPMarketing(ManagerAgent):
    """
    VP营销 — 负责对外内容创作与传播。
    子公司: 墨笔(文案)、墨韵(诗歌/韵律)、墨图(设计)、墨播(直播)、墨声配音(音频)
    """

    def __init__(self, subsidiary_configs: list[dict] | None = None):
        if subsidiary_configs is None:
            subsidiary_configs = [
                {"name": "墨笔", "model": "claude-3-opus"},
                {"name": "墨韵", "model": "claude-3-sonnet"},
                {"name": "墨图", "model": "dall-e-3"},
                {"name": "墨播", "model": "claude-3-haiku"},
                {"name": "墨声配音", "model": "elevenlabs-multilingual"},
            ]
        super().__init__(
            name="VP营销",
            subsidiary_configs=subsidiary_configs,
            quality_gate=70.0,
            escalation_model="deepseek-v4-pro",
        )

    async def dispatch_task(self, task: dict, context: dict) -> list[dict]:
        """营销任务分解：根据任务类型分派给对应子公司"""
        task_type = task.get("type", "marketing")
        content = task.get("content", "")

        sub_tasks: list[tuple[SubsidiaryAgent, dict]] = []

        for sub in self.subsidiaries:
            if sub.name == "墨笔":
                sub_tasks.append((sub, {"action": "撰写文案", "content": content, "requirements": task.get("requirements", "")}))
            elif sub.name == "墨韵":
                sub_tasks.append((sub, {"action": "创作韵律", "content": content, "style": task.get("style", "现代")}))
            elif sub.name == "墨图":
                sub_tasks.append((sub, {"action": "设计视觉", "content": content, "format": task.get("visual_format", "social")}))
            elif sub.name == "墨播":
                sub_tasks.append((sub, {"action": "直播策划", "content": content, "platform": task.get("platform", "抖音")}))
            elif sub.name == "墨声配音":
                sub_tasks.append((sub, {"action": "配音制作", "content": content, "language": task.get("language", "zh-CN")}))

        return await self._run_all_subsidiaries(sub_tasks, context)

    async def quality_check(self, result: dict) -> QualityGateResult:
        """营销内容质量检查"""
        score = result.get("quality_score", random.uniform(60, 100))
        details = f"营销内容质量评分: {score:.1f}"
        return QualityGateResult(score=score, passed=score >= self.quality_gate, details=details)

    async def consolidate(self, results: list[dict]) -> dict:
        """整合营销产出"""
        return {
            "vp": self.name,
            "status": "completed",
            "summary": f"营销任务完成，共 {len(results)} 个子任务",
            "details": results,
            "quality_summary": {
                "avg_score": sum(r.get("quality", {}).get("score", 0) for r in results) / len(results) if results else 0,
                "passed_count": sum(1 for r in results if r.get("quality", {}).get("passed", False)),
                "total": len(results),
            },
        }


class VPOps(ManagerAgent):
    """
    VP运营 — 负责平台运营、客服、学苑与链上生态。
    子公司: 墨域(主平台)、墨声客服(客服)、墨链(链上)、墨学(教育)
    """

    def __init__(self, subsidiary_configs: list[dict] | None = None):
        if subsidiary_configs is None:
            subsidiary_configs = [
                {"name": "墨域", "model": "deepseek-v4-pro"},
                {"name": "墨声客服", "model": "claude-3-haiku"},
                {"name": "墨链", "model": "deepseek-v4-pro"},
                {"name": "墨学", "model": "claude-3-sonnet"},
            ]
        super().__init__(
            name="VP运营",
            subsidiary_configs=subsidiary_configs,
            quality_gate=70.0,
            escalation_model="deepseek-v4-pro",
        )

    async def dispatch_task(self, task: dict, context: dict) -> list[dict]:
        """运营任务分解"""
        content = task.get("content", "")

        sub_tasks: list[tuple[SubsidiaryAgent, dict]] = []

        for sub in self.subsidiaries:
            if sub.name == "墨域":
                sub_tasks.append((sub, {"action": "平台运营", "content": content, "metrics": task.get("metrics", {})}))
            elif sub.name == "墨声客服":
                sub_tasks.append((sub, {"action": "客服应答", "content": content, "ticket_id": task.get("ticket_id", "")}))
            elif sub.name == "墨链":
                sub_tasks.append((sub, {"action": "链上操作", "content": content, "contract": task.get("contract", "")}))
            elif sub.name == "墨学":
                sub_tasks.append((sub, {"action": "学苑管理", "content": content, "course": task.get("course", "")}))

        return await self._run_all_subsidiaries(sub_tasks, context)

    async def quality_check(self, result: dict) -> QualityGateResult:
        """运营质量检查"""
        score = result.get("quality_score", random.uniform(60, 100))
        details = f"运营服务质量评分: {score:.1f}"
        return QualityGateResult(score=score, passed=score >= self.quality_gate, details=details)

    async def consolidate(self, results: list[dict]) -> dict:
        return {
            "vp": self.name,
            "status": "completed",
            "summary": f"运营任务完成，共 {len(results)} 个子任务",
            "details": results,
            "quality_summary": {
                "avg_score": sum(r.get("quality", {}).get("score", 0) for r in results) / len(results) if results else 0,
                "passed_count": sum(1 for r in results if r.get("quality", {}).get("passed", False)),
                "total": len(results),
            },
        }


class VPTech(ManagerAgent):
    """
    VP技术 — 负责研发、架构、安全与 AI 梦工场。
    子公司: 墨码(开发)、墨维(架构)、墨安(安全)、墨梦(AI研究)
    """

    def __init__(self, subsidiary_configs: list[dict] | None = None):
        if subsidiary_configs is None:
            subsidiary_configs = [
                {"name": "墨码", "model": "claude-3-opus"},
                {"name": "墨维", "model": "deepseek-v4-pro"},
                {"name": "墨安", "model": "claude-3-haiku"},
                {"name": "墨梦", "model": "claude-3-opus"},
            ]
        super().__init__(
            name="VP技术",
            subsidiary_configs=subsidiary_configs,
            quality_gate=75.0,  # 技术质量门控更严格
            escalation_model="claude-3-opus",  # 升级用最强模型
        )

    async def dispatch_task(self, task: dict, context: dict) -> list[dict]:
        """技术任务分解"""
        content = task.get("content", "")

        sub_tasks: list[tuple[SubsidiaryAgent, dict]] = []

        for sub in self.subsidiaries:
            if sub.name == "墨码":
                sub_tasks.append((sub, {"action": "编码开发", "content": content, "lang": task.get("language", "python")}))
            elif sub.name == "墨维":
                sub_tasks.append((sub, {"action": "架构设计", "content": content, "requirements": task.get("arch_requirements", {})}))
            elif sub.name == "墨安":
                sub_tasks.append((sub, {"action": "安全审计", "content": content, "audit_scope": task.get("audit_scope", "full")}))
            elif sub.name == "墨梦":
                sub_tasks.append((sub, {"action": "AI研究", "content": content, "research_question": task.get("research_question", "")}))

        return await self._run_all_subsidiaries(sub_tasks, context)

    async def quality_check(self, result: dict) -> QualityGateResult:
        """技术质量检查"""
        score = result.get("quality_score", random.uniform(60, 100))
        details = f"技术质量评分: {score:.1f}"
        return QualityGateResult(score=score, passed=score >= self.quality_gate, details=details)

    async def consolidate(self, results: list[dict]) -> dict:
        return {
            "vp": self.name,
            "status": "completed",
            "summary": f"技术任务完成，共 {len(results)} 个子任务",
            "details": results,
            "quality_summary": {
                "avg_score": sum(r.get("quality", {}).get("score", 0) for r in results) / len(results) if results else 0,
                "passed_count": sum(1 for r in results if r.get("quality", {}).get("passed", False)),
                "total": len(results),
            },
        }


class VPFinance(ManagerAgent):
    """
    VP财务 — 负责公司财务核算与预算控制。
    子公司: 墨算(财务引擎)
    """

    def __init__(self, subsidiary_configs: list[dict] | None = None):
        if subsidiary_configs is None:
            subsidiary_configs = [
                {"name": "墨算", "model": "deepseek-v4-pro"},
            ]
        super().__init__(
            name="VP财务",
            subsidiary_configs=subsidiary_configs,
            quality_gate=80.0,  # 财务数字要求极高
            escalation_model="claude-3-opus",
        )

    async def dispatch_task(self, task: dict, context: dict) -> list[dict]:
        """财务任务分解"""
        content = task.get("content", "")

        sub_tasks: list[tuple[SubsidiaryAgent, dict]] = []

        for sub in self.subsidiaries:
            if sub.name == "墨算":
                sub_tasks.append((sub, {
                    "action": "财务核算",
                    "content": content,
                    "period": task.get("period", "monthly"),
                    "budget_data": task.get("budget_data", {}),
                }))

        return await self._run_all_subsidiaries(sub_tasks, context)

    async def quality_check(self, result: dict) -> QualityGateResult:
        """财务质量检查 — 数字精确度要求极高"""
        score = result.get("quality_score", random.uniform(60, 100))
        # 财务数据必须精确核对
        details = f"财务核算评分: {score:.1f}"
        return QualityGateResult(score=score, passed=score >= self.quality_gate, details=details)

    async def consolidate(self, results: list[dict]) -> dict:
        return {
            "vp": self.name,
            "status": "completed",
            "summary": f"财务任务完成，共 {len(results)} 个子任务",
            "details": results,
            "quality_summary": {
                "avg_score": sum(r.get("quality", {}).get("score", 0) for r in results) / len(results) if results else 0,
                "passed_count": sum(1 for r in results if r.get("quality", {}).get("passed", False)),
                "total": len(results),
            },
        }


class VPStrategy(ManagerAgent):
    """
    VP战略 — 负责商业策略、市场调研与行业研究。
    子公司: 墨商(商业分析)、墨海(全球情报)、墨研(行业研究)
    """

    def __init__(self, subsidiary_configs: list[dict] | None = None):
        if subsidiary_configs is None:
            subsidiary_configs = [
                {"name": "墨商", "model": "claude-3-opus"},
                {"name": "墨海", "model": "deepseek-v4-pro"},
                {"name": "墨研", "model": "claude-3-sonnet"},
            ]
        super().__init__(
            name="VP战略",
            subsidiary_configs=subsidiary_configs,
            quality_gate=70.0,
            escalation_model="claude-3-opus",
        )

    async def dispatch_task(self, task: dict, context: dict) -> list[dict]:
        """战略任务分解"""
        content = task.get("content", "")

        sub_tasks: list[tuple[SubsidiaryAgent, dict]] = []

        for sub in self.subsidiaries:
            if sub.name == "墨商":
                sub_tasks.append((sub, {"action": "商业分析", "content": content, "analysis_type": task.get("analysis_type", "market")}))
            elif sub.name == "墨海":
                sub_tasks.append((sub, {"action": "全球情报", "content": content, "region": task.get("region", "global")}))
            elif sub.name == "墨研":
                sub_tasks.append((sub, {"action": "行业研究", "content": content, "industry": task.get("industry", "tech")}))

        return await self._run_all_subsidiaries(sub_tasks, context)

    async def quality_check(self, result: dict) -> QualityGateResult:
        """战略质量检查"""
        score = result.get("quality_score", random.uniform(60, 100))
        details = f"战略分析质量评分: {score:.1f}"
        return QualityGateResult(score=score, passed=score >= self.quality_gate, details=details)

    async def consolidate(self, results: list[dict]) -> dict:
        return {
            "vp": self.name,
            "status": "completed",
            "summary": f"战略任务完成，共 {len(results)} 个子任务",
            "details": results,
            "quality_summary": {
                "avg_score": sum(r.get("quality", {}).get("score", 0) for r in results) / len(results) if results else 0,
                "passed_count": sum(1 for r in results if r.get("quality", {}).get("passed", False)),
                "total": len(results),
            },
        }


# ---------------------------------------------------------------------------
# 简便工厂函数
# ---------------------------------------------------------------------------

def create_vp(vp_name: str, subsidiary_configs: list[dict] | None = None) -> ManagerAgent:
    """根据 VP 名称创建对应实例"""
    mapping = {
        "vp营销": VPMarketing,
        "vp运营": VPOps,
        "vp技术": VPTech,
        "vp财务": VPFinance,
        "vp战略": VPStrategy,
        "marketing": VPMarketing,
        "ops": VPOps,
        "tech": VPTech,
        "finance": VPFinance,
        "strategy": VPStrategy,
    }
    cls = mapping.get(vp_name.lower())
    if cls is None:
        raise ValueError(f"Unknown VP name: {vp_name!r}. Available: {list(mapping.keys())}")
    return cls(subsidiary_configs)
