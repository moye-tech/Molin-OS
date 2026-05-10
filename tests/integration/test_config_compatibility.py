#!/usr/bin/env python3
"""
测试配置兼容性
验证生成的hermes-agent配置是否有效
"""

import sys
import os
import yaml
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_yaml_loading():
    """测试YAML配置文件加载"""
    print("测试配置兼容性...")

    config_path = "config/hermes-agent/config.yaml"

    if not os.path.exists(config_path):
        print(f"配置文件不存在: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print(f"✓ 配置文件加载成功")
        print(f"  版本: {config.get('version')}")
        print(f"  技能数量: {len(config.get('skills', {}))}")
        print(f"  工具数量: {len(config.get('tools', {}))}")
        print(f"  记忆提供者数量: {len(config.get('memory_providers', {}))}")
        print(f"  模型路由规则数量: {len(config.get('model_preferences', {}))}")

        # 验证必需字段
        required_fields = ['version', 'skills', 'tools']
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            print(f"✗ 缺少必需字段: {missing_fields}")
            return False
        else:
            print("✓ 所有必需字段都存在")

        # 验证技能配置
        skills = config.get('skills', {})
        if not skills:
            print("✗ 没有技能定义")
            return False

        print(f"✓ 发现{len(skills)}个技能:")
        for skill_id in list(skills.keys())[:5]:  # 只显示前5个
            skill = skills[skill_id]
            print(f"  - {skill_id}: {skill.get('name')}")

        if len(skills) > 5:
            print(f"  ... 和{len(skills)-5}个其他技能")

        return True

    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        return False

def test_skill_yaml_files():
    """测试技能YAML文件"""
    print("\n测试技能YAML文件...")

    skills_dir = "config/hermes-agent/skills"

    if not os.path.exists(skills_dir):
        print(f"✗ 技能目录不存在: {skills_dir}")
        return False

    skill_files = [f for f in os.listdir(skills_dir) if f.endswith('.yaml') or f.endswith('.yml')]

    if not skill_files:
        print(f"✗ 没有技能YAML文件")
        return False

    print(f"✓ 发现{len(skill_files)}个技能YAML文件")

    # 测试随机文件加载
    test_files = skill_files[:3]  # 测试前3个文件
    for skill_file in test_files:
        file_path = os.path.join(skills_dir, skill_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                skill_config = yaml.safe_load(f)

            skill_id = skill_file.replace('.yaml', '').replace('.yml', '')
            print(f"  ✓ {skill_file}: 加载成功")

        except Exception as e:
            print(f"  ✗ {skill_file}: 加载失败 - {e}")
            return False

    return True

def test_tools_yaml_files():
    """测试工具YAML文件"""
    print("\n测试工具YAML文件...")

    tools_dir = "config/hermes-agent/tools"

    if not os.path.exists(tools_dir):
        print(f"✗ 工具目录不存在: {tools_dir}")
        return False

    tool_files = [f for f in os.listdir(tools_dir) if f.endswith('.yaml') or f.endswith('.yml')]

    if not tool_files:
        print(f"✗ 没有工具YAML文件")
        return False

    print(f"✓ 发现{len(tool_files)}个工具YAML文件")

    # 测试随机文件加载
    test_files = tool_files[:3]
    for tool_file in test_files:
        file_path = os.path.join(tools_dir, tool_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tool_config = yaml.safe_load(f)

            print(f"  ✓ {tool_file}: 加载成功")

        except Exception as e:
            print(f"  ✗ {tool_file}: 加载失败 - {e}")
            return False

    return True

def test_memory_providers_config():
    """测试记忆提供者配置"""
    print("\n测试记忆提供者配置...")

    config_path = "config/hermes-agent/config.yaml"

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        memory_providers = config.get('memory_providers', {})

        if not memory_providers:
            print("✗ 没有记忆提供者配置")
            return False

        print(f"✓ 发现{len(memory_providers)}个记忆提供者:")
        for provider_id, provider_config in memory_providers.items():
            provider_type = provider_config.get('type', 'unknown')
            enabled = provider_config.get('enabled', False)
            status = "启用" if enabled else "禁用"
            print(f"  - {provider_id}: {provider_type} ({status})")

        return True

    except Exception as e:
        print(f"✗ 记忆提供者配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("墨麟AI智能系统 配置兼容性测试")
    print("=" * 60)

    tests = [
        ("YAML配置文件加载", test_yaml_loading),
        ("技能YAML文件", test_skill_yaml_files),
        ("工具YAML文件", test_tools_yaml_files),
        ("记忆提供者配置", test_memory_providers_config),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n[测试] {test_name}")
        try:
            if test_func():
                print(f"  ✓ {test_name} - 通过")
                passed_tests += 1
            else:
                print(f"  ✗ {test_name} - 失败")
        except Exception as e:
            print(f"  ✗ {test_name} - 异常: {e}")

    print("\n" + "=" * 60)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")

    if passed_tests == total_tests:
        print("✓ 所有配置兼容性测试通过!")
        return True
    else:
        print("✗ 部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)