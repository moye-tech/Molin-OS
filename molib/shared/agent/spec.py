"""
墨麟 — Spec 引擎 (Immutable Seed)
从 Ouroboros (Q00/ouroboros) 提取的 Spec-first 模式。

Spec 是 Agent 任务的不可变"宪法"——在生成后不可修改，
所有执行和评估都基于这个基准。

用法:
    from molib.shared.agent.spec import Seed, SeedContract

    seed = Seed(
        goal="开发一个AI封面生成器",
        constraints=["仅用Python", "单文件", "使用千问API"],
        acceptance_criteria=["生成PNG输出", "支持中文文本"],
        priority="P0",
    )
    contract = SeedContract(seed)
    if contract.check_ambiguity() <= 0.2:
        tasks = contract.decompose_into_tasks()
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime, timezone


# ── 不可变规范 ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Seed:
    """
    不可变任务规范 — 一旦生成不可修改。

    frozen=True 确保所有字段在初始化后只读，
    防止 Agent 在运行时变更任务定义。
    """

    goal: str
    """任务的核心目标描述"""

    constraints: List[str] = field(default_factory=list)
    """约束列表 — 技术栈/预算/时间/范围限制"""

    acceptance_criteria: List[str] = field(default_factory=list)
    """验收标准列表 — 完成任务的判断依据"""

    priority: str = "P1"
    """优先级: P0(立即) / P1(本周) / P2(本月) / P3(长期)"""

    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    """创建时间 (ISO 8601)"""

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "goal": self.goal,
            "constraints": list(self.constraints),
            "acceptance_criteria": list(self.acceptance_criteria),
            "priority": self.priority,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Seed":
        """从字典反序列化"""
        return cls(
            goal=data["goal"],
            constraints=data.get("constraints", []),
            acceptance_criteria=data.get("acceptance_criteria", []),
            priority=data.get("priority", "P1"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Seed":
        """从 JSON 字符串反序列化"""
        return cls.from_dict(json.loads(json_str))


# ── 规范运行时解释层 ──────────────────────────────────────────────


class SeedContract:
    """Seed 的运行时解释层 — 将不可变规范转化为可执行的任务分解"""

    def __init__(self, seed: Seed):
        self._seed = seed

    @property
    def seed(self) -> Seed:
        """获取底层 Seed（只读）"""
        return self._seed

    def check_ambiguity(self) -> float:
        """
        评估目标的模糊程度。

        返回 0.0-1.0 的分数:
        - <= 0.2: 足够清晰，可直接执行
        - 0.2-0.5: 需要更多澄清
        - > 0.5: 过于模糊，需要重新定义

        评估维度:
        - 目标长度和关键信息密度
        - 约束数量和具体程度
        - 验收标准的可测量性
        """
        ambiguity = 0.0
        goal = self._seed.goal.strip()
        constraints = self._seed.constraints
        criteria = self._seed.acceptance_criteria

        # 目标维度 (权重 0.5)
        if len(goal) < 10:
            ambiguity += 0.3
        elif len(goal) < 30:
            ambiguity += 0.1

        has_verb = any(w in goal for w in ["开发", "创建", "生成", "实现", "设计", "写", "分析", "研究"])
        has_object = any(m in goal for m in ["系统", "工具", "脚本", "方案", "报告", "应用", "平台"])
        if not (has_verb and has_object):
            ambiguity += 0.2

        # 约束维度 (权重 0.3)
        if not constraints:
            ambiguity += 0.2
        elif len(constraints) < 2:
            ambiguity += 0.1

        specific_constraints = sum(
            1 for c in constraints
            if any(kw in c for kw in ["Python", "API", "¥", "元", "天", "小时", "GB", "MB"])
        )
        if specific_constraints == 0:
            ambiguity += 0.1

        # 验收标准维度 (权重 0.2)
        if not criteria:
            ambiguity += 0.2
        elif len(criteria) < 2:
            ambiguity += 0.1

        measurable = sum(
            1 for c in criteria
            if any(kw in c for kw in ["输出", "生成", "格式", "支持", "包含", "显示", "返回"])
        )
        if measurable == 0:
            ambiguity += 0.1

        return round(min(ambiguity, 1.0), 2)

    def decompose_into_tasks(self, max_depth: int = 3) -> List[dict]:
        """
        将 Seed 分解为可执行的子任务列表。

        参数:
            max_depth: 最大分解深度

        返回:
            List[dict] — 每个 dict 包含:
                - id: str (层级编号)
                - description: str (任务描述)
                - depends_on: List[str] (依赖的任务ID)
                - estimated_effort: str (估算工作量)
        """
        tasks = []
        goal = self._seed.goal
        constraints = self._seed.constraints
        criteria = self._seed.acceptance_criteria

        # 第1级: 通用分解模板
        task_id = 0

        # T1: 需求分析
        task_id += 1
        tasks.append({
            "id": f"T{task_id}",
            "description": f"需求分析: {goal}",
            "depends_on": [],
            "estimated_effort": "1h",
            "acceptance": f"明确{goal}的技术方案和实现路径",
        })

        # T2: 核心开发
        task_id += 1
        tech_stack = "、".join(constraints) if constraints else "按系统默认技术栈"
        tasks.append({
            "id": f"T{task_id}",
            "description": f"核心开发: 基于需求分析结果实现 {goal}",
            "depends_on": ["T1"],
            "estimated_effort": "4h",
            "acceptance": f"使用 {tech_stack}，满足 {len(criteria)} 项验收标准",
        })

        # T3: 测试验证
        task_id += 1
        criteria_desc = "、".join(criteria) if criteria else "功能完整性"
        tasks.append({
            "id": f"T{task_id}",
            "description": f"测试验证: 验证 {criteria_desc}",
            "depends_on": ["T2"],
            "estimated_effort": "1h",
            "acceptance": f"全部验收标准通过",
        })

        # T4: 交付
        task_id += 1
        tasks.append({
            "id": f"T{task_id}",
            "description": f"交付与文档: 输出最终产物和使用说明",
            "depends_on": ["T3"],
            "estimated_effort": "0.5h",
            "acceptance": "产物可部署、文档完整",
        })

        return tasks

    def estimate_total_effort(self) -> str:
        """估算总工作量"""
        tasks = self.decompose_into_tasks()
        total_minutes = 0
        for t in tasks:
            effort = t.get("estimated_effort", "1h")
            if effort.endswith("h") and "." in effort:
                total_minutes += int(float(effort[:-1]) * 60)
            elif effort.endswith("h"):
                total_minutes += int(effort[:-1]) * 60
            elif effort.endswith("min"):
                total_minutes += int(effort[:-3])
            elif effort.endswith("d"):
                total_minutes += int(effort[:-1]) * 480
        hours = total_minutes // 60
        mins = total_minutes % 60
        if hours > 0:
            return f"{hours}h{mins}min" if mins else f"{hours}h"
        return f"{mins}min"
