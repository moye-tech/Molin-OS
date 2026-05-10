#!/usr/bin/env python3
"""
测试hermes-agent技能发现
验证我们的技能能否被hermes-agent发现
"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_skill_discovery():
    """测试技能发现"""
    print("=" * 60)
    print("测试hermes-agent技能发现")
    print("=" * 60)

    try:
        # 导入hermes-agent工具
        from tools.skills_tool import _find_all_skills
        print("✓ 导入_find_all_skills成功")

        # 查找所有技能
        all_skills = _find_all_skills()
        print(f"找到 {len(all_skills)} 个技能")

        # 查找我们的CEO决策技能
        our_skills = []
        for skill in all_skills:
            name = skill.get('name', '').lower()
            if 'ceo' in name or '决策' in name:
                our_skills.append(skill)
                print(f"✓ 找到我们的技能: {skill.get('name')}")
                print(f"  描述: {skill.get('description', '')[:100]}...")
                print(f"  分类: {skill.get('category', '')}")

        if our_skills:
            print(f"\n成功发现 {len(our_skills)} 个我们的技能")
            return True
        else:
            print("\n✗ 未发现我们的技能")
            print("可能原因:")
            print("  1. external_dirs配置不正确")
            print("  2. SKILL.md格式不正确")
            print("  3. 技能目录路径不正确")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_skill_view():
    """测试技能查看"""
    print("\n" + "=" * 60)
    print("测试hermes-agent技能查看")
    print("=" * 60)

    try:
        from tools.skills_tool import skill_view
        print("✓ 导入skill_view成功")

        # 查看CEO决策技能
        result_json = skill_view("ceo-decision")
        result = json.loads(result_json)

        if result.get('success'):
            print("✓ skill_view成功")
            print(f"  技能名称: {result.get('name', 'N/A')}")
            print(f"  技能路径: {result.get('path', 'N/A')}")

            # 检查内容
            content = result.get('content', '')
            if content:
                print(f"  内容长度: {len(content)} 字符")
                print(f"  内容预览: {content[:200]}...")

            return True
        else:
            print(f"✗ skill_view失败: {result.get('error', '未知错误')}")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_external_dirs():
    """测试external_dirs配置"""
    print("\n" + "=" * 60)
    print("测试external_dirs配置")
    print("=" * 60)

    try:
        from hermes_cli.config import load_config
        config = load_config()
        print("✓ 配置加载成功")

        skills_config = config.get('skills', {})
        external_dirs = skills_config.get('external_dirs', [])

        print(f"  external_dirs配置: {external_dirs}")

        if external_dirs:
            print("✓ external_dirs配置存在")

            # 检查目录是否存在
            for dir_path in external_dirs:
                if os.path.exists(dir_path):
                    print(f"  ✓ 目录存在: {dir_path}")

                    # 检查SKILL.md文件
                    skill_files = []
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            if file == 'SKILL.md':
                                skill_files.append(os.path.join(root, file))

                    print(f"    找到 {len(skill_files)} 个SKILL.md文件")
                    for skill_file in skill_files[:3]:  # 显示前3个
                        print(f"    - {skill_file}")

                    if skill_files:
                        return True
                    else:
                        print(f"    ✗ 目录中未找到SKILL.md文件")
                        return False
                else:
                    print(f"  ✗ 目录不存在: {dir_path}")
                    return False
        else:
            print("✗ external_dirs配置为空")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("墨麟AI技能发现测试")
    print("=" * 60)

    tests = [
        ("external_dirs配置测试", test_config_external_dirs),
        ("技能发现测试", test_skill_discovery),
        ("技能查看测试", test_skill_view),
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

    if passed == len(results):
        print("✓ 所有测试通过，技能发现机制正常")
        print("\n建议下一步:")
        print("  1. 为所有子公司创建SKILL.md文件")
        print("  2. 测试实际hermes-agent会话中的技能调用")
        print("  3. 验证技能路由和执行")
    else:
        print("⚠️ 部分测试失败，建议检查:")
        print("  1. config.yaml中的external_dirs配置")
        print("  2. SKILL.md文件格式是否正确")
        print("  3. 技能目录权限和路径")
        print("  4. hermes-agent配置加载机制")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)