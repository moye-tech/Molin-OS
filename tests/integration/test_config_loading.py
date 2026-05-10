#!/usr/bin/env python3
"""
测试hermes-agent配置加载
验证项目配置是否正确加载
"""

import sys
import os
import yaml

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_project_config_exists():
    """测试项目配置文件存在"""
    print("=" * 60)
    print("测试项目配置文件")
    print("=" * 60)

    config_path = os.path.join(os.path.dirname(__file__), 'config', 'hermes-agent', 'config.yaml')

    if os.path.exists(config_path):
        print(f"✓ 项目配置文件存在: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # 检查关键配置部分
            required_sections = ['skills', 'gateways', 'memory_providers', 'model_preferences']
            missing_sections = []

            for section in required_sections:
                if section in config:
                    print(f"  ✓ 配置部分 '{section}' 存在")

                    # 统计技能数量
                    if section == 'skills':
                        # skills可能包含external_dirs列表或其他键
                        if isinstance(config['skills'], dict):
                            skill_count = len([k for k in config['skills'].keys() if not k.startswith('#') and k != 'external_dirs'])
                            print(f"    技能定义数量: {skill_count}")
                        elif isinstance(config['skills'], list):
                            print(f"    技能定义数量: {len(config['skills'])}")
                else:
                    print(f"  ✗ 配置部分 '{section}' 缺失")
                    missing_sections.append(section)

            if not missing_sections:
                print("\n✓ 项目配置文件完整性检查通过")
                return True
            else:
                print(f"\n✗ 配置缺少部分: {missing_sections}")
                return False

        except Exception as e:
            print(f"✗ 配置文件解析失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"✗ 项目配置文件不存在: {config_path}")
        return False

def test_hermes_agent_config_loading():
    """测试hermes-agent配置加载"""
    print("\n" + "=" * 60)
    print("测试hermes-agent配置加载")
    print("=" * 60)

    try:
        # 设置环境变量
        project_config_path = os.path.join(os.path.dirname(__file__), 'config', 'hermes-agent', 'config.yaml')
        os.environ['HERMES_CONFIG_PATH'] = project_config_path

        # 尝试导入hermes_agent配置
        import hermes_agent
        print("✓ hermes_agent模块导入成功")

        # 检查是否有配置属性
        if hasattr(hermes_agent, 'config'):
            print(f"  ✓ hermes_agent有config属性")
            config = hermes_agent.config
            print(f"    配置类型: {type(config)}")
        else:
            print("  ✗ hermes_agent没有config属性")

        # 尝试导入agent模块（主模块）
        import agent
        print("✓ agent模块导入成功")

        # 尝试导入skills模块
        import skills
        print("✓ skills模块导入成功")

        # 检查技能目录
        skills_dir = os.path.join(os.path.dirname(__file__), 'upstream', 'hermes-agent', 'skills')
        if os.path.exists(skills_dir):
            print(f"✓ 技能目录存在: {skills_dir}")
            skill_categories = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
            print(f"  技能类别数量: {len(skill_categories)}")
            print(f"  前5个类别: {', '.join(skill_categories[:5])}")
        else:
            print(f"✗ 技能目录不存在: {skills_dir}")

        print("\n✓ hermes-agent配置加载测试通过")
        return True

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_discovery():
    """测试技能发现"""
    print("\n" + "=" * 60)
    print("测试技能发现")
    print("=" * 60)

    try:
        # 检查项目技能目录
        project_skills_dir = os.path.join(os.path.dirname(__file__), 'hermes-agent-skills')
        if os.path.exists(project_skills_dir):
            print(f"✓ 项目技能目录存在: {project_skills_dir}")
            skill_dirs = [d for d in os.listdir(project_skills_dir) if os.path.isdir(os.path.join(project_skills_dir, d))]
            print(f"  项目技能数量: {len(skill_dirs)}")
            print(f"  技能列表: {', '.join(skill_dirs)}")
        else:
            print(f"✗ 项目技能目录不存在: {project_skills_dir}")

        # 检查config.yaml中的external_dirs配置
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'hermes-agent', 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if 'skills' in config and 'external_dirs' in config['skills']:
            external_dirs = config['skills']['external_dirs']
            print(f"✓ 配置中包含external_dirs: {external_dirs}")

            for dir_path in external_dirs:
                if os.path.exists(dir_path):
                    print(f"  ✓ 外部目录存在: {dir_path}")
                else:
                    print(f"  ✗ 外部目录不存在: {dir_path}")
        else:
            print("✗ 配置中没有external_dirs设置")

        print("\n✓ 技能发现测试通过")
        return True

    except Exception as e:
        print(f"✗ 技能发现测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("墨麟AI配置加载测试")
    print("=" * 60)

    tests = [
        ("项目配置文件检查", test_project_config_exists),
        ("hermes-agent配置加载", test_hermes_agent_config_loading),
        ("技能发现", test_skill_discovery),
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
    print("配置加载测试结果汇总")
    print("=" * 60)

    passed = 0
    for test_name, success in results:
        status = "✓" if success else "✗"
        print(f"  {status} {test_name}")
        if success:
            passed += 1

    total = len(results)
    print(f"\n通过: {passed}/{total} ({passed/total*100:.1f}%)")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)