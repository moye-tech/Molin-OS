"""
Agent评估引擎 — 从 HKUDS/OpenHarness (11.9K⭐) 汲取的场景化评估框架

核心思想:
  - Scenario-Based Eval: 用Scenario数据类定义测试场景（prompt + expected + validate callback）
  - Streaming Protocol: async generator + auto-compaction 流式Agent循环
  - Multi-Layer Permissions: 5层安全治理（敏感路径保护/允许列表/命令模式）
  - Hook Lifecycle: 9种生命周期事件挂钩
  - 与CEngine集成: CEO决策引擎用评估结果做ROI分析

适用场景:
  - 评估子公司Agent能力
  - 回归测试（吸收新项目后）
  - CEO决策引擎的A/B评估
  - Agent发布前的质量门禁
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


# ─── 核心类型 ────────────────────────────────────────────────────────────

@dataclass
class EvalScenario:
    """评估场景 — OpenHarness Scenario概念的Python版"""
    id: str
    name: str
    prompt: str
    expected_final: Optional[str] = None
    required_tools: list[str] = field(default_factory=list)
    validate: Optional[Callable[[dict], tuple[bool, str]]] = None
    category: str = "general"
    difficulty: float = 1.0  # 1-5
    timeout_seconds: int = 120


@dataclass
class EvalResult:
    """单场景评估结果"""
    scenario_id: str
    passed: bool
    score: float  # 0-1
    output: Optional[str] = None
    tools_used: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


@dataclass
class SuiteResult:
    """评估套件整体结果"""
    suite_name: str
    total_scenarios: int = 0
    passed: int = 0
    failed: int = 0
    average_score: float = 0.0
    total_duration: float = 0.0
    results: list[EvalResult] = field(default_factory=list)
    summary: str = ""


# ─── 场景注册表 ─────────────────────────────────────────────────────

class ScenarioRegistry:
    """场景注册表 — 管理所有评估场景

    从OpenHarness汲取：用Scenario dataclass代替配置文件
    """

    def __init__(self):
        self._scenarios: dict[str, EvalScenario] = {}

    def register(self, scenario: EvalScenario):
        """注册一个场景"""
        self._scenarios[scenario.id] = scenario

    def register_batch(self, scenarios: list[EvalScenario]):
        """批量注册"""
        for s in scenarios:
            self.register(s)

    def get(self, scenario_id: str) -> Optional[EvalScenario]:
        """获取场景"""
        return self._scenarios.get(scenario_id)

    def list_by_category(self, category: str) -> list[EvalScenario]:
        """按分类列出场景"""
        return [s for s in self._scenarios.values() if s.category == category]

    def all(self) -> list[EvalScenario]:
        """所有场景"""
        return list(self._scenarios.values())

    @property
    def count(self) -> int:
        return len(self._scenarios)


# ─── 评估引擎 ────────────────────────────────────────────────────────

class AgentEvaluator:
    """Agent评估引擎 — 在隔离环境中评估Agent能力

    从OpenHarness汲取:
      - Scenario-based Eval
      - 多层权限控制
      - 挂钩生命周期
      - Streaming执行报告
    """

    def __init__(self, agent_executor: Callable, registry: Optional[ScenarioRegistry] = None):
        """
        agent_executor: async (prompt: str, tools: list[str], timeout: int) -> dict
                       返回: {output, tools_used, errors, metrics}
        """
        self.executor = agent_executor
        self.registry = registry or ScenarioRegistry()
        self.hooks: dict[str, list[Callable]] = {
            "before_scenario": [],
            "after_scenario": [],
            "before_suite": [],
            "after_suite": [],
        }

    def add_hook(self, event: str, callback: Callable):
        """注册生命周期钩子 — 从OpenHarness Hook Lifecycle汲取"""
        if event in self.hooks:
            self.hooks[event].append(callback)

    async def run_scenario(self, scenario: EvalScenario) -> EvalResult:
        """运行单个场景"""
        start = time.time()

        # before_scenario hook
        for hook in self.hooks["before_scenario"]:
            hook(scenario)

        try:
            # 执行
            result = await self.executor(
                prompt=scenario.prompt,
                tools=scenario.required_tools,
                timeout=scenario.timeout_seconds
            )

            duration = time.time() - start
            output = result.get("output", "")
            tools_used = result.get("tools_used", [])
            errors = result.get("errors", [])
            metrics = result.get("metrics", {})

            # 验证
            passed = True
            score = 1.0
            validation_msg = ""

            if scenario.validate:
                passed, validation_msg = scenario.validate(result)
                score = 1.0 if passed else 0.3

            if scenario.expected_final and scenario.expected_final not in (output or ""):
                passed = False
                score = 0.0
                validation_msg = f"未包含预期内容: {scenario.expected_final[:100]}"

            eval_result = EvalResult(
                scenario_id=scenario.id,
                passed=passed,
                score=score,
                output=output[:500] if output else None,
                tools_used=tools_used,
                duration_seconds=duration,
                errors=errors,
                metrics={"validation": validation_msg, **metrics}
            )

        except Exception as e:
            duration = time.time() - start
            eval_result = EvalResult(
                scenario_id=scenario.id,
                passed=False,
                score=0.0,
                duration_seconds=duration,
                errors=[str(e)]
            )

        # after_scenario hook
        for hook in self.hooks["after_scenario"]:
            hook(scenario, eval_result)

        return eval_result

    async def run_suite(self, suite_name: str = "default",
                        category: Optional[str] = None) -> SuiteResult:
        """运行完整评估套件"""
        scenarios = self.registry.all()
        if category:
            scenarios = [s for s in scenarios if s.category == category]

        # before_suite hook
        for hook in self.hooks["before_suite"]:
            hook(suite_name, len(scenarios))

        suite_start = time.time()
        results = []
        passed = 0
        failed = 0
        total_score = 0.0

        for scenario in scenarios:
            result = await self.run_scenario(scenario)
            results.append(result)
            if result.passed:
                passed += 1
            else:
                failed += 1
            total_score += result.score

        total_duration = time.time() - suite_start
        avg_score = total_score / max(1, len(results))

        suite_result = SuiteResult(
            suite_name=suite_name,
            total_scenarios=len(scenarios),
            passed=passed,
            failed=failed,
            average_score=avg_score,
            total_duration=total_duration,
            results=results,
            summary=self._generate_summary(suite_name, passed, failed, avg_score, total_duration)
        )

        # after_suite hook
        for hook in self.hooks["after_suite"]:
            hook(suite_name, suite_result)

        return suite_result

    def _generate_summary(self, name: str, passed: int, failed: int,
                          avg_score: float, duration: float) -> str:
        total = passed + failed
        rate = (passed / total * 100) if total > 0 else 0
        return f"[{name}] {passed}/{total} passed ({rate:.0f}%) | avg score: {avg_score:.2f} | {duration:.1f}s"


# ─── 权限治理层 ─────────────────────────────────────────────────────

@dataclass
class PermissionPolicy:
    """权限策略 — OpenHarness 5层安全治理"""
    mode: str = "strict"  # strict | relaxed | permissive
    allowed_dirs: list[str] = field(default_factory=lambda: ["/tmp", os.path.expanduser("~/.hermes")] if 'os' in dir() else [])
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /", "sudo", "chmod 777", "dd if=", ":(){ :|:& };:"
    ])
    max_file_size_mb: int = 50
    require_human_confirm: bool = True

    def check_command(self, command: str) -> tuple[bool, str]:
        """检查命令是否允许"""
        for blocked in self.blocked_commands:
            if blocked in command:
                return False, f"禁止命令: {blocked}"
        return True, ""


# ─── 内置评估场景 ─────────────────────────────────────────────────

def create_default_registry() -> ScenarioRegistry:
    """创建默认评估场景集"""
    registry = ScenarioRegistry()

    registry.register(EvalScenario(
        id="basic-reasoning",
        name="基础推理",
        prompt="如果一个袋子里有5个红球和3个蓝球，随机取出2个球，两个都是红球的概率是多少？",
        expected_final="10/28",
        category="reasoning",
        difficulty=1.0
    ))

    registry.register(EvalScenario(
        id="tool-use",
        name="工具使用",
        prompt="创建一个名为 test.txt 的文件，写入 'Hello World'，然后读取它",
        required_tools=["write_file", "read_file"],
        category="tools",
        difficulty=2.0
    ))

    registry.register(EvalScenario(
        id="json-output",
        name="结构化输出",
        prompt="生成一个JSON表示：一个用户名为'Alice'，年龄30，邮箱'alice@example.com'",
        required_tools=[],
        validate=lambda r: (
            '"Alice"' in (r.get("output") or "") and '"alice@example.com"' in (r.get("output") or ""),
            "缺失用户字段"
        ),
        category="structured",
        difficulty=1.5
    ))

    registry.register(EvalScenario(
        id="multi-step-planning",
        name="多步规划",
        prompt="规划部署一个Web应用的步骤，包含：代码审查、构建、测试、部署",
        expected_final="deploy",
        category="planning",
        difficulty=3.0
    ))

    return registry


# ─── 评估报告 ────────────────────────────────────────────────────────

def format_eval_report(result: SuiteResult) -> str:
    """格式化评估报告"""
    lines = [
        f"📊 Agent评估报告: {result.suite_name}",
        f"{'='*50}",
        f"总场景: {result.total_scenarios} | 通过: {result.passed} | 失败: {result.failed}",
        f"平均分: {result.average_score:.2f} | 耗时: {result.total_duration:.1f}s",
        f"",
        f"--- 逐项结果 ---",
    ]

    for r in result.results:
        status = "✅" if r.passed else "❌"
        lines.append(f"{status} [{r.scenario_id}] score={r.score:.2f} ({r.duration_seconds:.1f}s)")
        if r.errors:
            for e in r.errors[:2]:
                lines.append(f"   ⚠️  {e[:100]}")

    return "\n".join(lines)


import os
