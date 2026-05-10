#!/usr/bin/env python3
"""
CLI工具适配器单元测试
测试CLIToolAdapter的基本功能，包括命令执行、脚本执行、批量执行
验证适配器在OpenCLI项目存在和不存在时的行为
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermes_fusion.integration.external_tools.cli_tools import CLIToolAdapter, cli_tool_adapter


class TestCLIToolAdapter:
    """CLI工具适配器测试类"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        adapter = CLIToolAdapter()
        assert adapter.tool_name == "cli_execute_command"
        assert adapter.toolset == "cli"
        assert adapter.external_module == "opencli.command"
        assert adapter.external_function == "execute"
        print("✓ 适配器初始化测试通过")

    def test_execute_command_success(self):
        """测试成功执行命令"""
        adapter = CLIToolAdapter()

        # 测试执行简单命令
        result = adapter.execute_command("echo", ["Hello, World"])

        assert result["status"] == "success"
        assert "Hello, World" in result.get("result", {}).get("stdout", "")
        assert result["result"]["exit_code"] == 0
        print("✓ 命令执行成功测试通过")

    def test_execute_command_timeout(self):
        """测试命令执行超时"""
        adapter = CLIToolAdapter()

        # 测试超时命令（sleep 2秒，但设置1秒超时）
        result = adapter.execute_command("sleep", ["2"], timeout=1)

        assert result["status"] == "error"
        assert "超时" in result.get("error", "")
        print("✓ 命令超时测试通过")

    def test_execute_command_not_found(self):
        """测试命令未找到"""
        adapter = CLIToolAdapter()

        # 测试不存在的命令
        result = adapter.execute_command("nonexistent_command_xyz")

        assert result["status"] == "error"
        assert "未找到" in result.get("error", "")
        print("✓ 命令未找到测试通过")

    def test_execute_script_success(self):
        """测试脚本执行成功"""
        adapter = CLIToolAdapter()

        # 创建简单脚本
        script_content = """#!/bin/bash
echo "Script test"
echo "Multiple lines"
exit 0
"""

        result = adapter.execute_script(script_content, interpreter="bash")

        assert result["status"] == "success"
        assert "Script test" in result.get("result", {}).get("stdout", "")
        assert "Multiple lines" in result.get("result", {}).get("stdout", "")
        print("✓ 脚本执行成功测试通过")

    def test_execute_script_failure(self):
        """测试脚本执行失败"""
        adapter = CLIToolAdapter()

        # 创建会失败的脚本
        script_content = """#!/bin/bash
echo "This will fail"
exit 1
"""

        result = adapter.execute_script(script_content, interpreter="bash")

        assert result["status"] == "success"  # 脚本执行本身成功，但退出码非0
        assert result["result"]["exit_code"] == 1
        print("✓ 脚本执行失败（退出码非0）测试通过")

    def test_batch_execute_success(self):
        """测试批量执行成功"""
        adapter = CLIToolAdapter()

        commands = [
            {"command": "echo", "args": ["First command"]},
            {"command": "echo", "args": ["Second command"]},
            {"command": "echo", "args": ["Third command"]}
        ]

        result = adapter.batch_execute(commands)

        assert result["status"] in ["success", "partial_success"]
        assert result["total_commands"] == 3
        assert result["successful_commands"] == 3
        print("✓ 批量执行成功测试通过")

    def test_batch_execute_with_stop_on_error(self):
        """测试批量执行（错误时停止）"""
        adapter = CLIToolAdapter()

        commands = [
            {"command": "echo", "args": ["This will succeed"]},
            {"command": "nonexistent_command_xyz", "args": []},
            {"command": "echo", "args": ["This should not run"]}
        ]

        result = adapter.batch_execute(commands, stop_on_error=True)

        assert result["status"] == "partial_success"
        assert result["total_commands"] == 3
        assert result["failed_commands"] >= 1
        print("✓ 批量执行错误时停止测试通过")

    def test_adapter_with_mock_external_module(self):
        """测试适配器与模拟外部模块的集成"""
        adapter = CLIToolAdapter()

        # 模拟外部模块不存在的情况
        with patch('importlib.import_module', side_effect=ImportError("No module named 'opencli'")):
            # 加载外部模块应该失败
            load_success = adapter.load_external()
            assert not load_success
            print("✓ 外部模块加载失败处理测试通过")

    def test_global_adapter_instance(self):
        """测试全局适配器实例"""
        assert cli_tool_adapter is not None
        assert isinstance(cli_tool_adapter, CLIToolAdapter)
        assert cli_tool_adapter.tool_name == "cli_execute_command"
        print("✓ 全局适配器实例测试通过")


def run_all_tests():
    """运行所有测试"""
    test = TestCLIToolAdapter()

    print("开始运行CLI工具适配器单元测试...")
    print("=" * 60)

    tests = [
        test.test_adapter_initialization,
        test.test_execute_command_success,
        test.test_execute_command_timeout,
        test.test_execute_command_not_found,
        test.test_execute_script_success,
        test.test_execute_script_failure,
        test.test_batch_execute_success,
        test.test_batch_execute_with_stop_on_error,
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