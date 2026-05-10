#!/usr/bin/env python3
"""
测试CLI和社交媒体技能执行
验证技能能实际处理请求并返回结果
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_cli_skill_execution():
    """测试CLI技能执行"""
    print("测试CLI技能执行...")

    try:
        from hermes_fusion.skills.subsidiaries.cli_subsidiary import CLISubsidiarySkill

        cli_skill = CLISubsidiarySkill()

        # 测试命令执行
        context = {
            'text': '执行ls命令',
            'command': 'ls',
            'args': ['-la']
        }

        result = cli_skill.execute(context)
        print(f"CLI技能执行结果: {result.get('success')}")
        print(f"  服务类型: {result.get('service')}")
        print(f"  执行时间: {result.get('execution_time')}")

        if result.get('success'):
            print("✓ CLI技能执行测试通过")
            return True
        else:
            print(f"✗ CLI技能执行失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"✗ CLI技能执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_social_media_skill_execution():
    """测试社交媒体技能执行"""
    print("\n测试社交媒体技能执行...")

    try:
        from hermes_fusion.skills.subsidiaries.social_media_subsidiary import SocialMediaSubsidiarySkill

        social_skill = SocialMediaSubsidiarySkill()

        # 测试内容发布
        context = {
            'text': '发布小红书内容',
            'content': '测试发布内容',
            'images': []
        }

        result = social_skill.execute(context)
        print(f"社交媒体技能执行结果: {result.get('success')}")
        print(f"  服务类型: {result.get('service')}")

        if result.get('success'):
            print("✓ 社交媒体技能执行测试通过")
            return True
        else:
            print(f"✗ 社交媒体技能执行失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"✗ 社交媒体技能执行异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("CLI和社交媒体技能执行测试")
    print("=" * 70)

    cli_success = await test_cli_skill_execution()
    social_success = await test_social_media_skill_execution()

    print("\n" + "=" * 70)
    print(f"测试结果: CLI技能={'通过' if cli_success else '失败'}, "
          f"社交媒体技能={'通过' if social_success else '失败'}")

    return cli_success and social_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)