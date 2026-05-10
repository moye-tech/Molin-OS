"""测试 Agency execute 方法 — Mock LLM 避免真实 API 调用"""
import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# 在导入任何 Agency 之前 mock redis
sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.asyncio", MagicMock())

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agencies.base import Task, AgencyResult


def make_mock_router(response_json: dict):
    """创建 mock router，返回预设的 JSON 响应"""
    mock_router = AsyncMock()
    mock_router.call_async = AsyncMock(return_value={
        "text": json.dumps(response_json, ensure_ascii=False),
        "model": "mock_model",
        "cost": 0.0,
        "latency": 0.1,
    })
    return mock_router


@pytest.mark.asyncio
async def test_edu_agency_execute():
    """教育 Agency 执行 — Mock LLM 返回课程方案"""
    from agencies.edu.agency import EduAgency

    agency = EduAgency()
    agency.router = make_mock_router({
        "course_name": "AI入门课程",
        "target_audience": "初学者",
        "duration_hours": 20,
        "modules": [{"title": "基础", "description": "基础模块", "hours": 5, "key_points": ["点1"]}],
        "learning_outcomes": ["学会AI基础"],
        "prerequisites": [],
        "quality_score": 8.0,
    })

    task = Task(task_id="test_1", task_type="edu", payload={"description": "设计一门AI入门课程"})
    result = await agency.execute(task)

    assert result.status == "success"
    assert result.agency_id == "edu"
    assert "course" in result.output
    assert result.output["quality_score"] == 8.0


@pytest.mark.asyncio
async def test_shop_agency_execute():
    """销售 Agency 执行 — Mock LLM 返回销售策略"""
    from agencies.shop.agency import ShopAgency

    agency = ShopAgency()
    agency.router = make_mock_router({
        "stage": "qualified",
        "intent": "用户咨询价格",
        "intent_score": 0.7,
        "recommended_product": "AI副业入门班",
        "recommended_tier": "entry",
        "talking_points": ["介绍课程亮点", "限时优惠"],
        "response": "您好，我们的课程...",
        "follow_up_action": "发送课程大纲",
        "quality_score": 7.5,
    })

    task = Task(task_id="test_2", task_type="shop", payload={"message": "这个课程多少钱？"})
    result = await agency.execute(task)

    assert result.status == "success"
    assert result.agency_id == "shop"
    assert result.output["recommended_tier"] == "entry"


@pytest.mark.asyncio
async def test_cs_agency_execute():
    """客服 Agency 执行 — Mock LLM 返回客服响应"""
    from agencies.cs.agency import CsAgency

    agency = CsAgency()
    agency.router = make_mock_router({
        "category": "complaint",
        "sentiment": "negative",
        "sentiment_score": -0.6,
        "urgency": "high",
        "response": "非常抱歉给您带来不便...",
        "resolution_steps": ["核实问题", "补偿方案", "跟进反馈"],
        "escalation_needed": True,
        "follow_up_required": True,
        "satisfaction_prediction": 4,
        "quality_score": 7.0,
    })

    task = Task(task_id="test_3", task_type="cs", payload={"description": "我要投诉，你们的产品有问题"})
    result = await agency.execute(task)

    assert result.status == "success"
    assert result.agency_id == "cs"
    assert result.output["category"] == "complaint"
    assert result.output["urgency"] == "high"


@pytest.mark.asyncio
async def test_growth_agency_execute():
    """增长 Agency 执行 — Mock LLM 返回增长实验方案"""
    from agencies.growth.agency import GrowthAgency

    agency = GrowthAgency()
    agency.router = make_mock_router({
        "experiment_name": "裂变拉新实验",
        "hypothesis": "邀请好友可获得优惠券",
        "channels": [{"name": "微信分享", "budget_pct": 40, "expected_cac": 15}],
        "viral_mechanics": "邀请3人成团",
        "ab_test": {"variant_a": "分享得优惠券", "variant_b": "分享得积分"},
        "timeline_days": 14,
        "expected_uplift_pct": 25.0,
        "risks": ["刷单风险"],
        "quality_score": 7.5,
    })

    task = Task(task_id="test_4", task_type="growth", payload={"description": "设计一个裂变增长实验"})
    result = await agency.execute(task)

    assert result.status == "success"
    assert result.agency_id == "growth"
    assert result.output["expected_uplift_pct"] == 25.0


@pytest.mark.asyncio
async def test_finance_agency_execute():
    """财务 Agency 执行 — Mock LLM 返回财务分析"""
    from agencies.finance.agency import FinanceAgency

    agency = FinanceAgency()
    agency.router = make_mock_router({
        "analysis_type": "roi",
        "summary": "本月ROI为2.5，较上月提升15%",
        "key_metrics": {"total_cost": 5000, "total_revenue": 12500, "roi_pct": 150, "profit_margin_pct": 60},
        "breakdown": [{"item": "广告支出", "amount": 3000, "pct_of_total": 60}],
        "alerts": ["广告成本占比偏高"],
        "recommendations": ["优化投放渠道"],
        "quality_score": 8.0,
    })

    task = Task(task_id="test_5", task_type="finance", payload={"description": "分析本月ROI"})
    result = await agency.execute(task)

    assert result.status == "success"
    assert result.agency_id == "finance"
    assert result.output["key_metrics"]["roi_pct"] == 150


@pytest.mark.asyncio
async def test_crm_agency_execute():
    """CRM Agency 执行 — Mock LLM 返回用户分层策略"""
    from agencies.crm.agency import CrmAgency

    agency = CrmAgency()
    agency.router = make_mock_router({
        "analysis_type": "rfm_segment",
        "user_segment": "高价值活跃用户",
        "key_findings": ["复购率下降", "高客单价用户占比增加"],
        "recommended_actions": [
            {"action": "推送VIP专属优惠", "channel": "私域群", "priority": "high"}
        ],
        "expected_impact": "复购率提升10%",
        "metrics_to_track": ["复购率", "客单价"],
        "quality_score": 7.5,
    })

    task = Task(task_id="test_6", task_type="crm", payload={"description": "做用户分层分析"})
    result = await agency.execute(task)

    assert result.status == "success"
    assert result.agency_id == "crm"
    assert result.output["user_segment"] == "高价值活跃用户"


@pytest.mark.asyncio
async def test_agency_load_sop():
    """验证 Agency 加载 SOP 不报错"""
    from agencies.edu.agency import EduAgency

    agency = EduAgency()
    sop = agency.load_sop()
    # SOP 应该加载成功（可能有内容也可能为空，取决于SOP文件是否存在）
    assert isinstance(sop, dict)


@pytest.mark.asyncio
async def test_agency_sop_prompt_format():
    """验证 SOP prompt 格式化正常"""
    from agencies.edu.agency import EduAgency

    agency = EduAgency()
    agency.load_sop()
    prompt = agency.get_sop_prompt()
    # 返回的应该是字符串
    assert isinstance(prompt, str)
