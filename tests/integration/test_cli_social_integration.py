#!/usr/bin/env python3
"""
测试CLI和社交媒体技能集成
验证OpenCLI和xiaohongshu-cli项目集成功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("测试CLI和社交媒体技能集成...")
print("=" * 70)

# 测试CLI技能导入
print("\n1. 测试CLI技能导入...")
try:
    from hermes_fusion.skills.subsidiaries.cli_subsidiary import CLISubsidiarySkill
    print("✓ CLI技能导入成功")

    # 创建实例
    cli_skill = CLISubsidiarySkill()
    print("✓ CLI技能实例创建成功")

    # 测试can_handle
    test_context = {'text': '执行ls命令'}
    can_handle = cli_skill.can_handle(test_context)
    print(f"  CLI技能can_handle测试: {can_handle} (期望: True)")

    # 测试初始化状态
    print(f"  CLI工具初始化状态: {cli_skill.cli_initialized}")

except ImportError as e:
    print(f"✗ CLI技能导入失败: {e}")
except Exception as e:
    print(f"✗ CLI技能测试异常: {e}")
    import traceback
    traceback.print_exc()

# 测试社交媒体技能导入
print("\n2. 测试社交媒体技能导入...")
try:
    from hermes_fusion.skills.subsidiaries.social_media_subsidiary import SocialMediaSubsidiarySkill
    print("✓ 社交媒体技能导入成功")

    # 创建实例
    social_skill = SocialMediaSubsidiarySkill()
    print("✓ 社交媒体技能实例创建成功")

    # 测试can_handle
    test_context = {'text': '发布小红书内容'}
    can_handle = social_skill.can_handle(test_context)
    print(f"  社交媒体技能can_handle测试: {can_handle} (期望: True)")

    # 测试初始化状态
    print(f"  社交媒体工具初始化状态: {social_skill.social_media_initialized}")

except ImportError as e:
    print(f"✗ 社交媒体技能导入失败: {e}")
except Exception as e:
    print(f"✗ 社交媒体技能测试异常: {e}")
    import traceback
    traceback.print_exc()

# 测试CLI工具适配器
print("\n3. 测试CLI工具适配器...")
try:
    from hermes_fusion.integration.external_tools.cli_tools import CLIToolAdapter, cli_tool_adapter
    print("✓ CLI工具适配器导入成功")

    # 创建适配器实例
    adapter = CLIToolAdapter()
    print("✓ CLI工具适配器实例创建成功")

    # 测试简单命令执行（模拟）
    result = adapter.execute_command("echo", ["test"])
    print(f"  CLI命令执行测试: {result.get('status')} (期望: success或error)")

except ImportError as e:
    print(f"✗ CLI工具适配器导入失败: {e}")
except Exception as e:
    print(f"✗ CLI工具适配器测试异常: {e}")
    import traceback
    traceback.print_exc()

# 测试社交媒体工具适配器
print("\n4. 测试社交媒体工具适配器...")
try:
    from hermes_fusion.integration.external_tools.social_media_tools import XiaohongshuToolAdapter, social_media_adapter
    print("✓ 社交媒体工具适配器导入成功")

    # 创建适配器实例
    adapter = XiaohongshuToolAdapter()
    print("✓ 社交媒体工具适配器实例创建成功")

    # 测试内容发布（模拟）
    result = adapter.publish_content("测试内容", images=[])
    print(f"  社交媒体内容发布测试: {result.get('status')} (期望: success)")

except ImportError as e:
    print(f"✗ 社交媒体工具适配器导入失败: {e}")
except Exception as e:
    print(f"✗ 社交媒体工具适配器测试异常: {e}")
    import traceback
    traceback.print_exc()

# 测试外部工具管理器
print("\n5. 测试外部工具管理器...")
try:
    from hermes_fusion.integration.external_tools.manager import ExternalToolManager
    print("✓ 外部工具管理器导入成功")

    # 创建管理器实例
    manager = ExternalToolManager()
    print("✓ 外部工具管理器实例创建成功")

    # 检查CLI工具定义
    cli_tool = manager.get_tool("cli_execute_command")
    if cli_tool:
        print(f"  CLI工具定义找到: {cli_tool.name}")
    else:
        print("  ✗ CLI工具定义未找到")

    # 检查社交媒体工具定义
    social_tool = manager.get_tool("xiaohongshu_publish_content")
    if social_tool:
        print(f"  社交媒体工具定义找到: {social_tool.name}")
    else:
        print("  ✗ 社交媒体工具定义未找到")

    # 列出所有工具
    all_tools = manager.list_tools()
    print(f"  总工具数量: {len(all_tools)}")

except ImportError as e:
    print(f"✗ 外部工具管理器导入失败: {e}")
except Exception as e:
    print(f"✗ 外部工具管理器测试异常: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("CLI和社交媒体技能集成测试完成")