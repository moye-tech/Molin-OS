"""
墨麟 Hermes OS — 核心模块测试
"""

import pytest
from pathlib import Path


class TestCoreEngine:
    """核心引擎测试"""

    def test_import_engine(self):
        from molin.core.engine import MolinEngine
        engine = MolinEngine()
        assert engine is not None

    def test_health_check(self):
        from molin.core.engine import engine
        result = engine.health_check()
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "departments" in result
        assert result["departments"] == 6

    def test_heartbeat(self):
        from molin.core.engine import engine
        result = engine.heartbeat()
        assert result["type"] == "heartbeat"
        assert "daily_brief" in result

    def test_company_config_default(self):
        from molin.core.engine import MolinEngine
        engine = MolinEngine()
        config = engine.company_config
        assert config["name"] == "墨麟 AI"
        assert config["budget_monthly"] == 1360
        assert len(config["departments"]) == 6


class TestGovernance:
    """治理系统测试"""

    def test_import_governance(self):
        from molin.core.governance import Governance
        gov = Governance()
        assert gov is not None

    def test_submit_decision(self):
        from molin.core.governance import Governance
        gov = Governance()
        dec = gov.submit("测试决策", 50, "content")
        assert dec.status == "pending"
        assert dec.level.value == 2  # L2 — 需要人工确认

    def test_auto_approve_l0(self):
        from molin.core.governance import Governance
        gov = Governance()
        dec = gov.submit("零成本任务", 0, "engineering")
        assert gov.auto_approve(dec) is True
        assert dec.status == "approved"

    def test_needs_human_approval(self):
        from molin.core.governance import Governance
        gov = Governance()
        dec_l2 = gov.submit("中额决策", 50, "content")
        dec_l3 = gov.submit("大额决策", 500, "ceo_office")
        assert gov.needs_human_approval(dec_l2) is True
        assert gov.needs_human_approval(dec_l3) is True


class TestCEOAgent:
    """CEO智能体测试"""

    def test_import_ceo(self):
        from molin.agents.ceo import CEOAgent
        ceo = CEOAgent()
        assert ceo.MISSION

    def test_run_strategy(self):
        from molin.agents.ceo import CEOAgent
        ceo = CEOAgent()
        result = ceo.run_strategy()
        assert "mission" in result
        assert "okr" in result
        assert "analysis" in result
        assert "decisions" in result


class TestSwarmEngine:
    """蜂群引擎测试"""

    def test_import_swarm(self):
        from molin.agents.swarm import SwarmEngine
        swarm = SwarmEngine()
        assert len(swarm.ROLES) == 7

    def test_assign_content_task(self):
        from molin.agents.swarm import SwarmEngine
        swarm = SwarmEngine()
        task = swarm.assign_task("content", "生成一篇小红书内容")
        assert task["type"] == "content"
        assert len(task["agents_assigned"]) == 3


class TestContentEngine:
    """内容引擎测试"""

    def test_xhs_generate(self):
        from molin.content.xiaohongshu import XiaohongshuEngine
        engine = XiaohongshuEngine()
        result = engine.generate("AI工具推荐")
        assert result["platform"] == "小红书"
        assert "content" in result

    def test_video_generate(self):
        from molin.content.video import VideoPipeline
        pipe = VideoPipeline()
        result = pipe.create_text_video("测试视频", 15)
        assert result["type"] == "text_animation"
        assert result["no_gpu_required"] is True

    def test_seo_generate(self):
        from molin.content.seo import SEOEngine
        engine = SEOEngine()
        result = engine.generate("AI一人公司")
        assert result["seo_score"] >= 0


class TestPublish:
    """发布引擎测试"""

    def test_social_push(self):
        from molin.publish.social_push import SocialPush, Content, Platform
        push = SocialPush()
        content = Content(
            platform=Platform.XIAOHONGSHU,
            title="测试标题",
            body="测试内容",
        )
        result = push.publish(content)
        assert result["platform"] == "xiaohongshu"

    def test_xianyu_store(self):
        from molin.publish.xianyu import XianyuStore
        store = XianyuStore()
        products = store.list_products()
        assert len(products) == 6  # 6标准商品
        assert products[0].price == 800


class TestIntelligence:
    """情报系统测试"""

    def test_trends(self):
        from molin.intelligence.trends import TrendsMonitor
        monitor = TrendsMonitor()
        result = monitor.run()
        assert "top_trends" in result
        assert len(result["top_trends"]) > 0


class TestBusiness:
    """商业引擎测试"""

    def test_bp_generate(self):
        from molin.business.bp import BusinessPlanGenerator
        gen = BusinessPlanGenerator()
        result = gen.generate("测试项目")
        assert result["sections_generated"] > 0

    def test_prd_generate(self):
        from molin.business.prd import PRDGenerator
        gen = PRDGenerator()
        result = gen.generate("测试产品")
        assert "P0_必须" in result["document_structure"]["3_核心功能"]


class TestSelfLearning:
    """自学习循环测试"""

    def test_learning_loop(self):
        from molin.agents.learner import SelfLearningLoop
        learner = SelfLearningLoop()
        result = learner.run()
        assert result["cycle"] == 1
        assert len(result["phases"]) == 4
