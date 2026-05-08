"""molib.shared.ai.swarm_router — 专才路由编排器

吸收自 VRSEN/OpenSwarm (1.3K⭐)

核心模式：
  Orchestrator 不直接回答问题，只做三件事：
  1. 分析用户请求 → 确定需要哪些 Specialist
  2. 路由任务给 Specialist
  3. 汇聚 Specialist 输出为最终交付

与 multi_agent_orchestrator.py 互补：
  - Director-Actor: 课堂/辩论场景，多轮对话
  - SwarmRouter: 任务编排场景，单次请求 → 多专才并行/串行 → 交付

零外部依赖，仅使用 Python 标准库。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Optional


@dataclass
class Specialist:
    """专才 Agent 定义"""
    name: str
    role: str
    capabilities: list[str]
    description: str = ""
    priority: int = 0  # 越高越优先被选择

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TaskAssignment:
    """任务分派结果"""
    specialist: str
    task: str
    context: dict = field(default_factory=dict)


@dataclass
class SpecialistOutput:
    """专才输出"""
    specialist: str
    role: str
    result: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "specialist": self.specialist,
            "role": self.role,
            "has_result": self.result is not None,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


@dataclass
class SwarmDeliverable:
    """最终交付物"""
    request: str
    specialists_used: list[str]
    outputs: list[SpecialistOutput]
    summary: str
    timestamp: str = ""
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "request": self.request,
            "specialists_used": self.specialists_used,
            "output_count": len(self.outputs),
            "errors": [o.error for o in self.outputs if o.error],
            "total_duration_ms": self.total_duration_ms,
        }


class SwarmRouter:
    """专才路由编排器

    用法:
        router = SwarmRouter(dispatch_fn)
        router.register(Specialist(name="研究员", role="research", capabilities=["调研", "竞品分析"]))
        router.register(Specialist(name="写手", role="writing", capabilities=["写作", "文案"]))

        # 自动分析并路由
        deliverable = router.execute("帮我做竞品分析并写报告")
    """

    def __init__(self, dispatch_fn: Optional[Callable] = None):
        """
        Args:
            dispatch_fn: 执行任务的函数 fn(specialist_name, task, context) -> result
                         如果为 None，使用本地模拟执行
        """
        self._specialists: dict[str, Specialist] = {}
        self._dispatch_fn = dispatch_fn

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib swarm register --name 研究员 --role research --cap 调研,分析
    #   python -m molib swarm execute --request "做竞品分析报告"
    # ------------------------------------------------------------------

    def register(self, specialist: Specialist):
        """注册一个专才"""
        self._specialists[specialist.name] = specialist

    def register_many(self, specialists: list[Specialist]):
        """批量注册"""
        for s in specialists:
            self.register(s)

    def analyze(self, request: str) -> list[TaskAssignment]:
        """分析请求 → 确定需要哪些专才

        Returns:
            TaskAssignment 列表 (有序，按依赖顺序)
        """
        if not self._specialists:
            return []

        request_lower = request.lower()
        assignments: list[TaskAssignment] = []
        assigned: set[str] = set()

        # 按优先级排序
        sorted_specs = sorted(
            self._specialists.values(),
            key=lambda s: s.priority,
            reverse=True,
        )

        for spec in sorted_specs:
            if spec.name in assigned:
                continue

            # 检查能力是否匹配请求
            match_score = self._match_score(request_lower, spec)
            if match_score < 0.15:
                continue

            # 构建任务上下文
            context = self._build_context(request, spec, match_score)
            assignments.append(TaskAssignment(
                specialist=spec.name,
                task=f"作为{spec.role}({spec.name})，处理请求: {request}",
                context=context,
            ))
            assigned.add(spec.name)

            # 最多选 3 个最匹配的
            if len(assignments) >= 3:
                break

        return assignments

    def _match_score(self, request_lower: str, spec: Specialist) -> float:
        """计算请求与专才的匹配度"""
        score = 0.0
        weights = 0.0

        # 能力关键词匹配
        for cap in spec.capabilities:
            if cap in request_lower:
                score += 1.0
            else:
                # 部分匹配
                for word in cap.split():
                    if len(word) > 1 and word in request_lower:
                        score += 0.5
                        break
            weights += 1.0

        # 角色名匹配
        if spec.role in request_lower:
            score += 1.0
        weights += 1.0

        # 专才名匹配
        if spec.name in request_lower:
            score += 0.5
        weights += 0.5

        return score / max(weights, 1.0)

    def _build_context(self, request: str, spec: Specialist,
                       match_score: float) -> dict:
        """构建任务上下文"""
        return {
            "request": request,
            "role": spec.role,
            "capabilities": spec.capabilities,
            "match_score": round(match_score, 2),
        }

    def execute(self, request: str) -> SwarmDeliverable:
        """执行完整请求

        1. 分析 → 确定专才
        2. 路由 → 分发任务（串行，依赖前序结果）
        3. 汇聚 → 生成最终交付

        Args:
            request: 用户请求

        Returns:
            SwarmDeliverable
        """
        import datetime

        start = time.time()
        assignments = self.analyze(request)

        outputs: list[SpecialistOutput] = []
        context_pool: dict[str, Any] = {"request": request}

        for assignment in assignments:
            task_start = time.time()
            try:
                # 注入前序结果作为上下文
                enriched_context = {**assignment.context, **context_pool}

                if self._dispatch_fn:
                    result = self._dispatch_fn(
                        assignment.specialist,
                        assignment.task,
                        enriched_context,
                    )
                else:
                    result = self._local_execute(assignment)

                duration = (time.time() - task_start) * 1000
                outputs.append(SpecialistOutput(
                    specialist=assignment.specialist,
                    role=self._specialists[assignment.specialist].role,
                    result=result,
                    duration_ms=round(duration, 1),
                ))
                context_pool[f"{assignment.specialist}_result"] = result

            except Exception as e:
                duration = (time.time() - task_start) * 1000
                outputs.append(SpecialistOutput(
                    specialist=assignment.specialist,
                    role=self._specialists.get(assignment.specialist, Specialist("?","?",[])).role,
                    error=str(e),
                    duration_ms=round(duration, 1),
                ))

        total_duration = (time.time() - start) * 1000
        specialists_used = [a.specialist for a in assignments]

        return SwarmDeliverable(
            request=request,
            specialists_used=specialists_used,
            outputs=outputs,
            summary=self._generate_summary(request, outputs),
            timestamp=datetime.datetime.now().isoformat(),
            total_duration_ms=round(total_duration, 1),
        )

    def _local_execute(self, assignment: TaskAssignment) -> str:
        """本地模拟执行（无 dispatch_fn 时的 fallback）"""
        spec = self._specialists.get(assignment.specialist)
        if not spec:
            return f"(未注册专才: {assignment.specialist})"

        return f"[{spec.role}] {spec.name} 正在处理: {assignment.task[:60]}..."

    def _generate_summary(self, request: str, outputs: list[SpecialistOutput]) -> str:
        """生成最终摘要"""
        parts = [f"请求: {request}"]
        for o in outputs:
            if o.error:
                parts.append(f"  ❌ {o.specialist}: 错误 - {o.error}")
            else:
                parts.append(f"  ✅ {o.specialist}: 完成 ({o.duration_ms:.0f}ms)")
        return "\n".join(parts)


# ─── 快速构建器 ─────────────────────────────────────────────────────

DEFAULT_SPECIALISTS = [
    Specialist(name="研究员", role="research",
               capabilities=["调研", "竞品分析", "数据采集", "趋势研究"],
               description="深度网络调研，带引用"),
    Specialist(name="分析师", role="analyst",
               capabilities=["数据分析", "图表", "统计模型", "报告"],
               description="结构化数据分析与可视化",
               priority=1),
    Specialist(name="写手", role="writing",
               capabilities=["写作", "文案", "内容创作", "博客", "SEO"],
               description="高质量文案与内容输出"),
    Specialist(name="设计师", role="design",
               capabilities=["设计", "图片", "封面", "视觉"],
               description="视觉设计与图表生成"),
    Specialist(name="助理", role="assistant",
               capabilities=["日程", "消息", "任务管理", "协作"],
               description="日常事务处理"),
]


def create_default_swarm(dispatch_fn: Optional[Callable] = None) -> SwarmRouter:
    """创建默认 Swarm（研究员+分析师+写手+设计师+助理）"""
    router = SwarmRouter(dispatch_fn)
    router.register_many(DEFAULT_SPECIALISTS)
    return router
