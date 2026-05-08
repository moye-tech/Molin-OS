"""molib.shared.gate — 门控评估系统

子包：
- stop_gate: Agent执行门控（StopGate/GateResult/GateRule）
"""

from .stop_gate import StopGate, GateResult, GateRule, GateBlockedError

__all__ = ["StopGate", "GateResult", "GateRule", "GateBlockedError"]
