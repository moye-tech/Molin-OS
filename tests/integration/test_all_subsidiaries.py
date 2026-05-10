#!/usr/bin/env python3
"""
测试所有11个原始子公司技能
"""
import sys
import os

def test_subsidiary_import(skill_name, module_name, class_name):
    """测试子公司技能导入"""
    try:
        module = __import__(f'hermes_fusion.skills.subsidiaries.{module_name}',
                          fromlist=[class_name])
        skill_class = getattr(module, class_name)
        skill = skill_class()
        print(f"✓ {skill_name}: 导入成功, 名称: {skill.name}")
        return True
    except Exception as e:
        print(f"✗ {skill_name}: 导入失败: {e}")
        return False

def test_subsidiary_can_handle(skill_name, module_name, class_name, test_context):
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

def main():
    print("测试所有11个原始子公司技能")
    print("=" * 70)

    # 子公司定义：名称，模块名，类名，测试上下文
    subsidiaries = [
        ("教育子公司", "edu_subsidiary", "EduSubsidiarySkill",
         {'text': '课程设计'}),
        ("订单子公司", "order_subsidiary", "OrderSubsidiarySkill",
         {'text': '订单处理'}),
        ("IP子公司", "ip_subsidiary", "IpSubsidiarySkill",
         {'text': '内容创作'}),
        ("开发子公司", "dev_subsidiary", "DevSubsidiarySkill",
         {'text': '代码开发'}),
        ("AI子公司", "ai_subsidiary", "AiSubsidiarySkill",
         {'text': 'AI优化'}),
        ("电商子公司", "shop_subsidiary", "ShopSubsidiarySkill",
         {'text': '商品管理'}),
        ("数据子公司", "data_subsidiary", "DataSubsidiarySkill",
         {'text': '数据分析'}),
        ("增长子公司", "growth_subsidiary", "GrowthSubsidiarySkill",
         {'text': '用户增长'}),
        ("安全子公司", "secure_subsidiary", "SecureSubsidiarySkill",
         {'text': '安全审计'}),
        ("研究子公司", "research_subsidiary", "ResearchSubsidiarySkill",
         {'text': '市场研究'}),
        ("产品子公司", "product_subsidiary", "ProductSubsidiarySkill",
         {'text': '产品设计'}),
    ]

    import_results = []
    can_handle_results = []

    for name, module_name, class_name, context in subsidiaries:
        print(f"\n{name}:")

        # 测试导入
        import_ok = test_subsidiary_import(name, module_name, class_name)
        import_results.append(import_ok)

        # 测试can_handle
        if import_ok:
            can_handle_ok = test_subsidiary_can_handle(name, module_name, class_name, context)
            can_handle_results.append(can_handle_ok)
        else:
            can_handle_results.append(False)

    print("\n" + "=" * 70)
    print("导入测试结果:")
    for i, (name, _, _, _) in enumerate(subsidiaries):
        status = "✓ 通过" if import_results[i] else "✗ 失败"
        print(f"  {name}: {status}")

    print("\ncan_handle测试结果:")
    for i, (name, _, _, _) in enumerate(subsidiaries):
        if import_results[i]:
            status = "✓ 通过" if can_handle_results[i] else "✗ 失败"
            print(f"  {name}: {status}")
        else:
            print(f"  {name}: 跳过（导入失败）")

    total_import_passed = sum(1 for r in import_results if r)
    total_can_handle_passed = sum(1 for r in can_handle_results if r)

    print(f"\n总计: {total_import_passed}/{len(subsidiaries)} 个技能导入成功")
    print(f"      {total_can_handle_passed}/{len(subsidiaries)} 个can_handle测试通过")

    # 测试配置加载
    print("\n" + "=" * 70)
    print("测试配置加载...")
    try:
        import yaml
        config_path = "config/hermes-agent/config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        skills_config = config.get('skills', {})
        print(f"主配置中找到 {len(skills_config)} 个技能配置")

        # 检查所有子公司是否在配置中
        required_skill_ids = ['edu', 'order', 'ip', 'dev', 'ai', 'shop', 'data',
                            'growth', 'secure', 'research', 'product']

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
            print("所有11个原始子公司都在配置中找到")

    except Exception as e:
        print(f"配置加载测试失败: {e}")

    return total_import_passed == len(subsidiaries)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)