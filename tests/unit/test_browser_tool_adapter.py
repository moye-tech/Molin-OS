#!/usr/bin/env python3
"""
浏览器工具适配器单元测试
测试BrowserToolAdapter的基本功能，包括网页抓取、截图、脚本执行等
验证适配器在多种浏览器引擎不可用时的模拟模式
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermes_fusion.integration.external_tools.browser_tools import BrowserToolAdapter, browser_tool_adapter


class TestBrowserToolAdapter:
    """浏览器工具适配器测试类"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = BrowserToolAdapter()
        assert adapter.tool_name == "browser_fetch_url"
        assert adapter.toolset == "browser"
        assert adapter.external_module is None  # 无外部Python模块
        assert adapter.external_function is None
        assert hasattr(adapter, 'lightpanda_available')
        assert hasattr(adapter, 'playwright_available')
        assert hasattr(adapter, 'selenium_available')
        print("✓ 适配器初始化测试通过")

    def test_fetch_url_success(self):
        """测试网页抓取成功"""
        adapter = BrowserToolAdapter()

        url = "https://example.com"
        result = adapter.fetch_url(url)

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "url" in result.get("result", {})
        print("✓ 网页抓取测试通过")

    def test_fetch_url_with_options(self):
        """测试带选项的网页抓取"""
        adapter = BrowserToolAdapter()

        url = "https://example.com"
        result = adapter.fetch_url(
            url=url,
            output_format="markdown",
            wait_until="networkidle",
            wait_ms=2000,
            wait_selector="#content",
            obey_robots=True,
            log_level="info"
        )

        assert result["status"] in ["success", "mock"]
        assert result["result"]["url"] == url
        print("✓ 带选项的网页抓取测试通过")

    def test_take_screenshot(self):
        """测试网页截图"""
        adapter = BrowserToolAdapter()

        url = "https://example.com"
        result = adapter.take_screenshot(url)

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "url" in result["result"]
        print("✓ 网页截图测试通过")

    def test_take_screenshot_with_options(self):
        """测试带选项的网页截图"""
        adapter = BrowserToolAdapter()

        url = "https://example.com"
        result = adapter.take_screenshot(
            url=url,
            output_path="/tmp/screenshot.png",
            full_page=True,
            viewport_size={"width": 1920, "height": 1080},
            wait_until="networkidle"
        )

        assert result["status"] in ["success", "mock"]
        assert result["result"]["url"] == url
        print("✓ 带选项的网页截图测试通过")

    def test_execute_script(self):
        """测试执行浏览器脚本"""
        adapter = BrowserToolAdapter()

        url = "https://example.com"
        script = "return document.title;"
        result = adapter.execute_script(url, script)

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        assert "url" in result["result"]
        assert "script" in result["result"]
        print("✓ 执行浏览器脚本测试通过")

    def test_execute_script_with_options(self):
        """测试带选项的执行浏览器脚本"""
        adapter = BrowserToolAdapter()

        url = "https://example.com"
        script = "return {title: document.title, url: window.location.href};"
        result = adapter.execute_script(
            url=url,
            script=script,
            wait_until="networkidle",
            timeout=30000
        )

        assert result["status"] in ["success", "mock"]
        assert result["result"]["url"] == url
        print("✓ 带选项的执行浏览器脚本测试通过")

    def test_start_cdp_server(self):
        """测试启动CDP服务器"""
        adapter = BrowserToolAdapter()

        result = adapter.start_cdp_server(
            host="127.0.0.1",
            port=9222,
            obey_robots=True,
            log_level="info"
        )

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        print("✓ 启动CDP服务器测试通过")

    def test_stop_cdp_server(self):
        """测试停止CDP服务器"""
        adapter = BrowserToolAdapter()

        result = adapter.stop_cdp_server()

        assert result["status"] in ["success", "mock"]
        assert "result" in result
        print("✓ 停止CDP服务器测试通过")

    def test_fetch_url_mock_mode(self):
        """测试模拟模式下的网页抓取"""
        adapter = BrowserToolAdapter()

        # 强制启用模拟模式
        adapter.lightpanda_available = False
        adapter.playwright_available = False
        adapter.selenium_available = False

        url = "https://example.com"
        result = adapter.fetch_url(url)

        assert result["status"] in ["success", "mock"]
        assert result["source"] == "mock"
        print("✓ 模拟模式下的网页抓取测试通过")

    def test_adapter_with_mock_external_module(self):
        """测试适配器与模拟外部模块的集成"""
        adapter = BrowserToolAdapter()

        # 模拟所有浏览器引擎都不可用
        with patch.object(adapter, '_check_lightpanda_availability', return_value=False):
            with patch.object(adapter, '_check_playwright_availability', return_value=False):
                with patch.object(adapter, '_check_selenium_availability', return_value=False):
                    # 测试模拟模式
                    result = adapter.fetch_url("https://example.com")
                    assert result["source"] == "mock"
                    print("✓ 所有浏览器引擎不可用时的模拟模式测试通过")

    def test_global_adapter_instance(self):
        """测试全局适配器实例"""
        assert browser_tool_adapter is not None
        assert isinstance(browser_tool_adapter, BrowserToolAdapter)
        assert browser_tool_adapter.tool_name == "browser_fetch_page"
        print("✓ 全局适配器实例测试通过")


def run_all_tests():
    """运行所有测试"""
    test = TestBrowserToolAdapter()

    print("开始运行浏览器工具适配器单元测试...")
    print("=" * 60)

    tests = [
        test.test_adapter_initialization,
        test.test_fetch_url_success,
        test.test_fetch_url_with_options,
        test.test_take_screenshot,
        test.test_take_screenshot_with_options,
        test.test_execute_script,
        test.test_execute_script_with_options,
        test.test_start_cdp_server,
        test.test_stop_cdp_server,
        test.test_fetch_url_mock_mode,
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