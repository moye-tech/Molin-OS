"""
墨麟 — 停止门控 (StopGate)
从 Harmonist (GammaLabTechnologies/harmonist) 提取的机械协议强制模式。

StopGate 是 Agent 协议执行的机械拦截点：
- 在关键操作前/后检查协议合规性
- 不符合条件时阻止或要求审核
- 不可绕过（不是"请遵守"而是"必须通过"）

用法:
    from molib.shared.gate.stop_gate import StopGate, GateResult

    gate = StopGate(required_reviewers=["qa-verifier"])
    result = gate.evaluate(
        writes=["file1.py"],
        subagent_calls=["qa-verifier"],
        memory_updates=True,
    )
    if not result.passed:
        print("缺少步骤:", result.missing_steps)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime, timezone


# ── 门控结果 ──────────────────────────────────────────────────────


@dataclass
class GateResult:
    """门控评估结果"""

    passed: bool
    """是否通过门控"""

    missing_steps: List[str] = field(default_factory=list)
    """缺失的必要步骤列表"""

    warnings: List[str] = field(default_factory=list)
    """警告信息（非阻塞性）"""

    evaluation_time: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    """评估时间"""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "missing_steps": self.missing_steps,
            "warnings": self.warnings,
            "evaluation_time": self.evaluation_time,
        }


# ── 门控规则 ──────────────────────────────────────────────────────


@dataclass
class GateRule:
    """单条门控规则"""

    name: str
    """规则名称"""

    check: Callable[[Dict[str, Any]], bool]
    """检查函数，接收上下文，返回 True=通过"""

    description: str = ""
    """规则描述"""

    blocking: bool = True
    """True=不通过则阻止，False=不通过仅警告"""


# ── 停止门控 ──────────────────────────────────────────────────────


class StopGate:
    """
    停止门控 — 机械协议强制拦截点。

    在 Agent 执行关键操作前/后调用 evaluate()，
    系统会根据门控规则判断是否允许继续。

    用法:
        gate = StopGate(required_reviewers=["qa-verifier"])
        result = gate.evaluate(...)
        if not result.passed:
            raise GateBlockedError(result.missing_steps)
    """

    def __init__(
        self,
        required_reviewers: Optional[List[str]] = None,
        loop_limit: int = 3,
        custom_rules: Optional[List[GateRule]] = None,
    ):
        self._required_reviewers = required_reviewers or []
        self._loop_limit = loop_limit
        self._loop_count: int = 0
        self._custom_rules: List[GateRule] = custom_rules or []

    def evaluate(
        self,
        writes: Optional[List[str]] = None,
        subagent_calls: Optional[List[str]] = None,
        memory_updates: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> GateResult:
        """
        执行门控评估。

        参数:
            writes: 本次写入的文件列表（空说明是纯查询）
            subagent_calls: 调用的子Agent列表
            memory_updates: 是否更新了记忆
            context: 额外上下文（传递给自定义规则）

        返回:
            GateResult
        """
        missing: List[str] = []
        warnings: List[str] = []

        # 规则1: 纯查询不需要门控
        if not writes and not subagent_calls:
            return GateResult(passed=True)

        # 规则2: 必要的审核者
        if self._required_reviewers:
            for reviewer in self._required_reviewers:
                if subagent_calls and reviewer not in subagent_calls:
                    missing.append(f"缺少必要审核: {reviewer}")

        # 规则3: 必须有记忆更新
        if writes and not memory_updates:
            warnings.append("写入文件但未更新记忆：可能丢失上下文")

        # 规则4: 循环次数限制
        self._loop_count += 1
        if self._loop_count > self._loop_limit:
            missing.append(f"循环次数超过限制 ({self._loop_limit})")

        # 规则5: 自定义规则
        ctx = {
            "writes": writes or [],
            "subagent_calls": subagent_calls or [],
            "memory_updates": memory_updates,
            "loop_count": self._loop_count,
            **(context or {}),
        }
        for rule in self._custom_rules:
            if not rule.check(ctx):
                msg = f"规则未通过: {rule.name}"
                if rule.blocking:
                    missing.append(msg)
                else:
                    warnings.append(msg)

        return GateResult(
            passed=len(missing) == 0,
            missing_steps=missing,
            warnings=warnings,
        )

    def reset_loop_count(self):
        """重置循环计数器"""
        self._loop_count = 0

    @property
    def loop_count(self) -> int:
        return self._loop_count


class GateBlockedError(Exception):
    """门控拦截异常 — 操作被机械门控阻止"""

    def __init__(self, missing_steps: List[str]):
        self.missing_steps = missing_steps
        super().__init__(f"Gate blocked: missing {', '.join(missing_steps)}")
