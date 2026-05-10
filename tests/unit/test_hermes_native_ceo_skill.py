"""
测试墨麟AI原生CEO决策技能
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from hermes_fusion.skills.hermes_native.ceo_decision_skill import CeoDecisionMolinSkill
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"导入失败: {e}")
    IMPORT_SUCCESS = False


@unittest.skipIf(not IMPORT_SUCCESS, "CeoDecisionMolinSkill导入失败")
class TestCeoDecisionMolinSkill(unittest.TestCase):
    """测试Hermes原生CEO决策技能"""

    def setUp(self):
        """设置测试环境"""
        self.skill_config = {
            'name': '测试CEO决策引擎',
            'description': '测试CEO决策系统',
            'version': '1.0.0',
            'triggers': {
                'keywords': ['决策', '分析', 'roi']
            },
            'model_preference': 'glm-5',
            'cost_level': 'high',
            'approval_level': 'high',
            'max_concurrent': 2
        }

        # 创建技能实例
        self.skill = CeoDecisionMolinSkill(self.skill_config)

    def test_initialization(self):
        """测试技能初始化"""
        self.assertEqual(self.skill.get_name(), '测试CEO决策引擎')
        self.assertEqual(self.skill.get_description(), '测试CEO决策系统')
        self.assertEqual(self.skill.get_version(), '1.0.0')
        self.assertEqual(self.skill.max_concurrent, 2)
        self.assertEqual(self.skill.cost_level, 'high')
        self.assertEqual(self.skill.approval_level, 'high')

        # 验证关键词配置
        self.assertIn('决策', self.skill.keywords)
        self.assertIn('分析', self.skill.keywords)
        self.assertIn('roi', self.skill.keywords)

    def test_get_tools(self):
        """测试获取工具列表"""
        tools = self.skill.get_tools()

        # 应该返回工具列表
        self.assertIsInstance(tools, list)

        # 验证工具格式
        if tools:
            for tool in tools:
                self.assertIn('name', tool)
                self.assertIn('description', tool)
                self.assertIn('category', tool)
                self.assertEqual(tool['category'], 'ceo_decision')

    async def _test_can_handle_async(self, context: Dict[str, Any]) -> bool:
        """异步测试can_handle的辅助方法"""
        return await self.skill.can_handle(context)

    def test_can_handle_with_keywords(self):
        """测试关键词匹配"""
        # 创建测试上下文
        context = {
            'text': '请帮我分析这个项目的ROI并做出决策',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z'
        }

        # 使用事件循环运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.skill.can_handle(context))
            self.assertTrue(result, "应该匹配到关键词'决策'和'ROI'")
        finally:
            loop.close()

    def test_can_handle_without_keywords(self):
        """测试无关键词时不匹配"""
        context = {
            'text': '今天天气怎么样',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z'
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.skill.can_handle(context))
            self.assertFalse(result, "不应该匹配天气查询")
        finally:
            loop.close()

    def test_can_handle_with_metadata(self):
        """测试元数据匹配"""
        context = {
            'text': '需要评估',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z',
            'metadata': {
                'budget': 100000,
                'revenue': 200000
            }
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.skill.can_handle(context))
            # 即使文本中没有关键词，元数据中有预算和收入字段也应该匹配
            self.assertTrue(result, "元数据中包含预算和收入应该触发CEO决策")
        finally:
            loop.close()

    async def _test_execute_async(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """异步测试execute的辅助方法"""
        return await self.skill.execute(context)

    def test_execute_with_complete_info(self):
        """测试完整信息的执行"""
        context = {
            'text': '预算10万元，时间线90天，目标收入20万元，请进行ROI分析和决策',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z',
            'metadata': {
                'budget': 100000,
                'timeline': '90天',
                'target_revenue': 200000
            }
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.skill.execute(context))

            # 验证结果结构
            self.assertIn('success', result)
            self.assertIn('execution_time', result)
            self.assertIn('cost_estimate', result)
            self.assertIn('requires_approval', result)

            # CEO特定字段
            if result.get('success'):
                self.assertIn('decision', result)
                self.assertIn('analysis', result)
                self.assertIn('score', result)

                # 验证决策类型
                self.assertIn(result['decision'], ['GO', 'NO_GO', 'NEED_INFO'])

                # 验证执行时间
                self.assertIsInstance(result['execution_time'], (int, float))
                self.assertGreaterEqual(result['execution_time'], 0)

        finally:
            loop.close()

    def test_execute_with_missing_info(self):
        """测试缺少必要信息的执行"""
        context = {
            'text': '请帮我做决策',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z'
            # 缺少预算、时间线、目标收入
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.skill.execute(context))

            # 即使缺少信息，也应该有结果
            self.assertIn('success', result)

            # 如果缺少信息，决策应该是NEED_INFO
            if result.get('success') and 'decision' in result:
                self.assertEqual(result['decision'], 'NEED_INFO')

        finally:
            loop.close()

    def test_concurrent_limit(self):
        """测试并发限制"""
        # 首先达到并发限制
        self.skill.current_concurrent = self.skill.max_concurrent

        context = {
            'text': '预算10万元，请决策',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z',
            'metadata': {
                'budget': 100000,
                'timeline': '30天',
                'target_revenue': 150000
            }
        }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.skill.execute(context))

            # 应该返回并发限制错误
            self.assertFalse(result.get('success', True))
            self.assertIn('error', result)
            self.assertIn('达到最大并发限制', result.get('error', ''))
            self.assertTrue(result.get('requires_retry', False))

        finally:
            loop.close()

    def test_sync_methods(self):
        """测试同步方法（向后兼容）"""
        context = {
            'text': '测试决策',
            'user_id': 'test_user',
            'platform': 'test'
        }

        # 测试同步can_handle
        can_handle_result = self.skill.sync_can_handle(context)
        self.assertIsInstance(can_handle_result, bool)

        # 测试同步execute（需要完整信息）
        context_with_info = {
            'text': '预算10万，时间线30天，目标收入15万',
            'user_id': 'test_user',
            'platform': 'test',
            'metadata': {
                'budget': 100000,
                'timeline': '30天',
                'target_revenue': 150000
            }
        }

        execute_result = self.skill.sync_execute(context_with_info)
        self.assertIn('success', execute_result)
        self.assertIn('execution_time', execute_result)

    def test_decision_history(self):
        """测试决策历史获取"""
        history = self.skill.get_decision_history(limit=5)
        self.assertIsInstance(history, list)

        # 初始状态应该是空的，或者有历史记录
        if history:
            for record in history:
                self.assertIn('timestamp', record)
                self.assertIn('decision', record)
                self.assertIn(record['decision'], ['GO', 'NO_GO', 'NEED_INFO'])

    def test_statistics_summary(self):
        """测试统计摘要获取"""
        stats = self.skill.get_statistics_summary()
        self.assertIsInstance(stats, dict)

        # 验证基本统计字段
        self.assertIn('total_executions', stats)
        self.assertIn('successful_executions', stats)
        self.assertIn('failed_executions', stats)

        # CEO特定统计（如果有决策历史）
        if 'total_decisions' in stats:
            self.assertIn('go_decisions', stats)
            self.assertIn('no_go_decisions', stats)
            self.assertIn('need_info_decisions', stats)

    def test_convert_to_hermes_format(self):
        """测试结果格式转换"""
        # 模拟CEO决策结果
        ceo_result = {
            'success': True,
            'result': '决策执行完成',
            'decision': 'GO',
            'roi_analysis': {'roi_ratio': 2.0, 'payback_days': 120},
            'composite_score': 8.5,
            'strategy': ['立即启动项目'],
            'risks': [{'risk': 'ROI偏低', 'mitigation': '优化成本'}],
            'execution_time': 1.5,
            'cost_estimate': 0.8,
            'requires_approval': True
        }

        context = {
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z'
        }

        # 调用私有方法（通过名称访问）
        hermes_result = self.skill._convert_to_hermes_format(ceo_result, context)

        # 验证转换结果
        self.assertEqual(hermes_result['success'], True)
        self.assertEqual(hermes_result['decision'], 'GO')
        self.assertEqual(hermes_result['analysis'], ceo_result['roi_analysis'])
        self.assertEqual(hermes_result['score'], 8.5)
        self.assertEqual(hermes_result['recommendations'], ['立即启动项目'])
        self.assertEqual(hermes_result['risks'], [{'risk': 'ROI偏低', 'mitigation': '优化成本'}])

        # 验证元数据
        self.assertIn('metadata', hermes_result)
        self.assertEqual(hermes_result['metadata']['skill_name'], '测试CEO决策引擎')
        self.assertEqual(hermes_result['metadata']['skill_version'], '1.0.0')


if __name__ == '__main__':
    # 运行测试
    unittest.main()