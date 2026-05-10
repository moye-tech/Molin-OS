"""Level 1 — Worker 单元测试

验收标准：所有 Worker 单元测试通过，耗时 <5s
运行命令：pytest tests/test_worker_execution.py -v
"""

import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# mock redis 防止导入失败
sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.asyncio", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

from agencies.workers.research_worker import ResearchWorker
from agencies.base import Task
from agencies.worker import ExecutionPlan, ExecutionStep
from core.tools.registry import ToolRegistry, ToolResult


@pytest.mark.asyncio
async def test_research_worker_builds_plan():
    """验证 ResearchWorker 对搜索类任务生成至少一步执行计划"""
    worker = ResearchWorker()
    subtask = {"description": "分析猪八戒网上AI服务的竞品情况"}
    plan = await worker.build_plan(subtask)
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) > 0, "Plan must have at least one step"
    assert plan.steps[0].tool_name in worker.available_tools


@pytest.mark.asyncio
async def test_research_worker_plan_has_valid_tool_args():
    """验证执行计划的 tool_args 包含合理参数"""
    worker = ResearchWorker()
    subtask = {"description": "调研竞品最近动态"}
    plan = await worker.build_plan(subtask)
    step = plan.steps[0]
    assert isinstance(step.tool_args, dict)
    assert "action" in step.tool_args
    assert "query" in step.tool_args


@pytest.mark.asyncio
async def test_research_worker_browser_steps_when_url_provided():
    """当子任务包含访问网页关键词和 URL 时，生成浏览器步骤"""
    worker = ResearchWorker()
    subtask = {
        "description": "访问竞品网站查看功能",
        "context": {"url": "https://example.com"},
    }
    plan = await worker.build_plan(subtask)
    browser_steps = [s for s in plan.steps if s.tool_name == "browser_tools"]
    assert len(browser_steps) > 0, "Should have browser_tools step when URL is provided"


class _AsyncMockTool:
    """可被 await 调用的 mock 工具"""
    def __init__(self, result: ToolResult):
        self._result = result

    async def __call__(self, **kwargs):
        return self._result


@pytest.mark.asyncio
async def test_worker_execute_with_mock_tools():
    """用 mock 工具验证 Worker 执行流程，不真实调用 API"""
    mock_result = ToolResult(success=True, output="猪八戒网搜索结果...")

    with patch.object(ToolRegistry, "get_tools_for_agent", return_value={"web_tool": _AsyncMockTool(mock_result)}):
        worker = ResearchWorker()
        await worker.initialize()
        worker._tools = {"web_tool": _AsyncMockTool(mock_result)}

        subtask = {"description": "AI服务市场调研"}
        result = await worker.execute(subtask)

        assert result.success is True
        assert result.metadata["worker_id"] == "research_worker"
        assert len(result.steps) > 0


@pytest.mark.asyncio
async def test_worker_handles_tool_failure():
    """单个工具失败时 Worker 不应抛出异常"""
    fail_result = ToolResult(success=False, error="模拟工具失败")

    with patch.object(ToolRegistry, "get_tools_for_agent", return_value={"web_tool": _AsyncMockTool(fail_result)}):
        worker = ResearchWorker()
        await worker.initialize()
        worker._tools = {"web_tool": _AsyncMockTool(fail_result)}

        subtask = {"description": "搜索市场信息"}
        result = await worker.execute(subtask)

        # 工具失败但 Worker 流程正常完成
        assert result.success is False
        assert result.report is not None
        assert len(result.steps) > 0


@pytest.mark.asyncio
async def test_worker_default_plan_for_unrelated_task():
    """无关任务也应生成默认搜索计划"""
    worker = ResearchWorker()
    subtask = {"description": "随便聊聊"}
    plan = await worker.build_plan(subtask)
    assert len(plan.steps) >= 1, "Should have at least one default step"
    assert plan.steps[0].tool_name == "web_tool"
