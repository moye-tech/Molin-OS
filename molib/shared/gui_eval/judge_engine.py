"""molib.shared.gui_eval.judge_engine — 评分规则 + 多模态判断

ClawGUI-Eval 的 Judge 阶段抽象：将模型输出与 ground truth 比较，
支持多种评分规则（精确匹配 / 语义匹配 / 多模态匹配）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from typing import Callable, Optional


class JudgeMethod(Enum):
    EXACT_MATCH = auto()
    SEMANTIC_MATCH = auto()
    MULTIMODAL = auto()


@dataclass
class JudgeResult:
    """单条判断结果"""
    sample_id: str
    model_name: str
    benchmark: str
    score: float  # 0.0 ~ 1.0
    method: str
    predicted: str
    ground_truth: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def passed(self) -> bool:
        return self.score >= 0.5


class JudgeEngine:
    """判断引擎

    将模型输出与预期结果比较，支持：
    1. 精确匹配 (EXACT_MATCH)
    2. 语义匹配 (SEMANTIC_MATCH) — 关键词 / 坐标 / 动作序列
    3. 多模态匹配 (MULTIMODAL) — 视觉相似度
    """

    def __init__(self, method: JudgeMethod = JudgeMethod.EXACT_MATCH,
                 semantic_rules: Optional[dict[str, Callable]] = None):
        self.method = method
        self.semantic_rules = semantic_rules or {}

    # ------------------------------------------------------------------
    # CLI Integration
    #   python -m molib gui-eval judge --results results.json --ground-truth gt.json
    # ------------------------------------------------------------------

    def evaluate(self, model_name: str, benchmark: str,
                 predictions: list[InferResult],
                 ground_truths: list[dict]) -> list[JudgeResult]:
        """批量判断

        Args:
            model_name: 模型名
            benchmark: 基准名
            predictions: InferResult 列表
            ground_truths: ground truth 列表，每项含 {id, action, coordinates, ...}

        Returns:
            JudgeResult 列表
        """
        gt_map = {g.get("id", g.get("sample_id", "")): g for g in ground_truths}
        results: list[JudgeResult] = []

        for pred in predictions:
            gt = gt_map.get(pred.sample_id, {})
            score = self._judge_single(
                predicted=pred.raw_output,
                ground_truth=gt.get("action", ""),
                extra={"benchmark": benchmark, "coordinates": gt.get("coordinates")},
            )
            results.append(JudgeResult(
                sample_id=pred.sample_id,
                model_name=model_name,
                benchmark=benchmark,
                score=score,
                method=self.method.name.lower(),
                predicted=pred.raw_output,
                ground_truth=gt.get("action", ""),
            ))

        return results

    def _judge_single(self, predicted: str, ground_truth: str,
                      extra: Optional[dict] = None) -> float:
        """单条判断"""
        if self.method == JudgeMethod.EXACT_MATCH:
            return self._exact_match(predicted, ground_truth)
        elif self.method == JudgeMethod.SEMANTIC_MATCH:
            return self._semantic_match(predicted, ground_truth, extra or {})
        elif self.method == JudgeMethod.MULTIMODAL:
            return self._multimodal_match(predicted, ground_truth, extra or {})
        return 0.0

    def _exact_match(self, predicted: str, ground_truth: str) -> float:
        """精确匹配 (归一化后比较)"""
        p = predicted.strip().lower()
        g = ground_truth.strip().lower()
        return 1.0 if p == g else 0.0

    def _semantic_match(self, predicted: str, ground_truth: str,
                        extra: dict) -> float:
        """语义匹配 — 坐标近似 / 动作类型匹配 / 关键词覆盖"""
        score = 0.0
        weights = []

        # 动作类型匹配 (点击/滑动/输入)
        action_re = re.compile(r"(tap|click|swipe|scroll|type|press|long.?press)", re.I)
        pred_actions = action_re.findall(predicted)
        gt_actions = action_re.findall(ground_truth)
        if gt_actions:
            shared = set(a.lower() for a in pred_actions) & set(a.lower() for a in gt_actions)
            score += len(shared) / len(gt_actions) * 0.5
            weights.append(0.5)

        # 坐标近似 (如果可用)
        coords = extra.get("coordinates")
        if coords:
            coord_score = self._coord_match(predicted, coords)
            score += coord_score * 0.3
            weights.append(0.3)

        # 自定义规则
        for rule_name, rule_fn in self.semantic_rules.items():
            rule_weight = 0.2
            if rule_name == "coord":
                continue
            try:
                score += rule_fn(predicted, ground_truth) * rule_weight
                weights.append(rule_weight)
            except Exception:
                pass

        if not weights:
            weights = [1.0]
        return min(1.0, score / sum(weights))

    def _coord_match(self, predicted: str, target_coords: tuple) -> float:
        """坐标近似匹配 (以像素距离为基准)"""
        coord_re = re.compile(r"\((\d+)\s*[,，\s]\s*(\d+)\)")
        matches = coord_re.findall(predicted)
        if not matches or not target_coords:
            return 0.0

        tx, ty = target_coords[:2]
        distances: list[float] = []
        for x, y in matches:
            d = ((int(x) - tx) ** 2 + (int(y) - ty) ** 2) ** 0.5
            distances.append(d)

        if not distances:
            return 0.0

        min_dist = min(distances)
        if min_dist < 10:
            return 1.0
        elif min_dist < 50:
            return 0.7
        elif min_dist < 100:
            return 0.4
        else:
            return 0.1

    def _multimodal_match(self, predicted: str, ground_truth: str,
                          extra: dict) -> float:
        """多模态匹配占位 — 需视觉模型接入"""
        return self._exact_match(predicted, ground_truth)


# 避免循环导入 — InferResult 在 judge 层只做类型提示
# 需要在使用时从 infer_runner 导入
from .infer_runner import InferResult
