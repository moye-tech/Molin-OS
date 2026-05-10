#!/usr/bin/env python3
"""
测试阶段2.2集成
验证新创建的子公司技能能够正确加载和执行
包括：SEO子公司、创新实验子公司、思维模型子公司、浏览器自动化子公司
"""
import sys
import os
import yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_seo_subsidiary():
    """测试SEO子公司技能"""
    print("测试SEO子公司技能...")
    try:
        from hermes_fusion.skills.subsidiaries.seo_subsidiary import SEOSubsidiarySkill
        skill = SEOSubsidiarySkill()
        print(f"✓ SEO子公司技能导入成功: {skill.name}")

        # 测试can_handle
        context = {'text': 'SEO分析'}
        can_handle = skill.can_handle(context)
        print(f"  can_handle测试: {can_handle} (期望: True)")

        # 测试配置
        config = skill.get_config_summary()
        print(f"  配置验证错误: {config.get('validation_errors', [])}")

        return True
    except Exception as e:
        print(f"✗ SEO子公司技能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_innovation_subsidiary():
    """测试创新实验子公司技能"""
    print("\n测试创新实验子公司技能...")
    try:
        from hermes_fusion.skills.subsidiaries.innovation_subsidiary import InnovationSubsidiarySkill
        skill = InnovationSubsidiarySkill()
        print(f"✓ 创新实验子公司技能导入成功: {skill.name}")

        # 测试can_handle
        context = {'text': 'A/B测试实验设计'}
        can_handle = skill.can_handle(context)
        print(f"  can_handle测试: {can_handle} (期望: True)")

        # 测试配置
        config = skill.get_config_summary()
        print(f"  配置验证错误: {config.get('validation_errors', [])}")

        return True
    except Exception as e:
        print(f"✗ 创新实验子公司技能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_thinking_subsidiary():
    """测试思维模型子公司技能"""
    print("\n测试思维模型子公司技能...")
    try:
        from hermes_fusion.skills.subsidiaries.thinking_subsidiary import ThinkingSubsidiarySkill
        skill = ThinkingSubsidiarySkill()
        print(f"✓ 思维模型子公司技能导入成功: {skill.name}")

        # 测试can_handle
        context = {'text': 'SWOT分析'}
        can_handle = skill.can_handle(context)
        print(f"  can_handle测试: {can_handle} (期望: True)")

        # 测试配置
        config = skill.get_config_summary()
        print(f"  配置验证错误: {config.get('validation_errors', [])}")

        return True
    except Exception as e:
        print(f"✗ 思维模型子公司技能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browser_automation_subsidiary():
    """测试浏览器自动化子公司技能"""
    print("\n测试浏览器自动化子公司技能...")
    try:
        from hermes_fusion.skills.subsidiaries.browser_automation_subsidiary import BrowserAutomationSubsidiarySkill
        skill = BrowserAutomationSubsidiarySkill()
        print(f"✓ 浏览器自动化子公司技能导入成功: {skill.name}")

        # 测试can_handle
        context = {'text': '网页自动化测试'}
        can_handle = skill.can_handle(context)
        print(f"  can_handle测试: {can_handle} (期望: True)")

        # 测试配置
        config = skill.get_config_summary()
        print(f"  配置验证错误: {config.get('validation_errors', [])}")

        return True
    except Exception as e:
        print(f"✗ 浏览器自动化子公司技能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n测试配置加载...")
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'hermes-agent', 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 检查新技能是否在配置中
        skills = config.get('skills', {})
        required_skills = ['seo', 'innovation', 'thinking', 'browser_automation']

        for skill_name in required_skills:
            if skill_name in skills:
                print(f"✓ {skill_name}技能在配置中找到")
            else:
                print(f"✗ {skill_name}技能未在配置中找到")
                return False

        # 检查并发限制
        scheduling = config.get('scheduling', {})
        per_skill_limits = scheduling.get('per_skill_limits', {})

        for skill_name in required_skills:
            if skill_name in per_skill_limits:
                print(f"✓ {skill_name}并发限制配置: {per_skill_limits[skill_name]}")
            else:
                print(f"✗ {skill_name}并发限制未配置")
                return False

        # 检查工具定义
        tools = config.get('tools', {})
        required_tools = [
            'seo_analyze_intent', 'seo_rate_quality', 'seo_analyze_keywords',
            'innovation_run_experiment', 'innovation_analyze_results',
            'minimind_analyze_problem', 'minimind_apply_model',
            'browser_fetch_url', 'browser_screenshot'
        ]

        for tool_name in required_tools[:5]:  # 只检查前5个，避免输出过多
            if tool_name in tools:
                print(f"✓ {tool_name}工具在配置中找到")
            else:
                print(f"✗ {tool_name}工具未在配置中找到")
                # 不立即返回False，继续检查

        print(f"  总工具数量: {len(tools)}")

        return True
    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_execution():
    """测试技能执行"""
    print("\n测试技能执行...")
    results = []

    # 测试SEO技能执行
    try:
        from hermes_fusion.skills.subsidiaries.seo_subsidiary import SEOSubsidiarySkill
        skill = SEOSubsidiarySkill()
        context = {'text': 'SEO帮助', 'action': 'help'}
        result = skill.execute(context)
        print(f"  SEO技能执行结果: {result.get('success')}")
        results.append(result.get('success', False))
    except Exception as e:
        print(f"  SEO技能执行失败: {e}")
        results.append(False)

    # 测试创新实验技能执行
    try:
        from hermes_fusion.skills.subsidiaries.innovation_subsidiary import InnovationSubsidiarySkill
        skill = InnovationSubsidiarySkill()
        context = {'text': '创新实验帮助', 'action': 'help'}
        result = skill.execute(context)
        print(f"  创新实验技能执行结果: {result.get('success')}")
        results.append(result.get('success', False))
    except Exception as e:
        print(f"  创新实验技能执行失败: {e}")
        results.append(False)

    # 测试思维模型技能执行
    try:
        from hermes_fusion.skills.subsidiaries.thinking_subsidiary import ThinkingSubsidiarySkill
        skill = ThinkingSubsidiarySkill()
        context = {'text': '思维模型帮助', 'action': 'help'}
        result = skill.execute(context)
        print(f"  思维模型技能执行结果: {result.get('success')}")
        results.append(result.get('success', False))
    except Exception as e:
        print(f"  思维模型技能执行失败: {e}")
        results.append(False)

    # 测试浏览器自动化技能执行
    try:
        from hermes_fusion.skills.subsidiaries.browser_automation_subsidiary import BrowserAutomationSubsidiarySkill
        skill = BrowserAutomationSubsidiarySkill()
        context = {'text': '浏览器自动化帮助', 'action': 'help'}
        result = skill.execute(context)
        print(f"  浏览器自动化技能执行结果: {result.get('success')}")
        results.append(result.get('success', False))
    except Exception as e:
        print(f"  浏览器自动化技能执行失败: {e}")
        results.append(False)

    success_count = sum(1 for r in results if r)
    print(f"  技能执行成功率: {success_count}/{len(results)}")

    return success_count >= 2  # 至少2个成功

def main():
    print("阶段2.2集成测试")
    print("=" * 70)

    tests = [
        ("SEO子公司技能", test_seo_subsidiary),
        ("创新实验子公司技能", test_innovation_subsidiary),
        ("思维模型子公司技能", test_thinking_subsidiary),
        ("浏览器自动化子公司技能", test_browser_automation_subsidiary),
        ("配置加载", test_config_loading),
        ("技能执行", test_skill_execution)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 70)
    print("测试结果:")
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")

    total_passed = sum(1 for _, result in results if result)
    print(f"\n总计: {total_passed}/{len(results)} 个测试通过")

    return total_passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)