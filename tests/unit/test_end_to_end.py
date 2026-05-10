#!/usr/bin/env python3
"""
端到端业务流程测试
测试从用户请求到技能执行再到结果返回的完整流程
验证hermes-agent与我们的技能适配器的实际集成效果
"""

import sys
import os
import asyncio
import logging
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_complete_request_flow():
    """测试完整请求流程：从用户输入到技能执行"""
    print("=" * 60)
    print("端到端业务流程测试")
    print("=" * 60)

    try:
        from hermes_fusion.skills.hermes_native import EduSubsidiaryMolinSkill
        from hermes_fusion.skills.hermes_native import OrderSubsidiaryMolinSkill
        from hermes_fusion.skills.hermes_native import CeoDecisionMolinSkill
        print("✓ 导入技能类成功")
    except ImportError as e:
        print(f"✗ 导入技能类失败: {e}")
        return False

    # 创建技能实例
    skills = [
        ('edu', EduSubsidiaryMolinSkill(), '教育子公司'),
        ('order', OrderSubsidiaryMolinSkill(), '订单子公司'),
        ('ceo', CeoDecisionMolinSkill(), 'CEO决策引擎'),
    ]

    # 测试用例
    test_cases = [
        {
            'name': '教育请求',
            'text': '我想报名一个Python培训课程',
            'expected_skill': 'edu',
            'metadata': {'user_id': 'test_user_1', 'platform': 'web'}
        },
        {
            'name': '订单请求',
            'text': '处理订单发货和物流跟踪',
            'expected_skill': 'order',
            'metadata': {'user_id': 'test_user_2', 'platform': 'mobile'}
        },
        {
            'name': 'CEO决策请求',
            'text': '分析一个投资项目的ROI和预算',
            'expected_skill': 'ceo',
            'metadata': {
                'user_id': 'test_user_3',
                'platform': 'desktop',
                'budget': 50000,
                'target_revenue': 150000,
                'timeline': '90天'
            }
        },
        {
            'name': '复杂混合请求',
            'text': '先分析项目ROI，然后安排培训课程',
            'expected_skills': ['ceo', 'edu'],  # 多个可能触发
            'metadata': {'user_id': 'test_user_4', 'platform': 'web'}
        }
    ]

    results = []

    for test_case in test_cases:
        print(f"\n测试用例: {test_case['name']}")
        print(f"  请求: '{test_case['text']}'")

        context = {
            'text': test_case['text'],
            'user_id': test_case['metadata']['user_id'],
            'platform': test_case['metadata']['platform'],
            'metadata': test_case['metadata']
        }

        # 检查每个技能的can_handle
        triggered_skills = []
        for skill_id, skill, skill_name in skills:
            try:
                # 使用同步can_handle
                can_handle = skill.sync_can_handle(context)
                if can_handle:
                    triggered_skills.append((skill_id, skill_name))
                    print(f"  ✓ {skill_name} 触发")
                else:
                    print(f"  ✗ {skill_name} 不触发")
            except Exception as e:
                print(f"  ✗ {skill_name} 检查异常: {e}")

        # 验证触发结果
        expected_skills = test_case.get('expected_skill')
        if isinstance(expected_skills, str):
            expected_skills = [expected_skills]
        elif 'expected_skills' in test_case:
            expected_skills = test_case['expected_skills']
        else:
            expected_skills = []

        triggered_ids = [skill_id for skill_id, _ in triggered_skills]
        expected_ids = expected_skills if isinstance(expected_skills, list) else [expected_skills]

        # 对于复杂混合请求，检查至少有一个技能触发
        if test_case['name'] == '复杂混合请求':
            success = len(triggered_skills) > 0
            print(f"  混合请求触发 {len(triggered_skills)} 个技能: {triggered_ids}")
        else:
            success = set(triggered_ids) == set(expected_ids)
            print(f"  触发技能: {triggered_ids} (期望: {expected_ids})")

        # 如果技能触发，执行技能
        execution_success = False
        if triggered_skills:
            # 选择第一个触发的技能执行
            skill_id, skill_name = triggered_skills[0]
            skill_instance = None
            for sid, s, sn in skills:
                if sid == skill_id:
                    skill_instance = s
                    break

            if skill_instance:
                try:
                    result = skill_instance.sync_execute(context)
                    execution_success = result.get('success', False)
                    print(f"  执行结果: {'成功' if execution_success else '失败'}")
                    if execution_success:
                        print(f"    决策: {result.get('decision', 'N/A')}")
                        print(f"    执行时间: {result.get('execution_time', 0):.2f}秒")
                except Exception as e:
                    print(f"  执行异常: {e}")
                    execution_success = False

        # 记录结果
        results.append({
            'test_case': test_case['name'],
            'trigger_success': success,
            'execution_success': execution_success if triggered_skills else None,
            'overall_success': success and (execution_success if triggered_skills else True)
        })

        print(f"  结果: {'✓' if success else '✗'} 触发, {'✓' if execution_success else '✗' if triggered_skills else 'N/A'} 执行")

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for r in results if r['overall_success'])
    total = len(results)

    for result in results:
        status = "✓" if result['overall_success'] else "✗"
        trigger_status = "✓" if result['trigger_success'] else "✗"
        exec_status = "✓" if result['execution_success'] else "✗" if result['execution_success'] is not None else "N/A"
        print(f"  {status} {result['test_case']}: 触发{trigger_status} 执行{exec_status}")

    print(f"\n总体通过率: {passed}/{total} ({passed/total*100:.1f}%)")

    return passed == total


def test_hermes_agent_integration():
    """测试hermes-agent实际会话集成"""
    print("\n" + "=" * 60)
    print("hermes-agent实际会话集成测试")
    print("=" * 60)

    try:
        # 检查hermes-agent是否可用
        import agent
        import hermes_cli
        print("✓ hermes-agent核心模块可用")
    except ImportError as e:
        print(f"✗ hermes-agent导入失败: {e}")
        return False

    # 测试配置加载
    try:
        from hermes_cli.skills_config import load_config
        config = load_config()
        print("✓ hermes-agent配置加载成功")

        # 检查我们的技能是否在配置中
        if 'skills' in config:
            skills = config['skills']
            print(f"  配置中包含 {len(skills)} 个技能")

            # 查找我们的技能
            our_skill_ids = ['edu_subsidiary', 'order_subsidiary', 'ceo_decision']
            found_skills = []

            if isinstance(skills, dict):
                for skill_id in our_skill_ids:
                    if skill_id in skills:
                        found_skills.append(skill_id)
                        skill_config = skills[skill_id]
                        print(f"    ✓ {skill_id}: {skill_config.get('name', '无名')}")
                    else:
                        print(f"    ✗ {skill_id}: 未找到")

            print(f"  找到 {len(found_skills)}/{len(our_skill_ids)} 个我们的技能")
        else:
            print("  ✗ 配置中没有'skills'部分")
            return False

    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试工具注册
    try:
        from tools.registry import registry
        print("✓ 工具注册系统可用")

        tool_names = registry.get_all_tool_names()
        print(f"  已注册工具数量: {len(tool_names)}")

        # 查找我们的工具（基于关键词）
        our_tool_keywords = ['skill', 'ceo', 'edu', 'order']
        our_tools = []
        for tool_name in tool_names:
            if any(keyword in tool_name.lower() for keyword in our_tool_keywords):
                our_tools.append(tool_name)

        print(f"  找到 {len(our_tools)} 个可能属于我们的工具")
        if our_tools:
            print(f"  示例: {our_tools[:3]}...")

    except ImportError as e:
        print(f"⚠️  工具注册系统导入失败: {e}")
        print("  这可能是正常的，如果工具是动态注册的")

    print("\n集成状态评估:")
    print("  ✓ hermes-agent框架可用")
    print("  ✓ 配置系统工作正常")
    print("  ⚠️  需要实际会话测试验证技能调用")

    return True


def test_concurrent_requests():
    """测试并发请求处理"""
    print("\n" + "=" * 60)
    print("并发请求处理测试")
    print("=" * 60)

    try:
        from hermes_fusion.skills.hermes_native import EduSubsidiaryMolinSkill
        print("✓ 导入技能类成功")
    except ImportError as e:
        print(f"✗ 导入技能类失败: {e}")
        return False

    skill = EduSubsidiaryMolinSkill()

    # 模拟并发请求
    async def make_request(request_id):
        context = {
            'text': f'我想报名课程 {request_id}',
            'user_id': f'user_{request_id}',
            'platform': 'test',
            'timestamp': f'2026-04-19T10:00:{request_id:02d}'
        }

        try:
            result = await skill.execute(context)
            return {
                'request_id': request_id,
                'success': result.get('success', False),
                'concurrent_count': skill.current_concurrent
            }
        except Exception as e:
            return {
                'request_id': request_id,
                'success': False,
                'error': str(e)
            }

    async def run_concurrent_tests():
        # 创建5个并发请求
        tasks = [make_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        success_count = sum(1 for r in results if r.get('success', False))
        print(f"  并发请求结果: {success_count}/{len(results)} 成功")

        # 检查并发计数
        max_concurrent = max(r.get('concurrent_count', 0) for r in results if 'concurrent_count' in r)
        print(f"  最大并发计数: {max_concurrent}")

        # 验证并发限制
        if max_concurrent <= skill.max_concurrent:
            print(f"  ✓ 并发限制遵守: {max_concurrent} <= {skill.max_concurrent}")
            return True
        else:
            print(f"  ✗ 并发限制违规: {max_concurrent} > {skill.max_concurrent}")
            return False

    try:
        success = asyncio.run(run_concurrent_tests())
        return success
    except Exception as e:
        print(f"✗ 并发测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("墨麟AI智能系统端到端业务流程测试")
    print("=" * 60)

    tests = [
        ("完整请求流程测试", test_complete_request_flow),
        ("hermes-agent实际会话集成测试", test_hermes_agent_integration),
        ("并发请求处理测试", test_concurrent_requests),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n运行测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    print("\n" + "=" * 60)
    print("端到端测试结果汇总")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {test_name}")
        if success:
            passed += 1

    print(f"\n通过: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")

    # 诊断建议
    print("\n" + "=" * 60)
    print("端到端业务流程诊断")
    print("=" * 60)

    if passed == len(results):
        print("✓ 所有端到端测试通过，业务流程正常")
        print("\n建议下一步:")
        print("  1. 部署到测试环境进行真实场景验证")
        print("  2. 进行性能压测和负载测试")
        print("  3. 集成监控和告警系统")
    else:
        print("⚠️  部分端到端测试失败，建议检查:")
        print("  1. 技能触发关键词是否准确")
        print("  2. 技能执行逻辑是否正确")
        print("  3. hermes-agent集成配置")
        print("  4. 并发控制和资源限制")

    return passed == len(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)