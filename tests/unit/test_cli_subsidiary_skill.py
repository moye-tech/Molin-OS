#!/usr/bin/env python3
"""
CLI工具子公司技能单元测试
测试CLISubsidiarySkill的基本功能，包括请求识别、命令执行、脚本执行、批量执行
验证技能在各种输入下的行为
"""

import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermes_fusion.skills.subsidiaries.cli_subsidiary import CLISubsidiarySkill


class TestCLISubsidiarySkill:
    """CLI工具子公司技能测试类"""

    def __init__(self):
        """初始化测试类"""
        self.skill = CLISubsidiarySkill()

    def test_skill_initialization(self):
        """测试技能初始化"""
        assert self.skill.name == "CLI工具子公司"
        assert self.skill.description == "负责命令行工具执行、脚本自动化、系统管理等业务"
        assert "命令行" in self.skill.keywords
        assert "CLI" in self.skill.keywords
        assert self.skill.model_preference == "claude-3-sonnet"
        assert self.skill.cost_level == "medium"
        print("✓ 技能初始化测试通过")

    def test_can_handle_keywords(self):
        """测试关键词触发"""
        # 测试各种关键词
        test_cases = [
            ("执行ls命令", True),
            ("运行Python脚本", True),
            ("批量执行命令", True),
            ("系统管理任务", True),
            ("终端操作", True),
            ("shell脚本", True),
            ("这是一个普通请求", False),  # 不包含关键词
            ("请帮忙写代码", False),  # 不包含关键词
        ]

        for text, expected in test_cases:
            context = {"text": text}
            result = self.skill.can_handle(context)
            assert result == expected, f"文本: '{text}' 期望: {expected}, 实际: {result}"

        print("✓ 关键词触发测试通过")

    def test_can_handle_command_patterns(self):
        """测试命令模式触发"""
        test_cases = [
            ("执行系统命令", True),
            ("运行bash脚本", True),
            ("批量执行任务", True),
            ("shell脚本执行", True),
            ("终端操作管理", True),
        ]

        for text, expected in test_cases:
            context = {"text": text}
            result = self.skill.can_handle(context)
            assert result == expected, f"文本: '{text}' 期望: {expected}, 实际: {result}"

        print("✓ 命令模式触发测试通过")

    def test_can_handle_code_field(self):
        """测试code字段触发"""
        # 包含shell脚本的code字段
        context = {
            "text": "运行这个脚本",
            "code": "#!/bin/bash\necho 'Hello'\n"
        }
        assert self.skill.can_handle(context) == True

        # 包含Python代码的code字段
        context = {
            "text": "执行代码",
            "code": "import os\nprint('Hello')"
        }
        assert self.skill.can_handle(context) == True

        # 不包含命令标记的code字段
        context = {
            "text": "普通文本",
            "code": "这是一段普通文本"
        }
        assert self.skill.can_handle(context) == False

        print("✓ code字段触发测试通过")

    def test_identify_request_type(self):
        """测试请求类型识别"""
        test_cases = [
            ("执行ls命令", "command_execution"),
            ("运行脚本", "script_execution"),
            ("批量执行", "batch_execution"),
            ("系统管理", "system_management"),
            ("配置服务器", "system_management"),
            ("安装软件", "system_management"),
            ("一般CLI请求", "general_cli"),
        ]

        for text, expected in test_cases:
            context = {"text": text}
            result = self.skill._identify_request_type(context)
            assert result == expected, f"文本: '{text}' 期望: {expected}, 实际: {result}"

        print("✓ 请求类型识别测试通过")

    @patch('hermes_fusion.integration.external_tools.cli_tools.cli_tool_adapter')
    def test_handle_command_execution(self, mock_adapter):
        """测试处理命令执行请求"""
        # 设置模拟返回值
        mock_adapter.execute_command.return_value = {
            "status": "success",
            "result": {
                "success": True,
                "stdout": "Hello, World\n",
                "stderr": "",
                "exit_code": 0,
                "execution_time": 0.1
            },
            "command": "echo Hello, World",
            "execution_time": 0.1
        }

        context = {
            "text": "执行echo Hello, World命令",
            "command": "echo",
            "args": ["Hello, World"]
        }

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "cli_command_execution"
        assert result["requires_approval"] == False
        mock_adapter.execute_command.assert_called_once_with("echo", ["Hello, World"], 30)
        print("✓ 命令执行请求处理测试通过")

    @patch('hermes_fusion.integration.external_tools.cli_tools.cli_tool_adapter')
    def test_handle_script_execution(self, mock_adapter):
        """测试处理脚本执行请求"""
        mock_adapter.execute_script.return_value = {
            "status": "success",
            "result": {
                "success": True,
                "stdout": "Script output\n",
                "stderr": "",
                "exit_code": 0,
                "execution_time": 0.2
            },
            "execution_time": 0.2
        }

        script_content = "#!/bin/bash\necho 'Script output'"
        context = {
            "text": "运行这个脚本",
            "code": script_content
        }

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "cli_script_execution"
        mock_adapter.execute_script.assert_called_once_with(script_content, "bash", 60)
        print("✓ 脚本执行请求处理测试通过")

    @patch('hermes_fusion.integration.external_tools.cli_tools.cli_tool_adapter')
    def test_handle_batch_execution(self, mock_adapter):
        """测试处理批量执行请求"""
        mock_adapter.batch_execute.return_value = {
            "status": "success",
            "total_commands": 2,
            "successful_commands": 2,
            "failed_commands": 0,
            "results": [
                {"index": 0, "command": "echo first", "result": {"status": "success"}},
                {"index": 1, "command": "echo second", "result": {"status": "success"}}
            ]
        }

        commands = [
            {"command": "echo", "args": ["first"]},
            {"command": "echo", "args": ["second"]}
        ]
        context = {
            "text": "批量执行命令",
            "commands": commands
        }

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "cli_batch_execution"
        mock_adapter.batch_execute.assert_called_once_with(commands, False)
        print("✓ 批量执行请求处理测试通过")

    def test_handle_system_management(self):
        """测试处理系统管理请求"""
        context = {"text": "安装Python软件包"}

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "system_management"
        assert result["requires_approval"] == True  # 系统管理需要审批
        assert "task_type" in result["result"]
        assert "recommendations" in result["result"]
        assert "example_commands" in result["result"]
        print("✓ 系统管理请求处理测试通过")

    def test_handle_general_cli_request(self):
        """测试处理一般CLI请求"""
        context = {"text": "CLI工具帮助"}

        result = self.skill.execute(context)

        assert result["success"] == True
        assert result["service"] == "cli_general_assistance"
        assert "available_services" in result["result"]
        assert "example_usage" in result["result"]
        assert result["requires_approval"] == False
        print("✓ 一般CLI请求处理测试通过")

    def test_extract_command_from_text(self):
        """测试从文本提取命令"""
        # 测试有明确命令的情况
        context = {"text": "执行 ls -la 命令"}
        result = self.skill._handle_command_execution(context)
        # 即使没有模拟适配器，也应该返回错误（因为没有命令）
        assert result["success"] == False
        assert "未提供要执行的命令" in result.get("error", "")

        print("✓ 从文本提取命令测试通过")

    def test_cli_initialization_status(self):
        """测试CLI工具初始化状态"""
        # 技能初始化时会尝试初始化CLI工具
        # 这里只是验证技能有初始化状态属性
        assert hasattr(self.skill, 'cli_initialized')
        print("✓ CLI初始化状态测试通过")


def run_all_tests():
    """运行所有测试"""
    test = TestCLISubsidiarySkill()

    print("开始运行CLI工具子公司技能单元测试...")
    print("=" * 60)

    tests = [
        test.test_skill_initialization,
        test.test_can_handle_keywords,
        test.test_can_handle_command_patterns,
        test.test_can_handle_code_field,
        test.test_identify_request_type,
        test.test_handle_command_execution,
        test.test_handle_script_execution,
        test.test_handle_batch_execution,
        test.test_handle_system_management,
        test.test_handle_general_cli_request,
        test.test_extract_command_from_text,
        test.test_cli_initialization_status
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