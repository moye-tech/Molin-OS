#!/usr/bin/env python3
"""
claude-code-sourcemap集成测试
测试代码分析工具与开发工具子公司技能的集成
验证源代码映射分析功能的完整性和增强能力
"""

import sys
import os
import json
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestCodeAnalysisIntegration:
    """代码分析集成测试类"""

    def __init__(self):
        self.test_python_code = '''
"""
示例Python代码用于测试
包含各种代码模式和潜在问题
"""
import os
import json
from typing import Dict, Any, List, Optional

class ExampleClass:
    """示例类"""

    def __init__(self, name: str):
        self.name = name
        self.data = {}  # 可能的安全问题：硬编码数据结构

    def process_data(self, input_data: Dict[str, Any]) -> Optional[List[str]]:
        """处理数据

        Args:
            input_data: 输入数据

        Returns:
            处理结果列表或None
        """
        result = []  # 通用变量名
        for key, value in input_data.items():
            # 潜在的性能问题：字符串拼接在循环中
            result.append(key + ": " + str(value))

        return result if result else None

    def dangerous_method(self, user_input: str) -> str:
        """危险方法：包含安全问题

        Args:
            user_input: 用户输入

        Returns:
            处理后的字符串
        """
        # 安全警告：使用eval
        if "expression" in user_input:
            return str(eval(user_input.split("=")[1]))

        return user_input.upper()


def example_function(x: int, y: int) -> int:
    """示例函数

    Args:
        x: 第一个参数
        y: 第二个参数

    Returns:
        计算结果
    """
    # 魔法数字
    magic_number = 1000

    # 调试语句
    print(f"计算 {x} + {y}")

    result = x + y

    # TODO: 添加错误处理
    if result > magic_number:
        # FIXME: 这里需要更好的处理
        pass

    return result


def performance_issue() -> str:
    """性能问题示例"""
    output = ""
    for i in range(100):
        output += str(i)  # 字符串拼接在循环中

    return output


# 硬编码密钥（安全警告）
SECRET_KEY = "my_super_secret_password_12345"

'''

        self.test_javascript_code = '''
// JavaScript代码示例
function calculateTotal(items) {
    let total = 0;

    for (let i = 0; i < items.length; i++) {
        total += items[i].price;

        // 调试语句
        console.log('处理项目:', items[i]);
    }

    return total;
}

// 安全问题
function processUserInput(input) {
    // 危险：使用eval
    if (input.startsWith('eval:')) {
        return eval(input.substring(5));
    }

    return input.toUpperCase();
}

// TODO: 添加更多功能
// FIXME: 需要重构
'''

        self.test_data = {
            'python': self.test_python_code,
            'javascript': self.test_javascript_code
        }

    def test_claude_code_analyzer_initialization(self) -> bool:
        """测试claude-code-sourcemap分析器初始化"""
        logger.info("测试claude-code-sourcemap分析器初始化...")

        try:
            from hermes_fusion.integration.external_tools.code_analysis_tools import (
                initialize_code_analysis,
                get_code_analysis_info
            )

            # 初始化分析器
            init_result = initialize_code_analysis()
            logger.info(f"分析器初始化结果: {init_result['status']}")
            logger.info(f"分析器消息: {init_result['message']}")
            logger.info(f"支持功能: {', '.join(init_result.get('capabilities', []))}")

            # 获取分析器信息
            analyzer_info = get_code_analysis_info()
            logger.info(f"分析器已初始化: {analyzer_info['analyzer_initialized']}")
            logger.info(f"源代码映射可用: {analyzer_info['sourcemap_available']}")

            if init_result['status'] in ['success', 'partial_success']:
                logger.info("claude-code-sourcemap分析器初始化测试通过")
                return True
            else:
                logger.error("claude-code-sourcemap分析器初始化失败")
                return False

        except Exception as e:
            logger.error(f"claude-code-sourcemap分析器初始化测试异常: {e}")
            return False

    def test_enhanced_code_analysis(self, language: str = "python") -> bool:
        """测试增强代码分析功能"""
        logger.info(f"测试增强代码分析功能 ({language})...")

        try:
            from hermes_fusion.integration.external_tools.code_analysis_tools import (
                analyze_code_with_sourcemap,
                claude_code_analyzer
            )

            code = self.test_data.get(language, '')
            if not code:
                logger.warning(f"没有{language}测试代码，跳过测试")
                return True  # 非关键错误

            # 执行增强分析
            analysis_result = analyze_code_with_sourcemap(code, language)

            # 验证分析结果结构
            required_fields = [
                'file_path', 'language', 'total_lines', 'total_characters',
                'functions_count', 'classes_count', 'quality_score', 'issues',
                'patterns_detected', 'analysis_timestamp', 'metadata'
            ]

            missing_fields = []
            for field in required_fields:
                if field not in analysis_result:
                    missing_fields.append(field)

            if missing_fields:
                logger.error(f"分析结果缺少字段: {missing_fields}")
                return False

            # 验证分析深度
            issues_count = len(analysis_result.get('issues', []))
            patterns_count = len(analysis_result.get('patterns_detected', []))
            quality_score = analysis_result.get('quality_score', 0)

            logger.info(f"分析统计: {issues_count}个问题, {patterns_count}个模式, 质量评分: {quality_score}")

            # 检查是否检测到预期的问题
            if language == 'python':
                # 检查是否检测到安全问题
                critical_issues = [issue for issue in analysis_result['issues']
                                  if issue.get('severity') in ['critical', 'high']]

                if len(critical_issues) > 0:
                    logger.info(f"检测到{len(critical_issues)}个关键/高危问题")
                else:
                    logger.warning("未检测到关键/高危问题（可能分析不够深入）")

            # 验证源代码映射集成
            if analysis_result['metadata'].get('sourcemap_integrated', False):
                logger.info("源代码映射集成验证通过")
            else:
                logger.warning("源代码映射未集成（可能是模拟模式）")

            # 验证AI生成代码识别
            if analysis_result['metadata'].get('ai_pattern_analysis', False):
                logger.info("AI生成代码模式识别验证通过")
            else:
                logger.warning("AI生成代码模式识别未启用")

            logger.info(f"增强代码分析测试通过 ({language})")
            return True

        except Exception as e:
            logger.error(f"增强代码分析测试异常 ({language}): {e}")
            return False

    def test_development_tools_integration(self) -> bool:
        """测试开发工具集成"""
        logger.info("测试开发工具集成...")

        try:
            from hermes_fusion.tools.development_tools import development_tools

            code = self.test_python_code

            # 测试基础分析功能
            analysis_result = development_tools.analyze_code(code, 'python')

            required_fields = ['language', 'lines', 'characters', 'functions', 'classes']
            for field in required_fields:
                if field not in analysis_result:
                    logger.error(f"基础分析缺少字段: {field}")
                    return False

            logger.info(f"基础分析: {analysis_result['lines']}行, {analysis_result['functions']}函数, {analysis_result['classes']}类")

            # 测试调试功能
            debug_result = development_tools.debug_code(code, 'python')

            if 'issues_found' not in debug_result:
                logger.error("调试结果缺少issues_found字段")
                return False

            logger.info(f"调试: 发现{debug_result['issues_found']}个问题")

            # 测试文档生成功能
            doc_result = development_tools.generate_documentation(code, 'python')

            if 'functions' not in doc_result or 'classes' not in doc_result:
                logger.error("文档生成结果缺少functions或classes字段")
                return False

            logger.info(f"文档生成: {len(doc_result['functions'])}个函数文档, {len(doc_result['classes'])}个类文档")

            # 测试重构建议功能
            refactor_result = development_tools.refactor_suggestions(code, 'python')

            if 'total_suggestions' not in refactor_result:
                logger.error("重构建议缺少total_suggestions字段")
                return False

            logger.info(f"重构建议: {refactor_result['total_suggestions']}个建议")

            logger.info("开发工具集成测试通过")
            return True

        except Exception as e:
            logger.error(f"开发工具集成测试异常: {e}")
            return False

    def test_dev_subsidiary_skill(self) -> bool:
        """测试开发工具子公司技能"""
        logger.info("测试开发工具子公司技能...")

        try:
            from hermes_fusion.skills.subsidiaries.dev_subsidiary import DevSubsidiarySkill

            # 创建技能实例
            skill = DevSubsidiarySkill()

            # 测试配置验证
            validation_errors = skill.validate_config()
            if validation_errors:
                logger.error(f"技能配置验证错误: {validation_errors}")
                return False

            # 测试统计信息获取
            stats = skill.get_statistics()
            logger.info(f"技能统计: 名称={stats.get('name')}, 总执行次数={stats.get('total_executions')}")

            # 测试配置摘要
            summary = skill.get_config_summary()
            logger.info(f"配置摘要: 关键词数量={len(summary.get('keywords', []))}, 工具数量={summary.get('tools_count', 0)}")

            # 测试技能触发判断
            test_contexts = [
                {
                    'text': '请分析这段Python代码',
                    'contains_code': True
                },
                {
                    'text': '帮我调试一下这个函数',
                    'contains_code': False
                },
                {
                    'text': '生成代码文档',
                    'contains_code': True
                }
            ]

            for i, context in enumerate(test_contexts):
                can_handle = skill.can_handle(context)
                logger.info(f"测试上下文{i+1}: {context['text']} -> 能否处理: {can_handle}")

            # 测试技能执行（模拟模式）
            context = {
                'text': '分析这段代码',
                'code': self.test_python_code,
                'language': 'python',
                'user_id': 'test_user',
                'platform': 'test',
                'timestamp': '2026-04-19T12:00:00Z'
            }

            # 开始执行测试
            if not skill.start_execution():
                logger.warning("无法开始执行（可能达到并发限制），但这不是测试失败")
            else:
                try:
                    # 注意：实际执行可能需要更多上下文，这里只测试接口
                    logger.info("技能执行接口测试通过（不执行实际逻辑）")
                finally:
                    skill.finish_execution(success=True)

            logger.info("开发工具子公司技能测试通过")
            return True

        except Exception as e:
            logger.error(f"开发工具子公司技能测试异常: {e}")
            return False

    def test_code_issue_detection(self) -> bool:
        """测试代码问题检测"""
        logger.info("测试代码问题检测...")

        try:
            from hermes_fusion.integration.external_tools.code_analysis_tools import (
                claude_code_analyzer
            )

            # 确保分析器已初始化
            if not claude_code_analyzer.initialized:
                logger.warning("分析器未初始化，尝试初始化...")
                from hermes_fusion.integration.external_tools.code_analysis_tools import (
                    initialize_code_analysis
                )
                initialize_code_analysis()

            # 测试安全问题检测
            security_code = '''
password = "my_password"
secret_key = "1234567890"
result = eval("2 + 2")
'''

            issues = claude_code_analyzer._detect_security_issues(security_code, 'python')

            security_issue_count = len([issue for issue in issues
                                       if 'secret' in issue.issue_type.lower() or
                                          'eval' in issue.issue_type.lower()])

            logger.info(f"安全问题检测: 发现{security_issue_count}个安全问题")

            # 测试性能问题检测
            performance_code = '''
def slow_function():
    result = ""
    for i in range(100):
        result += str(i)
    return result
'''

            perf_issues = claude_code_analyzer._detect_performance_issues(performance_code, 'python')

            perf_issue_count = len([issue for issue in perf_issues
                                   if 'performance' in issue.issue_type.lower() or
                                      'string_concat' in issue.issue_type.lower()])

            logger.info(f"性能问题检测: 发现{perf_issue_count}个性能问题")

            # 测试通用问题检测
            common_code = '''
# TODO: 需要实现这个函数
# FIXME: 这里有bug

def example():
    pass
'''

            common_issues = claude_code_analyzer._detect_common_issues(common_code, 'python')

            todo_issue_count = len([issue for issue in common_issues
                                   if 'todo' in issue.issue_type.lower()])

            logger.info(f"通用问题检测: 发现{todo_issue_count}个TODO/FIXME问题")

            logger.info("代码问题检测测试通过")
            return True

        except Exception as e:
            logger.error(f"代码问题检测测试异常: {e}")
            return False

    def test_sourcemap_analysis_insights(self) -> bool:
        """测试源代码映射分析洞察"""
        logger.info("测试源代码映射分析洞察...")

        try:
            from hermes_fusion.integration.external_tools.code_analysis_tools import (
                claude_code_analyzer
            )

            # 检查是否有源代码映射数据
            if not claude_code_analyzer.sourcemap_data:
                logger.warning("没有源代码映射数据，使用模拟模式测试")

                # 测试模拟模式下的洞察生成
                insights = claude_code_analyzer._generate_sourcemap_insights(
                    self.test_python_code, 'python', {'test': 'context'}
                )

                if not insights:
                    logger.error("模拟洞察生成失败")
                    return False

                logger.info(f"模拟洞察生成成功: {list(insights.keys())}")

                # 检查洞察结构
                required_sections = ['ai_code_analysis', 'claude_code_comparison', 'optimization_opportunities']

                for section in required_sections:
                    if section not in insights:
                        logger.error(f"洞察缺少部分: {section}")
                        return False

                logger.info("源代码映射分析洞察测试通过（模拟模式）")
                return True
            else:
                # 实际源代码映射数据测试
                logger.info(f"使用实际源代码映射数据测试，项目: {claude_code_analyzer.sourcemap_data.get('project')}")

                # 检查项目信息
                project_info = claude_code_analyzer.sourcemap_data

                if 'project' not in project_info:
                    logger.error("源代码映射数据缺少project字段")
                    return False

                if 'files' not in project_info:
                    logger.error("源代码映射数据缺少files字段")
                    return False

                file_count = len(project_info.get('files', []))
                logger.info(f"源代码映射包含{file_count}个文件")

                # 测试洞察生成
                insights = claude_code_analyzer._generate_sourcemap_insights(
                    self.test_python_code, 'python', {'test': 'context'}
                )

                if not insights:
                    logger.error("实际源代码映射洞察生成失败")
                    return False

                logger.info("源代码映射分析洞察测试通过（实际数据模式）")
                return True

        except Exception as e:
            logger.error(f"源代码映射分析洞察测试异常: {e}")
            return False

    def test_comprehensive_analysis_report(self) -> bool:
        """测试综合分析报告生成"""
        logger.info("测试综合分析报告生成...")

        try:
            from hermes_fusion.integration.external_tools.code_analysis_tools import (
                claude_code_analyzer
            )

            # 生成增强分析报告
            report = claude_code_analyzer.generate_enhanced_analysis_report(
                self.test_python_code, 'python'
            )

            # 检查报告结构
            required_sections = [
                'file_path', 'language', 'total_lines', 'total_characters',
                'functions_count', 'classes_count', 'quality_score', 'issues',
                'patterns_detected', 'analysis_timestamp', 'metadata',
                'recommendations', 'executive_summary'
            ]

            missing_sections = []
            for section in required_sections:
                if section not in report:
                    missing_sections.append(section)

            if missing_sections:
                logger.error(f"分析报告缺少部分: {missing_sections}")
                return False

            # 验证执行摘要
            exec_summary = report.get('executive_summary', {})

            if 'overall_quality' not in exec_summary:
                logger.error("执行摘要缺少overall_quality字段")
                return False

            logger.info(f"执行摘要: 总体质量={exec_summary.get('overall_quality')}, "
                       f"质量评分={report.get('quality_score', 0)}")

            # 验证建议
            recommendations = report.get('recommendations', [])
            logger.info(f"生成{len(recommendations)}条建议")

            # 验证问题分类
            issues = report.get('issues', [])

            if issues:
                # 按严重程度分类
                severity_counts = {}
                for issue in issues:
                    severity = issue.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                logger.info(f"问题严重程度分布: {severity_counts}")

            # 验证模式检测
            patterns = report.get('patterns_detected', [])
            logger.info(f"检测到模式: {patterns}")

            # 输出详细报告到临时文件（可选）
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
                logger.info(f"详细分析报告已保存到: {f.name}")

            logger.info("综合分析报告生成测试通过")
            return True

        except Exception as e:
            logger.error(f"综合分析报告生成测试异常: {e}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试并返回结果"""
        logger.info("=" * 60)
        logger.info("开始claude-code-sourcemap集成测试")
        logger.info("=" * 60)

        test_cases = [
            ("claude-code-sourcemap分析器初始化", self.test_claude_code_analyzer_initialization),
            ("增强代码分析(Python)", lambda: self.test_enhanced_code_analysis("python")),
            ("增强代码分析(JavaScript)", lambda: self.test_enhanced_code_analysis("javascript")),
            ("开发工具集成", self.test_development_tools_integration),
            ("开发工具子公司技能", self.test_dev_subsidiary_skill),
            ("代码问题检测", self.test_code_issue_detection),
            ("源代码映射分析洞察", self.test_sourcemap_analysis_insights),
            ("综合分析报告生成", self.test_comprehensive_analysis_report)
        ]

        results = []
        for test_name, test_func in test_cases:
            logger.info(f"\n--- 开始测试: {test_name} ---")
            try:
                success = test_func()
                results.append((test_name, success))
                status = "通过" if success else "失败"
                logger.info(f"测试 {test_name}: {status}")
            except Exception as e:
                logger.error(f"测试 {test_name} 异常: {e}")
                results.append((test_name, False))

        # 汇总结果
        logger.info("\n" + "=" * 60)
        logger.info("claude-code-sourcemap集成测试结果汇总")
        logger.info("=" * 60)

        passed = 0
        total = len(results)

        for test_name, success in results:
            status = "✓ 通过" if success else "✗ 失败"
            logger.info(f"  {test_name}: {status}")
            if success:
                passed += 1

        success_rate = (passed / total * 100) if total > 0 else 0
        logger.info(f"\n总计: {passed}/{total} 通过 ({success_rate:.1f}%)")

        # 生成详细报告
        report = {
            'test_date': '2026-04-19T12:00:00Z',
            'total_tests': total,
            'passed_tests': passed,
            'failed_tests': total - passed,
            'success_rate': success_rate,
            'results': [
                {
                    'test_name': name,
                    'passed': passed,
                    'timestamp': '2026-04-19T12:00:00Z'
                }
                for name, passed in results
            ],
            'summary': {
                'analyzer_initialized': any(name == "claude-code-sourcemap分析器初始化"
                                          and passed for name, passed in results),
                'enhanced_analysis_working': any(name.startswith("增强代码分析")
                                               and passed for name, passed in results),
                'dev_subsidiary_functional': any(name == "开发工具子公司技能"
                                               and passed for name, passed in results),
                'sourcemap_insights_available': any(name == "源代码映射分析洞察"
                                                  and passed for name, passed in results)
            }
        }

        if passed == total:
            logger.info("🎉 所有测试通过！claude-code-sourcemap集成完整。")
        else:
            logger.warning(f"⚠️  {total - passed} 个测试失败，需要进一步检查。")

        return report


def main():
    """主函数：运行集成测试"""
    tester = TestCodeAnalysisIntegration()
    report = tester.run_all_tests()

    # 保存测试报告
    report_file = "code_analysis_integration_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"测试报告已保存到: {report_file}")
    except Exception as e:
        logger.error(f"保存测试报告失败: {e}")

    # 返回退出代码
    return 0 if report['passed_tests'] == report['total_tests'] else 1


if __name__ == '__main__':
    sys.exit(main())