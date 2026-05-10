#!/usr/bin/env python3
"""
SEO工具适配器单元测试
测试SEOToolAdapter的基本功能，包括搜索意图分析、SEO质量评分、关键词密度分析等
验证适配器在seomachine项目存在和不存在时的行为
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermes_fusion.integration.external_tools.seo_tools import SEOToolAdapter, seo_tool_adapter


class TestSEOToolAdapter:
    """SEO工具适配器测试类"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = SEOToolAdapter()
        assert adapter.tool_name == "seo_analyze_intent"
        assert adapter.toolset == "seo"
        assert adapter.external_module == "data_sources.modules.search_intent_analyzer"
        assert adapter.external_function == "analyze_intent"
        assert hasattr(adapter, 'seomachine_available')
        print("✓ 适配器初始化测试通过")

    def test_analyze_search_intent_success(self):
        """测试搜索意图分析成功"""
        adapter = SEOToolAdapter()

        # 测试搜索意图分析
        keyword = "如何学习Python编程"
        result = adapter.analyze_search_intent(keyword)

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "keyword" in result["result"]
        assert "primary_intent" in result["result"]
        print("✓ 搜索意图分析测试通过")

    def test_analyze_search_intent_with_serp_features(self):
        """测试带SERP特征的搜索意图分析"""
        adapter = SEOToolAdapter()

        keyword = "最佳Python教程"
        serp_features = ["featured_snippet", "related_questions"]
        top_results = [
            {"title": "Python教程 - 从入门到精通", "description": "全面的Python学习指南", "url": "https://example.com/1"},
            {"title": "Python编程基础", "description": "Python基础语法教学", "url": "https://example.com/2"}
        ]

        result = adapter.analyze_search_intent(keyword, serp_features, top_results)

        assert result["status"] in ["success", "mock"]
        assert result["result"]["keyword"] == keyword
        print("✓ 带SERP特征的搜索意图分析测试通过")

    def test_rate_seo_quality_basic(self):
        """测试SEO质量评分基础功能"""
        adapter = SEOToolAdapter()

        content = "Python是一种流行的编程语言，广泛用于Web开发、数据分析和人工智能。"
        meta_title = "Python编程教程"
        meta_description = "学习Python编程的基础知识和高级技巧"
        primary_keyword = "Python编程"

        result = adapter.rate_seo_quality(
            content=content,
            meta_title=meta_title,
            meta_description=meta_description,
            primary_keyword=primary_keyword
        )

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "overall_score" in result["result"]
        assert "grade" in result["result"]
        print("✓ SEO质量评分基础测试通过")

    def test_rate_seo_quality_full_params(self):
        """测试SEO质量评分全参数"""
        adapter = SEOToolAdapter()

        content = "Python是一种流行的编程语言，广泛用于Web开发、数据分析和人工智能。"
        meta_title = "Python编程教程"
        meta_description = "学习Python编程的基础知识和高级技巧"
        primary_keyword = "Python编程"
        secondary_keywords = ["编程语言", "Python学习", "Python教程"]
        keyword_density = 1.5
        internal_link_count = 5
        external_link_count = 3

        result = adapter.rate_seo_quality(
            content=content,
            meta_title=meta_title,
            meta_description=meta_description,
            primary_keyword=primary_keyword,
            secondary_keywords=secondary_keywords,
            keyword_density=keyword_density,
            internal_link_count=internal_link_count,
            external_link_count=external_link_count
        )

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        print("✓ SEO质量评分全参数测试通过")

    def test_analyze_keyword_density(self):
        """测试关键词密度分析"""
        adapter = SEOToolAdapter()

        content = "Python是一种流行的编程语言，广泛用于Web开发、数据分析和人工智能。Python编程简单易学。"
        primary_keyword = "Python"
        secondary_keywords = ["编程语言"]
        target_density = 2.0

        result = adapter.analyze_keyword_density(
            content=content,
            primary_keyword=primary_keyword,
            secondary_keywords=secondary_keywords,
            target_density=target_density
        )

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "keyword" in result["result"]
        assert "density" in result["result"]
        print("✓ 关键词密度分析测试通过")

    def test_compare_content_length(self):
        """测试内容长度对比分析"""
        adapter = SEOToolAdapter()

        keyword = "Python编程教程"
        your_word_count = 1500

        result = adapter.compare_content_length(
            keyword=keyword,
            your_word_count=your_word_count
        )

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "keyword" in result["result"]
        assert "your_word_count" in result["result"]
        print("✓ 内容长度对比分析测试通过")

    def test_score_opportunity(self):
        """测试机会评分"""
        adapter = SEOToolAdapter()

        keyword = "Python编程"
        metrics = {
            "search_volume": 5000,
            "competition": 0.3,
            "current_position": 15,
            "click_through_rate": 0.05
        }
        opportunity_type = "quick_win"

        result = adapter.score_opportunity(
            keyword=keyword,
            metrics=metrics,
            opportunity_type=opportunity_type
        )

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "keyword" in result["result"]
        assert "opportunity_type" in result["result"]
        print("✓ 机会评分测试通过")

    def test_adapter_with_mock_external_module(self):
        """测试适配器与模拟外部模块的集成"""
        adapter = SEOToolAdapter()

        # 模拟外部模块不存在的情况
        with patch('importlib.util.find_spec', return_value=None):
            # 重新检查可用性
            available = adapter._check_seomachine_availability()
            assert not available
            print("✓ 外部模块不可用处理测试通过")

    def test_global_adapter_instance(self):
        """测试全局适配器实例"""
        assert seo_tool_adapter is not None
        assert isinstance(seo_tool_adapter, SEOToolAdapter)
        assert seo_tool_adapter.tool_name == "seo_analyze_intent"
        print("✓ 全局适配器实例测试通过")


def run_all_tests():
    """运行所有测试"""
    test = TestSEOToolAdapter()

    print("开始运行SEO工具适配器单元测试...")
    print("=" * 60)

    tests = [
        test.test_adapter_initialization,
        test.test_analyze_search_intent_success,
        test.test_analyze_search_intent_with_serp_features,
        test.test_rate_seo_quality_basic,
        test.test_rate_seo_quality_full_params,
        test.test_analyze_keyword_density,
        test.test_compare_content_length,
        test.test_score_opportunity,
        test.test_adapter_with_mock_external_module,
        test.test_global_adapter_instance
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