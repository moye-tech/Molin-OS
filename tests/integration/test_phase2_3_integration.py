#!/usr/bin/env python3
"""
测试阶段2.3：优先级3项目集成
测试vision、finance等新子公司技能
"""
import sys
import os

def test_skill_import(skill_name, module_name, class_name):
    """测试技能导入"""
    try:
        module = __import__(f'hermes_fusion.skills.subsidiaries.{module_name}',
                          fromlist=[class_name])
        skill_class = getattr(module, class_name)
        skill = skill_class()
        print(f"✓ {skill_name}: 导入成功, 名称: {skill.name}")
        return True
    except Exception as e:
        print(f"✗ {skill_name}: 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_can_handle(skill_name, module_name, class_name, test_context):
    """测试can_handle功能"""
    try:
        module = __import__(f'hermes_fusion.skills.subsidiaries.{module_name}',
                          fromlist=[class_name])
        skill_class = getattr(module, class_name)
        skill = skill_class()

        can_handle = skill.can_handle(test_context)
        print(f"  {skill_name} can_handle测试: {can_handle}")
        return can_handle
    except Exception as e:
        print(f"  {skill_name} can_handle测试失败: {e}")
        return False

def test_skill_execute(skill_name, module_name, class_name, test_context):
    """测试技能执行（使用action='help'触发一般响应）"""
    try:
        module = __import__(f'hermes_fusion.skills.subsidiaries.{module_name}',
                          fromlist=[class_name])
        skill_class = getattr(module, class_name)
        skill = skill_class()

        # 使用action='help'触发一般响应
        context = test_context.copy()
        if 'action' not in context:
            context['action'] = 'help'

        result = skill.execute(context)
        print(f"  {skill_name} execute测试: {result.get('success', False)}")
        if result.get('success', False):
            print(f"    结果: {result.get('message', '无消息')[:100]}...")
        else:
            print(f"    错误: {result.get('error', '未知错误')}")
        return result.get('success', False)
    except Exception as e:
        print(f"  {skill_name} execute测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("阶段2.3：优先级3项目集成测试")
    print("=" * 70)

    # 新子公司技能定义
    new_subsidiaries = [
        ("视觉分析子公司", "vision_subsidiary", "VisionSubsidiarySkill",
         {'text': '图像分析测试', 'image_data': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', 'action': 'image_analysis'}),
        ("金融交易子公司", "finance_subsidiary", "FinanceSubsidiarySkill",
         {'text': '股票分析测试'}),
        ("SEO优化子公司", "seo_subsidiary", "SEOSubsidiarySkill",
         {'text': 'SEO分析测试'}),
        ("创新实验子公司", "innovation_subsidiary", "InnovationSubsidiarySkill",
         {'text': 'A/B测试实验'}),
        ("思维模型子公司", "thinking_subsidiary", "ThinkingSubsidiarySkill",
         {'text': '思维模型分析'}),
        ("浏览器自动化子公司", "browser_automation_subsidiary", "BrowserAutomationSubsidiarySkill",
         {'text': '网页自动化测试'}),
    ]

    import_results = []
    can_handle_results = []
    execute_results = []

    for name, module_name, class_name, context in new_subsidiaries:
        print(f"\n{name}:")

        # 测试导入
        import_ok = test_skill_import(name, module_name, class_name)
        import_results.append(import_ok)

        # 测试can_handle
        if import_ok:
            can_handle_ok = test_skill_can_handle(name, module_name, class_name, context)
            can_handle_results.append(can_handle_ok)

            # 测试execute（使用action='help'触发一般响应）
            if can_handle_ok:
                execute_ok = test_skill_execute(name, module_name, class_name, context)
                execute_results.append(execute_ok)
            else:
                execute_results.append(False)
        else:
            can_handle_results.append(False)
            execute_results.append(False)

    print("\n" + "=" * 70)
    print("导入测试结果:")
    for i, (name, _, _, _) in enumerate(new_subsidiaries):
        status = "✓ 通过" if import_results[i] else "✗ 失败"
        print(f"  {name}: {status}")

    print("\ncan_handle测试结果:")
    for i, (name, _, _, _) in enumerate(new_subsidiaries):
        if import_results[i]:
            status = "✓ 通过" if can_handle_results[i] else "✗ 失败"
            print(f"  {name}: {status}")
        else:
            print(f"  {name}: 跳过（导入失败）")

    print("\nexecute测试结果:")
    for i, (name, _, _, _) in enumerate(new_subsidiaries):
        if import_results[i] and can_handle_results[i]:
            status = "✓ 通过" if execute_results[i] else "✗ 失败"
            print(f"  {name}: {status}")
        else:
            print(f"  {name}: 跳过（导入或can_handle失败）")

    total_import_passed = sum(1 for r in import_results if r)
    total_can_handle_passed = sum(1 for r in can_handle_results if r)
    total_execute_passed = sum(1 for r in execute_results if r)

    print(f"\n总计: {total_import_passed}/{len(new_subsidiaries)} 个技能导入成功")
    print(f"      {total_can_handle_passed}/{len(new_subsidiaries)} 个can_handle测试通过")
    print(f"      {total_execute_passed}/{len(new_subsidiaries)} 个execute测试通过")

    # 测试配置加载
    print("\n" + "=" * 70)
    print("测试配置加载...")
    try:
        import yaml
        config_path = "config/hermes-agent/config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        skills_config = config.get('skills', {})
        print(f"主配置中找到 {len(skills_config)} 个技能配置（包括外部目录）")

        # 检查新技能是否在配置中
        required_skill_ids = ['vision', 'finance', 'seo', 'innovation', 'thinking', 'browser_automation']

        missing_skills = []
        for skill_id in required_skill_ids:
            if skill_id in skills_config:
                print(f"  ✓ {skill_id}: 在配置中找到")
            else:
                print(f"  ✗ {skill_id}: 未在配置中找到")
                missing_skills.append(skill_id)

        if missing_skills:
            print(f"警告: {len(missing_skills)} 个技能未在配置中找到: {missing_skills}")
        else:
            print("所有6个新子公司都在配置中找到")

        # 检查scheduling配置
        scheduling_config = config.get('scheduling', {})
        per_skill_limits = scheduling_config.get('per_skill_limits', {})
        print(f"\n并发限制配置检查:")
        for skill_id in required_skill_ids:
            limit = per_skill_limits.get(skill_id)
            if limit is not None:
                print(f"  ✓ {skill_id}: 并发限制 = {limit}")
            else:
                print(f"  ✗ {skill_id}: 未设置并发限制")

    except Exception as e:
        print(f"配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()

    return total_import_passed == len(new_subsidiaries)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)