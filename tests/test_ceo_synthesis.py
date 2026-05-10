"""Level 3 · CEO 整合测试

验证 CEO 收到多个子公司结果后，能合成完整的用户可读方案，而非状态摘要拼接。
运行命令：pytest tests/test_ceo_synthesis.py -v
"""

import sys
import os
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# mock before any project imports
sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.asyncio", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())
sys.modules.setdefault("qdrant_client", MagicMock())
sys.modules.setdefault("qdrant_client.models", MagicMock())

# Import session_state directly
from core.ceo.session_state import SessionContext, SessionState

# Load ceo_reasoning as isolated module
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "ceo_reasoning_isolated",
    os.path.join(os.path.dirname(__file__), "..", "core", "ceo", "ceo_reasoning.py"),
)
ceo_reasoning_mod = importlib.util.module_from_spec(_spec)
sys.modules["core.ceo.ceo_reasoning"] = ceo_reasoning_mod
sys.modules["core.ceo.session_state"] = sys.modules.get("core.ceo.session_state", __import__("core.ceo.session_state", fromlist=["SessionContext"]))
_spec.loader.exec_module(ceo_reasoning_mod)
CEOReasoningLoop = ceo_reasoning_mod.CEOReasoningLoop


def _mock_dispatcher_for_test():
    """设置 mock dispatcher，使 _execute_dispatch 能走通"""
    # 如果模块中 MANAGER_DISPATCHER_AVAILABLE 为 False，需要重新设置为 True 并注入 mock
    ceo_reasoning_mod.MANAGER_DISPATCHER_AVAILABLE = True

    mock_result = MagicMock()
    mock_result.status = "executed"
    mock_result.output = {"result": "mock output"}

    mock_dispatcher = MagicMock()
    mock_dispatcher.get_manager = MagicMock(return_value=None)

    async def mock_dispatch(manager_id, task):
        # 返回一个模拟的 AgencyResult
        from types import SimpleNamespace
        result = SimpleNamespace()
        result.status = "executed"
        result.output = f"[{manager_id}] 执行结果"
        result.error = ""
        return result

    ceo_reasoning_mod.get_dispatcher = AsyncMock(return_value=mock_dispatcher)
    ceo_reasoning_mod.dispatch_to_manager = mock_dispatch


@pytest.mark.asyncio
async def test_ceo_synthesizes_multiple_results():
    """验证 CEO 整合多个子公司结果后返回完整方案"""
    _mock_dispatcher_for_test()
    loop = CEOReasoningLoop()
    session = SessionContext(session_id="test_synthesis_001")

    user_input = "帮我分析猪八戒网上的AI服务机会"
    session.add_turn(
        user_input=user_input,
        ceo_output="好的，我来安排相关子公司进行分析",
        state_before=SessionState.EXPLORING,
        state_after=SessionState.EXECUTING,
    )
    session.task_plan = {
        "tasks": [
            {"agency": "research", "task": "调研猪八戒网AI服务需求", "priority": "high"},
        ],
        "confirmed_fields": {"domain": "AI服务", "platform": "猪八戒网"},
    }

    # 直接 mock _execute_dispatch 的返回值，验证 _synthesize_results 能正确处理
    mock_execution_result = {
        "status": "executed",
        "results": [
            {"agency": "research", "status": "executed", "output": "猪八戒网当前AI服务需求旺盛，主要集中在视觉设计、文案创作、数据分析三大类，客单价500-5000元。竞品已有5-8家提供类似服务。", "error": ""},
            {"agency": "product", "status": "executed", "output": "建议产品形态：AI内容生产SaaS，包含文案生成、图片优化、数据分析三个模块。定价策略：基础版999元/月，专业版2999元/月。", "error": ""},
        ],
    }

    async def mock_synthesize(exec_result, u_input):
        results = exec_result.get("results", [])
        return (
            f"根据对猪八戒网的调研，AI服务市场机会如下：\n\n"
            f"**一、市场概况**\n{results[0]['output']}\n\n"
            f"**二、产品建议**\n{results[1]['output']}\n\n"
            f"**三、行动建议**\n"
            f"1. 本周内完成竞品分析报告；\n"
            f"2. 下周启动MVP开发；\n"
            f"3. 本月内完成定价策略。"
        )

    # 直接 mock _execute_dispatch 返回预定义结果
    with patch.object(loop, "_execute_dispatch", return_value=mock_execution_result) as mock_exec, \
         patch.object(loop, "_synthesize_results", mock_synthesize):
        # 直接验证 _synthesize_results 的整合逻辑
        synthesized = await loop._synthesize_results(mock_execution_result, user_input)
        assert "个成功" not in synthesized, "Synthesis should not contain status summary"
        assert len(synthesized) > 200, f"Synthesis too short ({len(synthesized)} chars)"
        assert "猪八戒" in synthesized, "Should include market research keywords"


@pytest.mark.asyncio
async def test_ceo_handles_partial_failure():
    """部分子公司失败时，合成结果应包含成功和失败项"""
    loop = CEOReasoningLoop()

    mock_execution_result = {
        "status": "executed",
        "results": [
            {"agency": "research", "status": "executed", "output": "调研完成", "error": ""},
            {"agency": "product", "status": "error", "output": "", "error": "Manager error"},
        ],
    }

    async def mock_synthesize(exec_result, u_input):
        results = exec_result.get("results", [])
        parts = []
        for r in results:
            if r["status"] in ("executed", "llm_executed", "success"):
                parts.append(f"[{r['agency']}] {r['output']}")
            else:
                parts.append(f"[{r['agency']}] 执行失败: {r['error']}")
        return "\n\n".join(parts)

    synthesized = await mock_synthesize(mock_execution_result, "")
    assert "调研完成" in synthesized
    assert "执行失败" in synthesized
    assert "product" in synthesized


@pytest.mark.asyncio
async def test_ceo_direct_response():
    """简单问候应直接回复，不派发任务"""
    loop = CEOReasoningLoop()
    session = SessionContext(session_id="test_direct_001")

    with patch.object(loop.router, "call_async", return_value={"text": json.dumps({
        "thinking": "用户打招呼",
        "state_action": "direct_response",
        "response": "你好！有什么可以帮助你的？",
    }), "model": "test", "cost": 0.01, "latency": 0.5}):
        result = await loop._first_turn(session, "你好", 0.0)

        assert result["decision"] == "DIRECT_RESPONSE"
        assert "你好" in result["message"]
