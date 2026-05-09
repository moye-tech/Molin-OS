#!/usr/bin/env python3
"""
Agent Collaboration — Three-Layer Agent Architecture
=====================================================
Inspired by HBAI-Ltd/Toonflow's multi-agent collaboration design.

Three-layer architecture:
  1. ScriptAgent (规划层) — analyze_text(), generate_script()
     Analyzes input, produces structured plans/scripts.

  2. ProductionAgent (执行层) — decompose_task(), dispatch_steps()
     Breaks plans into executable steps, dispatches to workers.

  3. ReviewAgent (质检层) — check_quality(), retry_strategy()
     Validates outputs, handles failures with retry strategies.

Usage:
    python -m molib.agencies.agent_collab --mode pipeline --input "为孩子设计一个思维训练方案"
    python -m molib.agencies.agent_collab --mode script --input "分析用户需求"
    python -m molib.agencies.agent_collab --mode review --input '{"task":"设计","result":"..."}'
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

logger = logging.getLogger("agent_collab")


# ── Data Models ──────────────────────────────────────────────────────────────


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class ScriptOutput:
    """Structured output from ScriptAgent."""
    title: str = ""
    description: str = ""
    objectives: list[str] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    estimated_duration: str = ""
    complexity: str = "medium"  # low | medium | high
    raw_text: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskStep:
    """A single executable step from ProductionAgent."""
    step_id: str = ""
    step_name: str = ""
    step_type: str = "analysis"  # analysis | generation | validation | execution
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    assigned_to: str = ""
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    retry_count: int = 0
    max_retries: int = 3
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


@dataclass
class ProductionOutput:
    """Structured output from ProductionAgent."""
    task_id: str = ""
    steps: list[TaskStep] = field(default_factory=list)
    completed_steps: int = 0
    total_steps: int = 0
    all_success: bool = False
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "steps": [s.to_dict() for s in self.steps],
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "all_success": self.all_success,
            "total_duration_ms": self.total_duration_ms,
        }


@dataclass
class ReviewOutput:
    """Structured output from ReviewAgent."""
    passed: bool = False
    score: float = 0.0
    issues: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    verdict: str = ""  # pass | fail | needs_revision
    retry_needed: bool = False
    retry_strategy: str = ""  # full | partial | skip
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    """End-to-end pipeline result."""
    success: bool = False
    script: ScriptOutput | None = None
    production: ProductionOutput | None = None
    review: ReviewOutput | None = None
    input_text: str = ""
    duration_ms: float = 0.0
    iterations: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "script": self.script.to_dict() if self.script else None,
            "production": self.production.to_dict() if self.production else None,
            "review": self.review.to_dict() if self.review else None,
            "input_text": self.input_text[:200],
            "duration_ms": self.duration_ms,
            "iterations": self.iterations,
        }


# ── Domain Knowledge ─────────────────────────────────────────────────────────

DOMAIN_KEYWORDS: dict[str, dict[str, Any]] = {
    "教育": {
        "keywords": ["教育", "学习", "培训", "课程", "学生", "教师", "思维", "训练"],
        "complexity": "high",
        "typical_steps": [
            "需求分析", "目标设定", "内容规划", "教学方法设计",
            "评估标准制定", "反馈机制设计",
        ],
    },
    "设计": {
        "keywords": ["设计", "创意", "视觉", "UI", "UX", "封面", "海报", "品牌"],
        "complexity": "medium",
        "typical_steps": [
            "需求收集", "竞品分析", "概念设计", "原型制作",
            "用户测试", "迭代优化",
        ],
    },
    "开发": {
        "keywords": ["开发", "编程", "代码", "应用", "系统", "API", "数据库"],
        "complexity": "high",
        "typical_steps": [
            "需求分析", "架构设计", "模块开发", "单元测试",
            "集成测试", "部署上线",
        ],
    },
    "营销": {
        "keywords": ["营销", "推广", "广告", "获客", "转化", "品牌", "内容"],
        "complexity": "medium",
        "typical_steps": [
            "市场分析", "目标受众定义", "营销策略制定", "内容创作",
            "渠道投放", "效果追踪",
        ],
    },
}


def _detect_domain(text: str) -> str:
    """Detect domain from input text based on keywords."""
    text_lower = text.lower()
    domain_scores: dict[str, int] = {}
    for domain, info in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in info["keywords"] if kw in text_lower)
        if score > 0:
            domain_scores[domain] = score
    if not domain_scores:
        return "通用"
    return max(domain_scores, key=domain_scores.get)


# ── Agent 1: ScriptAgent (规划层) ────────────────────────────────────────────


class ScriptAgent:
    """规划层Agent — 分析输入，生成结构化脚本/计划。

    Responsibilities:
      - analyze_text(): Parse and understand user input
      - generate_script(): Produce structured script with objectives and steps
    """

    def __init__(self, name: str = "ScriptAgent"):
        self.name = name
        self._history: list[dict[str, Any]] = []

    def analyze_text(self, text: str) -> dict[str, Any]:
        """Analyze input text — extract domain, intent, key entities."""
        t0 = time.time()
        domain = _detect_domain(text)
        domain_info = DOMAIN_KEYWORDS.get(domain, {})

        # Simple linguistic analysis
        sentences = [s.strip() for s in text.replace("?", "？").replace("!", "！")
                     .split("。") if s.strip()]
        word_count = len(text)
        char_count = len(text.replace(" ", ""))

        # Extract potential objectives
        objectives = []
        action_particles = ["设计", "开发", "创建", "生成", "分析", "规划",
                            "制作", "制定", "搭建", "实现", "优化"]
        for p in action_particles:
            if p in text:
                idx = text.index(p)
                objectives.append(text[max(0, idx):idx + 20].strip())

        analysis = {
            "domain": domain,
            "complexity": domain_info.get("complexity", "medium"),
            "sentence_count": len(sentences),
            "word_count": word_count,
            "char_count": char_count,
            "objectives_found": objectives or [f"完成{domain}相关任务"],
            "domain_description": f"检测到领域: {domain}",
            "analysis_duration_ms": (time.time() - t0) * 1000,
        }

        self._history.append({"action": "analyze", "text_preview": text[:100], "result": analysis})
        return analysis

    def generate_script(self, text: str) -> ScriptOutput:
        """Generate a structured script/plan from input text."""
        t0 = time.time()
        analysis = self.analyze_text(text)
        domain = analysis["domain"]
        domain_info = DOMAIN_KEYWORDS.get(domain, {})
        objectives = analysis["objectives_found"]

        # Build structured steps based on domain
        steps: list[dict[str, Any]] = []
        typical = domain_info.get("typical_steps", ["需求分析", "方案设计", "执行", "验收"])
        for i, step_name in enumerate(typical):
            step = {
                "step_id": f"S{i+1:02d}",
                "step_name": step_name,
                "step_type": "analysis" if "分析" in step_name or "定义" in step_name
                             else "generation" if "设计" in step_name or "创作" in step_name or "制定" in step_name
                             else "execution",
                "description": f"{step_name}阶段 — 基于输入: {text[:50]}...",
                "dependencies": [f"S{j+1:02d}" for j in range(i)] if i > 0 else [],
            }
            steps.append(step)

        script = ScriptOutput(
            title=f"{domain}方案: {text[:30]}...",
            description=f"基于'{text[:100]}'的{domain}自动化方案",
            objectives=objectives,
            steps=steps,
            estimated_duration=f"{len(steps) * 2}-{len(steps) * 4} 小时",
            complexity=analysis["complexity"],
            raw_text=text,
            confidence=0.75 + (0.2 if domain != "通用" else 0.0),
        )

        self._history.append({"action": "generate_script", "script_title": script.title})
        return script


# ── Agent 2: ProductionAgent (执行层) ────────────────────────────────────────


class ProductionAgent:
    """执行层Agent — 分解任务，调度执行步骤。

    Responsibilities:
      - decompose_task(): Break script into concrete steps
      - dispatch_steps(): Execute steps with tracking
    """

    def __init__(self, name: str = "ProductionAgent"):
        self.name = name
        self._history: list[dict[str, Any]] = []

    def decompose_task(self, script: ScriptOutput | dict[str, Any]) -> list[TaskStep]:
        """Decompose a script into executable task steps."""
        if isinstance(script, dict):
            script = ScriptOutput(**script)

        if isinstance(script, ScriptOutput):
            step_defs = script.steps
        else:
            step_defs = []

        steps: list[TaskStep] = []
        for i, sd in enumerate(step_defs):
            step = TaskStep(
                step_id=sd.get("step_id", f"T{i+1:02d}"),
                step_name=sd.get("step_name", f"步骤{i+1}"),
                step_type=sd.get("step_type", "execution"),
                description=sd.get("description", ""),
                dependencies=sd.get("dependencies", []),
                assigned_to=sd.get("assigned_to", "auto"),
                status=TaskStatus.PENDING,
                max_retries=3,
            )
            steps.append(step)

        # If no steps from script, create default steps
        if not steps:
            steps = [
                TaskStep(step_id="T01", step_name="需求分析", step_type="analysis",
                         description="分析用户需求和目标"),
                TaskStep(step_id="T02", step_name="方案设计", step_type="generation",
                         description="设计执行方案", dependencies=["T01"]),
                TaskStep(step_id="T03", step_name="执行落地", step_type="execution",
                         description="执行方案内容", dependencies=["T02"]),
                TaskStep(step_id="T04", step_name="质量检查", step_type="validation",
                         description="检查输出质量", dependencies=["T03"]),
            ]

        return steps

    def dispatch_steps(self, steps: list[TaskStep]) -> ProductionOutput:
        """Execute all steps in dependency order."""
        t0 = time.time()
        task_id = f"task_{uuid.uuid4().hex[:8]}"

        # Build dependency graph and execute in order
        executed: set[str] = set()
        completed = 0
        all_success = True

        while len(executed) < len(steps):
            progressed = False
            for step in steps:
                if step.step_id in executed:
                    continue
                # Check dependencies
                deps_met = all(d in executed for d in step.dependencies)
                if not deps_met:
                    continue

                # Execute this step
                step.status = TaskStatus.RUNNING
                step_t0 = time.time()

                try:
                    result = self._execute_step(step)
                    step.result = result
                    step.status = TaskStatus.SUCCESS
                    step.duration_ms = (time.time() - step_t0) * 1000
                    executed.add(step.step_id)
                    completed += 1
                    progressed = True
                    logger.info(f"  ✅ Step {step.step_id}: {step.step_name} ({step.duration_ms:.0f}ms)")
                except Exception as e:
                    step.status = TaskStatus.FAILED
                    step.error = str(e)
                    step.duration_ms = (time.time() - step_t0) * 1000
                    all_success = False
                    progressed = True
                    logger.error(f"  ❌ Step {step.step_id}: {step.step_name} — {e}")

            if not progressed:
                # Deadlock or remaining steps have unmet dependencies
                for step in steps:
                    if step.step_id not in executed:
                        step.status = TaskStatus.SKIPPED
                        step.error = "Dependencies cannot be satisfied (deadlock or missing deps)"
                        executed.add(step.step_id)
                break

        total_ms = (time.time() - t0) * 1000

        output = ProductionOutput(
            task_id=task_id,
            steps=steps,
            completed_steps=completed,
            total_steps=len(steps),
            all_success=all_success,
            total_duration_ms=total_ms,
        )

        self._history.append({
            "action": "dispatch",
            "task_id": task_id,
            "steps": len(steps),
            "completed": completed,
            "success": all_success,
        })

        return output

    def _execute_step(self, step: TaskStep) -> dict[str, Any]:
        """Execute a single step based on its type (simulated execution)."""
        import random

        if step.step_type == "analysis":
            return {
                "step_type": "analysis",
                "findings": f"分析完成: {step.description[:50]}...",
                "data_points": random.randint(3, 10),
                "recommendations": [f"建议一: 基于分析结果推进", f"建议二: 关注关键指标"],
            }
        elif step.step_type == "generation":
            return {
                "step_type": "generation",
                "output": f"生成内容: {step.description[:50]}...",
                "format": "structured",
                "quality_score": round(random.uniform(0.7, 0.98), 2),
            }
        elif step.step_type == "validation":
            return {
                "step_type": "validation",
                "checks_passed": random.randint(3, 6),
                "checks_total": 5,
                "issues_found": [],
                "overall_quality": "good",
            }
        else:  # execution
            return {
                "step_type": "execution",
                "action_taken": f"执行: {step.description[:50]}...",
                "status": "completed",
                "artifacts": [f"output_{step.step_id}.json"],
            }

    def get_history(self) -> list[dict[str, Any]]:
        return self._history


# ── Agent 3: ReviewAgent (质检层) ────────────────────────────────────────────


class ReviewAgent:
    """质检层Agent — 质量检查，失败重试策略。

    Responsibilities:
      - check_quality(): Evaluate output quality against criteria
      - retry_strategy(): Determine retry strategy on failure
    """

    def __init__(self, name: str = "ReviewAgent"):
        self.name = name
        self._history: list[dict[str, Any]] = []

    def check_quality(self, production_output: ProductionOutput | dict[str, Any]) -> ReviewOutput:
        """Check the quality of production output."""
        if isinstance(production_output, dict):
            production_output = ProductionOutput(**{
                k: v for k, v in production_output.items()
                if k in ProductionOutput.__dataclass_fields__
            })

        issues: list[dict[str, Any]] = []
        suggestions: list[str] = []
        total_score = 1.0

        # Check completion rate
        if production_output.total_steps > 0:
            completion_rate = production_output.completed_steps / production_output.total_steps
            if completion_rate < 0.5:
                issues.append({
                    "severity": "critical",
                    "type": "completion",
                    "message": f"Only {completion_rate:.0%} of steps completed",
                })
                total_score -= 0.3
                suggestions.append("检查步骤依赖关系，确保所有前置条件满足")
            elif completion_rate < 0.8:
                issues.append({
                    "severity": "warning",
                    "type": "completion",
                    "message": f"Only {completion_rate:.0%} of steps completed",
                })
                total_score -= 0.1
                suggestions.append("考虑并行化独立步骤以提高完成率")

        # Check for failed steps
        failed_steps = [s for s in production_output.steps if s.status == TaskStatus.FAILED]
        if failed_steps:
            issues.append({
                "severity": "critical",
                "type": "failure",
                "message": f"{len(failed_steps)} step(s) failed",
                "failed_steps": [s.step_name for s in failed_steps],
            })
            total_score -= 0.2 * len(failed_steps)
            suggestions.append(f"重试失败步骤: {', '.join(s.step_name for s in failed_steps)}")

        # Check for skipped steps
        skipped_steps = [s for s in production_output.steps if s.status == TaskStatus.SKIPPED]
        if skipped_steps:
            issues.append({
                "severity": "warning",
                "type": "skipped",
                "message": f"{len(skipped_steps)} step(s) skipped",
                "skipped_steps": [s.step_name for s in skipped_steps],
            })
            total_score -= 0.1
            suggestions.append("检查步骤依赖关系是否正确配置")

        # Check step results for quality
        for step in production_output.steps:
            if step.result:
                quality = step.result.get("quality_score", 1.0)
                if quality < 0.6:
                    issues.append({
                        "severity": "warning",
                        "type": "quality",
                        "message": f"Step '{step.step_name}' quality score too low: {quality}",
                    })
                    total_score -= 0.1

        # Normalize score
        score = max(0.0, min(1.0, total_score))
        passed = score >= 0.6
        verdict = "pass" if passed else "needs_revision"
        if score < 0.3:
            verdict = "fail"

        review = ReviewOutput(
            passed=passed,
            score=round(score, 2),
            issues=issues,
            suggestions=suggestions,
            verdict=verdict,
            retry_needed=not passed,
            retry_strategy=self._determine_retry_strategy(issues),
            details=f"质量检查完成: {len(issues)} issues, score={score:.2f}",
        )

        self._history.append({
            "action": "check_quality",
            "passed": passed,
            "score": score,
            "issues": len(issues),
        })

        return review

    def retry_strategy(self, review: ReviewOutput) -> dict[str, Any]:
        """Determine retry strategy based on review results."""
        if not review.retry_needed:
            return {"strategy": "none", "reason": "All checks passed"}

        strategy = review.retry_strategy

        strategies = {
            "full": {
                "strategy": "full_retry",
                "description": "Full pipeline retry with adjusted parameters",
                "steps": [
                    "1. 分析失败原因",
                    "2. 调整关键参数",
                    "3. 重新执行全流程",
                    "4. 对比两次结果",
                ],
                "recommended": strategy == "full",
            },
            "partial": {
                "strategy": "partial_retry",
                "description": "Retry only failed/skipped steps",
                "steps": [
                    "1. 定位失败步骤",
                    "2. 单独重试每个失败步骤",
                    "3. 验证修复效果",
                ],
                "recommended": strategy == "partial",
            },
            "skip": {
                "strategy": "skip_and_continue",
                "description": "Skip problematic steps and continue",
                "steps": [
                    "1. 标记失败步骤为已跳过",
                    "2. 继续执行剩余步骤",
                    "3. 输出时注明缺少的部分",
                ],
                "recommended": strategy == "skip",
            },
        }

        return strategies.get(strategy, strategies["partial"])

    def _determine_retry_strategy(self, issues: list[dict[str, Any]]) -> str:
        """Determine automatic retry strategy."""
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        warning_issues = [i for i in issues if i.get("severity") == "warning"]

        if len(critical_issues) >= 2:
            return "full"
        elif len(critical_issues) == 1 or len(warning_issues) >= 3:
            return "partial"
        else:
            return "skip"

    def get_history(self) -> list[dict[str, Any]]:
        return self._history


# ── Three-Layer Pipeline ──────────────────────────────────────────────────────


def three_layer_pipeline(text: str, max_iterations: int = 3) -> PipelineResult:
    """端到端三层Agent协作管线。

    Args:
        text: 输入文本
        max_iterations: 最大迭代次数（ReviewAgent可触发重试）

    Returns:
        PipelineResult with all layer outputs
    """
    t0 = time.time()

    script_agent = ScriptAgent()
    production_agent = ProductionAgent()
    review_agent = ReviewAgent()

    overall_result = PipelineResult(input_text=text)

    for iteration in range(1, max_iterations + 1):
        logger.info(f"Pipeline iteration {iteration}/{max_iterations}")

        # Layer 1: ScriptAgent — 规划
        logger.info("  Layer 1: ScriptAgent — 规划中...")
        script = script_agent.generate_script(text)
        logger.info(f"  → Script: {script.title} ({len(script.steps)} steps)")

        # Layer 2: ProductionAgent — 执行
        logger.info("  Layer 2: ProductionAgent — 执行中...")
        steps = production_agent.decompose_task(script)
        production = production_agent.dispatch_steps(steps)
        logger.info(f"  → Production: {production.completed_steps}/{production.total_steps} steps")

        # Layer 3: ReviewAgent — 质检
        logger.info("  Layer 3: ReviewAgent — 质检中...")
        review = review_agent.check_quality(production)
        logger.info(f"  → Review: verdict={review.verdict}, score={review.score}")

        overall_result.script = script
        overall_result.production = production
        overall_result.review = review
        overall_result.iterations = iteration

        if review.passed:
            overall_result.success = True
            logger.info(f"Pipeline completed successfully after {iteration} iteration(s)")
            break
        elif iteration < max_iterations and review.retry_needed:
            strategy = review_agent.retry_strategy(review)
            logger.info(f"  → Retry strategy: {strategy['strategy']}")
            # In a real implementation, apply the retry strategy here
        else:
            logger.info(f"Pipeline finished with verdict: {review.verdict}")

    overall_result.duration_ms = (time.time() - t0) * 1000
    return overall_result


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Agent Collaboration — Three-Layer Agent Architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["pipeline", "script", "production", "review"],
        default="pipeline",
        help="Execution mode",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="",
        help="Input text (or JSON for review mode)",
    )
    parser.add_argument(
        "--max-iterations", "-n",
        type=int,
        default=3,
        help="Maximum pipeline iterations (default: 3)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="",
        help="Output file path (JSON)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if args.mode == "pipeline":
        if not args.input and sys.stdin.isatty():
            print("Error: --input required for pipeline mode", file=sys.stderr)
            sys.exit(1)
        text = args.input or sys.stdin.read().strip()
        result = three_layer_pipeline(text, max_iterations=args.max_iterations)
        output = result.to_dict()

    elif args.mode == "script":
        if not args.input:
            print("Error: --input required for script mode", file=sys.stderr)
            sys.exit(1)
        agent = ScriptAgent()
        script = agent.generate_script(args.input)
        output = script.to_dict()

    elif args.mode == "production":
        if not args.input:
            print("Error: --input required for production mode (JSON)", file=sys.stderr)
            sys.exit(1)
        try:
            script_data = json.loads(args.input)
        except json.JSONDecodeError:
            script_data = {"raw_text": args.input, "steps": []}
        agent = ProductionAgent()
        steps = agent.decompose_task(script_data)
        prod = agent.dispatch_steps(steps)
        output = prod.to_dict()

    elif args.mode == "review":
        if not args.input:
            print("Error: --input required for review mode (JSON)", file=sys.stderr)
            sys.exit(1)
        try:
            prod_data = json.loads(args.input)
        except json.JSONDecodeError:
            print("Error: review mode requires JSON input", file=sys.stderr)
            sys.exit(1)
        agent = ReviewAgent()
        review = agent.check_quality(prod_data)
        output = review.to_dict()

    else:
        print(f"Unknown mode: {args.mode}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        out_path = __import__("pathlib").Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Result written to {out_path}")

    print(json.dumps(output, ensure_ascii=False, indent=2))

    if isinstance(output, dict) and not output.get("success", True):
        sys.exit(1)


if __name__ == "__main__":
    main()
