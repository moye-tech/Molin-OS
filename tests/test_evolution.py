"""进化引擎全链路测试"""
import asyncio
import logging
import sys, time
sys.path.insert(0, "/home/ubuntu/hermes-os")
logging.basicConfig(level=logging.WARNING)

from molib.evolution.quality_gate import get_quality_gate
from molib.evolution.engine import EvolutionEngine
from molib.evolution.session_state import SessionState, SessionContext, SessionStore
from molib.evolution.autonomous_planner import AutonomousPlanner, PlannedTask, get_autonomous_planner, ProgressTracker
from molib.evolution.tracing import set_request_id, get_request_id
from molib.evolution.failure_analyzer import FailureAnalyzer
from molib.evolution.knowledge_extractor import KnowledgeExtractor


async def test_all():
    print("=== 1. QualityGate ===")
    qg = get_quality_gate()
    result = {"status": "success", "output": {"score": 8.5, "result": "很棒的结果"}}
    task = {"task_id": "test_001", "description": "测试"}
    r, meta = await qg.evaluate(result, task)
    print(f"  高分通过: action={meta['action']} score={meta['score']}")

    result2 = {"status": "error", "output": {}}
    r2, meta2 = await qg.evaluate(result2, task)
    print(f"  失败评分: action={meta2['action']} score={meta2['score']}")
    print(f"  指标: {qg.get_metrics()}")

    print("\n=== 2. EvolutionEngine ===")
    engine = EvolutionEngine()
    eval_result = await engine.evaluate({
        "status": "success", "score": 8.5,
        "task_type": "吸收测试", "agency": "engine",
        "output": "成功吸收 QualityGate 到进化引擎包",
        "metadata": {"tools_used": ["memory_tool"]},
    })
    print(f"  成功: outcome={eval_result.outcome.value}, 卡片={len(eval_result.knowledge_cards)}张")
    for c in eval_result.knowledge_cards:
        print(f"    - {c['type']}")

    eval_fail = await engine.evaluate({
        "status": "error", "score": 2.0, "task_type": "失败测试",
        "error": "Connection timeout after 30s",
        "metadata": {"tools_used": ["web_tool"]},
    })
    print(f"  失败: outcome={eval_fail.outcome.value}")
    for p in eval_fail.failure_patterns:
        print(f"    - {p['error_type']}")
    print(f"  建议: {eval_fail.improvement_suggestions}")

    print("\n=== 3. SessionState ===")
    ctx = await SessionStore.get_or_create("test_session")
    print(f"  初始状态: {ctx.state.value}")
    ctx.transition(SessionState.EXPLORING)
    ctx.add_turn("你好", "你好！", SessionState.INITIAL, SessionState.EXPLORING)
    print(f"  轮数: {ctx.turn_count}")

    print("\n=== 4. AutonomousPlanner ===")
    plan = get_autonomous_planner()
    okr = plan.create_okr("提升稳定性", ["减少故障", "完善监控"])
    plan.add_task_to_okr(okr.okr_id, PlannedTask(
        task_id="t1", title="部署自愈", agency="ops", priority="high", deadline=time.time() + 86400
    ))
    plan.add_task_to_okr(okr.okr_id, PlannedTask(
        task_id="t2", title="完善告警", agency="ops", priority="medium", deadline=time.time() + 86400 * 2
    ))
    plan.tracker.start("t1")
    plan.tracker.complete("t1")
    print(f"  任务统计: {plan.tracker.get_stats()}")

    print("\n=== 5. Tracing ===")
    rid = set_request_id()
    print(f"  请求ID: {rid}")
    assert get_request_id() == rid
    print("  get_request_id OK")

    print("\n=== 6. FailureAnalyzer ===")
    fa = FailureAnalyzer()
    patterns = await fa.analyze({"status": "error", "error": "json parse error", "metadata": {}})
    print(f"  错误分类: {patterns[0]['error_type'] if patterns else 'none'}")

    print("\n=== 7. KnowledgeExtractor ===")
    ke = KnowledgeExtractor()
    cards = await ke.extract({"status": "success", "task_type": "研发", "score": 9.0,
                              "output": "成功部署系统", "metadata": {"tools_used": ["terminal"]}})
    print(f"  提取卡片: {len(cards)}张")
    for c in cards:
        print(f"    - {c.get('type', '?')} / {c.get('task_type', '?')}")

    print("\n=== ✅ ALL TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(test_all())
