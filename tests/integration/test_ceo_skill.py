#!/usr/bin/env python3
"""
测试CEO决策技能
验证重构后的CEO决策技能功能是否正常
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill


def test_ceo_skill_initialization():
    """测试CEO技能初始化"""
    print("测试CEO决策技能初始化...")

    # 测试默认配置
    skill = CeoDecisionSkill()
    print(f"✓ 技能名称: {skill.name}")
    print(f"✓ 技能描述: {skill.description}")
    print(f"✓ 关键词: {skill.get_keywords()[:3]}...")
    print(f"✓ 模型偏好: {skill.get_model_preference()}")
    print(f"✓ 成本级别: {skill.get_cost_level()}")
    print(f"✓ 审批级别: {skill.get_approval_level()}")
    print(f"✓ 最大并发: {skill.max_concurrent}")
    print(f"✓ 工具列表: {skill.get_tools()}")

    # 验证配置
    errors = skill.validate_config()
    if errors:
        print(f"✗ 配置错误: {errors}")
        return False
    else:
        print("✓ 配置验证通过")

    return True


def test_ceo_skill_can_handle():
    """测试CEO技能请求处理判断"""
    print("\n测试CEO技能请求处理判断...")

    skill = CeoDecisionSkill()

    test_cases = [
        {
            "name": "包含决策关键词",
            "context": {"text": "请帮我做一个投资决策"},
            "expected": True
        },
        {
            "name": "包含ROI关键词",
            "context": {"text": "分析一下这个项目的ROI"},
            "expected": True
        },
        {
            "name": "包含预算关键词",
            "context": {"text": "这个项目的预算需要多少"},
            "expected": True
        },
        {
            "name": "不相关请求",
            "context": {"text": "今天天气怎么样"},
            "expected": False
        },
        {
            "name": "包含元数据中的预算字段",
            "context": {
                "text": "帮我看看",
                "metadata": {"budget": 10000}
            },
            "expected": True
        }
    ]

    all_passed = True
    for test in test_cases:
        result = skill.can_handle(test["context"])
        passed = result == test["expected"]
        status = "✓" if passed else "✗"
        print(f"{status} {test['name']}: {result} (期望: {test['expected']})")
        if not passed:
            all_passed = False

    return all_passed


def test_ceo_skill_execution():
    """测试CEO技能执行"""
    print("\n测试CEO技能执行...")

    skill = CeoDecisionSkill()

    test_contexts = [
        {
            "name": "完整信息请求",
            "context": {
                "text": "请分析这个项目：预算50000元，周期90天，目标收入150000元",
                "user_id": "test_user",
                "platform": "test"
            }
        },
        {
            "name": "缺少信息请求",
            "context": {
                "text": "请帮我做个决策",
                "user_id": "test_user",
                "platform": "test"
            }
        }
    ]

    all_passed = True
    for test in test_contexts:
        print(f"\n执行测试: {test['name']}")

        # 检查是否可以处理
        if not skill.can_handle(test["context"]):
            print("✗ 技能无法处理该请求")
            all_passed = False
            continue

        # 执行技能
        result = skill.execute(test["context"])

        print(f"✓ 执行成功: {result['success']}")
        print(f"✓ 决策结果: {result.get('decision', 'N/A')}")
        print(f"✓ 执行时间: {result.get('execution_time', 0)}s")
        print(f"✓ 成本估算: {result.get('cost_estimate', 0)}")

        # 基本验证
        if not result['success']:
            print("✗ 执行失败")
            all_passed = False
            continue

        # 验证决策结果格式
        decision = result.get('decision')
        if decision not in ['GO', 'NO_GO', 'NEED_INFO']:
            print(f"✗ 无效的决策结果: {decision}")
            all_passed = False

        # 验证必要字段
        required_fields = ['success', 'result', 'execution_time', 'cost_estimate']
        for field in required_fields:
            if field not in result:
                print(f"✗ 缺少必要字段: {field}")
                all_passed = False

    return all_passed


def test_ceo_skill_concurrent():
    """测试CEO技能并发控制"""
    print("\n测试CEO技能并发控制...")

    skill = CeoDecisionSkill()

    print(f"初始并发状态: {skill.current_concurrent}/{skill.max_concurrent}")

    # 测试开始执行
    can_accept = skill.can_accept_task()
    print(f"可接受新任务: {can_accept}")

    if can_accept:
        started = skill.start_execution()
        print(f"开始执行结果: {started}")
        print(f"当前并发: {skill.current_concurrent}/{skill.max_concurrent}")

        # 尝试再次开始执行（应该失败，因为并发已满）
        can_accept2 = skill.can_accept_task()
        print(f"再次检查可接受新任务: {can_accept2}")

        # 完成执行
        skill.finish_execution(success=True)
        print(f"完成执行后并发: {skill.current_concurrent}/{skill.max_concurrent}")

    # 检查统计信息
    stats = skill.get_statistics()
    print(f"统计信息: {stats}")

    return True


def test_ceo_skill_history():
    """测试CEO决策历史"""
    print("\n测试CEO决策历史...")

    skill = CeoDecisionSkill()

    # 执行一些测试决策
    test_context = {
        "text": "测试决策: 预算10000元，周期30天，目标收入30000元",
        "user_id": "test_user",
        "platform": "test"
    }

    for i in range(3):
        if skill.can_handle(test_context):
            result = skill.execute(test_context)
            print(f"执行 {i+1}: {result.get('decision')} (分数: {result.get('composite_score', 0)})")

    # 获取历史记录
    history = skill.get_decision_history(limit=5)
    print(f"决策历史记录数: {len(history)}")

    for i, record in enumerate(history):
        print(f"记录 {i+1}: {record.get('decision')} - {record.get('timestamp')}")

    # 获取统计摘要
    stats_summary = skill.get_statistics_summary()
    print(f"统计摘要: 总决策数={stats_summary.get('total_decisions', 0)}, GO率={stats_summary.get('go_rate', 0):.2f}")

    return len(history) > 0


def main():
    """主测试函数"""
    print("=" * 60)
    print("CEO决策技能测试")
    print("=" * 60)

    tests = [
        ("技能初始化", test_ceo_skill_initialization),
        ("请求处理判断", test_ceo_skill_can_handle),
        ("技能执行", test_ceo_skill_execution),
        ("并发控制", test_ceo_skill_concurrent),
        ("决策历史", test_ceo_skill_history)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n[测试] {test_name}")
        try:
            if test_func():
                print(f"✓ {test_name} - 通过")
                passed_tests += 1
            else:
                print(f"✗ {test_name} - 失败")
        except Exception as e:
            print(f"✗ {test_name} - 异常: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")

    if passed_tests == total_tests:
        print("✓ 所有CEO决策技能测试通过!")
        return True
    else:
        print("✗ 部分测试失败，请检查实现")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)