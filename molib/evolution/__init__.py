"""
molib.evolution — 进化引擎包
任务执行后的自动学习闭环
"""
from molib.evolution.quality_gate import QualityGate, get_quality_gate
from molib.evolution.engine import EvolutionEngine, EvalOutcome, EvalResult
from molib.evolution.knowledge_extractor import KnowledgeExtractor
from molib.evolution.failure_analyzer import FailureAnalyzer
from molib.evolution.session_state import SessionState, SessionContext, SessionStore
from molib.evolution.autonomous_planner import AutonomousPlanner, PlannedTask, OKR, get_autonomous_planner, ProgressTracker

__all__ = [
    "QualityGate", "get_quality_gate",
    "EvolutionEngine", "EvalOutcome", "EvalResult",
    "KnowledgeExtractor",
    "FailureAnalyzer",
    "SessionState", "SessionContext", "SessionStore",
    "AutonomousPlanner", "PlannedTask", "OKR", "get_autonomous_planner", "ProgressTracker",
]
