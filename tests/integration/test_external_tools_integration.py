#!/usr/bin/env python3
"""
测试外部工具集成 - CLI和社交媒体工具适配器
验证OpenCLI和xiaohongshu-cli项目的集成效果
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_cli_tools_import():
    """测试CLI工具导入"""
    print("=" * 60)
    print("测试CLI工具导入")
    print("=" * 60)

    try:
        from hermes_fusion.integration.external_tools.cli_tools import (
            CLIToolAdapter,
            cli_tool_adapter,
            initialize_cli_tools,
            execute_cli_command
        )

        print("✓ 导入成功")
        print(f"  适配器类: {CLIToolAdapter.__name__}")
        print(f"  适配器实例: {cli_tool_adapter.__class__.__name__}")
        print(f"  工具名称: {cli_tool_adapter.tool_name}")
        print(f"  工具集: {cli_tool_adapter.toolset}")
        print(f"  描述: {cli_tool_adapter.description}")

        # 测试初始化
        print("\n测试CLI工具初始化...")
        init_result = initialize_cli_tools()
        print(f"  初始化结果: {init_result.get('status', 'unknown')}")
        print(f"  描述: {init_result.get('description', 'N/A')}")
        print(f"  外部项目: {init_result.get('external_project', 'N/A')}")
        print(f"  外部加载: {init_result.get('external_loaded', False)}")

        # 测试命令执行（简单命令）
        print("\n测试简单命令执行...")
        result = execute_cli_command("echo", ["Hello CLI Integration Test"])

        print(f"  状态: {result.get('status', 'unknown')}")
        print(f"  命令: {result.get('command', 'N/A')}")
        print(f"  执行时间: {result.get('execution_time', 0):.3f}秒")

        if result.get('status') == 'success':
            cmd_result = result.get('result', {})
            print(f"  退出码: {cmd_result.get('exit_code', 'N/A')}")
            print(f"  标准输出: {cmd_result.get('stdout', 'N/A')[:100]}...")
            return True
        else:
            print(f"  错误: {result.get('error', '未知错误')}")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_social_media_tools_import():
    """测试社交媒体工具导入"""
    print("\n" + "=" * 60)
    print("测试社交媒体工具导入")
    print("=" * 60)

    try:
        from hermes_fusion.integration.external_tools.social_media_tools import (
            XiaohongshuToolAdapter,
            social_media_adapter,
            initialize_social_media_tools,
            publish_to_xiaohongshu,
            SocialMediaPlatform,
            SocialMediaContentType
        )

        print("✓ 导入成功")
        print(f"  适配器类: {XiaohongshuToolAdapter.__name__}")
        print(f"  适配器实例: {social_media_adapter.__class__.__name__}")
        print(f"  工具名称: {social_media_adapter.tool_name}")
        print(f"  工具集: {social_media_adapter.toolset}")
        print(f"  描述: {social_media_adapter.description}")

        # 测试平台枚举
        print(f"\n支持的平台:")
        for platform in SocialMediaPlatform:
            print(f"  - {platform.value}")

        # 测试内容类型枚举
        print(f"支持的内容类型:")
        for content_type in SocialMediaContentType:
            print(f"  - {content_type.value}")

        # 测试初始化
        print("\n测试社交媒体工具初始化...")
        init_result = initialize_social_media_tools()
        print(f"  初始化结果: {init_result.get('status', 'unknown')}")
        print(f"  描述: {init_result.get('description', 'N/A')}")
        print(f"  外部项目: {init_result.get('external_project', 'N/A')}")
        print(f"  外部加载: {init_result.get('external_loaded', False)}")
        print(f"  支持的平台: {init_result.get('platforms_supported', [])}")

        # 测试发布功能（模拟模式）
        print("\n测试小红书内容发布（模拟模式）...")
        result = publish_to_xiaohongshu(
            content="测试集成内容 - 这是一个测试帖",
            images=["test_image1.jpg", "test_image2.jpg"],
            tags=["测试", "集成", "小红书"]
        )

        print(f"  状态: {result.get('status', 'unknown')}")
        print(f"  平台: {result.get('platform', 'N/A')}")

        if result.get('status') == 'success':
            post_result = result.get('result', {})
            print(f"  帖子ID: {post_result.get('post_id', 'N/A')}")
            print(f"  帖子状态: {post_result.get('status', 'N/A')}")
            print(f"  内容预览: {post_result.get('content', 'N/A')[:50]}...")
            print(f"  标签: {post_result.get('tags', [])}")
            return True
        else:
            print(f"  错误: {result.get('error', '未知错误')}")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_subsidiary_skill():
    """测试CLI子公司技能"""
    print("\n" + "=" * 60)
    print("测试CLI子公司技能")
    print("=" * 60)

    try:
        from hermes_fusion.skills.subsidiaries.cli_subsidiary import CLISubsidiarySkill

        print("✓ 技能导入成功")

        # 创建技能实例
        skill = CLISubsidiarySkill()
        print(f"  技能名称: {skill.name}")
        print(f"  技能描述: {skill.description}")
        print(f"  触发关键词: {skill.keywords}")
        print(f"  CLI工具初始化: {skill.cli_initialized}")

        # 测试can_handle
        print("\n测试can_handle功能...")
        test_contexts = [
            {"text": "执行ls命令查看文件"},
            {"text": "运行一个shell脚本"},
            {"text": "批量执行命令"},
            {"text": "配置系统参数"},
            {"text": "分析数据生成报告"}  # 应该返回False
        ]

        for context in test_contexts:
            can_handle = skill.can_handle(context)
            status = "✓" if can_handle else "✗"
            print(f"  {status} '{context['text']}' -> {can_handle}")

        # 测试执行（简单命令）
        print("\n测试执行功能（简单命令）...")
        context = {
            "text": "执行echo命令",
            "command": "echo",
            "args": ["Hello from CLISubsidiarySkill"],
            "timeout": 10
        }

        result = skill.execute(context)
        print(f"  执行成功: {result.get('success', False)}")
        print(f"  服务类型: {result.get('service', 'N/A')}")
        print(f"  执行时间: {result.get('execution_time', 0):.3f}秒")
        print(f"  成本估计: {result.get('cost_estimate', 0)}")
        print(f"  需要审批: {result.get('requires_approval', False)}")

        if result.get('success'):
            result_data = result.get('result', {})
            print(f"  适配器: {result.get('adapter', 'N/A')}")
            return True
        else:
            print(f"  错误: {result.get('error', '未知错误')}")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_social_media_subsidiary_skill():
    """测试社交媒体子公司技能"""
    print("\n" + "=" * 60)
    print("测试社交媒体子公司技能")
    print("=" * 60)

    try:
        from hermes_fusion.skills.subsidiaries.social_media_subsidiary import SocialMediaSubsidiarySkill

        print("✓ 技能导入成功")

        # 创建技能实例
        skill = SocialMediaSubsidiarySkill()
        print(f"  技能名称: {skill.name}")
        print(f"  技能描述: {skill.description}")
        print(f"  触发关键词: {skill.keywords}")
        print(f"  社交媒体工具初始化: {skill.social_media_initialized}")

        # 测试can_handle
        print("\n测试can_handle功能...")
        test_contexts = [
            {"text": "发布一篇小红书"},
            {"text": "分析用户互动数据"},
            {"text": "定时发布内容"},
            {"text": "策划营销活动"},
            {"text": "执行系统命令"}  # 应该返回False
        ]

        for context in test_contexts:
            can_handle = skill.can_handle(context)
            status = "✓" if can_handle else "✗"
            print(f"  {status} '{context['text']}' -> {can_handle}")

        # 测试执行（内容发布）
        print("\n测试执行功能（内容发布）...")
        context = {
            "text": "发布一篇关于美食的小红书",
            "content": "今天分享一道家常菜的做法，简单又美味！",
            "images": ["food1.jpg", "food2.jpg"],
            "tags": ["美食", "家常菜", "食谱"],
            "platform": "xiaohongshu"
        }

        result = skill.execute(context)
        print(f"  执行成功: {result.get('success', False)}")
        print(f"  服务类型: {result.get('service', 'N/A')}")
        print(f"  平台: {result.get('platform', 'N/A')}")
        print(f"  执行时间: {result.get('execution_time', 0):.3f}秒")
        print(f"  成本估计: {result.get('cost_estimate', 0)}")
        print(f"  需要审批: {result.get('requires_approval', False)}")

        if result.get('success'):
            result_data = result.get('result', {})
            print(f"  适配器: {result.get('adapter', 'N/A')}")
            return True
        else:
            print(f"  错误: {result.get('error', '未知错误')}")
            return False

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_subsidiary_integration():
    """测试子公司技能集成"""
    print("\n" + "=" * 60)
    print("测试子公司技能集成到hermes-native系统")
    print("=" * 60)

    try:
        from hermes_fusion.skills.hermes_native.subsidiary_base_skill import SubsidiaryMolinSkill

        print("✓ 导入SubsidiaryMolinSkill成功")

        # 测试CLI子公司集成
        print("\n测试CLI子公司集成...")
        cli_skill = SubsidiaryMolinSkill({'subsidiary_type': 'cli'})

        print(f"  技能名称: {cli_skill.name}")
        print(f"  技能类型: {cli_skill.subsidiary_type}")
        print(f"  是否有子公司实例: {hasattr(cli_skill, 'subsidiary_skill')}")

        # 测试can_handle
        context = {"text": "执行ls命令"}
        can_handle = cli_skill.sync_can_handle(context)
        print(f"  can_handle('执行ls命令'): {can_handle}")

        # 测试社交媒体子公司集成
        print("\n测试社交媒体子公司集成...")
        social_skill = SubsidiaryMolinSkill({'subsidiary_type': 'social_media'})

        print(f"  技能名称: {social_skill.name}")
        print(f"  技能类型: {social_skill.subsidiary_type}")
        print(f"  是否有子公司实例: {hasattr(social_skill, 'subsidiary_skill')}")

        # 测试can_handle
        context = {"text": "发布小红书内容"}
        can_handle = social_skill.sync_can_handle(context)
        print(f"  can_handle('发布小红书内容'): {can_handle}")

        return True

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
    print("外部工具集成测试 - OpenCLI和xiaohongshu-cli集成")
    print("=" * 60)

    tests = [
        ("CLI工具导入测试", test_cli_tools_import),
        ("社交媒体工具导入测试", test_social_media_tools_import),
        ("CLI子公司技能测试", test_cli_subsidiary_skill),
        ("社交媒体子公司技能测试", test_social_media_subsidiary_skill),
        ("子公司集成测试", test_subsidiary_integration),
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

    success_rate = passed / len(results) if results else 0
    print(f"\n通过率: {success_rate:.1%} ({passed}/{len(results)})")

    # 诊断建议
    print("\n" + "=" * 60)
    print("诊断建议")
    print("=" * 60)

    if passed == len(results):
        print("✓ 所有外部工具集成测试通过")
        print("\n集成状态:")
        print("  1. CLI工具适配器 - 功能完整")
        print("  2. 社交媒体工具适配器 - 功能完整")
        print("  3. CLI子公司技能 - 集成成功")
        print("  4. 社交媒体子公司技能 - 集成成功")
        print("  5. hermes-native集成 - 正常工作")
    else:
        print("⚠️ 部分测试失败，建议检查:")
        print("  1. 项目路径配置是否正确")
        print("  2. 外部项目是否存在（OpenCLI/xiaohongshu-cli）")
        print("  3. 导入路径和依赖是否完整")
        print("  4. 技能配置是否正确")

    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)