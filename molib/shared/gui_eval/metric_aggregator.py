"""molib.shared.gui_eval.metric_aggregator — 聚合指标 + 基准对比

ClawGUI-Eval 的 Metric 阶段抽象：将 JudgeResult 聚合为
可对比的 BenchmarkReport，支持成功率/准确率/详细统计。
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class BenchmarkReport:
    """基准报告 — 聚合结果"""
    benchmark: str
    model_name: str
    total_samples: int
    passed: int
    success_rate: float  # 0.0 ~ 1.0
    avg_latency_ms: float = 0.0
    score_distribution: dict[str, int] = field(default_factory=dict)
    error_count: int = 0
    details: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)


class MetricAggregator:
    """指标聚合器

    将 JudgeResult 列表聚合为 BenchmarkReport。
    支持多模型对比、历史基准对比。
    """

    def __init__(self, reference_results: Optional[dict] = None):
        """
        Args:
            reference_results: 历史基准结果 {benchmark: {model: success_rate}}
        """
        self.reference = reference_results or {}

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib gui-eval metric --results results.json
    # ------------------------------------------------------------------

    def aggregate(self, judge_results: list[JudgeResult],
                  infer_results: Optional[list[InferResult]] = None) -> BenchmarkReport:
        """聚合判断结果为基准报告

        Args:
            judge_results: JudgeResult 列表
            infer_results: 对应 InferResult (可选，用于延迟统计)

        Returns:
            BenchmarkReport
        """
        if not judge_results:
            return BenchmarkReport(
                benchmark="unknown",
                model_name="unknown",
                total_samples=0,
                passed=0,
                success_rate=0.0,
            )

        model = judge_results[0].model_name
        benchmark = judge_results[0].benchmark
        total = len(judge_results)
        passed = sum(1 for r in judge_results if r.passed)
        errors = sum(1 for r in judge_results if r.score < 0.0)

        # 延迟统计
        latencies = [r.latency_ms for r in (infer_results or [])
                     if hasattr(r, 'latency_ms') and r.latency_ms > 0]
        avg_lat = statistics.mean(latencies) if latencies else 0.0

        # 分数分布
        dist = {"0-0.25": 0, "0.25-0.5": 0, "0.5-0.75": 0, "0.75-1.0": 0}
        for r in judge_results:
            s = r.score
            if s < 0.25:
                dist["0-0.25"] += 1
            elif s < 0.5:
                dist["0.25-0.5"] += 1
            elif s < 0.75:
                dist["0.5-0.75"] += 1
            else:
                dist["0.75-1.0"] += 1

        details = [r.to_dict() for r in judge_results]

        return BenchmarkReport(
            benchmark=benchmark,
            model_name=model,
            total_samples=total,
            passed=passed,
            success_rate=round(passed / total, 4) if total > 0 else 0.0,
            avg_latency_ms=round(avg_lat, 1),
            score_distribution=dist,
            error_count=errors,
            details=details,
        )

    def compare_to_reference(self, report: BenchmarkReport) -> dict:
        """与基准结果对比

        Returns:
            {"absolute_diff": 0.05, "relative_change": "+12.3%", "reference_success_rate": 0.70}
        """
        ref = self.reference.get(report.benchmark, {}).get(report.model_name)
        if ref is None:
            return {"absolute_diff": None, "relative_change": "N/A", "reference_success_rate": None}

        diff = report.success_rate - ref
        rel = f"{'+' if diff >= 0 else ''}{diff * 100:.1f}%"
        return {
            "absolute_diff": round(diff, 4),
            "relative_change": rel,
            "reference_success_rate": ref,
        }


# 避免循环导入
from .judge_engine import JudgeResult
from .infer_runner import InferResult
