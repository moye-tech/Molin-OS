"""molib.shared.gui_eval — GUI Agent 评估框架

吸收自 ZJU-REAL/ClawGUI (1.1K⭐)
提取核心设计模式: Infer→Judge→Metric 三层评估管线。

GUI 接地评估分为三个阶段：
1. Infer: 多模型推理，统一输出格式
2. Judge: 评分规则 + 多模态判断
3. Metric: 聚合指标 + 基准对比

零外部依赖，仅使用 Python 标准库。
"""

from .infer_runner import InferRunner, InferResult
from .judge_engine import JudgeEngine, JudgeResult
from .metric_aggregator import MetricAggregator, BenchmarkReport

__all__ = [
    "InferRunner", "InferResult",
    "JudgeEngine", "JudgeResult",
    "MetricAggregator", "BenchmarkReport",
]
