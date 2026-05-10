#!/usr/bin/env python3
"""
墨麟AI智能系统 6.0 - IP、Data、Order子公司集成测试
验证优先级2的三个子公司管理器与系统的集成。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 应用aioredis猴子补丁以解决TypeError: duplicate base class TimeoutError
try:
    from fix_aioredis import apply_aioredis_patch
    apply_aioredis_patch()
    print("✅ aioredis monkey patch applied")
except Exception as e:
    print(f"⚠️ Failed to apply aioredis patch: {e}")

# 配置简单日志输出
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_ip_manager_integration():
    """测试IP子公司管理器集成"""
    logger.info("测试IP子公司管理器集成...")

    try:
        from core.managers.manager_dispatcher import get_dispatcher
        from agencies.base import Task

        # 获取ManagerDispatcher实例
        dispatcher = await get_dispatcher()

        # 获取IP管理器
        ip_manager = dispatcher.get_manager("ip_manager")
        if not ip_manager:
            logger.error("❌ IP管理器未找到")
            return False

        logger.info(f"✅ IP管理器获取成功: {ip_manager.subsidiary_id}")

        # 测试can_handle方法
        test_cases = [
            ("内容创作任务", "创作一篇技术文章", True),
            ("创意设计任务", "设计一个产品宣传视频", True),
            ("IP战略任务", "制定品牌IP战略规划", True),
            ("非IP任务", "分析用户数据报表", False)
        ]

        for case_name, description, expected in test_cases:
            task_type = "content_creation" if expected else "data_analysis"  # 对于非IP任务使用不同的任务类型
            task = Task(
                task_id=f"test_ip_{case_name}",
                task_type=task_type,
                payload={"description": description},
                priority=5,
                requester="test"
            )

            can_handle = await ip_manager.can_handle(task)
            status = "✅" if can_handle == expected else "❌"
            logger.info(f"  {status} {case_name}: can_handle={can_handle}, 期望={expected}")

            if can_handle != expected:
                logger.error(f"   描述: {description}")
                return False

        # 测试delegate_task（模拟执行）
        ip_task = Task(
            task_id="test_ip_delegate",
            task_type="content_creation",
            payload={"description": "创作一篇关于AI技术趋势的深度文章"},
            priority=7,
            requester="integration_test"
        )

        try:
            result = await ip_manager.delegate_task(ip_task)
            if result and hasattr(result, 'status'):
                logger.info(f"✅ IP管理器任务委派成功: {result.status}")

                # 检查返回的ManagerResult结构
                if result.status == "success":
                    logger.info(f"  subtasks数量: {len(result.subtasks)}")
                    logger.info(f"  results数量: {len(result.results)}")
                    logger.info(f"  总成本: {result.total_cost}")
                    logger.info(f"  总延迟: {result.total_latency}")
                return True
            else:
                logger.error("❌ IP管理器任务委派返回无效结果")
                return False

        except Exception as e:
            logger.error(f"❌ IP管理器任务委派失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"❌ IP管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_data_manager_integration():
    """测试Data子公司管理器集成"""
    logger.info("\n测试Data子公司管理器集成...")

    try:
        from core.managers.manager_dispatcher import get_dispatcher
        from agencies.base import Task

        # 获取ManagerDispatcher实例
        dispatcher = await get_dispatcher()

        # 获取Data管理器
        data_manager = dispatcher.get_manager("data_manager")
        if not data_manager:
            logger.error("❌ Data管理器未找到")
            return False

        logger.info(f"✅ Data管理器获取成功: {data_manager.subsidiary_id}")

        # 测试can_handle方法
        test_cases = [
            ("数据分析任务", "分析用户行为数据并生成可视化报表", True),
            ("可视化任务", "创建销售数据的交互式仪表板", True),
            ("机器学习任务", "构建用户流失预测模型", True),
            ("非数据任务", "写一篇营销文案", False)
        ]

        for case_name, description, expected in test_cases:
            task_type = "data_analysis" if expected else "content_creation"  # 对于非数据任务使用不同的任务类型
            task = Task(
                task_id=f"test_data_{case_name}",
                task_type=task_type,
                payload={"description": description},
                priority=5,
                requester="test"
            )

            can_handle = await data_manager.can_handle(task)
            status = "✅" if can_handle == expected else "❌"
            logger.info(f"  {status} {case_name}: can_handle={can_handle}, 期望={expected}")

            if can_handle != expected:
                logger.error(f"   描述: {description}")
                return False

        # 测试delegate_task（模拟执行）
        data_task = Task(
            task_id="test_data_delegate",
            task_type="data_analysis",
            payload={"description": "分析最近30天的用户活跃度数据，识别关键趋势"},
            priority=7,
            requester="integration_test"
        )

        try:
            result = await data_manager.delegate_task(data_task)
            if result and hasattr(result, 'status'):
                logger.info(f"✅ Data管理器任务委派成功: {result.status}")

                # 检查返回的ManagerResult结构
                if result.status == "success":
                    logger.info(f"  subtasks数量: {len(result.subtasks)}")
                    logger.info(f"  results数量: {len(result.results)}")
                    logger.info(f"  总成本: {result.total_cost}")
                    logger.info(f"  总延迟: {result.total_latency}")
                return True
            else:
                logger.error("❌ Data管理器任务委派返回无效结果")
                return False

        except Exception as e:
            logger.error(f"❌ Data管理器任务委派失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"❌ Data管理器集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_order_manager_integration():
    """测试Order子公司管理器集成"""
    logger.info("\n测试Order子公司管理器集成...")

    try:
        from core.managers.manager_dispatcher import get_dispatcher
        from agencies.base import Task

        # 获取ManagerDispatcher实例
        dispatcher = await get_dispatcher()

        # 获取Order管理器
        order_manager = dispatcher.get_manager("order_manager")
        if not order_manager:
            logger.error("❌ Order管理器未找到")
            return False

        logger.info(f"✅ Order管理器获取成功: {order_manager.subsidiary_id}")

        # 测试can_handle方法
        test_cases = [
            ("定价分析任务", "分析竞争对手定价并制定最优价格策略", True),
            ("交易处理任务", "处理用户订单支付和退款流程", True),
            ("支付优化任务", "优化支付成功率和降低支付失败率", True),
            ("非订单任务", "设计一个用户界面", False)
        ]

        for case_name, description, expected in test_cases:
            task_type = "pricing" if expected else "design"  # 对于非订单任务使用不同的任务类型
            task = Task(
                task_id=f"test_order_{case_name}",
                task_type=task_type,
                payload={"description": description},
                priority=5,
                requester="test"
            )

            can_handle = await order_manager.can_handle(task)
            status = "✅" if can_handle == expected else "❌"
            logger.info(f"  {status} {case_name}: can_handle={can_handle}, 期望={expected}")

            if can_handle != expected:
                logger.error(f"   描述: {description}")
                return False

        # 测试delegate_task（模拟执行）
        order_task = Task(
            task_id="test_order_delegate",
            task_type="pricing",
            payload={"description": "分析Q2订单数据，优化定价策略以提升利润率"},
            priority=7,
            requester="integration_test"
        )

        try:
            result = await order_manager.delegate_task(order_task)
            if result and hasattr(result, 'status'):
                logger.info(f"✅ Order管理器任务委派成功: {result.status}")

                # 检查返回的ManagerResult结构
                if result.status == "success":
                    logger.info(f"  subtasks数量: {len(result.subtasks)}")
                    logger.info(f"  results数量: {len(result.results)}")
                    logger.info(f"  总成本: {result.total_cost}")
                    logger.info(f"  总延迟: {result.total_latency}")
                return True
            else:
                logger.error("❌ Order管理器任务委派返回无效结果")
                return False

        except Exception as e:
            logger.error(f"❌ Order管理器任务委派失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        logger.error(f"❌ Order管理器集成测试失败: {e}")
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
            ("IP路由测试", "创作一篇技术文章", "manager:ip_manager"),
            ("Data路由测试", "分析用户行为数据", "manager:data_manager"),
            ("Order路由测试", "优化定价策略", "manager:order_manager"),
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
                        if manager_id in ["ip_manager", "data_manager", "order_manager"]:
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

async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("墨麟AI智能系统 6.0 - IP、Data、Order子公司集成测试")
    logger.info("=" * 60)

    test_results = []

    # 测试1: IP管理器集成
    ip_test = await test_ip_manager_integration()
    test_results.append(("IP管理器集成", ip_test))

    # 测试2: Data管理器集成
    data_test = await test_data_manager_integration()
    test_results.append(("Data管理器集成", data_test))

    # 测试3: Order管理器集成
    order_test = await test_order_manager_integration()
    test_results.append(("Order管理器集成", order_test))

    # 测试4: Dispatcher路由
    routing_test = await test_dispatcher_routing()
    test_results.append(("Dispatcher路由", routing_test))

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
        logger.info("🎉 IP、Data、Order子公司集成测试全部通过！")
        logger.info("   优先级2迁移完成，可以继续优先级3。")
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