"""molib.shared.content.rubric — 内容评分公式引擎

吸收自 XBuilderLAB/cheat-on-content (1.0K⭐)

核心模式：
1. 评分公式 (RubricScore): 自定义维度的加权评分
2. 盲预测 (BlindPredict): 发布前预测结果 → 发布后复盘校准
3. 自动进化 (AutoEvolve): 连续偏差自动触发公式升级

零外部依赖，仅使用 Python 标准库。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional


@dataclass
class RubricDimension:
    """评分维度"""
    name: str
    weight: float  # 权重 0.0 ~ 1.0
    score: float = 0.0  # 本次得分 0.0 ~ 10.0
    description: str = ""

    def weighted_score(self) -> float:
        return self.weight * self.score / 10.0


@dataclass
class RubricScore:
    """评分结果"""
    dimensions: list[RubricDimension]
    total: float = 0.0  # 加权总分 0.0 ~ 1.0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "dimensions": [
                {"name": d.name, "weight": d.weight, "score": d.score,
                 "weighted": round(d.weighted_score(), 3)}
                for d in self.dimensions
            ],
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class BlindPrediction:
    """盲预测记录"""
    content_id: str
    title: str
    predicted_score: float  # 预测总分 0.0 ~ 1.0
    actual_score: float = 0.0  # 实际得分 (发布后复盘填入)
    deviation: float = 0.0  # 偏差 (正=高估,负=低估)
    reviewed: bool = False
    dimensions: list[dict] = field(default_factory=list)
    notes: str = ""

    def calc_deviation(self) -> float:
        if self.actual_score > 0:
            self.deviation = round(self.predicted_score - self.actual_score, 3)
        return self.deviation


class ContentRubricEngine:
    """内容评分公式引擎

    用法:
        engine = ContentRubricEngine()
        score = engine.score(
            content="...",
            dimensions=[
                ("封面吸引力", 0.3),
                ("标题冲击力", 0.25),
                ("内容结构", 0.2),
                ("情感共鸣", 0.15),
                ("行动召唤", 0.1),
            ]
        )
        print(score.to_json())
    """

    def __init__(self, custom_scorer: Optional[Callable] = None):
        self.custom_scorer = custom_scorer
        self._history: list[RubricScore] = []
        self._predictions: list[BlindPrediction] = []

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib content rubric-score --content "..." --dims "cover:0.3,title:0.25"
    #   python -m molib content rubric-predict --id xxx --score 0.75
    #   python -m molib content rubric-review --id xxx --actual 0.6
    # ------------------------------------------------------------------

    def score(self, content: str,
              dimensions: Optional[list[tuple[str, float, str]]] = None) -> RubricScore:
        """对内容评分

        Args:
            content: 内容文本
            dimensions: 维度列表 [(名称, 权重, 描述), ...]

        Returns:
            RubricScore
        """
        if dimensions is None:
            dimensions = DEFAULT_DIMENSIONS

        import datetime
        dims: list[RubricDimension] = []
        for name, weight, desc in dimensions:
            dim_score = self._score_dimension(content, name)
            dims.append(RubricDimension(
                name=name, weight=weight, score=dim_score, description=desc,
            ))

        total = sum(d.weighted_score() for d in dims)
        score_obj = RubricScore(
            dimensions=dims,
            total=round(min(1.0, total), 3),
            timestamp=datetime.datetime.now().isoformat(),
        )
        self._history.append(score_obj)
        return score_obj

    def _score_dimension(self, content: str, dim_name: str) -> float:
        """单维度评分 (0~10)"""
        if self.custom_scorer:
            try:
                result = self.custom_scorer(content, dim_name)
                if isinstance(result, (int, float)):
                    return max(0.0, min(10.0, float(result)))
            except Exception:
                pass

        # 默认启发式评分
        return self._default_scorer(content, dim_name)

    @staticmethod
    def _default_scorer(content: str, dim_name: str) -> float:
        """默认评分 — 基于内容特征"""
        c = content.lower()
        score = 5.0  # 基准 5/10

        if dim_name == "封面吸引力":
            # 有数字、感叹号、情绪词加分
            if any(ch.isdigit() for ch in c):
                score += 1.0
            if "!" in c or "！" in c:
                score += 0.5
            if any(w in c for w in ["震惊", "绝了", "太", "超", "最"]):
                score += 1.0
        elif dim_name == "标题冲击力":
            # 短标题加分，有问句/反问加分
            words = len(c.split())
            if words < 20:
                score += 1.0
            if "?" in c or "？" in c or "吗" in c:
                score += 1.0
            if "你" in c or "我" in c:
                score += 0.5
        elif dim_name == "内容结构":
            # 有分段、列表加分
            if "\n" in c:
                score += 1.0
            if "- " in c or "* " in c or c.count(".") > 3:
                score += 1.0
            if len(c) > 200:
                score += 0.5
        elif dim_name == "情感共鸣":
            # 情绪词、个人经历词
            if any(w in c for w in ["我", "我们", "你", "你们", "大家"]):
                score += 1.0
            if any(w in c for w in ["难过", "感动", "开心", "焦虑", "迷茫", "奋斗"]):
                score += 1.5
        elif dim_name == "行动召唤":
            if any(w in c for w in ["关注", "点赞", "收藏", "转发", "评论区", "关注我"]):
                score += 2.0
            if any(w in c for w in ["试试", "去", "看", "点"]):
                score += 1.0

        return max(0.0, min(10.0, score))

    def predict(self, content_id: str, title: str,
                predicted_score: float, dimensions: Optional[list[dict]] = None,
                notes: str = "") -> BlindPrediction:
        """创建盲预测"""
        pred = BlindPrediction(
            content_id=content_id,
            title=title,
            predicted_score=min(1.0, max(0.0, predicted_score)),
            dimensions=dimensions or [],
            notes=notes,
        )
        self._predictions.append(pred)
        return pred

    def review(self, content_id: str, actual_score: float) -> Optional[BlindPrediction]:
        """复盘: 填入实际得分，计算偏差"""
        for pred in self._predictions:
            if pred.content_id == content_id:
                pred.actual_score = min(1.0, max(0.0, actual_score))
                pred.calc_deviation()
                pred.reviewed = True
                return pred
        return None

    def check_evolution_needed(self, threshold: float = 0.3,
                               streak: int = 3) -> Optional[list[BlindPrediction]]:
        """检查是否需要升级公式

        连续 streak 次同方向偏差超过 threshold 则触发升级提示。

        Returns:
            触发升级的预测列表, 或 None
        """
        recent = [p for p in self._predictions if p.reviewed][-streak:]
        if len(recent) < streak:
            return None

        # 检查是否同方向
        directions = [p.deviation >= 0 for p in recent]
        if all(directions) or not any(directions):
            avg_dev = abs(sum(p.deviation for p in recent)) / streak
            if avg_dev > threshold:
                return recent
        return None

    def export_history(self) -> dict:
        """导出历史数据"""
        return {
            "scores": [s.to_dict() for s in self._history],
            "predictions": [
                {"id": p.content_id, "title": p.title,
                 "predicted": p.predicted_score, "actual": p.actual_score,
                 "deviation": p.deviation, "reviewed": p.reviewed}
                for p in self._predictions
            ],
        }


# 默认维度
DEFAULT_DIMENSIONS: list[tuple[str, float, str]] = [
    ("封面吸引力", 0.30, "封面图是否吸引点击"),
    ("标题冲击力", 0.25, "标题是否制造好奇/紧迫"),
    ("内容结构", 0.20, "信息是否清晰有序"),
    ("情感共鸣", 0.15, "是否能触发情绪反应"),
    ("行动召唤", 0.10, "是否引导互动/转化"),
]
