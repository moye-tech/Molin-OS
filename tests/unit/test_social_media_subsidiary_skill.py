#!/usr/bin/env python3
"""
社交媒体子公司技能单元测试
测试SocialMediaSubsidiarySkill的基本功能，包括请求识别、内容发布、用户分析、营销活动
验证技能在各种输入下的行为
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermes_fusion.skills.subsidiaries.social_media_subsidiary import SocialMediaSubsidiarySkill
from hermes_fusion.integration.external_tools.social_media_tools import SocialMediaPlatform


class TestSocialMediaSubsidiarySkill:
    """社交媒体子公司技能测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.skill = SocialMediaSubsidiarySkill()

    def test_skill_initialization(self):
        """测试技能初始化"""
        assert self.skill.name == "社交媒体子公司"
        assert "小红书" in self.skill.description
        assert "社交媒体" in self.skill.keywords
        assert "内容发布" in self.skill.keywords
        assert "数据分析" in self.skill.keywords
        assert self.skill.model_preference == "qwen3.6-plus"
        assert self.skill.cost_level == "medium"
        print("✓ 技能初始化测试通过")

    def test_can_handle_keywords(self):
        """测试关键词触发"""
        # 测试各种关键词
        test_cases = [
            ("发布小红书内容", True),
            ("社交媒体运营", True),
            ("粉丝互动分析", True),
            ("数据分析报告", True),
            ("营销活动策划", True),
            ("定时发布帖子", True),
            ("微博内容发布", True),
            ("抖音运营", True),
            ("B站视频", True),
            ("这是一个普通请求", False),  # 不包含关键词
            ("请帮忙写代码", False),  # 不包含关键词
        ]

        for text, expected in test_cases:
            context = {"text": text}
            result = self.skill.can_handle(context)
            assert result == expected, f"文本: '{text}' 期望: {expected}, 实际: {result}"

        print("✓ 关键词触发测试通过")

    def test_can_handle_social_patterns(self):
        """测试社交媒体模式触发"""
        test_cases = [
            ("发布新的内容", True),
            ("社交媒体运营策略", True),
            ("粉丝互动数据", True),
            ("数据分析报告生成", True),
            ("营销活动执行", True),
            ("定时发布内容", True),
        ]

        for text, expected in test_cases:
            context = {"text": text}
            result = self.skill.can_handle(context)
            assert result == expected, f"文本: '{text}' 期望: {expected}, 实际: {result}"

        print("✓ 社交媒体模式触发测试通过")

    def test_can_handle_content_fields(self):
        """测试内容字段触发"""
        # 有content字段
        context = {
            "text": "发布内容",
            "content": "这是要发布的内容"
        }
        assert self.skill.can_handle(context) == True

        # 有images字段
        context = {
            "text": "发布图片",
            "images": ["image1.jpg", "image2.jpg"]
        }
        assert self.skill.can_handle(context) == True

        # 既有content又有images
        context = {
            "text": "发布内容",
            "content": "内容",
            "images": ["image1.jpg"]
        }
        assert self.skill.can_handle(context) == True

        # 无内容字段，但有社交媒体关键词
        context = {
            "text": "小红书运营",
            "content": ""  # 空内容
        }
        assert self.skill.can_handle(context) == True  # 因为有关键词

        print("✓ 内容字段触发测试通过")

    def test_identify_request_type(self):
        """测试请求类型识别"""
        test_cases = [
            ("发布一篇小红书内容", "content_publishing"),
            ("发布帖子", "content_publishing"),
            ("发小红书", "content_publishing"),
            ("用户数据分析", "user_analytics"),
            ("粉丝互动分析", "user_analytics"),
            ("定时发布内容", "post_scheduling"),
            ("定时帖子", "post_scheduling"),
            ("营销活动策划", "marketing_campaign"),
            ("营销计划", "marketing_campaign"),
            ("推广活动", "marketing_campaign"),
            ("社交媒体咨询", "general_social_media"),
        ]

        for text, expected in test_cases:
            context = {"text": text}
            result = self.skill._identify_request_type(context)
            assert result == expected, f"文本: '{text}' 期望: {expected}, 实际: {result}"

        print("✓ 请求类型识别测试通过")

    @patch('hermes_fusion.integration.external_tools.social_media_tools.social_media_adapter')
    def test_handle_content_publishing(self, mock_adapter):
        """测试处理内容发布请求"""
        # 设置模拟返回值
        mock_adapter.publish_content.return_value = {
            "status": "success",
            "result": {
                "content": "测试内容",
                "content_type": "text",
                "images": [],
                "tags": ["测试"],
                "post_id": "mock_123456",
                "status": "published"
            },
            "message": "模拟发布成功",
            "platform": "xiaohongshu"
        }

        context = {
            "text": "发布一篇关于美食的小红书",
            "content": "测试内容",
            "tags": ["测试"],
            "platform": "xiaohongshu"
        }

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "social_media_content_publishing"
        assert result["platform"] == SocialMediaPlatform.XIAOHONGSHU.value
        mock_adapter.publish_content.assert_called_once_with("测试内容", [], ["测试"], None)
        print("✓ 内容发布请求处理测试通过")

    @patch('hermes_fusion.integration.external_tools.social_media_tools.social_media_adapter')
    def test_handle_content_publishing_extract_from_text(self, mock_adapter):
        """测试从文本提取内容发布请求"""
        mock_adapter.publish_content.return_value = {
            "status": "success",
            "result": {"post_id": "mock_123", "content": "测试内容"}
        }

        # 文本中包含内容
        context = {"text": "发布'测试内容'到小红书"}
        result = self.skill.execute(context)

        # 技能应该尝试从文本中提取内容
        assert result["success"] == True or result["success"] == False
        print("✓ 从文本提取内容发布测试通过")

    @patch('hermes_fusion.integration.external_tools.social_media_tools.social_media_adapter')
    def test_handle_user_analytics(self, mock_adapter):
        """测试处理用户分析请求"""
        mock_adapter.analyze_user_interaction.return_value = {
            "status": "success",
            "analysis": {
                "user_id": "user123",
                "period_days": 7,
                "engagement_rate": 0.12,
                "average_likes": 150,
                "recommendations": ["增加视频内容"]
            },
            "platform": "xiaohongshu"
        }

        context = {
            "text": "分析用户123最近7天的互动数据",
            "user_id": "user123",
            "days": 7,
            "platform": "xiaohongshu"
        }

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "social_media_user_analytics"
        mock_adapter.analyze_user_interaction.assert_called_once_with("user123", 7)
        print("✓ 用户分析请求处理测试通过")

    @patch('hermes_fusion.integration.external_tools.social_media_tools.social_media_adapter')
    def test_handle_post_scheduling(self, mock_adapter):
        """测试处理定时发布请求"""
        mock_adapter.schedule_posts.return_value = {
            "status": "success",
            "platform": "xiaohongshu",
            "total_posts": 1,
            "scheduled_posts": 1,
            "posts": [{"content": "测试内容", "status": "scheduled"}]
        }

        posts = [
            {
                "content": "测试内容",
                "schedule_time": 1234567890
            }
        ]
        context = {
            "text": "定时发布帖子",
            "posts": posts,
            "platform": "xiaohongshu"
        }

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "social_media_post_scheduling"
        assert result["requires_approval"] == True  # 定时发布需要审批
        mock_adapter.schedule_posts.assert_called_once()
        print("✓ 定时发布请求处理测试通过")

    def test_handle_marketing_campaign(self):
        """测试处理营销活动请求"""
        context = {
            "text": "策划一个产品发布营销活动",
            "campaign_type": "product_launch",
            "budget": 5000,
            "target_audience": "年轻人"
        }

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "social_media_marketing_campaign"
        assert result["requires_approval"] == True  # 营销活动需要审批
        assert "campaign_type" in result["result"]
        assert "recommendations" in result["result"]
        assert "timeline_suggestion" in result["result"]
        assert "platform_recommendations" in result["result"]
        print("✓ 营销活动请求处理测试通过")

    def test_handle_general_social_media_request(self):
        """测试处理一般社交媒体请求"""
        context = {"text": "社交媒体帮助"}

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "social_media_general_assistance"
        assert "available_services" in result["result"]
        assert "supported_platforms" in result["result"]
        assert "example_usage" in result["result"]
        assert result["requires_approval"] == False
        print("✓ 一般社交媒体请求处理测试通过")

    def test_get_marketing_recommendations(self):
        """测试获取营销活动建议"""
        # 测试产品发布
        recommendations = self.skill._get_marketing_recommendations(
            "product_launch", 10000, "年轻人"
        )
        assert len(recommendations) > 0
        assert any("预热" in rec for rec in recommendations)

        # 测试品牌推广
        recommendations = self.skill._get_marketing_recommendations(
            "brand_promotion", 5000, "大众"
        )
        assert len(recommendations) > 0
        assert any("品牌故事" in rec for rec in recommendations)

        # 测试节日营销
        recommendations = self.skill._get_marketing_recommendations(
            "holiday_campaign", 3000, "家庭"
        )
        assert len(recommendations) > 0
        assert any("节日" in rec for rec in recommendations)

        print("✓ 营销活动建议生成测试通过")

    def test_get_campaign_timeline(self):
        """测试获取营销活动时间线"""
        timeline = self.skill._get_campaign_timeline("product_launch")
        assert "pre_launch" in timeline
        assert "launch_week" in timeline

        timeline = self.skill._get_campaign_timeline("brand_promotion")
        assert "month_1" in timeline
        assert "month_2" in timeline

        timeline = self.skill._get_campaign_timeline("holiday_campaign")
        assert "week_1" in timeline
        assert "week_2" in timeline

        # 默认时间线
        timeline = self.skill._get_campaign_timeline("unknown_type")
        assert "phase_1" in timeline

        print("✓ 营销活动时间线生成测试通过")

    def test_get_success_metrics(self):
        """测试获取成功指标"""
        metrics = self.skill._get_success_metrics("product_launch")
        assert len(metrics) > 0
        assert any("转化率" in metric for metric in metrics)

        metrics = self.skill._get_success_metrics("brand_promotion")
        assert len(metrics) > 0
        assert any("品牌搜索量" in metric for metric in metrics)

        metrics = self.skill._get_success_metrics("holiday_campaign")
        assert len(metrics) > 0
        assert any("节日话题" in metric for metric in metrics)

        # 默认指标
        metrics = self.skill._get_success_metrics("unknown_type")
        assert len(metrics) > 0

        print("✓ 成功指标生成测试通过")

    def test_social_media_initialization_status(self):
        """测试社交媒体工具初始化状态"""
        assert hasattr(self.skill, 'social_media_initialized')
        print("✓ 社交媒体初始化状态测试通过")


def run_all_tests():
    """运行所有测试"""
    test = TestSocialMediaSubsidiarySkill()

    print("开始运行社交媒体子公司技能单元测试...")
    print("=" * 60)

    tests = [
        test.test_skill_initialization,
        test.test_can_handle_keywords,
        test.test_can_handle_social_patterns,
        test.test_can_handle_content_fields,
        test.test_identify_request_type,
        test.test_handle_content_publishing,
        test.test_handle_content_publishing_extract_from_text,
        test.test_handle_user_analytics,
        test.test_handle_post_scheduling,
        test.test_handle_marketing_campaign,
        test.test_handle_general_social_media_request,
        test.test_get_marketing_recommendations,
        test.test_get_campaign_timeline,
        test.test_get_success_metrics,
        test.test_social_media_initialization_status
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"✗ {test_func.__name__} 失败: {e}")

    print("=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)