"""
墨麟OS — Paperclip DAG 任务编排引擎
=====================================
从蓝图概念代码化，将复杂任务分解为有向无环图，
支持依赖关系、并行标记、超时配置、拓扑排序。

输入: IntentResult  → 输出: list[DAGTask] (已排序、已标记依赖)

用法:
    dag = DAGEngine()
    tasks = dag.decompose(intent_result)
    # tasks 已拓扑排序，ready=True 表示可立即执行
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("molin.ceo.dag")

# ── 任务复杂度与分解策略 ──────────────────────────────────────────
# 当 complexity_score 超过阈值时启用多步分解

SIMPLE_THRESHOLD = 30    # 简单任务: 单步执行
MEDIUM_THRESHOLD = 60     # 中等任务: 2-3步
COMPLEX_THRESHOLD = 80    # 复杂任务: 多步+依赖

# 各意图类型的默认分解策略
INTENT_DECOMPOSITION_MAP: dict[str, list[dict]] = {
    "content": [
        {"step": "research", "desc": "调研与素材收集", "depends_on": []},
        {"step": "draft", "desc": "内容撰写", "depends_on": ["research"]},
        {"step": "review", "desc": "质量审核", "depends_on": ["draft"]},
        {"step": "publish", "desc": "发布推送", "depends_on": ["review"]},
    ],
    "marketing": [
        {"step": "research", "desc": "市场分析", "depends_on": []},
        {"step": "strategy", "desc": "策略制定", "depends_on": ["research"]},
        {"step": "content", "desc": "物料生产", "depends_on": ["strategy"]},
        {"step": "launch", "desc": "投放执行", "depends_on": ["content"]},
        {"step": "monitor", "desc": "效果监控", "depends_on": ["launch"]},
    ],
    "analysis": [
        {"step": "collect", "desc": "数据采集", "depends_on": []},
        {"step": "process", "desc": "数据处理", "depends_on": ["collect"]},
        {"step": "analyze", "desc": "分析建模", "depends_on": ["process"]},
        {"step": "report", "desc": "报告生成", "depends_on": ["analyze"]},
    ],
    "development": [
        {"step": "requirements", "desc": "需求分析", "depends_on": []},
        {"step": "design", "desc": "方案设计", "depends_on": ["requirements"]},
        {"step": "implement", "desc": "编码实现", "depends_on": ["design"]},
        {"step": "test", "desc": "测试验证", "depends_on": ["implement"]},
        {"step": "deploy", "desc": "部署上线", "depends_on": ["test"]},
    ],
    "operation": [
        {"step": "diagnose", "desc": "问题诊断", "depends_on": []},
        {"step": "plan", "desc": "处理方案", "depends_on": ["diagnose"]},
        {"step": "execute", "desc": "执行操作", "depends_on": ["plan"]},
        {"step": "verify", "desc": "结果验证", "depends_on": ["execute"]},
    ],
    "strategy": [
        {"step": "scan", "desc": "环境扫描", "depends_on": []},
        {"step": "analysis", "desc": "深度分析", "depends_on": ["scan"]},
        {"step": "proposal", "desc": "方案拟定", "depends_on": ["analysis"]},
        {"step": "review", "desc": "评审修订", "depends_on": ["proposal"]},
    ],
    "finance": [
        {"step": "collect", "desc": "财务数据收集", "depends_on": []},
        {"step": "calculate", "desc": "核算统计", "depends_on": ["collect"]},
        {"step": "analyze", "desc": "财务分析", "depends_on": ["calculate"]},
        {"step": "report", "desc": "报表输出", "depends_on": ["analyze"]},
    ],
    "legal": [
        {"step": "document_review", "desc": "文档审查", "depends_on": []},
        {"step": "risk_analysis", "desc": "风险分析", "depends_on": ["document_review"]},
        {"step": "recommendation", "desc": "建议输出", "depends_on": ["risk_analysis"]},
    ],
}

# 通用兜底策略
FALLBACK_STEPS = [
    {"step": "understand", "desc": "需求理解", "depends_on": []},
    {"step": "execute", "desc": "任务执行", "depends_on": ["understand"]},
    {"step": "verify", "desc": "结果验证", "depends_on": ["execute"]},
]


@dataclass
class DAGTask:
    """DAG中的单个任务节点"""
    step_id: str               # 步骤标识符
    description: str           # 步骤描述
    depends_on: list[str]      # 依赖的上一步步ID列表
    assigned_vp: str = ""      # 负责的VP
    assigned_subsidiary: str = ""  # 负责的子公司
    timeout_seconds: int = 300  # 超时时间
    model_tier: str = "turbo"  # 模型等级 (turbo/plus/max/long)
    status: str = "pending"    # pending | running | completed | failed | skipped
    ready: bool = False        # 依赖是否全部满足
    result: dict | None = None # 执行结果


@dataclass
class DAGResult:
    """DAG分解的完整结果"""
    tasks: list[DAGTask]        # 已排序的任务列表
    parallel_groups: list[list[int]] = field(default_factory=list)  # 可并行的任务组(索引)
    total_sp: int = 300         # 预估总耗时(秒)
    description: str = ""       # 任务描述
    intent_type: str = ""       # 意图类型


class DAGEngine:
    """
    Paperclip DAG 引擎。

    将 IntentResult 分解为带依赖关系的任务序列，
    支持拓扑排序、并行组检测、超时配置。
    """

    def __init__(self):
        self._steps_cache: dict[str, list[dict]] = {}

    def decompose(
        self,
        intent_type: str,
        target_vps: list[str],
        target_subsidiaries: list[str],
        complexity_score: float,
        entities: dict[str, Any] | None = None,
        description: str = "",
    ) -> DAGResult:
        """
        将意图分解为DAG任务列表。

        参数:
            intent_type: 意图类型
            target_vps: 目标VP列表
            target_subsidiaries: 目标子公司列表
            complexity_score: 复杂度 (0-100)
            entities: 提取的实体信息
            description: 任务描述

        返回:
            DAGResult — 包含排序后的任务列表和并行组
        """
        # 1. 选择分解策略
        steps = self._get_steps(intent_type, complexity_score)

        # 2. 构建任务节点
        tasks = self._build_tasks(steps, target_vps, target_subsidiaries)

        # 3. 拓扑排序 + 标记就绪状态
        tasks = self._topological_sort(tasks)
        tasks = self._mark_ready(tasks)

        # 4. 检测并行组
        parallel_groups = self._detect_parallel_groups(tasks)

        # 5. 估算总耗时
        total_sp = self._estimate_duration(tasks)

        # 6. 根据目标子公司分配模型等级
        tasks = self._assign_model_tiers(tasks, complexity_score, target_subsidiaries)

        return DAGResult(
            tasks=tasks,
            parallel_groups=parallel_groups,
            total_sp=total_sp,
            description=description or f"意图类型: {intent_type}",
            intent_type=intent_type,
        )

    def _get_steps(self, intent_type: str, complexity: float) -> list[dict]:
        """根据意图类型和复杂度选择分解策略"""
        # 低复杂度 → 简化
        if complexity < SIMPLE_THRESHOLD:
            return [
                {"step": "execute", "desc": "直接执行", "depends_on": []},
            ]

        # 高复杂度 → 详细
        if complexity > COMPLEX_THRESHOLD:
            steps = INTENT_DECOMPOSITION_MAP.get(intent_type, FALLBACK_STEPS)
            # 高复杂度任务添加复盘步骤
            return steps + [{"step": "retrospect", "desc": "任务复盘", "depends_on": [steps[-1]["step"]]}]

        # 中等复杂度 → 标准流程
        return INTENT_DECOMPOSITION_MAP.get(intent_type, FALLBACK_STEPS)

    def _build_tasks(
        self,
        steps: list[dict],
        target_vps: list[str],
        target_subsidiaries: list[str],
    ) -> list[DAGTask]:
        """从步骤定义构建DAGTask列表"""
        tasks: list[DAGTask] = []
        for i, step in enumerate(steps):
            vp = ""
            sub = ""

            # 尝试分配负责的VP和子公司
            if target_subsidiaries:
                idx = i % len(target_subsidiaries)
                sub = target_subsidiaries[idx]
            if target_vps:
                idx = i % len(target_vps)
                vp = target_vps[idx]

            tasks.append(DAGTask(
                step_id=step["step"],
                description=step["desc"],
                depends_on=step.get("depends_on", []),
                assigned_vp=vp,
                assigned_subsidiary=sub,
            ))
        return tasks

    def _topological_sort(self, tasks: list[DAGTask]) -> list[DAGTask]:
        """拓扑排序：保证依赖在前，被依赖在后"""
        # 构建依赖关系图
        step_map = {t.step_id: t for t in tasks}
        sorted_tasks: list[DAGTask] = []
        visited: set[str] = set()

        def dfs(step_id: str):
            if step_id in visited:
                return
            visited.add(step_id)
            task = step_map.get(step_id)
            if not task:
                return
            for dep in task.depends_on:
                if dep in step_map:
                    dfs(dep)
            sorted_tasks.append(task)

        for task in tasks:
            dfs(task.step_id)

        return sorted_tasks

    def _mark_ready(self, tasks: list[DAGTask]) -> list[DAGTask]:
        """标记哪些任务可以立即执行（依赖已全部完成）"""
        completed: set[str] = set()
        for task in tasks:
            if not task.depends_on or all(d in completed for d in task.depends_on):
                task.ready = True
            completed.add(task.step_id)
        return tasks

    def _detect_parallel_groups(self, tasks: list[DAGTask]) -> list[list[int]]:
        """检测可并行的任务组（无依赖关系的同级任务）"""
        groups: list[list[int]] = []
        current_group: list[int] = []
        completed: set[str] = set()

        for i, task in enumerate(tasks):
            if not task.depends_on or all(d in completed for d in task.depends_on):
                current_group.append(i)
            else:
                if current_group:
                    groups.append(current_group)
                current_group = [i]
            completed.add(task.step_id)

        if current_group:
            groups.append(current_group)

        return groups

    def _estimate_duration(self, tasks: list[DAGTask]) -> int:
        """估算任务总耗时（秒）"""
        # 简单估算：每个步骤约60秒
        return len(tasks) * 60

    def _assign_model_tiers(
        self,
        tasks: list[DAGTask],
        complexity: float,
        target_subsidiaries: list[str],
    ) -> list[DAGTask]:
        """根据复杂度和子公司分配模型等级"""
        # 等级: turbo(最便宜) → plus → max(最贵) → long(长文本)
        for task in tasks:
            if complexity >= COMPLEX_THRESHOLD and task.step_id in ("analysis", "strategy", "review", "retrospect"):
                task.model_tier = "max"
            elif complexity >= MEDIUM_THRESHOLD and task.step_id in ("draft", "proposal", "analyze", "design"):
                task.model_tier = "plus"
            elif task.step_id in ("document_review", "report"):
                task.model_tier = "long"
            else:
                task.model_tier = "turbo"
        return tasks

    def get_executable_tasks(self, tasks: list[DAGTask]) -> list[DAGTask]:
        """获取当前可执行的任务列表（ready=True且pending状态）"""
        return [t for t in tasks if t.ready and t.status == "pending"]

    def mark_completed(self, tasks: list[DAGTask], step_id: str, result: dict | None = None) -> list[DAGTask]:
        """标记某步已完成，更新后续任务的ready状态"""
        for task in tasks:
            if task.step_id == step_id:
                task.status = "completed"
                task.result = result
                break

        # 重新计算ready
        completed = {t.step_id for t in tasks if t.status == "completed"}
        for task in tasks:
            if task.status == "pending":
                task.ready = bool(
                    not task.depends_on or
                    all(d in completed for d in task.depends_on)
                )
        return tasks

    def format_dag_string(self, result: DAGResult) -> str:
        """格式化输出DAG为可读字符串（用于日志和看板）"""
        lines = [f"📋 DAG: {result.description} ({result.intent_type})"]
        lines.append(f"   预估耗时: {result.total_sp}s | 并行组: {len(result.parallel_groups)}")

        for i, task in enumerate(result.tasks):
            status_icon = {
                "pending": "⏳", "running": "▶️",
                "completed": "✅", "failed": "❌", "skipped": "⏭️",
            }.get(task.status, "⏳")
            deps = f" ← {','.join(task.depends_on)}" if task.depends_on else ""
            ready_mark = " ✓" if task.ready else ""
            lines.append(f"  {status_icon} [{i}] {task.step_id}: {task.description}{deps}{ready_mark}")

        if result.parallel_groups:
            lines.append(f"   并行组: {[[result.tasks[j].step_id for j in g] for g in result.parallel_groups]}")

        return "\n".join(lines)
