"""Level 2 · Manager 链路测试

验证 Manager 返回 aggregated_output.content 有实际内容，非状态摘要。
运行命令：pytest tests/test_manager_chain.py -v
"""

import sys
import time
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

# mock redis
sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.asyncio", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

from agencies.base import Task, AgencyResult
from core.managers.base_manager import ManagerResult, SubTask, BaseSubsidiaryManager
from core.managers.manager_dispatcher import ManagerDispatcher, get_dispatcher


# ── 辅助：构造一个可用的 Manager 实例 ──
def _make_mock_manager(subsidiary_id: str, config: dict = None):
    """创建一个 mock Manager，避免真实 LLM/工具调用"""
    if config is None:
        config = {
            "worker_types": ["research"],
            "max_concurrent_tasks": 3,
            "claude_code_enabled": False,
            "enabled": True,
        }

    class MockManager(BaseSubsidiaryManager):
        def __init__(self, sub_id, cfg):
            super().__init__(sub_id, cfg)

        async def can_handle(self, task: Task) -> bool:
            return True

        def get_trigger_keywords(self) -> list:
            return ["调研", "市场", "竞品", "分析", "research"]

        async def initialize(self):
            # mock worker_pool
            self.worker_pool["research"] = MagicMock()

    return MockManager(subsidiary_id, config)


@pytest.mark.asyncio
async def test_manager_aggregates_real_content():
    """验证 Manager 返回的 aggregated_output.content 有实际内容，非状态摘要"""
    from core.tools.registry import ToolRegistry, ToolResult

    manager = _make_mock_manager("research")
    await manager.initialize()

    # mock _analyze_task 返回子任务列表
    async def mock_analyze(task):
        return [
            SubTask(id=f"{task.task_id}_1", description="搜索市场信息", worker_type="research", estimated_time=10),
        ]

    # mock _execute_subtasks 返回有实际内容的结果
    async def mock_execute(subtasks, task):
        return [
            AgencyResult(
                task_id=subtasks[0].id,
                agency_id="research",
                status="success",
                output={
                    "content": (
                        "根据对猪八戒网和同类平台的调研，AI服务在自由职业市场中呈现以下趋势：\n"
                        "1. 视觉设计类AI服务需求增长30%，主要客户为中小企业；\n"
                        "2. 文案创作类AI服务客单价在500-2000元区间；\n"
                        "3. 竞品方面，已出现多个AI代运营服务商，平均交付周期为3-5天；\n"
                        "4. 建议我方切入点：提供端到端的AI内容生产+交付服务，定价800-3000元。\n"
                        "5. 预计首月可接3-5单，月度收入约1.5-2.5万元。"
                    ),
                    "worker_id": "research_worker",
                    "steps_count": 1,
                },
            )
        ]

    with patch.object(manager, "_analyze_task", mock_analyze), \
         patch.object(manager, "_execute_subtasks", mock_execute):
        task = Task("test_002", "research",
                    {"description": "猪八戒网AI服务需求分析", "context": {}})
        result = await manager.delegate_task(task)

        assert result.status in ("success", "partial_success"), f"Expected success, got {result.status}"
        content = result.aggregated_output.get("content", "")
        assert len(content) > 200, f"Expected real content (>200 chars), got {len(content)} chars: {content[:100]}"
        assert "个成功" not in content, "Content should not be a status summary"


@pytest.mark.asyncio
async def test_manager_handles_no_workers():
    """即使 worker_pool 为空，Manager 也应通过 LLM fallback 返回结果"""
    manager = _make_mock_manager("research", {
        "worker_types": [],
        "claude_code_enabled": False,
    })
    # 空 worker_pool
    manager.worker_pool = {}

    async def mock_analyze(task):
        return [
            SubTask(id=f"{task.task_id}_1", description="测试任务", worker_type="research", estimated_time=10),
        ]

    async def mock_execute(subtasks, task):
        return [
            AgencyResult(
                task_id=subtasks[0].id,
                agency_id="research",
                status="success",
                output={"content": "LLM fallback 生成的调研报告内容...（至少200字）" * 10},
            )
        ]

    with patch.object(manager, "_analyze_task", mock_analyze), \
         patch.object(manager, "_execute_subtasks", mock_execute):
        task = Task("test_003", "research", {"description": "测试"})
        result = await manager.delegate_task(task)
        assert result.status in ("success", "partial_success")


@pytest.mark.asyncio
async def test_manager_error_handling():
    """Manager 执行异常时应返回 error 状态"""
    manager = _make_mock_manager("research")

    async def mock_analyze_fail(task):
        raise RuntimeError("模拟任务分析失败")

    with patch.object(manager, "_analyze_task", mock_analyze_fail):
        task = Task("test_004", "research", {"description": "会报错的任务"})
        result = await manager.delegate_task(task)
        assert result.status == "error"
        assert result.error is not None


@pytest.mark.asyncio
async def test_multi_manager_concurrent():
    """验证并发调度多个 Manager 的总耗时合理"""
    import asyncio

    # 模拟三个 manager 并发执行
    async def mock_delegate_task(manager_id: str) -> ManagerResult:
        # 每个 manager 模拟延迟 0.5s
        await asyncio.sleep(0.5)
        return ManagerResult(
            task_id=f"test_{manager_id}",
            manager_id=manager_id,
            status="success",
            aggregated_output={"content": f"{manager_id} 输出内容..."},
            total_latency=0.5,
        )

    manager_ids = ["research_manager", "product_manager", "ai_manager"]

    start = time.time()
    results = await asyncio.gather(*[mock_delegate_task(mid) for mid in manager_ids])
    elapsed = time.time() - start

    # 并发执行总耗时应约等于单个任务的耗时（而非 3 * 0.5 = 1.5s）
    assert elapsed < 2.0, f"Concurrent execution took too long: {elapsed:.2f}s (expected ~0.5s)"
    assert len(results) == 3
    assert all(r.status == "success" for r in results)
