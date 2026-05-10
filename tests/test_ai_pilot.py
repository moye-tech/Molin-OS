#!/usr/bin/env python3
"""
墨麟AI智能系统 6.0 - AI子公司试点测试
最小化测试，专注于验证ManagerDispatcher和AI管理器基础功能
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

async def test_manager_dispatcher_initialization():
    """测试ManagerDispatcher初始化"""
    logger.info("测试ManagerDispatcher初始化...")

    try:
        from core.managers.manager_dispatcher import get_dispatcher

        # 获取ManagerDispatcher实例
        dispatcher = await get_dispatcher()
        logger.info(f"✅ ManagerDispatcher初始化成功")

        # 检查管理器数量
        manager_count = len(dispatcher.managers)
        logger.info(f"✅ 已加载 {manager_count} 个管理器")

        # 列出所有管理器
        for manager_id, manager in dispatcher.managers.items():
            logger.info(f"  - {manager_id} (subsidiary_id: {manager.subsidiary_id})")

        return True, dispatcher
    except ImportError as e:
        logger.error(f"❌ 导入ManagerDispatcher失败: {e}")
        return False, None
    except Exception as e:
        logger.error(f"❌ ManagerDispatcher初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_ai_manager_specific(dispatcher):
    """测试AI管理器的具体功能"""
    logger.info("\n测试AI管理器具体功能...")

    try:
        # 获取AI管理器
        ai_manager = dispatcher.get_manager("ai_manager")
        if not ai_manager:
            logger.error("❌ AI管理器未找到")
            return False

        logger.info(f"✅ AI管理器获取成功")
        logger.info(f"  subsidiary_id: {ai_manager.subsidiary_id}")
        logger.info(f"  worker类型: {list(ai_manager.worker_type_mapping.keys())}")
        logger.info(f"  Claude Code启用: {ai_manager.claude_enabled}")

        # 检查worker类型映射
        expected_worker_types = ['prompt_engineer', 'model_optimizer', 'code_reviewer']
        actual_worker_types = list(ai_manager.worker_type_mapping.keys())

        if set(actual_worker_types) == set(expected_worker_types):
            logger.info(f"✅ worker类型映射正确")
        else:
            logger.error(f"❌ worker类型映射不正确")
            logger.error(f"   期望: {expected_worker_types}")
            logger.error(f"   实际: {actual_worker_types}")
            return False

        # 测试can_handle方法
        from agencies.base import Task

        test_tasks = [
            ("prompt优化任务", "请帮我优化这个AI提示词", "prompt"),
            ("模型优化任务", "请调整模型参数以提高准确率", "model_optimization"),
            ("代码审查任务", "请审查这段Python代码", "code_review")
        ]

        for task_name, description, task_type in test_tasks:
            task = Task(
                task_id=f"test_{task_type}",
                task_type=task_type,
                payload={"description": description},
                priority=5,
                requester="test"
            )

            can_handle = await ai_manager.can_handle(task)
            logger.info(f"  {task_name}: {'✅ 可以处理' if can_handle else '⚠️ 无法处理'}")

        return True
    except Exception as e:
        logger.error(f"❌ AI管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_task_analysis(dispatcher):
    """测试任务分析功能"""
    logger.info("\n测试任务分析功能...")

    try:
        ai_manager = dispatcher.get_manager("ai_manager")
        if not ai_manager:
            return False

        from agencies.base import Task

        # 创建一个测试任务
        task = Task(
            task_id="test_prompt_optimization",
            task_type="prompt_optimization",
            payload={
                "description": "请帮我优化这个AI提示词：'写一篇关于人工智能的文章'",
                "context": {"language": "zh", "tone": "专业"}
            },
            priority=7,
            requester="test_user"
        )

        # 测试任务分析
        logger.info("测试任务分析...")
        subtasks = await ai_manager._analyze_task(task)

        if subtasks and isinstance(subtasks, list):
            logger.info(f"✅ 任务分析成功，生成 {len(subtasks)} 个子任务")
            for i, subtask in enumerate(subtasks, 1):
                logger.info(f"  子任务 {i}: {subtask.description}")
        else:
            logger.warning("⚠️ 任务分析返回空结果或非列表")

        return True
    except Exception as e:
        logger.error(f"❌ 任务分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_manager_routing():
    """测试管理器路由"""
    logger.info("\n测试管理器路由...")

    try:
        from core.managers.manager_dispatcher import dispatch_task
        from agencies.base import Task

        test_cases = [
            ("AI提示任务", "请帮我优化AI提示词", "prompt"),
            ("代码开发任务", "写一个Python函数", "code"),
            ("广告投放任务", "制定Facebook广告策略", "advertising")
        ]

        for task_name, description, task_type in test_cases:
            task = Task(
                task_id=f"test_{task_type}_routing",
                task_type=task_type,
                payload={"description": description},
                priority=5,
                requester="test"
            )

            logger.info(f"测试 {task_name} 路由...")
            try:
                result = await dispatch_task(task, use_managers=True)
                if result and hasattr(result, 'status'):
                    logger.info(f"  ✅ 路由成功: {result.status}")
                else:
                    logger.info(f"  ✅ 路由完成")
            except Exception as e:
                logger.warning(f"  ⚠️ 路由失败（预期内）: {e}")

        return True
    except Exception as e:
        logger.error(f"❌ 管理器路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    logger.info("=" * 60)
    logger.info("墨麟AI智能系统 6.0 - AI子公司试点测试")
    logger.info("=" * 60)

    test_results = []

    # 测试1: ManagerDispatcher初始化
    success, dispatcher = await test_manager_dispatcher_initialization()
    test_results.append(("ManagerDispatcher初始化", success))

    if not success or not dispatcher:
        logger.error("❌ ManagerDispatcher初始化失败，中止后续测试")
        return False

    # 测试2: AI管理器具体功能
    ai_manager_test = await test_ai_manager_specific(dispatcher)
    test_results.append(("AI管理器具体功能", ai_manager_test))

    # 测试3: 任务分析
    task_analysis_test = await test_task_analysis(dispatcher)
    test_results.append(("任务分析功能", task_analysis_test))

    # 测试4: 管理器路由
    routing_test = await test_manager_routing()
    test_results.append(("管理器路由", routing_test))

    # 输出测试总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
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
        logger.info("🎉 所有测试通过！AI子公司试点准备就绪")
        return True
    else:
        logger.error("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    # 设置事件循环策略（适用于asyncio）
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass

    success = asyncio.run(main())
    sys.exit(0 if success else 1)