"""墨麟OS — Plan Mode单元测试"""
import pytest
import asyncio
from molib.ceo.plan_mode import PlanMode, ApprovalRequest


def test_needs_approval():
    """审批判断逻辑"""
    pm = PlanMode()
    assert pm.needs_approval(45) is False
    assert pm.needs_approval(65) is True
    assert pm.needs_approval(85) is True
    assert pm.needs_approval(60) is False  # 等于60不需要
    assert pm.needs_approval(61) is True


def test_parse_response():
    """飞书回复解析"""
    pm = PlanMode()
    assert pm.parse_response("批准 task-test-001") == ("approve", "task-test-001", "")
    assert pm.parse_response("拒绝 task-test-002 预算不够") == ("reject", "task-test-002", "预算不够")
    assert pm.parse_response("approve task-test-003") == ("approve", "task-test-003", "")
    assert pm.parse_response("reject task-test-004 风险高") == ("reject", "task-test-004", "风险高")
    assert pm.parse_response("随便说说") is None
    assert pm.parse_response("") is None


@pytest.mark.asyncio
async def test_lifecycle():
    """审批生命周期：pending→approved"""
    pm = PlanMode()
    r = await pm.request_approval("task-lc-001", 70, "测试", "operation", ["vp_ops"], [], "生命周期测试")
    assert r.status == "pending"
    
    pm.approve("task-lc-001", "没问题")
    assert r.status == "approved"
    assert r.response == "approved"


@pytest.mark.asyncio
async def test_rejection():
    """拒绝流程"""
    pm = PlanMode()
    r = await pm.request_approval("task-rej-001", 90, "高风险", "finance", ["vp_finance"], [])
    assert r.status == "pending"
    
    pm.reject("task-rej-001", "不批准")
    assert r.status == "rejected"
    assert r.response == "rejected"


def test_build_card():
    """审批卡片格式"""
    pm = PlanMode()
    r = ApprovalRequest(
        task_id="task-card-001", risk_score=75, risk_reason="大额操作",
        intent_type="finance", target_vps=["vp_finance"],
        target_subsidiaries=["墨算财务"], description="审批",
        budget_estimate=5000,
    )
    card = pm._build_card(r)
    assert "Plan Mode" in card
    assert "task-card-001" in card
    assert "75" in card
    assert "墨算财务" in card


def test_get_pending_and_history():
    """待审批列表和历史记录"""
    pm = PlanMode()
    assert len(pm.get_pending()) == 0
    assert len(pm.get_history()) == 0
