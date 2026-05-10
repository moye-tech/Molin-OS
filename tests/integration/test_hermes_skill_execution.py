#!/usr/bin/env python3
"""
测试hermes-agent技能执行
验证技能能否被实际调用和执行
"""

import sys
import os
import json
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_skill_can_handle():
    """测试技能can_handle方法"""
    print("=" * 60)
    print("测试技能can_handle方法")
    print("=" * 60)

    try:
        from hermes_fusion.skills.hermes_native.subsidiary_base_skill import SubsidiaryMolinSkill

        # 测试教育子公司
        print("测试教育子公司技能触发...")
        skill = SubsidiaryMolinSkill({'subsidiary_type': 'edu'})

        test_cases = [
            ("我想报名一个Python培训课程", True),
            ("处理订单发货", False),
            ("分析项目ROI", False),
            ("创建培训材料", True),
        ]

        for text, expected in test_cases:
            context = {'text': text}
            can_handle = skill.sync_can_handle(context)
            status = "✓" if can_handle == expected else "✗"
            print(f"  {status} '{text[:20]}...' -> 触发: {can_handle} (期望: {expected})")

        return True

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_execution():
    """测试技能执行方法"""
    print("\n" + "=" * 60)
    print("测试技能执行方法")
    print("=" * 60)

    try:
        from hermes_fusion.skills.hermes_native.subsidiary_base_skill import SubsidiaryMolinSkill

        # 测试教育子公司执行
        print("测试教育子公司执行...")
        skill = SubsidiaryMolinSkill({'subsidiary_type': 'edu'})

        context = {
            'text': '我想报名一个Python培训课程',
            'user_id': 'test_user_1',
            'platform': 'test',
            'metadata': {'course_type': 'python', 'level': 'beginner'}
        }

        result = skill.sync_execute(context)

        print(f"  执行结果:")
        print(f"    成功: {result.get('success', False)}")
        print(f"    决策: {result.get('decision', 'N/A')}")
        print(f"    执行时间: {result.get('execution_time', 0):.2f}秒")

        if result.get('success'):
            print("  ✓ 技能执行成功")
            return True
        else:
            print(f"  ✗ 技能执行失败: {result.get('error', '未知错误')}")
            return False

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_hermes_agent_skill_integration():
    """测试hermes-agent技能集成"""
    print("\n" + "=" * 60)
    print("测试hermes-agent技能集成")
    print("=" * 60)

    try:
        # 尝试导入hermes-agent的技能工具
        from tools.skills_tool import skill_view

        # 测试查看教育子公司技能
        print("测试查看教育子公司技能...")
        result_json = skill_view("education")
        result = json.loads(result_json)

        if result.get('success'):
            print(f"  ✓ 技能查看成功: {result.get('name', 'N/A')}")

            # 检查技能内容
            content = result.get('content', '')
            if '教育子公司' in content:
                print("  ✓ 技能内容包含正确信息")
            else:
                print("  ⚠️  技能内容可能不完整")

            return True
        else:
            print(f"  ✗ 技能查看失败: {result.get('error', '未知错误')}")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_routing():
    """测试技能路由"""
    print("\n" + "=" * 60)
    print("测试技能路由")
    print("=" * 60)

    try:
        from hermes_fusion.skills.hermes_native.subsidiary_base_skill import SubsidiaryMolinSkill

        # 创建多个技能实例
        skills = [
            ('edu', SubsidiaryMolinSkill({'subsidiary_type': 'edu'}), '教育子公司'),
            ('order', SubsidiaryMolinSkill({'subsidiary_type': 'order'}), '订单子公司'),
            ('dev', SubsidiaryMolinSkill({'subsidiary_type': 'dev'}), '开发子公司'),
        ]

        test_requests = [
            ('我想报名一个培训课程', 'edu'),
            ('处理订单发货', 'order'),
            ('写一个Python函数', 'dev'),
            ('分析市场趋势', None),  # 没有对应技能
        ]

        correct_count = 0

        for request_text, expected_skill in test_requests:
            print(f"\n请求: '{request_text}'")
            context = {'text': request_text}

            triggered_skills = []
            for skill_id, skill, skill_name in skills:
                can_handle = skill.sync_can_handle(context)
                if can_handle:
                    triggered_skills.append(skill_id)
                    print(f"  ✓ {skill_name} 触发")
                else:
                    print(f"  ✗ {skill_name} 不触发")

            # 验证路由结果
            if expected_skill is None:
                if not triggered_skills:
                    print(f"  ✓ 正确: 无技能触发 (期望: 无)")
                    correct_count += 1
                else:
                    print(f"  ✗ 错误: {triggered_skills} 触发 (期望: 无)")
            elif expected_skill in triggered_skills:
                print(f"  ✓ 正确: {expected_skill} 触发")
                correct_count += 1
            else:
                print(f"  ✗ 错误: {triggered_skills} 触发 (期望: {expected_skill})")

        accuracy = correct_count / len(test_requests)
        print(f"\n路由准确率: {accuracy:.1%} ({correct_count}/{len(test_requests)})")

        return accuracy >= 0.75  # 75%准确率即可

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("墨麟AI技能执行测试")
    print("=" * 60)

    tests = [
        ("技能can_handle测试", test_skill_can_handle),
        ("技能执行测试", test_skill_execution),
        ("技能路由测试", test_skill_routing),
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

    # 运行异步测试
    print(f"\n运行测试: hermes-agent技能集成测试")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(test_hermes_agent_skill_integration())
        loop.close()
        results.append(("hermes-agent技能集成测试", success))
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("hermes-agent技能集成测试", False))

    print("\n" + "=" * 60)
    print("测试结果汇总")
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
    print("诊断建议")
    print("=" * 60)

    if passed == len(results):
        print("✓ 所有测试通过，技能执行机制正常")
        print("\n下一步:")
        print("  1. 进行端到端hermes-agent会话测试")
        print("  2. 验证实际业务场景中的技能调用")
        print("  3. 测试并发请求处理")
    else:
        print("⚠️ 部分测试失败，建议检查:")
        print("  1. 技能can_handle方法的实现")
        print("  2. 技能执行逻辑是否正确")
        print("  3. hermes-agent集成配置")
        print("  4. 技能路由优先级")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)