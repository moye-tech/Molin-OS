#!/usr/bin/env python3
"""
项目管理工具适配器单元测试

测试 PMToolAdapter 类的功能，包括技能验证、项目结构分析、模板创建、任务分解、风险评估等
"""

import sys
import os
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hermes_fusion.integration.external_tools.pm_tools import PMToolAdapter


class TestPMToolAdapter(unittest.TestCase):
    """项目管理工具适配器测试类"""

    def setUp(self):
        """设置测试环境"""
        self.adapter = PMToolAdapter()

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        self.assertEqual(self.adapter.tool_name, "pm_validate_skill")
        self.assertEqual(self.adapter.external_module, "validate_plugins")
        self.assertEqual(self.adapter.external_function, "validate_skill")
        self.assertEqual(self.adapter.toolset, "pm")

    def test_validate_skill_simulation(self):
        """测试技能验证（模拟模式）"""
        # 测试技能验证
        skill_path = "/mock/path/to/skill"
        result = self.adapter.validate_skill(skill_path, "skill")

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "skill验证完成（模拟模式）")
        self.assertEqual(result["source"], "mock")
        self.assertEqual(result["is_valid"], True)
        self.assertIn("errors", result)
        self.assertIn("warnings", result)
        self.assertIn("info", result)

        # 验证警告信息
        self.assertIn("模拟验证", result["warnings"][0])

    def test_validate_command_simulation(self):
        """测试命令验证（模拟模式）"""
        # 测试命令验证
        command_path = "/mock/path/to/command.md"
        result = self.adapter.validate_skill(command_path, "command")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "command验证完成（模拟模式）")
        self.assertEqual(result["is_valid"], True)

    def test_validate_manifest_simulation(self):
        """测试清单验证（模拟模式）"""
        # 测试清单验证
        manifest_path = "/mock/path/to/plugin"
        result = self.adapter.validate_skill(manifest_path, "manifest")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "manifest验证完成（模拟模式）")

    def test_validate_readme_simulation(self):
        """测试README验证（模拟模式）"""
        # 测试README验证
        readme_path = "/mock/path/to/project"
        result = self.adapter.validate_skill(readme_path, "readme")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "readme验证完成（模拟模式）")

    def test_validate_skill_invalid_type(self):
        """测试无效验证类型"""
        # 测试无效验证类型
        result = self.adapter.validate_skill("/mock/path", "invalid_type")

        self.assertEqual(result["status"], "error")
        self.assertIn("不支持验证类型", result["message"])
        self.assertIn("invalid_type", result["errors"][0])

    def test_analyze_project_structure_simulation(self):
        """测试项目结构分析（模拟模式）"""
        # 测试项目结构分析
        project_path = "/mock/project/path"
        result = self.adapter.analyze_project_structure(project_path, analysis_depth=2)

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "项目结构分析完成（模拟模式）")
        self.assertEqual(result["source"], "mock")
        self.assertIn("project_type", result)
        self.assertIn("structure", result)
        self.assertIn("skills_found", result)
        self.assertIn("commands_found", result)
        self.assertIn("analysis_depth", result)
        self.assertIn("total_files", result)
        self.assertIn("total_directories", result)

        # 验证结构数据
        structure = result["structure"]
        self.assertEqual(structure["name"], Path(project_path).name)
        self.assertEqual(structure["type"], "directory")
        self.assertEqual(structure["path"], project_path)
        self.assertIn("children", structure)

        # 验证技能和命令
        self.assertEqual(result["skills_found"], 1)
        self.assertEqual(result["commands_found"], 1)
        self.assertEqual(len(result["skills"]), 1)
        self.assertEqual(len(result["commands"]), 1)

    def test_analyze_project_structure_different_depths(self):
        """测试不同深度的项目结构分析"""
        # 测试深度1
        result_depth1 = self.adapter.analyze_project_structure("/mock/path", analysis_depth=1)
        self.assertEqual(result_depth1["analysis_depth"], 1)

        # 测试深度3
        result_depth3 = self.adapter.analyze_project_structure("/mock/path", analysis_depth=3)
        self.assertEqual(result_depth3["analysis_depth"], 3)

    def test_create_project_template_basic(self):
        """测试创建基础项目模板"""
        # 测试基础模板
        result = self.adapter.create_project_template(
            template_type="basic",
            project_name="MyProject",
            parameters={"description": "测试项目"}
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "basic模板创建成功（模拟模式）")
        self.assertEqual(result["template_type"], "basic")
        self.assertEqual(result["project_name"], "MyProject")
        self.assertIn("structure", result)
        self.assertIn("files_created", result)
        self.assertIn("next_steps", result)
        self.assertIn("template_metadata", result)
        self.assertEqual(result["source"], "mock")

        # 验证模板元数据
        metadata = result["template_metadata"]
        self.assertEqual(metadata["framework"], "Basic")
        self.assertEqual(metadata["mode"], "mock")

    def test_create_project_template_agile(self):
        """测试创建敏捷项目模板"""
        # 测试敏捷模板
        result = self.adapter.create_project_template(
            template_type="agile",
            project_name="AgileProject",
            parameters={"sprint_length": "2 weeks"}
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "agile模板创建成功（模拟模式）")
        self.assertEqual(result["template_type"], "agile")
        self.assertEqual(result["project_name"], "AgileProject")

    def test_create_project_template_product(self):
        """测试创建产品项目模板"""
        # 测试产品模板
        result = self.adapter.create_project_template(
            template_type="product",
            project_name="ProductProject",
            parameters={"market": "B2B"}
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "product模板创建成功（模拟模式）")
        self.assertEqual(result["template_type"], "product")

    def test_perform_task_decomposition_agile(self):
        """测试敏捷方法论任务分解"""
        # 测试敏捷任务分解
        project_goal = "开发新的电商平台"
        result = self.adapter.perform_task_decomposition(
            project_goal=project_goal,
            complexity_level="medium",
            methodology="agile"
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "任务分解完成（模拟模式）")
        self.assertEqual(result["project_goal"], project_goal)
        self.assertEqual(result["methodology"], "agile")
        self.assertEqual(result["complexity_level"], "medium")
        self.assertIn("total_tasks", result)
        self.assertIn("tasks", result)
        self.assertIn("estimates", result)
        self.assertIn("dependencies", result)
        self.assertIn("recommendations", result)
        self.assertEqual(result["source"], "mock")

        # 验证任务数据
        tasks = result["tasks"]
        self.assertGreater(len(tasks), 0)

        for task in tasks:
            self.assertIn("id", task)
            self.assertIn("name", task)
            self.assertIn("description", task)
            self.assertIn("type", task)
            self.assertIn("estimated_hours", task)
            self.assertIn("priority", task)
            self.assertIn("dependencies", task)
            self.assertIn("status", task)
            self.assertTrue(task["id"].startswith("task_"))

        # 验证估算数据
        estimates = result["estimates"]
        self.assertIn("total_tasks", estimates)
        self.assertIn("estimated_hours", estimates)
        self.assertIn("adjusted_hours", estimates)
        self.assertIn("estimated_weeks", estimates)
        self.assertIn("methodology_adjustment", estimates)
        self.assertIn("team_size_recommendation", estimates)

        # 验证依赖关系
        dependencies = result["dependencies"]
        if dependencies:
            for dep in dependencies:
                self.assertIn("from", dep)
                self.assertIn("to", dep)
                self.assertIn("type", dep)
                self.assertIn("description", dep)

    def test_perform_task_decomposition_waterfall(self):
        """测试瀑布方法论任务分解"""
        # 测试瀑布任务分解
        result = self.adapter.perform_task_decomposition(
            project_goal="构建企业ERP系统",
            complexity_level="complex",
            methodology="waterfall"
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["methodology"], "waterfall")
        self.assertEqual(result["complexity_level"], "complex")

    def test_perform_task_decomposition_scrum(self):
        """测试Scrum方法论任务分解"""
        # 测试Scrum任务分解
        result = self.adapter.perform_task_decomposition(
            project_goal="移动应用开发",
            complexity_level="simple",
            methodology="scrum"
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["methodology"], "scrum")
        self.assertEqual(result["complexity_level"], "simple")

    def test_perform_task_decomposition_kanban(self):
        """测试Kanban方法论任务分解"""
        # 测试Kanban任务分解
        result = self.adapter.perform_task_decomposition(
            project_goal="持续改进项目",
            complexity_level="medium",
            methodology="kanban"
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["methodology"], "kanban")

    def test_assess_project_risk_basic(self):
        """测试基本风险评估"""
        # 测试风险评估
        project_context = {
            "name": "测试项目",
            "complexity": "medium",
            "budget": 100000,
            "timeline": "6 months"
        }

        risk_factors = ["schedule", "budget", "scope"]

        result = self.adapter.assess_project_risk(
            project_context=project_context,
            risk_factors=risk_factors
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "风险评估完成（模拟模式）")
        self.assertEqual(result["risk_factors_analyzed"], risk_factors)
        self.assertIn("risk_score", result)
        self.assertIn("risk_level", result)
        self.assertIn("risk_analysis", result)
        self.assertIn("mitigation_strategies", result)
        self.assertIn("recommendations", result)
        self.assertEqual(result["source"], "mock")

        # 验证风险评分
        risk_score = result["risk_score"]
        self.assertGreaterEqual(risk_score, 1)
        self.assertLessEqual(risk_score, 10)

        # 验证风险级别
        risk_level = result["risk_level"]
        self.assertIn(risk_level, ["low", "medium", "high", "critical"])

        # 验证风险分析
        risk_analysis = result["risk_analysis"]
        self.assertIn("factors", risk_analysis)
        self.assertIn("highest_risk", risk_analysis)
        self.assertIn("average_score", risk_analysis)

        # 验证最高风险
        highest_risk = risk_analysis["highest_risk"]
        self.assertIn("factor", highest_risk)
        self.assertIn("score", highest_risk)

        # 验证缓解策略
        strategies = result["mitigation_strategies"]
        if strategies:
            for strategy in strategies:
                self.assertIn("risk_factor", strategy)
                self.assertIn("risk_level", strategy)
                self.assertIn("current_score", strategy)
                self.assertIn("mitigation_strategy", strategy)
                self.assertIn("target_score", strategy)
                self.assertIn("timeline", strategy)
                self.assertIn("owner", strategy)

    def test_assess_project_risk_all_factors(self):
        """测试所有风险因素评估"""
        # 测试所有风险因素
        project_context = {"complexity": "high"}
        all_factors = ["schedule", "budget", "scope", "quality", "resources", "technology"]

        result = self.adapter.assess_project_risk(
            project_context=project_context,
            risk_factors=all_factors
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["risk_factors_analyzed"]), len(all_factors))

        # 验证每个风险因素的分析
        risk_analysis = result["risk_analysis"]["factors"]
        for factor in all_factors:
            self.assertIn(factor, risk_analysis)
            factor_analysis = risk_analysis[factor]
            self.assertIn("score", factor_analysis)
            self.assertIn("level", factor_analysis)
            self.assertIn("description", factor_analysis)
            self.assertIn("mitigation", factor_analysis)

    def test_assess_project_risk_empty_context(self):
        """测试空上下文风险评估"""
        # 测试空上下文
        result = self.adapter.assess_project_risk(
            project_context={},
            risk_factors=["schedule"]
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("risk_score", result)

    def test_adapter_with_mock_external_module(self):
        """测试适配器使用模拟外部模块的情况"""
        # 在模拟模式下测试所有主要方法
        test_cases = [
            ("validate_skill", ("/mock/path", "skill")),
            ("analyze_project_structure", ("/mock/project", 2)),
            ("create_project_template", ("basic", "TestProject", None)),
            ("perform_task_decomposition", ("Test Goal", "medium", "agile")),
            ("assess_project_risk", ({"name": "Test"}, ["schedule"])),
        ]

        for method_name, args in test_cases:
            method = getattr(self.adapter, method_name)

            try:
                result = method(*args)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["source"], "mock")
            except Exception as e:
                self.fail(f"方法 {method_name} 失败: {e}")

    def test_check_pm_skills_availability(self):
        """测试pm-skills可用性检查"""
        # 由于我们还没有安装pm-skills，应该返回False或True
        availability = self.adapter.pm_skills_available

        # 可以是False或True，取决于环境
        self.assertIsInstance(availability, bool)

        # 如果返回False，确保模拟方法正常工作
        if not availability:
            result = self.adapter.validate_skill("/mock", "skill")
            self.assertEqual(result["source"], "mock")

    def test_error_handling_invalid_path(self):
        """测试无效路径错误处理"""
        # 测试不存在的路径
        result = self.adapter.analyze_project_structure("/this/path/does/not/exist")

        # 在模拟模式下，应该仍然返回成功
        self.assertEqual(result["status"], "success")
        self.assertIn("模拟模式", result["message"])


if __name__ == "__main__":
    unittest.main()