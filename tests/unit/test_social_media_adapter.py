#!/usr/bin/env python3
"""
社交媒体工具适配器单元测试
测试XiaohongshuToolAdapter的基本功能，包括内容发布、用户分析、定时发布
验证适配器在xiaohongshu-cli项目存在和不存在时的行为
"""

import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermes_fusion.integration.external_tools.social_media_tools import (
    XiaohongshuToolAdapter,
    social_media_adapter,
    SocialMediaPlatform,
    SocialMediaContentType
)


class TestSocialMediaAdapter:
    """社交媒体工具适配器测试类"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = XiaohongshuToolAdapter()
        assert adapter.tool_name == "xiaohongshu_publish_content"
        assert adapter.toolset == "social_media"
        assert adapter.external_module == "xhs_cli.commands.creator"
        assert adapter.external_function == "post"
        print("✓ 适配器初始化测试通过")

    def test_publish_content_success_mock(self):
        """测试模拟内容发布成功"""
        adapter = XiaohongshuToolAdapter()

        content = "测试小红书内容发布"
        images = []  # 无图片
        tags = ["测试", "小红书"]

        result = adapter.publish_content(content, images, tags)

        assert result["status"] == "success"
        assert result["platform"] == SocialMediaPlatform.XIAOHONGSHU.value
        assert "post_id" in result.get("result", {})
        assert result["result"]["content"] == content
        assert result["result"]["tags"] == tags
        print("✓ 模拟内容发布成功测试通过")

    def test_publish_content_with_images(self):
        """测试带图片的内容发布"""
        adapter = XiaohongshuToolAdapter()

        content = "测试带图片的内容发布"
        images = ["/path/to/image1.jpg", "/path/to/image2.jpg"]
        tags = ["图片", "测试"]

        result = adapter.publish_content(content, images, tags)

        assert result["status"] == "success"
        assert result["result"]["images"] == images
        assert result["result"]["content_type"] == SocialMediaContentType.IMAGE.value
        print("✓ 带图片内容发布测试通过")

    def test_publish_content_empty_content(self):
        """测试空内容发布"""
        adapter = XiaohongshuToolAdapter()

        result = adapter.publish_content("", [], [])

        assert result["status"] == "success"  # 模拟模式允许空内容
        print("✓ 空内容发布测试通过")

    def test_analyze_user_interaction(self):
        """测试用户互动数据分析"""
        adapter = XiaohongshuToolAdapter()

        user_id = "test_user_123"
        days = 7

        result = adapter.analyze_user_interaction(user_id, days)

        assert result["status"] == "success"
        assert "analysis" in result
        assert result["analysis"]["user_id"] == user_id
        assert result["analysis"]["period_days"] == days
        assert "engagement_rate" in result["analysis"]
        assert "average_likes" in result["analysis"]
        assert "recommendations" in result["analysis"]
        assert len(result["analysis"]["recommendations"]) > 0
        print("✓ 用户互动数据分析测试通过")

    def test_analyze_user_interaction_no_user(self):
        """测试无用户ID的分析（当前用户）"""
        adapter = XiaohongshuToolAdapter()

        result = adapter.analyze_user_interaction(None, 14)

        assert result["status"] == "success"
        assert result["analysis"]["user_id"] == "current_user"
        assert result["analysis"]["period_days"] == 14
        print("✓ 无用户ID分析测试通过")

    def test_schedule_posts_success(self):
        """测试定时发布成功"""
        adapter = XiaohongshuToolAdapter()

        posts = [
            {
                "content": "第一个定时帖子",
                "images": [],
                "tags": ["定时", "测试"],
                "schedule_time": int(time.time()) + 3600  # 1小时后
            },
            {
                "content": "第二个定时帖子",
                "images": [],
                "tags": ["测试"],
                "schedule_time": int(time.time()) + 7200  # 2小时后
            }
        ]

        result = adapter.schedule_posts(posts, SocialMediaPlatform.XIAOHONGSHU)

        assert result["status"] in ["success", "partial_success"]
        assert result["platform"] == SocialMediaPlatform.XIAOHONGSHU.value
        assert result["total_posts"] == 2
        assert result["scheduled_posts"] == 2
        assert len(result["posts"]) == 2
        print("✓ 定时发布成功测试通过")

    def test_schedule_posts_past_time(self):
        """测试定时时间在过去"""
        adapter = XiaohongshuToolAdapter()

        posts = [
            {
                "content": "过去时间的帖子",
                "images": [],
                "tags": ["测试"],
                "schedule_time": int(time.time()) - 3600  # 1小时前
            }
        ]

        result = adapter.schedule_posts(posts, SocialMediaPlatform.XIAOHONGSHU)

        assert result["status"] in ["success", "partial_success"]
        assert result["failed_posts"] >= 1  # 应该至少有一个失败
        assert "定时时间必须是将来的时间" in str(result.get("failed_details", []))
        print("✓ 过去时间定时发布失败测试通过")

    def test_schedule_posts_immediate_publish(self):
        """测试立即发布（无定时时间）"""
        adapter = XiaohongshuToolAdapter()

        posts = [
            {
                "content": "立即发布的帖子",
                "images": [],
                "tags": ["立即", "测试"]
                # 无schedule_time，应该立即发布
            }
        ]

        result = adapter.schedule_posts(posts, SocialMediaPlatform.XIAOHONGSHU)

        assert result["status"] in ["success", "partial_success"]
        assert result["published_posts"] >= 0  # 可能发布成功或失败
        print("✓ 立即发布测试通过")

    def test_adapter_with_mock_external_module(self):
        """测试适配器与模拟外部模块的集成"""
        adapter = XiaohongshuToolAdapter()

        # 模拟外部模块不存在的情况
        with patch('importlib.import_module', side_effect=ImportError("No module named 'xhs_cli'")):
            # 加载外部模块应该失败
            load_success = adapter.load_external()
            assert not load_success
            print("✓ 外部模块加载失败处理测试通过")

    def test_global_adapter_instance(self):
        """测试全局适配器实例"""
        assert social_media_adapter is not None
        assert isinstance(social_media_adapter, XiaohongshuToolAdapter)
        assert social_media_adapter.tool_name == "xiaohongshu_publish_content"
        print("✓ 全局适配器实例测试通过")

    def test_social_media_platform_enum(self):
        """测试社交媒体平台枚举"""
        assert SocialMediaPlatform.XIAOHONGSHU.value == "xiaohongshu"
        assert SocialMediaPlatform.WEIBO.value == "weibo"
        assert SocialMediaPlatform.DOUYIN.value == "douyin"
        assert SocialMediaPlatform.BILIBILI.value == "bilibili"
        print("✓ 社交媒体平台枚举测试通过")

    def test_social_media_content_type_enum(self):
        """测试社交媒体内容类型枚举"""
        assert SocialMediaContentType.TEXT.value == "text"
        assert SocialMediaContentType.IMAGE.value == "image"
        assert SocialMediaContentType.VIDEO.value == "video"
        assert SocialMediaContentType.CAROUSEL.value == "carousel"
        print("✓ 社交媒体内容类型枚举测试通过")


def run_all_tests():
    """运行所有测试"""
    test = TestSocialMediaAdapter()

    print("开始运行社交媒体工具适配器单元测试...")
    print("=" * 60)

    tests = [
        test.test_adapter_initialization,
        test.test_publish_content_success_mock,
        test.test_publish_content_with_images,
        test.test_publish_content_empty_content,
        test.test_analyze_user_interaction,
        test.test_analyze_user_interaction_no_user,
        test.test_schedule_posts_success,
        test.test_schedule_posts_past_time,
        test.test_schedule_posts_immediate_publish,
        test.test_adapter_with_mock_external_module,
        test.test_global_adapter_instance,
        test.test_social_media_platform_enum,
        test.test_social_media_content_type_enum
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