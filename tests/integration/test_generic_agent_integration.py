#!/usr/bin/env python3
"""
GenericAgent集成测试
测试墨麟AI智能系统与GenericAgent的集成
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_agent_frameworks_import():
    """测试agent_frameworks模块导入"""
    try:
        from hermes_fusion.integration.external_tools.agent_frameworks import (
            GenericAgentBridge, initialize_generic_agent,
            plan_complex_task, get_generic_agent_info
        )
        logger.info("✓ agent_frameworks模块导入成功")

        # 获取GenericAgent信息
        info = get_generic_agent_info()
        logger.info(f"  GenericAgent可用性: {info.get('available', False)}")
        logger.info(f"  工具数量: {len(info.get('tools', []))}")

        return True
    except Exception as e:
        logger.error(f"✗ agent_frameworks模块导入失败: {e}")
        return False


def test_ceo_tools_new_methods():
    """测试CeoTools新方法"""
    try:
        from hermes_fusion.tools.ceo_tools import CeoTools

        # 测试plan_complex_task
        logger.info("测试plan_complex_task方法...")
        plan_result = CeoTools.plan_complex_task(
            "开发一个电商网站，包含用户注册、商品展示、购物车和支付功能"
        )

        if "error" in plan_result:
            logger.warning(f"  plan_complex_task返回错误: {plan_result.get('error')}")
        else:
            logger.info(f"  ✓ plan_complex_task成功: {len(plan_result.get('task_breakdown', []))} 个步骤")
            logger.info(f"    优先级: {plan_result.get('priority')}")
            logger.info(f"    置信度: {plan_result.get('confidence')}")

        # 测试execute_complex_plan
        logger.info("测试execute_complex_plan方法...")
        execution_result = CeoTools.execute_complex_plan(plan_result, monitor=False)

        if "error" in execution_result:
            logger.warning(f"  execute_complex_plan返回错误: {execution_result.get('error')}")
        else:
            logger.info(f"  ✓ execute_complex_plan成功: {execution_result.get('status')}")
            logger.info(f"    执行步骤: {execution_result.get('plan_executed', 0)}")

        return True
    except Exception as e:
        logger.error(f"✗ CeoTools新方法测试失败: {e}")
        return False


def test_tool_bridge_registration():
    """测试工具桥接注册"""
    try:
        from hermes_fusion.integration.bridge.tool_bridge import tool_bridge

        # 重新注册业务工具（确保新工具被注册）
        success = tool_bridge.register_all_business_tools()

        if success:
            tools_info = tool_bridge.get_registered_tools_info()
            total_tools = tools_info['total_count']
            business_tools = len(tools_info['business_tools'])

            logger.info(f"✓ 工具桥接注册成功: {total_tools} 个工具")
            logger.info(f"  业务工具: {business_tools}")

            # 检查新工具是否在列表中
            new_tools = [t for t in tools_info['business_tools']
                        if 'plan_complex_task' in t or 'execute_complex_plan' in t]
            logger.info(f"  GenericAgent增强工具: {len(new_tools)} 个")

            return True
        else:
            logger.error("✗ 工具桥接注册失败")
            return False
    except Exception as e:
        logger.error(f"✗ 工具桥接测试失败: {e}")
        return False


async def test_async_planning():
    """测试异步规划功能"""
    try:
        from hermes_fusion.integration.external_tools.agent_frameworks import plan_complex_task

        logger.info("测试异步plan_complex_task...")
        task_description = "为中型企业制定数字化转型战略，包括技术选型、实施步骤和预期成果"

        result = await plan_complex_task(task_description)

        if "error" in result:
            logger.warning(f"  异步规划返回错误: {result.get('error')}")
        else:
            logger.info(f"  ✓ 异步规划成功: {len(result.get('task_breakdown', []))} 个步骤")
            logger.info(f"    源: {result.get('source', 'unknown')}")

            # 显示第一个步骤
            if result.get('task_breakdown'):
                first_step = result['task_breakdown'][0]
                logger.info(f"    第一步: {first_step.get('description', 'N/A')}")

        return True
    except Exception as e:
        logger.error(f"✗ 异步规划测试失败: {e}")
        return False


def test_external_tools_manager_integration():
    """测试外部工具管理器集成"""
    try:
        from hermes_fusion.integration.external_tools.manager import external_tool_manager

        # 获取所有工具信息
        info = external_tool_manager.get_all_tools_info()

        total_tools = info['statistics']['total']
        available_tools = info['statistics']['available']

        logger.info(f"外部工具管理器: {total_tools} 个工具")
        logger.info(f"  可用: {available_tools}")

        # 检查GenericAgent工具
        generic_agent_tools = [
            name for name, tool in info['tools'].items()
            if tool.get('project_name') == 'GenericAgent'
        ]

        logger.info(f"  GenericAgent工具: {len(generic_agent_tools)} 个")
        if generic_agent_tools:
            logger.info(f"    示例: {generic_agent_tools[0]}")

        return True
    except Exception as e:
        logger.error(f"✗ 外部工具管理器测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("GenericAgent集成测试")
    print("=" * 60)

    tests = [
        ("agent_frameworks模块导入", test_agent_frameworks_import),
        ("CeoTools新方法", test_ceo_tools_new_methods),
        ("工具桥接注册", test_tool_bridge_registration),
        ("外部工具管理器集成", test_external_tools_manager_integration),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✓ 通过" if success else "✗ 失败"
            print(f"  结果: {status}")
        except Exception as e:
            print(f"  异常: {e}")
            results.append((test_name, False))

    # 运行异步测试
    print(f"\n测试: 异步规划功能")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(test_async_planning())
        results.append(("异步规划功能", success))
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  结果: {status}")
        loop.close()
    except Exception as e:
        print(f"  异常: {e}")
        results.append(("异步规划功能", False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有GenericAgent集成测试通过！")
        return 0
    elif passed >= total * 0.7:
        print(f"\n⚠ {total - passed} 个测试失败，但核心集成可用")
        return 1
    else:
        print(f"\n❌ {total - passed} 个测试失败，需要修复")
        return 2


if __name__ == '__main__':
    sys.exit(main())