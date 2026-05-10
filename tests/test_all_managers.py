#!/usr/bin/env python3
"""
墨麟AI智能系统 6.0 - 所有管理器验证测试
验证所有12个子公司的管理器是否能正确加载和初始化。
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

async def test_all_managers():
    """测试所有管理器加载和初始化"""
    logger.info("=" * 60)
    logger.info("墨麟AI智能系统 6.0 - 所有管理器验证测试")
    logger.info("=" * 60)

    try:
        from core.managers.manager_dispatcher import get_dispatcher

        # 获取ManagerDispatcher实例
        dispatcher = await get_dispatcher()
        logger.info(f"✅ ManagerDispatcher初始化成功")

        # 检查管理器数量
        manager_count = len(dispatcher.managers)
        logger.info(f"✅ 已加载 {manager_count} 个管理器")

        if manager_count != 12:
            logger.warning(f"⚠️ 预期12个管理器，实际加载 {manager_count} 个")

        # 列出所有管理器及其状态
        logger.info("\n管理器状态详情:")
        for manager_id, manager in dispatcher.managers.items():
            logger.info(f"  - {manager_id}:")
            logger.info(f"    子公司ID: {manager.subsidiary_id}")
            logger.info(f"    worker类型: {list(manager.worker_type_mapping.keys()) if hasattr(manager, 'worker_type_mapping') else 'N/A'}")
            logger.info(f"    Claude Code启用: {manager.claude_enabled}")

            # 获取指标
            try:
                metrics = manager.get_metrics()
                worker_count = metrics.get('worker_count', 0)
                logger.info(f"    worker数量: {worker_count}")
            except Exception as e:
                logger.warning(f"    获取指标失败: {e}")

        # 验证配置文件中的每个管理器是否都加载了
        import toml
        config_path = project_root / "config" / "managers.toml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = toml.load(f)

        manager_configs = config.get('managers', {})
        logger.info(f"\n配置文件中的管理器数量: {len(manager_configs)}")

        missing_managers = []
        for manager_id in manager_configs:
            if manager_id not in dispatcher.managers:
                missing_managers.append(manager_id)

        if missing_managers:
            logger.error(f"❌ 以下管理器配置了但未加载: {missing_managers}")
            return False
        else:
            logger.info("✅ 所有配置的管理器都已成功加载")

        # 测试每个管理器的基本功能
        logger.info("\n测试每个管理器的基本功能...")
        from agencies.base import Task

        test_results = []
        for manager_id, manager in dispatcher.managers.items():
            try:
                # 创建测试任务
                task = Task(
                    task_id=f"test_basic_{manager_id}",
                    task_type=manager.subsidiary_id,
                    payload={"description": f"测试{manager_id}的基本功能"},
                    priority=5,
                    requester="test"
                )

                # 测试can_handle方法
                can_handle = await manager.can_handle(task)

                # 获取触发关键词
                keywords = manager.get_trigger_keywords()

                test_results.append({
                    "manager_id": manager_id,
                    "can_handle": can_handle,
                    "keywords_count": len(keywords),
                    "status": "✅"
                })

                logger.info(f"  {manager_id}: can_handle={can_handle}, 触发关键词={len(keywords)}个")

            except Exception as e:
                logger.error(f"  {manager_id}: 测试失败 - {e}")
                test_results.append({
                    "manager_id": manager_id,
                    "error": str(e),
                    "status": "❌"
                })

        # 输出总结
        logger.info("\n" + "=" * 60)
        logger.info("所有管理器验证总结")
        logger.info("=" * 60)

        success_count = sum(1 for r in test_results if r.get("status") == "✅")
        total_count = len(test_results)

        logger.info(f"总管理器数: {total_count}")
        logger.info(f"测试通过: {success_count}")
        logger.info(f"测试失败: {total_count - success_count}")

        if success_count == total_count:
            logger.info("🎉 所有管理器验证通过！")
            return True
        else:
            logger.error("⚠️ 部分管理器验证失败")
            for result in test_results:
                if result.get("status") == "❌":
                    logger.error(f"  {result['manager_id']}: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"❌ 管理器验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    success = await test_all_managers()

    if success:
        logger.info("\n✅ 所有管理器验证完成，系统准备就绪")
        return True
    else:
        logger.error("\n❌ 管理器验证失败，需要修复")
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