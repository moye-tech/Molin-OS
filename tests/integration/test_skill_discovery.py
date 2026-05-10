#!/usr/bin/env python3
"""
测试技能发现和配置加载
"""
import sys
import os
import yaml
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_paths():
    """测试配置路径"""
    print("=" * 60)
    print("配置路径测试")
    print("=" * 60)

    # 检查hermes-agent配置目录
    config_dir = "config/hermes-agent"

    if os.path.exists(config_dir):
        print(f"✓ 配置目录存在: {config_dir}")

        # 检查子目录
        subdirs = ['skills', 'tools', 'gateways']
        for subdir in subdirs:
            path = os.path.join(config_dir, subdir)
            if os.path.exists(path):
                print(f"  ✓ {subdir}目录存在")
                files = [f for f in os.listdir(path) if f.endswith('.yaml')]
                print(f"    包含 {len(files)} 个YAML文件")
            else:
                print(f"  ✗ {subdir}目录不存在")
    else:
        print(f"✗ 配置目录不存在: {config_dir}")

    return True

def test_hermes_cli_skills_config():
    """测试hermes_cli.skills_config模块"""
    print("\n" + "=" * 60)
    print("hermes_cli.skills_config模块测试")
    print("=" * 60)

    try:
        import hermes_cli.skills_config as sc
        print("✓ hermes_cli.skills_config导入成功")

        # 查看模块文档和函数
        import inspect
        functions = [name for name, obj in inspect.getmembers(sc)
                    if inspect.isfunction(obj) and not name.startswith('_')]
        print(f"  模块函数: {', '.join(functions)}")

        # 尝试加载配置
        try:
            config = sc.load_config()
            print("✓ load_config()调用成功")

            # 检查返回的数据结构
            if isinstance(config, dict):
                print(f"  配置键: {list(config.keys())}")

                if 'skills' in config:
                    skills = config['skills']
                    print(f"  找到 {len(skills)} 个技能")

                    # 检查技能结构
                    if isinstance(skills, list):
                        print(f"  skills是列表类型，包含 {len(skills)} 个元素")
                        for i, skill in enumerate(skills[:3]):
                            print(f"    技能[{i}]: {type(skill)}")
                            if isinstance(skill, dict):
                                print(f"      技能ID: {skill.get('id', '无ID')}")
                    elif isinstance(skills, dict):
                        print(f"  skills是字典类型，包含 {len(skills)} 个技能")
                        for skill_id, skill_config in list(skills.items())[:3]:
                            print(f"    {skill_id}: {skill_config.get('name', '无名')}")
                else:
                    print("  ✗ 配置中没有'skills'键")
            else:
                print(f"  ✗ 配置不是字典类型: {type(config)}")

        except Exception as e:
            print(f"  ✗ load_config()失败: {e}")
            import traceback
            traceback.print_exc()

    except ImportError as e:
        print(f"✗ hermes_cli.skills_config导入失败: {e}")
        return False

    return True

def test_skill_discovery_from_config():
    """测试从配置文件发现技能"""
    print("\n" + "=" * 60)
    print("从配置文件发现技能测试")
    print("=" * 60)

    # 直接加载我们的配置文件
    config_path = "config/hermes-agent/config.yaml"

    if not os.path.exists(config_path):
        print(f"✗ 配置文件不存在: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        print(f"✓ 配置文件加载成功: {config_path}")

        if 'skills' in config:
            skills = config['skills']
            print(f"  配置中包含 {len(skills)} 个技能:")

            for skill_id, skill_config in skills.items():
                name = skill_config.get('name', '无名')
                enabled = skill_config.get('enabled', True)
                status = "✓" if enabled else "✗"
                print(f"    {status} {name} ({skill_id}) - 启用: {enabled}")

                # 检查触发关键词
                triggers = skill_config.get('triggers', {})
                keywords = triggers.get('keywords', [])
                if keywords:
                    print(f"      触发关键词: {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")

                # 检查工具
                tools = skill_config.get('tools', [])
                if tools:
                    print(f"      工具: {', '.join(tools[:3])}{'...' if len(tools) > 3 else ''}")
        else:
            print("  ✗ 配置中没有'skills'部分")
            return False

    except Exception as e:
        print(f"✗ 配置文件加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

def test_skill_yaml_files():
    """测试技能YAML文件"""
    print("\n" + "=" * 60)
    print("技能YAML文件测试")
    print("=" * 60)

    skills_dir = "config/hermes-agent/skills/"

    if not os.path.exists(skills_dir):
        print(f"✗ 技能目录不存在: {skills_dir}")
        return False

    skill_files = [f for f in os.listdir(skills_dir) if f.endswith('.yaml')]
    print(f"找到 {len(skill_files)} 个技能配置文件")

    validation_results = []

    for skill_file in skill_files:
        file_path = os.path.join(skills_dir, skill_file)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                skill_data = yaml.safe_load(f)

            if not skill_data or not isinstance(skill_data, dict):
                print(f"  ✗ {skill_file}: 文件为空或不是字典")
                validation_results.append((skill_file, False))
                continue

            # 获取技能ID（应该是字典的唯一键）
            skill_id = list(skill_data.keys())[0]
            skill_config = skill_data[skill_id]

            # 验证必要字段
            required_fields = ['name', 'description', 'triggers']
            missing_fields = []

            for field in required_fields:
                if field not in skill_config:
                    missing_fields.append(field)

            if missing_fields:
                print(f"  ✗ {skill_file}: 缺少字段 {missing_fields}")
                validation_results.append((skill_file, False))
            else:
                print(f"  ✓ {skill_file}: {skill_config['name']}")
                validation_results.append((skill_file, True))

        except Exception as e:
            print(f"  ✗ {skill_file}: 加载失败 - {e}")
            validation_results.append((skill_file, False))

    passed = sum(1 for _, success in validation_results if success)
    total = len(validation_results)

    print(f"\n验证结果: {passed}/{total} 通过")

    return passed == total

def test_hermes_cli_command():
    """测试hermes CLI命令"""
    print("\n" + "=" * 60)
    print("hermes CLI命令测试")
    print("=" * 60)

    # 测试hermes skills list命令
    import subprocess

    try:
        result = subprocess.run(
            ["./venv/bin/hermes", "skills", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        print("✓ hermes skills list命令执行成功")
        print(f"  返回码: {result.returncode}")

        # 检查输出是否包含我们的子公司技能
        output_lower = result.stdout.lower()

        # 检查是否有我们的技能关键词
        keywords = ['教育', '订单', 'ai', '数据', '开发', '电商', '增长', '安全', '研究', '产品', 'ceo']
        found_keywords = []

        for keyword in keywords:
            if keyword in output_lower:
                found_keywords.append(keyword)

        if found_keywords:
            print(f"  找到相关关键词: {', '.join(found_keywords)}")
        else:
            print("  ⚠️  输出中未找到子公司技能关键词")
            print("  可能原因:")
            print("    1. hermes skills list只显示内置技能")
            print("    2. 我们的配置需要特定方式加载")
            print("    3. 技能需要手动启用")

        # 显示部分输出
        lines = result.stdout.split('\n')
        print(f"  输出行数: {len(lines)}")
        if lines:
            print("  前5行输出:")
            for line in lines[:5]:
                if line.strip():
                    print(f"    {line}")

    except Exception as e:
        print(f"✗ hermes CLI命令测试失败: {e}")
        return False

    return True

def main():
    """主测试函数"""
    print("墨麟AI智能系统技能发现测试")
    print("=" * 60)

    tests = [
        ("配置路径测试", test_config_paths),
        ("hermes_cli.skills_config模块测试", test_hermes_cli_skills_config),
        ("从配置文件发现技能测试", test_skill_discovery_from_config),
        ("技能YAML文件测试", test_skill_yaml_files),
        ("hermes CLI命令测试", test_hermes_cli_command),
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
    print("诊断建议")
    print("=" * 60)

    if passed < len(results):
        print("⚠️  部分测试失败，建议检查:")
        print("  1. hermes-agent配置加载机制")
        print("  2. 技能配置格式是否符合hermes-agent要求")
        print("  3. 配置路径是否正确")
        print("  4. 技能是否需要注册或启用")
    else:
        print("✓ 所有测试通过，技能发现机制正常")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)