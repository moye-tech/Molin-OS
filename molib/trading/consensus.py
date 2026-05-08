"""
墨麟 — 共识聚合引擎 (Consensus)
从 UZI-Skill (wbh604/UZI-Skill) 提取的多评委共识聚合算法。

核心公式:
    consensus = polarize(0.65 × score_mean + 0.35 × vote_weighted, k=1.3)

用法:
    from molib.trading.consensus import ConsensusEngine, Judge, JudgeResult

    judges = [
        Judge(name="巴菲特", weight=3.0),
        Judge(name="段永平", weight=2.0),
    ]
    engine = ConsensusEngine(judges)

    results = [
        JudgeResult(judge="巴菲特", score=7.5, vote="bullish"),
        JudgeResult(judge="段永平", score=6.0, vote="neutral"),
    ]
    consensus = engine.aggregate(results)
    print(consensus)  # {"score": 7.8, "verdict": "bullish", ...}
"""

import statistics
import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Literal


# ── 数据类型 ──────────────────────────────────────────────────────

VoteType = Literal["bullish", "neutral", "bearish"]
VerdictType = Literal["strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"]


@dataclass
class JudgeResult:
    """单评委的评分结果"""

    judge: str
    """评委名称"""

    score: float
    """评分 (1-10)"""

    vote: VoteType = "neutral"
    """投票: bullish / neutral / bearish"""

    confidence: float = 1.0
    """可信度权重 (0.0-1.0)，默认1.0"""

    detail: Optional[str] = None
    """评委的具体评语"""


@dataclass
class ConsensusResult:
    """共识聚合结果"""

    score: float
    """综合评分 (1-10)"""

    verdict: VerdictType
    """最终判断"""

    bullish_ratio: float
    """看涨比例"""

    neutral_ratio: float
    """中性比例"""

    bearish_ratio: float
    """看跌比例"""

    judge_count: int
    """参与评委数"""

    details: List[Dict] = field(default_factory=list)
    """各评委详情"""

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "verdict": self.verdict,
            "bullish_ratio": self.bullish_ratio,
            "neutral_ratio": self.neutral_ratio,
            "bearish_ratio": self.bearish_ratio,
            "judge_count": self.judge_count,
            "details": self.details,
        }


# ── 评委定义 ──────────────────────────────────────────────────────


@dataclass
class Judge:
    """单评委定义"""

    name: str
    """评委名称"""

    weight: float = 1.0
    """权重 (默认1.0，大咖可设为2.0-5.0)"""

    tags: List[str] = field(default_factory=list)
    """标签: 价值投资/成长派/技术派/量化/游资"""

    style: str = ""
    """投资风格描述"""


# ── 共识引擎 ──────────────────────────────────────────────────────


class ConsensusEngine:
    """
    多评委共识聚合引擎。

    从 UZI-Skill 提取的核心算法:
    - 混合连续分 + 离散票
    - 极化拉伸 (polarize) 放大分歧
    - 权重加权

    用法:
        engine = ConsensusEngine(judges)
        result = engine.aggregate(judge_results)
    """

    def __init__(self, judges: Optional[List[Judge]] = None):
        self._judges: Dict[str, Judge] = {}
        if judges:
            for j in judges:
                self._judges[j.name] = j

    def add_judge(self, judge: Judge):
        """添加评委"""
        self._judges[judge.name] = judge

    def get_judge(self, name: str) -> Optional[Judge]:
        """获取评委定义"""
        return self._judges.get(name)

    def aggregate(
        self,
        results: List[JudgeResult],
        polarization_k: float = 1.3,
    ) -> ConsensusResult:
        """
        聚合多评委评分，产出共识结果。

        参数:
            results: 各评委的评分结果
            polarization_k: 极化系数 (越大分歧越被放大)

        返回:
            ConsensusResult
        """
        if not results:
            return ConsensusResult(
                score=5.0, verdict="neutral",
                bullish_ratio=0.0, neutral_ratio=1.0, bearish_ratio=0.0,
                judge_count=0, details=[],
            )

        # 活跃评委 (有分数)
        active = [r for r in results if r.score > 0]

        if not active:
            return ConsensusResult(
                score=5.0, verdict="neutral",
                bullish_ratio=0.0, neutral_ratio=1.0, bearish_ratio=0.0,
                judge_count=0, details=[],
            )

        # 加权分数均值 (连续分)
        total_weight = 0.0
        weighted_score = 0.0
        for r in active:
            w = self._judges.get(r.judge, Judge(name=r.judge)).weight
            w *= r.confidence  # 自信度调整
            total_weight += w
            weighted_score += r.score * w

        score_mean = weighted_score / total_weight if total_weight > 0 else 5.0

        # 离散投票加权 (看涨/中性/看跌比例)
        vote_weights = {"bullish": 0.0, "neutral": 0.0, "bearish": 0.0}
        vote_total = 0.0
        for r in active:
            w = self._judges.get(r.judge, Judge(name=r.judge)).weight
            w *= r.confidence
            vote_weights[r.vote] = vote_weights.get(r.vote, 0) + w
            vote_total += w

        bullish_ratio = vote_weights["bullish"] / vote_total if vote_total > 0 else 0.0
        neutral_ratio = vote_weights["neutral"] / vote_total if vote_total > 0 else 0.0
        bearish_ratio = vote_weights["bearish"] / vote_total if vote_total > 0 else 0.0

        # 投票加权分 (离散)
        vote_weighted = bullish_ratio * 100  # 0-100

        # 共识公式: 0.65 × 连续分 + 0.35 × 离散票, 再极化
        raw = 0.65 * (score_mean / 10 * 100) + 0.35 * vote_weighted

        # 极化拉伸
        consensus = self._polarize(raw, polarization_k)

        # 判断
        if consensus >= 75:
            verdict: VerdictType = "strong_bullish"
        elif consensus >= 60:
            verdict = "bullish"
        elif consensus >= 40:
            verdict = "neutral"
        elif consensus >= 25:
            verdict = "bearish"
        else:
            verdict = "strong_bearish"

        details = []
        for r in active:
            details.append({
                "judge": r.judge,
                "score": r.score,
                "vote": r.vote,
                "confidence": r.confidence,
                "detail": r.detail or "",
            })

        return ConsensusResult(
            score=round(consensus, 1),
            verdict=verdict,
            bullish_ratio=round(bullish_ratio, 2),
            neutral_ratio=round(neutral_ratio, 2),
            bearish_ratio=round(bearish_ratio, 2),
            judge_count=len(active),
            details=details,
        )

    @staticmethod
    def _polarize(value: float, k: float = 1.3) -> float:
        """
        极化拉伸函数 — 放大两端差异。

        公式: 50 + (value - 50) × k
        当 k > 1 时，低于50的向0拉，高于50的向100拉。
        """
        polarized = 50 + (value - 50) * k
        return max(0, min(100, polarized))
