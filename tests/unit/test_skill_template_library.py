#!/usr/bin/env python3
"""
技能模板库单元测试

测试 SkillTemplateLibrary 类的功能，包括模板管理、技能创建、验证、质量分析等
"""

import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hermes_fusion.skills.templates.skill_template_library import (
    SkillTemplateLibrary, SkillTemplate, SkillCategory, SkillComplexity
)


class TestSkillTemplateLibrary(unittest.TestCase):
    """技能模板库测试类"""

    def setUp(self):
        """设置测试环境"""
        self.library = SkillTemplateLibrary()

    def test_library_initialization(self):
        """测试库初始化"""
        # 验证库已初始化
        self.assertIsInstance(self.library, SkillTemplateLibrary)
        self.assertIsInstance(self.library.templates, dict)
        self.assertGreater(len(self.library.templates), 0)

        # 验证默认模板已加载
        self.assertIn("spec-driven-development", self.library.templates)
        self.assertIn("planning-and-task-breakdown", self.library.templates)
        self.assertIn("code-review-and-quality", self.library.templates)

    def test_get_template_existing(self):
        """测试获取现有模板"""
        # 测试获取现有模板
        template = self.library.get_template("spec-driven-development")

        self.assertIsNotNone(template)
        self.assertEqual(template.name, "spec-driven-development")
        self.assertEqual(template.category, SkillCategory.DEFINE)
        self.assertEqual(template.complexity, SkillComplexity.INTERMEDIATE)
        self.assertIn("Spec before code", template.description)

    def test_get_template_nonexistent(self):
        """测试获取不存在的模板"""
        # 测试获取不存在的模板
        template = self.library.get_template("non-existent-template")

        self.assertIsNone(template)

    def test_list_templates_all(self):
        """测试列出所有模板"""
        # 测试列出所有模板
        templates = self.library.list_templates()

        self.assertGreater(len(templates), 0)
        self.assertIsInstance(templates[0], SkillTemplate)

        # 验证模板按名称排序
        template_names = [t.name for t in templates]
        self.assertEqual(template_names, sorted(template_names))

    def test_list_templates_by_category(self):
        """测试按类别列出模板"""
        # 测试按DEFINE类别筛选
        define_templates = self.library.list_templates(category=SkillCategory.DEFINE)

        self.assertGreater(len(define_templates), 0)
        for template in define_templates:
            self.assertEqual(template.category, SkillCategory.DEFINE)

        # 测试按BUILD类别筛选
        build_templates = self.library.list_templates(category=SkillCategory.BUILD)

        self.assertGreater(len(build_templates), 0)
        for template in build_templates:
            self.assertEqual(template.category, SkillCategory.BUILD)

    def test_list_templates_by_complexity(self):
        """测试按复杂度列出模板"""
        # 测试按基础复杂度筛选
        basic_templates = self.library.list_templates(complexity=SkillComplexity.BASIC)

        if basic_templates:  # 可能没有BASIC复杂度的模板
            for template in basic_templates:
                self.assertEqual(template.complexity, SkillComplexity.BASIC)

        # 测试按高级复杂度筛选
        advanced_templates = self.library.list_templates(complexity=SkillComplexity.ADVANCED)

        if advanced_templates:
            for template in advanced_templates:
                self.assertEqual(template.complexity, SkillComplexity.ADVANCED)

    def test_list_templates_by_category_and_complexity(self):
        """测试按类别和复杂度列出模板"""
        # 测试组合筛选
        intermediate_build_templates = self.library.list_templates(
            category=SkillCategory.BUILD,
            complexity=SkillComplexity.INTERMEDIATE
        )

        if intermediate_build_templates:
            for template in intermediate_build_templates:
                self.assertEqual(template.category, SkillCategory.BUILD)
                self.assertEqual(template.complexity, SkillComplexity.INTERMEDIATE)

    def test_create_skill_from_template_valid(self):
        """测试从有效模板创建技能"""
        # 测试从有效模板创建技能
        result = self.library.create_skill_from_template(
            template_name="spec-driven-development",
            skill_name="需求驱动开发技能",
            skill_description="基于规格驱动的开发方法",
            custom_fields={
                "requirements": "明确的功能需求列表",
                "acceptance_criteria": "验收标准定义",
                "user_stories": "用户故事描述"
            }
        )

        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertIn("从模板'spec-driven-development'创建技能成功", result["message"])
        self.assertIn("skill_definition", result)
        self.assertIn("template_used", result)
        self.assertIn("next_steps", result)

        # 验证技能定义
        skill_def = result["skill_definition"]
        self.assertEqual(skill_def["name"], "需求驱动开发技能")
        self.assertEqual(skill_def["description"], "基于规格驱动的开发方法")
        self.assertEqual(skill_def["template"], "spec-driven-development")
        self.assertEqual(skill_def["category"], "define")
        self.assertEqual(skill_def["complexity"], "intermediate")
        self.assertIn("content", skill_def)
        self.assertIn("metadata", skill_def)

        # 验证内容字段
        content = skill_def["content"]
        self.assertIn("requirements", content)
        self.assertIn("acceptance_criteria", content)
        self.assertIn("user_stories", content)

        # 验证模板信息
        template_used = result["template_used"]
        self.assertEqual(template_used["name"], "spec-driven-development")

    def test_create_skill_from_template_invalid(self):
        """测试从无效模板创建技能"""
        # 测试从无效模板创建
        result = self.library.create_skill_from_template(
            template_name="non-existent-template",
            skill_name="测试技能",
            skill_description="测试描述"
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("模板不存在", result["message"])
        self.assertIn("available_templates", result)

    def test_create_skill_from_template_minimal(self):
        """测试从模板创建技能（最小参数）"""
        # 测试最小参数创建
        result = self.library.create_skill_from_template(
            template_name="planning-and-task-breakdown",
            skill_name="任务分解技能",
            skill_description="任务分解和规划方法"
        )

        self.assertEqual(result["status"], "success")

        # 验证必填字段占位符
        skill_def = result["skill_definition"]
        content = skill_def["content"]

        # 模板的必填字段应该有占位符
        template = self.library.get_template("planning-and-task-breakdown")
        for field in template.required_fields:
            self.assertIn(field, content)
            self.assertIn(f"请提供{field}", content[field])

    def test_validate_skill_definition_valid(self):
        """测试验证有效技能定义"""
        # 创建有效的技能定义
        skill_definition = {
            "name": "测试技能",
            "description": "这是一个测试技能",
            "template": "spec-driven-development",
            "content": {
                "name": "测试技能",
                "description": "这是一个测试技能",
                "requirements": "测试需求",
                "acceptance_criteria": "测试验收标准"
            }
        }

        result = self.library.validate_skill_definition(skill_definition)

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertIn("summary", result)

    def test_validate_skill_definition_missing_fields(self):
        """测试验证缺少字段的技能定义"""
        # 创建缺少必填字段的技能定义
        skill_definition = {
            "name": "测试技能",
            # 缺少description
            "template": "spec-driven-development",
            "content": {
                "name": "测试技能"
                # 缺少description, requirements, acceptance_criteria
            }
        }

        result = self.library.validate_skill_definition(skill_definition)

        # 应该有错误
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["errors"]), 0)
        self.assertIn("缺少必填字段", result["errors"][0])

    def test_validate_skill_definition_no_template(self):
        """测试验证无模板的技能定义"""
        # 创建无模板的技能定义
        skill_definition = {
            "name": "测试技能",
            "description": "这是一个测试技能",
            "content": {
                "name": "测试技能",
                "description": "这是一个测试技能"
            }
        }

        result = self.library.validate_skill_definition(skill_definition)

        # 无模板时只检查通用字段
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["is_valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_skill_definition_quality_warnings(self):
        """测试验证技能定义的质量警告"""
        # 创建描述过短的技能定义
        skill_definition = {
            "name": "测试技能",
            "description": "短描述",
            "content": {
                "name": "测试技能",
                "description": "短描述"
            }
        }

        result = self.library.validate_skill_definition(skill_definition)

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["is_valid"])
        # 应该有警告
        self.assertGreater(len(result["warnings"]), 0)
        self.assertIn("过短", result["warnings"][0])

    def test_generate_skill_markdown_basic(self):
        """测试生成基本技能Markdown"""
        # 创建基本技能定义
        skill_definition = {
            "name": "测试技能",
            "description": "这是一个测试技能描述",
            "content": {
                "when_to_use": "在需要测试时使用",
                "process": ["步骤1: 准备", "步骤2: 执行", "步骤3: 验证"],
                "examples": ["示例1: 测试用例", "示例2: 测试场景"]
            }
        }

        markdown = self.library.generate_skill_markdown(skill_definition)

        # 验证Markdown结构
        self.assertIsInstance(markdown, str)
        self.assertGreater(len(markdown), 0)

        # 验证包含关键部分
        self.assertIn("# 测试技能", markdown)
        self.assertIn("**这是一个测试技能描述**", markdown)
        self.assertIn("## 使用时机", markdown)
        self.assertIn("## 过程", markdown)
        self.assertIn("## 示例", markdown)
        self.assertIn("步骤1: 准备", markdown)

    def test_generate_skill_markdown_without_frontmatter(self):
        """测试生成无前置元数据的Markdown"""
        # 创建技能定义
        skill_definition = {
            "name": "测试技能",
            "description": "测试描述",
            "content": {}
        }

        markdown = self.library.generate_skill_markdown(
            skill_definition,
            include_frontmatter=False
        )

        # 验证不包含YAML前置元数据
        self.assertNotIn("---", markdown)
        self.assertIn("# 测试技能", markdown)

    def test_generate_skill_markdown_complete(self):
        """测试生成完整技能Markdown"""
        # 创建完整技能定义
        skill_definition = {
            "name": "完整测试技能",
            "description": "完整的技能描述",
            "content": {
                "when_to_use": ["场景1", "场景2"],
                "process": [
                    {"title": "准备阶段", "description": "准备工作"},
                    {"title": "执行阶段", "description": "执行任务"}
                ],
                "examples": [
                    {"场景": "测试场景", "步骤": "具体步骤", "结果": "预期结果"}
                ],
                "checklist": ["检查项1", "检查项2"],
                "common_pitfalls": ["常见错误1", "常见错误2"],
                "best_practices": ["最佳实践1", "最佳实践2"]
            }
        }

        markdown = self.library.generate_skill_markdown(skill_definition)

        # 验证所有部分
        sections = [
            "# 完整测试技能",
            "## 使用时机",
            "## 过程",
            "### 准备阶段",
            "### 执行阶段",
            "## 示例",
            "## 检查清单",
            "## 常见陷阱",
            "## 最佳实践"
        ]

        for section in sections:
            self.assertIn(section, markdown)

    def test_analyze_skill_quality_basic(self):
        """测试分析基本技能质量"""
        # 创建基本技能定义
        skill_definition = {
            "name": "测试技能",
            "description": "这是一个详细的技能描述，包含具体的方法和步骤",
            "template": "spec-driven-development",
            "content": {
                "name": "测试技能",
                "description": "这是一个详细的技能描述，包含具体的方法和步骤",
                "requirements": "明确的需求",
                "acceptance_criteria": "验收标准",
                "when_to_use": "使用时机描述",
                "process": ["步骤1", "步骤2", "步骤3"],
                "examples": ["示例1", "示例2"]
            }
        }

        result = self.library.analyze_skill_quality(skill_definition)

        # 验证结果结构
        self.assertEqual(result["status"], "success")
        self.assertIn("overall_score", result)
        self.assertIn("quality_level", result)
        self.assertIn("category_scores", result)
        self.assertIn("recommendations", result)
        self.assertIn("skill_metadata", result)

        # 验证分数范围
        overall_score = result["overall_score"]
        self.assertGreaterEqual(overall_score, 0)
        self.assertLessEqual(overall_score, 100)

        # 验证类别分数
        category_scores = result["category_scores"]
        expected_categories = ["completeness", "clarity", "actionability", "structure", "examples"]
        for category in expected_categories:
            self.assertIn(category, category_scores)
            score = category_scores[category]
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

    def test_analyze_skill_quality_minimal(self):
        """测试分析最小技能质量"""
        # 创建最小技能定义
        skill_definition = {
            "name": "最小技能",
            "description": "短",
            "content": {
                "name": "最小技能",
                "description": "短"
            }
        }

        result = self.library.analyze_skill_quality(skill_definition)

        self.assertEqual(result["status"], "success")
        # 最小技能应该分数较低
        overall_score = result["overall_score"]
        self.assertLess(overall_score, 60)  # 应该低于良好线

    def test_search_templates_by_name(self):
        """测试按名称搜索模板"""
        # 搜索"spec"
        results = self.library.search_templates("spec")

        self.assertGreater(len(results), 0)

        # 验证结果包含spec-driven-development
        spec_templates = [r for r in results if "spec-driven-development" in r["template"]["name"]]
        self.assertGreater(len(spec_templates), 0)

        # 验证结果结构
        for result in results:
            self.assertIn("template", result)
            self.assertIn("match_score", result)
            self.assertIn("matched_fields", result)
            self.assertGreater(result["match_score"], 0)

    def test_search_templates_by_description(self):
        """测试按描述搜索模板"""
        # 搜索"code review"
        results = self.library.search_templates("code review")

        if results:  # 可能有匹配结果
            for result in results:
                self.assertGreater(result["match_score"], 0)

    def test_search_templates_no_results(self):
        """测试无结果搜索"""
        # 搜索不存在的术语
        results = self.library.search_templates("xyz123nonexistent")

        self.assertEqual(len(results), 0)

    def test_search_templates_specific_fields(self):
        """测试指定字段搜索"""
        # 只在名称中搜索
        results = self.library.search_templates("development", search_fields=["name"])

        if results:
            for result in results:
                self.assertIn("development", result["template"]["name"].lower())

    def test_get_development_workflow_complete(self):
        """测试获取完整开发工作流"""
        result = self.library.get_development_workflow()

        self.assertEqual(result["status"], "success")
        self.assertIn("complete_workflow", result)
        self.assertIn("phases", result)
        self.assertIn("total_templates", result)

        # 验证阶段
        phases = result["phases"]
        expected_phases = ["define", "plan", "build", "verify", "review", "ship"]
        for phase in expected_phases:
            self.assertIn(phase, phases)

        # 验证每个阶段的结构
        workflow = result["complete_workflow"]
        for phase_name, phase_info in workflow.items():
            self.assertIn("phase", phase_info)
            self.assertIn("description", phase_info)
            self.assertIn("templates", phase_info)
            self.assertIn("outputs", phase_info)
            self.assertIn("key_principle", phase_info)

    def test_get_development_workflow_specific_phase(self):
        """测试获取特定阶段工作流"""
        # 测试获取"build"阶段
        result = self.library.get_development_workflow("build")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["phase"], "build")
        self.assertIn("workflow", result)

        workflow = result["workflow"]
        self.assertEqual(workflow["phase"], "构建")
        self.assertIn("templates", workflow)
        self.assertIn("incremental-implementation", workflow["templates"])

    def test_get_development_workflow_invalid_phase(self):
        """测试获取无效阶段工作流"""
        # 测试无效阶段
        result = self.library.get_development_workflow("invalid_phase")

        self.assertEqual(result["status"], "success")
        # 应该返回空字典
        self.assertEqual(result["workflow"], {})

    def test_template_to_dict(self):
        """测试模板转换为字典"""
        # 获取一个模板
        template = self.library.get_template("spec-driven-development")
        template_dict = template.to_dict()

        # 验证字典结构
        expected_keys = [
            "name", "description", "category", "complexity",
            "source_project", "version", "required_fields",
            "recommended_fields", "examples_count", "patterns_count"
        ]

        for key in expected_keys:
            self.assertIn(key, template_dict)

        # 验证值
        self.assertEqual(template_dict["name"], "spec-driven-development")
        self.assertEqual(template_dict["category"], "define")
        self.assertEqual(template_dict["complexity"], "intermediate")

    def test_skill_category_enum(self):
        """测试技能类别枚举"""
        # 验证枚举值
        self.assertEqual(SkillCategory.DEFINE.value, "define")
        self.assertEqual(SkillCategory.PLAN.value, "plan")
        self.assertEqual(SkillCategory.BUILD.value, "build")
        self.assertEqual(SkillCategory.VERIFY.value, "verify")
        self.assertEqual(SkillCategory.REVIEW.value, "review")
        self.assertEqual(SkillCategory.SHIP.value, "ship")

        # 验证枚举成员
        self.assertIsInstance(SkillCategory.DEFINE, SkillCategory)

    def test_skill_complexity_enum(self):
        """测试技能复杂度枚举"""
        # 验证枚举值
        self.assertEqual(SkillComplexity.BASIC.value, "basic")
        self.assertEqual(SkillComplexity.INTERMEDIATE.value, "intermediate")
        self.assertEqual(SkillComplexity.ADVANCED.value, "advanced")

        # 验证枚举成员
        self.assertIsInstance(SkillComplexity.BASIC, SkillComplexity)

    def test_agent_skills_availability_check(self):
        """测试agent-skills可用性检查"""
        # 检查可用性（应该返回布尔值）
        availability = self.library.agent_skills_available

        self.assertIsInstance(availability, bool)

        # 即使不可用，库也应该工作（使用默认模板）
        self.assertGreater(len(self.library.templates), 0)


if __name__ == "__main__":
    unittest.main()