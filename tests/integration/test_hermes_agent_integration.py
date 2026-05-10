"""
测试墨麟AI集成 - 验证Hermes Native CEO决策技能可以正确加载和工作
"""

import sys
import os
import asyncio
import yaml
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_config():
    """加载hermes-agent配置"""
    config_path = Path(__file__).parent / "config" / "hermes-agent" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test_config_loading():
    """测试配置加载"""
    print("测试配置加载...")
    try:
        config = load_config()
        print(f"✓ 配置加载成功")
        print(f"  版本: {config.get('version')}")
        print(f"  描述: {config.get('description')}")

        # 检查技能配置
        if 'skills' in config:
            print(f"  找到 {len(config['skills'])} 个技能")
            if 'ceo_decision' in config['skills']:
                ceo_skill = config['skills']['ceo_decision']
                print(f"  ✓ 找到CEO决策技能: {ceo_skill.get('name')}")
                if 'implementation' in ceo_skill:
                    print(f"    implementation: {ceo_skill['implementation']}")
                else:
                    print(f"    ⚠ 无implementation字段")

        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False

def test_skill_initialization():
    """测试技能初始化"""
    print("\n测试技能初始化...")
    try:
        from hermes_fusion.skills.hermes_native.ceo_decision_skill import CeoDecisionMolinSkill

        # 创建技能实例
        skill_config = {
            'name': '测试CEO决策引擎',
            'description': '测试CEO决策系统',
            'version': '1.0.0',
            'triggers': {
                'keywords': ['决策', '分析', 'roi']
            },
            'model_preference': 'glm-5',
            'cost_level': 'high',
            'approval_level': 'high',
            'max_concurrent': 1
        }

        skill = CeoDecisionMolinSkill(skill_config)
        print(f"✓ 技能初始化成功: {skill.get_name()}")
        print(f"  描述: {skill.get_description()}")
        print(f"  版本: {skill.get_version()}")
        print(f"  工具数量: {len(skill.get_tools())}")

        return True
    except Exception as e:
        print(f"✗ 技能初始化失败: {e}")
        return False

async def test_async_methods():
    """测试异步方法"""
    print("\n测试异步方法...")
    try:
        from hermes_fusion.skills.hermes_native.ceo_decision_skill import CeoDecisionMolinSkill

        skill_config = {
            'name': '测试CEO决策引擎',
            'description': '测试CEO决策系统',
            'version': '1.0.0',
            'triggers': {
                'keywords': ['决策', '分析', 'roi']
            },
            'model_preference': 'glm-5',
            'cost_level': 'high',
            'approval_level': 'high',
            'max_concurrent': 1
        }

        skill = CeoDecisionMolinSkill(skill_config)

        # 测试can_handle
        context = {
            'text': '请帮我分析这个项目的ROI并做出决策',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z'
        }

        can_handle = await skill.can_handle(context)
        print(f"✓ can_handle测试: {can_handle}")

        # 测试execute（需要完整信息）
        execute_context = {
            'text': '预算10万元，时间线90天，目标收入20万元',
            'user_id': 'test_user',
            'platform': 'test',
            'timestamp': '2026-04-19T10:00:00Z',
            'metadata': {
                'budget': 100000,
                'timeline': '90天',
                'target_revenue': 200000
            }
        }

        result = await skill.execute(execute_context)
        print(f"✓ execute测试完成")
        print(f"  成功: {result.get('success')}")
        print(f"  决策: {result.get('decision', 'N/A')}")
        print(f"  执行时间: {result.get('execution_time', 0)}秒")

        return True
    except Exception as e:
        print(f"✗ 异步方法测试失败: {e}")
        return False

def test_sync_methods():
    """测试同步方法"""
    print("\n测试同步方法...")
    try:
        from hermes_fusion.skills.hermes_native.ceo_decision_skill import CeoDecisionMolinSkill

        skill_config = {
            'name': '测试CEO决策引擎',
            'description': '测试CEO决策系统',
            'version': '1.0.0',
            'triggers': {
                'keywords': ['决策', '分析', 'roi']
            },
            'model_preference': 'glm-5',
            'cost_level': 'high',
            'approval_level': 'high',
            'max_concurrent': 1
        }

        skill = CeoDecisionMolinSkill(skill_config)

        # 测试同步can_handle
        context = {
            'text': '请帮我分析这个项目的ROI并做出决策',
            'user_id': 'test_user',
            'platform': 'test'
        }

        can_handle = skill.sync_can_handle(context)
        print(f"✓ 同步can_handle测试: {can_handle}")

        # 测试同步execute
        execute_context = {
            'text': '预算10万元，时间线90天，目标收入20万元',
            'user_id': 'test_user',
            'platform': 'test',
            'metadata': {
                'budget': 100000,
                'timeline': '90天',
                'target_revenue': 200000
            }
        }

        result = skill.sync_execute(execute_context)
        print(f"✓ 同步execute测试完成")
        print(f"  成功: {result.get('success')}")
        print(f"  决策: {result.get('decision', 'N/A')}")

        return True
    except Exception as e:
        print(f"✗ 同步方法测试失败: {e}")
        return False

def test_hermes_skill_adapter():
    """测试Hermes技能适配器（将现有技能适配到hermes-agent）"""
    print("\n测试Hermes技能适配器...")
    try:
        from hermes_fusion.skills.hermes_skill_base import HermesSkillAdapter
        from hermes_fusion.skills.ceo_decision.skill import CeoDecisionSkill

        # 创建现有CEO技能
        existing_skill = CeoDecisionSkill()

        # 创建适配器
        adapter = HermesSkillAdapter(existing_skill)

        print(f"✓ HermesSkillAdapter创建成功: {adapter.get_name()}")
        print(f"  描述: {adapter.get_description()}")
        print(f"  版本: {adapter.get_version()}")
        print(f"  工具数量: {len(adapter.get_tools())}")

        # 测试同步方法（向后兼容）
        context = {
            'text': '请帮我分析这个项目的ROI并做出决策',
            'user_id': 'test_user',
            'platform': 'test'
        }

        can_handle = adapter.sync_can_handle(context)
        print(f"  适配器同步can_handle: {can_handle}")

        return True
    except Exception as e:
        print(f"✗ Hermes技能适配器测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("墨麟AI集成测试")
    print("=" * 60)

    tests_passed = 0
    tests_total = 0

    # 运行测试
    if test_config_loading():
        tests_passed += 1
    tests_total += 1

    if test_skill_initialization():
        tests_passed += 1
    tests_total += 1

    if await test_async_methods():
        tests_passed += 1
    tests_total += 1

    if test_sync_methods():
        tests_passed += 1
    tests_total += 1

    if test_hermes_skill_adapter():
        tests_passed += 1
    tests_total += 1

    # 打印总结
    print("\n" + "=" * 60)
    print(f"测试完成: {tests_passed}/{tests_total} 通过")
    print("=" * 60)

    if tests_passed == tests_total:
        print("✓ 所有测试通过！墨麟AI集成正常。")
    else:
        print(f"⚠ {tests_total - tests_passed} 个测试失败。")

    return tests_passed == tests_total

if __name__ == "__main__":
    # 运行异步主函数
    success = asyncio.run(main())
    sys.exit(0 if success else 1)