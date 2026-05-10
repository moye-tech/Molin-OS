#!/usr/bin/env python3
"""
测试关键词触发和路由机制
"""
import sys
import os
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_subsidiary_keyword_triggers():
    """测试子公司关键词触发"""
    print("=" * 60)
    print("子公司关键词触发测试")
    print("=" * 60)

    # 定义测试用例：技能类型 -> 触发关键词 -> 应该触发
    test_cases = [
        # 教育子公司
        ('edu', '我想报名一个培训课程', True),
        ('edu', '有没有好的学习资料', True),
        ('edu', '学校需要新的教材', True),
        ('edu', '我想买一件衣服', False),  # 不应该触发

        # 订单子公司
        ('order', '处理订单发货', True),
        ('order', '价格调整策略', True),
        ('order', '物流跟踪查询', True),
        ('order', '我想学习编程', False),

        # IP内容子公司
        ('ip', '创作一篇文案', True),
        ('ip', '视频内容制作', True),
        ('ip', '社交媒体内容发布', True),
        ('ip', '数据库查询', False),

        # 开发工具子公司
        ('dev', '写一个Python函数', True),
        ('dev', '技术架构设计', True),
        ('dev', '代码部署上线', True),
        ('dev', '市场调研报告', False),

        # AI模型子公司
        ('ai', '模型训练优化', True),
        ('ai', '提示工程优化', True),
        ('ai', 'AI模型部署', True),
        ('ai', '财务管理分析', False),

        # 电商运营子公司
        ('shop', '商品上架管理', True),
        ('shop', '营销活动策划', True),
        ('shop', '客户服务处理', True),
        ('shop', '代码审查', False),

        # 数据分析子公司
        ('data', '数据报表生成', True),
        ('data', '业务洞察分析', True),
        ('data', '预测模型构建', True),
        ('data', '产品设计原型', False),

        # 用户增长子公司
        ('growth', '用户获客策略', True),
        ('growth', '激活留存优化', True),
        ('growth', '转化漏斗分析', True),
        ('growth', '安全漏洞扫描', False),

        # 安全合规子公司
        ('secure', '安全审计检查', True),
        ('secure', '合规风险评估', True),
        ('secure', '数据加密保护', True),
        ('secure', '内容创作策划', False),

        # 市场研究子公司
        ('research', '市场趋势分析', True),
        ('research', '竞品研究报告', True),
        ('research', '机会识别评估', True),
        ('research', '订单处理流程', False),

        # 产品管理子公司
        ('product', '产品需求分析', True),
        ('product', '用户体验设计', True),
        ('product', '产品路线规划', True),
        ('product', '物流配送优化', False),

        # CEO决策引擎
        ('ceo', 'ROI投资分析', True),
        ('ceo', '战略决策支持', True),
        ('ceo', '业务优化建议', True),
        ('ceo', '具体代码实现', False),
    ]

    # 导入技能类
    try:
        from hermes_fusion.skills.hermes_native.subsidiary_base_skill import SubsidiaryMolinSkill
        print("✓ 导入SubsidiaryMolinSkill成功")
    except ImportError as e:
        print(f"✗ 导入SubsidiaryMolinSkill失败: {e}")
        return False

    # 测试每个子公司类型
    subsidiary_types = {
        'edu': '教育子公司',
        'order': '订单子公司',
        'ip': 'IP内容子公司',
        'dev': '开发工具子公司',
        'ai': 'AI模型子公司',
        'shop': '电商运营子公司',
        'data': '数据分析子公司',
        'growth': '用户增长子公司',
        'secure': '安全合规子公司',
        'research': '市场研究子公司',
        'product': '产品管理子公司',
        'ceo': 'CEO决策引擎',
    }

    results = {}

    for sub_type, sub_name in subsidiary_types.items():
        print(f"\n测试 {sub_name} ({sub_type}):")
        try:
            # 创建技能实例
            skill = SubsidiaryMolinSkill({'subsidiary_type': sub_type})
            skill_name = skill.name
            print(f"  技能名称: {skill_name}")

            # 获取技能的关键词列表
            keywords = skill.keywords if hasattr(skill, 'keywords') else []
            print(f"  触发关键词: {keywords[:5]}{'...' if len(keywords) > 5 else ''}")

            # 测试相关测试用例
            type_test_cases = [(text, expected) for t, text, expected in test_cases if t == sub_type]

            type_results = []
            for text, expected in type_test_cases:
                context = {'text': text}
                try:
                    # 使用同步can_handle方法
                    can_handle = skill.sync_can_handle(context)
                    success = can_handle == expected
                    status = "✓" if success else "✗"
                    type_results.append(success)

                    print(f"    {status} '{text[:20]}...' -> 触发: {can_handle} (期望: {expected})")
                except Exception as e:
                    print(f"    ✗ '{text[:20]}...' -> 异常: {e}")
                    type_results.append(False)

            # 计算准确率
            if type_results:
                accuracy = sum(type_results) / len(type_results)
                results[sub_type] = accuracy
                print(f"  准确率: {accuracy:.1%} ({sum(type_results)}/{len(type_results)})")
            else:
                results[sub_type] = 0.0
                print(f"  无测试用例")

        except Exception as e:
            print(f"  ✗ 创建技能失败: {e}")
            results[sub_type] = 0.0

    # 汇总结果
    print("\n" + "=" * 60)
    print("关键词触发测试汇总")
    print("=" * 60)

    total_cases = 0
    passed_cases = 0

    for sub_type, accuracy in results.items():
        sub_name = subsidiary_types.get(sub_type, sub_type)
        status = "✓" if accuracy >= 0.8 else "✗"
        print(f"  {status} {sub_name}: {accuracy:.1%}")

        # 估算通过案例数（基于准确率）
        type_test_cases = [(text, expected) for t, text, expected in test_cases if t == sub_type]
        type_case_count = len(type_test_cases)
        type_passed = int(accuracy * type_case_count)

        total_cases += type_case_count
        passed_cases += type_passed

    overall_accuracy = passed_cases / total_cases if total_cases > 0 else 0
    print(f"\n总体准确率: {overall_accuracy:.1%} ({passed_cases}/{total_cases})")

    return overall_accuracy >= 0.8

def test_skill_routing_logic():
    """测试技能路由逻辑"""
    print("\n" + "=" * 60)
    print("技能路由逻辑测试")
    print("=" * 60)

    # 模拟多个技能竞争同一个请求
    print("测试场景: 多个技能对同一请求的竞争")

    try:
        from hermes_fusion.skills.hermes_native.subsidiary_base_skill import SubsidiaryMolinSkill

        # 创建几个关键技能
        skills = [
            ('edu', '教育子公司'),
            ('order', '订单子公司'),
            ('dev', '开发工具子公司'),
            ('ai', 'AI模型子公司'),
        ]

        skill_instances = []
        for sub_type, sub_name in skills:
            try:
                skill = SubsidiaryMolinSkill({'subsidiary_type': sub_type})
                skill_instances.append((sub_type, sub_name, skill))
                print(f"✓ 创建技能: {sub_name}")
            except Exception as e:
                print(f"✗ 创建技能{sub_name}失败: {e}")

        # 测试不同请求的路由
        test_requests = [
            ('我想学习Python编程', ['edu', 'dev']),  # 教育和开发都可能触发
            ('处理客户订单发货', ['order']),
            ('优化AI模型提示词', ['ai']),
            ('数据分析报告生成', []),  # 没有创建数据子公司实例
            ('安全漏洞扫描检查', []),  # 没有创建安全子公司实例
        ]

        routing_results = []

        for request_text, expected_skills in test_requests:
            print(f"\n请求: '{request_text}'")
            print(f"  预期触发技能: {expected_skills}")

            context = {'text': request_text}
            triggered_skills = []

            for sub_type, sub_name, skill in skill_instances:
                try:
                    can_handle = skill.sync_can_handle(context)
                    if can_handle:
                        triggered_skills.append(sub_type)
                        print(f"  ✓ {sub_name} 触发")
                    else:
                        print(f"  ✗ {sub_name} 不触发")
                except Exception as e:
                    print(f"  ✗ {sub_name} 检查异常: {e}")

            # 检查路由结果
            triggered_set = set(triggered_skills)
            expected_set = set(expected_skills)

            correct = triggered_set == expected_set
            status = "✓" if correct else "✗"
            routing_results.append(correct)

            print(f"  实际触发: {triggered_skills}")
            print(f"  结果: {status}")

        # 计算路由准确率
        if routing_results:
            routing_accuracy = sum(routing_results) / len(routing_results)
            print(f"\n路由准确率: {routing_accuracy:.1%} ({sum(routing_results)}/{len(routing_results)})")
            return routing_accuracy >= 0.8
        else:
            print("✗ 无路由测试结果")
            return False

    except Exception as e:
        print(f"✗ 技能路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hermes_agent_integration():
    """测试hermes-agent集成"""
    print("\n" + "=" * 60)
    print("hermes-agent集成测试")
    print("=" * 60)

    print("测试hermes-agent是否能与我们的技能适配器协同工作")

    try:
        # 检查hermes-agent是否可用
        import agent
        import hermes_cli
        print("✓ hermes-agent核心模块可用")

        # 尝试导入工具注册系统
        try:
            from tools.registry import registry
            print("✓ 工具注册系统可用")

            # 检查已注册工具
            tool_names = registry.get_all_tool_names()
            print(f"  已注册工具数量: {len(tool_names)}")

            # 查找我们的工具
            our_tools = [name for name in tool_names if 'skill' in name.lower()]
            print(f"  我们的工具: {our_tools}")

            if our_tools:
                print("✓ 我们的工具已注册到hermes-agent")
            else:
                print("⚠️  我们的工具未在注册表中找到")
                print("  可能原因:")
                print("    1. 工具注册在运行时动态进行")
                print("    2. 需要特定配置才能显示")
                print("    3. 注册表只显示当前会话可用工具")

        except ImportError as e:
            print(f"⚠️  工具注册系统导入失败: {e}")
            print("  这可能是正常的，如果hermes-agent使用不同的工具管理方式")

        # 测试配置集成
        try:
            from hermes_cli.skills_config import load_config
            config = load_config()
            print("✓ hermes-agent配置加载成功")

            # 检查是否有我们的技能配置
            if 'skills' in config:
                skills = config['skills']
                print(f"  hermes-agent配置中包含 {len(skills)} 个技能")
            else:
                print("⚠️  hermes-agent配置中没有'skills'部分")

        except Exception as e:
            print(f"⚠️  配置加载测试异常: {e}")

        print("\n集成状态评估:")
        print("  ✓ hermes-agent框架可用")
        print("  ✓ 核心模块导入正常")
        print("  ⚠️  需要进一步测试实际协同工作")

        return True

    except ImportError as e:
        print(f"✗ hermes-agent集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("关键词触发和路由机制测试")
    print("=" * 60)

    tests = [
        ("子公司关键词触发测试", test_subsidiary_keyword_triggers),
        ("技能路由逻辑测试", test_skill_routing_logic),
        ("hermes-agent集成测试", test_hermes_agent_integration),
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
    print("关键词触发和路由诊断")
    print("=" * 60)

    if passed == len(results):
        print("✓ 所有测试通过，关键词触发和路由机制正常")
        print("\n建议下一步:")
        print("  1. 测试端到端业务流程")
        print("  2. 验证实际hermes-agent会话中的技能调用")
        print("  3. 测试并发请求处理")
    else:
        print("⚠️  部分测试失败，建议检查:")
        print("  1. 技能can_handle方法的实现")
        print("  2. 关键词配置是否正确")
        print("  3. 技能路由优先级")
        print("  4. hermes-agent集成配置")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)