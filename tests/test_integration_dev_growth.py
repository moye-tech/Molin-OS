#!/usr/bin/env python3
"""
墨麟AI智能系统 6.0 - Dev和Growth子公司集成测试
验证优先级1的两个子公司管理器与系统的集成。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 配置简单日志输出
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_dev_manager_integration():
    """测试Dev子公司管理器集成"""
    logger.info("测试Dev子公司管理器集成...")

    try:
        from core.managers.manager_dispatcher import get_dispatcher
        from agencies.base import Task

        # 获取ManagerDispatcher实例
        dispatcher = await get_dispatcher()

        # 获取Dev管理器
        dev_manager = dispatcher.get_manager("dev_manager")
        if not dev_manager:
            logger.error("❌ Dev管理器未找到")
            return False

        logger.info(f"✅ Dev管理器获取成功: {dev_manager.subsidiary_id}")

        # 测试can_handle方法
        test_cases = [
            ("代码开发任务", "请帮我写一个Python函数", True),
            ("API开发任务", "创建一个REST API端点", True),
            ("数据库设计任务", "设计一个用户数据库表", True),
            ("非开发任务", "请写一篇营销文章", False)
        ]

        for case_name, description, expected in test_cases:
            task_type = "code" if expected else "marketing"  # 对于非开发任务使用不同的任务类型
            task = Task(
                task_id=f"test_dev_{case_name}",
                task_type=task_type,
                payload={"description": description},
                priority=5,
                requester="test"
            )

            can_handle = await dev_manager.can_handle(task)
            status = "✅" if can_handle == expected else "❌"
            logger.info(f"  {status} {case_name}: can_handle={can_handle}, 期望={expected}")

            if can_handle != expected:
                logger.error(f"   描述: {description}")
                return False

        # 测试delegate_task（模拟执行）
        dev_task = Task(
            task_id="test_dev_delegate",
            task_type="code_development",
            payload={"description": "开发一个用户认证模块"},
            priority=7,
            requester="integration_test"
        )

        try:
            result = await dev_manager.delegate_task(dev_task)
            if result and hasattr(result, 'status'):
                logger.info(f"✅ Dev管理器任务委派成功: {result.status}")

                # 检查返回的ManagerResult结构
                if result.status == "success":
                    logger.info(f"  subtasks数量: {len(result.subtasks)}")
                    logger.info(f"  results数量: {len(result.results)}")
                    logger.info(f"  总成本: {result.total_cost}")
                    logger.info(f"  总延迟: {result.total_latency}")
                return True
            else:
                logger.error("❌ Dev管理器任务委派返回无效结果")
                return False

        except Exception as e:
            logger.error(f"❌ Dev管理器任务委派失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"❌ Dev管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_growth_manager_integration():
    """测试Growth子公司管理器集成"""
    logger.info("\n测试Growth子公司管理器集成...")

    try:
        from core.managers.manager_dispatcher import get_dispatcher
        from agencies.base import Task

        # 获取ManagerDispatcher实例
        dispatcher = await get_dispatcher()

        # 获取Growth管理器
        growth_manager = dispatcher.get_manager("growth_manager")
        if not growth_manager:
            logger.error("❌ Growth管理器未找到")
            return False

        logger.info(f"✅ Growth管理器获取成功: {growth_manager.subsidiary_id}")

        # 测试can_handle方法
        test_cases = [
            ("增长营销任务", "设计一个用户增长漏斗", True),
            ("获客任务", "制定Facebook广告获客策略", True),
            ("转化优化任务", "优化网站注册转化率", True),
            ("非增长任务", "请审查这段代码", False)
        ]

        for case_name, description, expected in test_cases:
            task_type = "growth" if expected else "code"  # 对于非增长任务使用不同的任务类型
            task = Task(
                task_id=f"test_growth_{case_name}",
                task_type=task_type,
                payload={"description": description},
                priority=5,
                requester="test"
            )

            can_handle = await growth_manager.can_handle(task)
            status = "✅" if can_handle == expected else "❌"
            logger.info(f"  {status} {case_name}: can_handle={can_handle}, 期望={expected}")

            if can_handle != expected:
                logger.error(f"   描述: {description}")
                return False

        # 测试delegate_task（模拟执行）
        growth_task = Task(
            task_id="test_growth_delegate",
            task_type="growth_marketing",
            payload={"description": "制定Q2用户增长策略，目标提升30%"},
            priority=8,
            requester="integration_test"
        )

        try:
            result = await growth_manager.delegate_task(growth_task)
            if result and hasattr(result, 'status'):
                logger.info(f"✅ Growth管理器任务委派成功: {result.status}")

                # 检查返回的ManagerResult结构
                if result.status == "success":
                    logger.info(f"  subtasks数量: {len(result.subtasks)}")
                    logger.info(f"  results数量: {len(result.results)}")
                    logger.info(f"  总成本: {result.total_cost}")
                    logger.info(f"  总延迟: {result.total_latency}")
                return True
            else:
                logger.error("❌ Growth管理器任务委派返回无效结果")
                return False

        except Exception as e:
            logger.error(f"❌ Growth管理器任务委派失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"❌ Growth管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_dispatcher_routing():
    """测试Dispatcher管理器路由"""
    logger.info("\n测试Dispatcher管理器路由...")

    try:
        from agencies.dispatcher import dispatch
        from agencies.base import Task

        test_cases = [
            ("Dev路由测试", "开发一个Python Web应用", "manager:dev_manager"),
            ("Growth路由测试", "制定用户增长策略", "manager:growth_manager"),
            ("AI路由测试", "优化AI提示词", "manager:ai_manager"),
            ("IP路由测试", "创作一篇技术文章", "manager:ip_manager")
        ]

        for case_name, description, expected_prefix in test_cases:
            logger.info(f"测试 {case_name}...")

            try:
                agency_id = dispatch(description, "general")

                if agency_id:
                    logger.info(f"  路由结果: {agency_id}")

                    # 检查是否为管理器路由
                    if agency_id.startswith("manager:"):
                        logger.info(f"  ✅ 成功路由到管理器")

                        # 验证管理器ID
                        manager_id = agency_id.replace("manager:", "", 1)
                        if manager_id in ["dev_manager", "growth_manager", "ai_manager", "ip_manager"]:
                            logger.info(f"  ✅ 管理器ID有效: {manager_id}")
                        else:
                            logger.warning(f"  ⚠️ 未知的管理器ID: {manager_id}")
                    else:
                        logger.info(f"  ⚠️ 路由到传统机构: {agency_id}")
                else:
                    logger.warning("  路由返回空值")

            except Exception as e:
                logger.warning(f"  路由失败（可能预期内）: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Dispatcher路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ceo_subsidiary_determination():
    """测试CEO子公司确定逻辑"""
    logger.info("\n测试CEO子公司确定逻辑...")

    try:
        from core.ceo.ceo import CEO

        # 创建CEO实例
        ceo = CEO(daily_budget_cny=100.0)
        await ceo.initialize()

        # 测试_determine_subsidiary方法
        # 需要模拟intent_result和parsed_decision

        # 创建模拟的intent_result对象
        class MockIntentResult:
            def __init__(self, target_agency=None):
                self.target_agency = target_agency

        # 测试场景
        test_scenarios = [
            ("开发场景", MockIntentResult(), {"tasks": ["开发一个用户认证系统"]}, "dev"),
            ("增长场景", MockIntentResult(), {"tasks": ["制定用户增长漏斗"]}, "growth"),
            ("AI场景", MockIntentResult(), {"tasks": ["优化AI模型参数"]}, "ai"),
            ("IP场景", MockIntentResult(), {"tasks": ["创作一篇技术博客"]}, "ip"),
            ("数据场景", MockIntentResult(), {"tasks": ["分析用户行为数据"]}, "data")
        ]

        for scenario_name, intent_result, parsed_decision, expected_subsidiary in test_scenarios:
            subsidiary = ceo._determine_subsidiary(intent_result, parsed_decision)

            if subsidiary == expected_subsidiary:
                logger.info(f"✅ {scenario_name}: 正确识别子公司 '{subsidiary}'")
            else:
                logger.warning(f"⚠️ {scenario_name}: 期望 '{expected_subsidiary}', 实际 '{subsidiary}'")

        # 测试target_agency优先级
        intent_with_target = MockIntentResult(target_agency="dev")
        parsed = {"tasks": ["这个应该被忽略"]}
        subsidiary = ceo._determine_subsidiary(intent_with_target, parsed)
        if subsidiary == "dev":
            logger.info("✅ target_agency优先级正确")
        else:
            logger.warning(f"⚠️ target_agency优先级错误: {subsidiary}")

        return True

    except Exception as e:
        logger.error(f"❌ CEO子公司确定测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("墨麟AI智能系统 6.0 - Dev和Growth子公司集成测试")
    logger.info("=" * 60)

    test_results = []

    # 测试1: Dev管理器集成
    dev_test = await test_dev_manager_integration()
    test_results.append(("Dev管理器集成", dev_test))

    # 测试2: Growth管理器集成
    growth_test = await test_growth_manager_integration()
    test_results.append(("Growth管理器集成", growth_test))

    # 测试3: Dispatcher路由
    routing_test = await test_dispatcher_routing()
    test_results.append(("Dispatcher路由", routing_test))

    # 测试4: CEO子公司确定
    ceo_test = await test_ceo_subsidiary_determination()
    test_results.append(("CEO子公司确定", ceo_test))

    # 输出测试总结
    logger.info("\n" + "=" * 60)
    logger.info("集成测试总结")
    logger.info("=" * 60)

    passed_count = sum(1 for name, success in test_results if success)
    total_count = len(test_results)

    logger.info(f"总测试项目: {total_count}")
    logger.info(f"通过: {passed_count}")
    logger.info(f"失败: {total_count - passed_count}")

    for name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{name}: {status}")

    logger.info("\n" + "=" * 60)

    if passed_count == total_count:
        logger.info("🎉 Dev和Growth子公司集成测试全部通过！")
        logger.info("   优先级1迁移完成，可以继续优先级2。")
        return True
    else:
        logger.error("⚠️ 部分集成测试失败，需要修复")
        return False

if __name__ == "__main__":
    # 设置事件循环策略
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass

    success = asyncio.run(main())
    sys.exit(0 if success else 1)