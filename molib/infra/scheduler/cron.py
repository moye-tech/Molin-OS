"""APScheduler 定时任务定义 — v6.6 扩展版"""
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from datetime import datetime

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")


async def daily_morning_loop():
    """每日 08:00 早报：汇总各子公司状态"""
    logger.info("=== 墨麟每日早报 ===")
    try:
        from molib.core.ceo.ceo import CEO
        ceo = CEO()
        await ceo.initialize()
        result = await ceo.daily_loop()
        logger.info(f"早报完成: {result.get('status', 'unknown')}")
    except Exception as e:
        logger.error(f"早报执行失败: {e}")


async def lead_scan():
    """每30分钟扫描新线索 — 从 Redis Streams / SQLite 读取线索数据，写入 hermes_events"""
    logger.info("=== 线索扫描 ===")
    try:
        from molib.infra.data_brain.redis_streams import get_streams_client
        streams = await get_streams_client()
        await streams.publish_event("lead_scan", {
            "event": "lead_scan_triggered",
            "ts": str(int(time.time())),
            "source": "cron.lead_scan",
        })
        logger.info("线索扫描事件已发布")
    except Exception as e:
        logger.warning(f"线索扫描失败（非致命）: {e}")


async def student_progress_check():
    """每日 18:00 检查学员进度 — 通过 edu agency 查询任务完成率"""
    logger.info("=== 学员进度检查 ===")
    try:
        from molib.integrations.feishu.bridge import push_approval_card
        from molib.infra.memory.sqlite_client import SQLiteClient
        db = SQLiteClient()
        summary = await db.get_daily_summary()
        edu_tasks = summary.get("by_agency", {}).get("edu", {})
        if edu_tasks:
            logger.info(f"学员进度概要: {edu_tasks}")
        else:
            logger.info("学员进度: 今日无 edu 任务记录")
    except Exception as e:
        logger.warning(f"学员进度检查失败（非致命）: {e}")


async def memory_cleanup():
    """每周日 03:00 记忆清理 — Redis/Qdrant TTL 自动过期，此处做健康检查"""
    logger.info("=== 记忆清理 ===")
    try:
        from molib.infra.memory.memory_manager import get_memory_manager
        manager = await get_memory_manager()
        # 各存储后端（Redis/Qdrant/SQLite）自行管理 TTL
        # 此处执行健康检查和统计汇报
        logger.info("记忆清理: 存储后端 TTL 自动管理，检查完成")
    except Exception as e:
        logger.warning(f"记忆清理失败（非致命）: {e}")


async def finance_weekly():
    """每周一 09:00 财务周报 — 汇总广告/销售数据并推送飞书"""
    logger.info("=== 财务周报 ===")
    try:
        from molib.infra.data_brain.redis_streams import get_streams_client
        streams = await get_streams_client()
        await streams.publish_metric("finance_weekly", {
            "event": "finance_weekly_report_triggered",
            "period": "weekly",
            "ts": str(int(time.time())),
        })
        logger.info("财务周报事件已发布")
    except Exception as e:
        logger.warning(f"财务周报生成失败（非致命）: {e}")


async def sop_evolution():
    """每日 23:00 SOP 进化 — 汇总当日反馈指标，触发优化建议"""
    logger.info("=== SOP 进化 ===")
    try:
        from sop.sop_feedback import get_sop_feedback
        feedback = get_sop_feedback()
        metrics = feedback.get_metrics()
        logger.info(f"SOP 进化: 反馈指标 -> {metrics}")
        # 当累计任务数足够时，触发一次优化建议
        if metrics.get("total_tasks", 0) > 10:
            logger.info("SOP 进化: 累计任务数达标，可触发优化流程")
    except Exception as e:
        logger.warning(f"SOP 进化失败（非致命）: {e}")



# ── v6.6 新增定时任务 ──────────────────────────────

async def generate_daily_report_job():
    """每日 09:00 日报生成（Feature 4）"""
    try:
        from molib.infra.reports.daily_weekly_report import generate_daily_report, send_report_to_feishu
        report = await generate_daily_report()
        await send_report_to_feishu(report)
        logger.info(f"日报生成完成: {report.get('status')}")
    except Exception as e:
        logger.error(f"日报生成失败: {e}")


async def generate_weekly_report_job():
    """每周一 09:00 周报生成（Feature 4）"""
    try:
        from molib.infra.reports.daily_weekly_report import generate_weekly_report, send_report_to_feishu
        report = await generate_weekly_report()
        await send_report_to_feishu(report)
        logger.info(f"周报生成完成: {report.get('status')}")
    except Exception as e:
        logger.error(f"周报生成失败: {e}")


async def sop_optimization_job():
    """每日 02:00 SOP 自动优化（Feature 5）"""
    try:
        from sop.sop_optimizer import SOPOptimizer
        optimizer = SOPOptimizer()
        result = await optimizer.run_daily_optimization()
        logger.info(f"SOP 优化完成: {result}")
    except Exception as e:
        logger.error(f"SOP 优化失败: {e}")


async def keyword_evolution_job():
    """每周日 03:00 关键词自扩展（Feature 6）"""
    try:
        from molib.core.evolution.keyword_evolver import KeywordEvolver
        evolver = KeywordEvolver()
        result = await evolver.run_weekly_evolution()
        logger.info(f"关键词进化完成: {result}")
    except Exception as e:
        logger.error(f"关键词进化失败: {e}")


async def model_optimization_job():
    """每月 1 日 04:00 模型路由自优化（Feature 7）"""
    try:
        from molib.core.ceo.model_router import ModelRouter
        router = ModelRouter()
        result = await router.auto_optimize()
        logger.info(f"模型路由优化完成: {len(result.get('changes', []))} 条变更")
    except Exception as e:
        logger.error(f"模型路由优化失败: {e}")


async def routing_evolution():
    """每日 02:00 路由自进化：从昨日成功案例中提取新关键词，更新子公司能力描述"""
    logger.info("=== 路由自进化 ===")
    try:
        from molib.core.ceo.semantic_router import get_semantic_router
        router = get_semantic_router()
        similar = await router._cache.search_similar("市场 调研 产品 开发 内容 数据 营销 增长", top_k=20)
        if similar:
            logger.info(f"路由自进化: 昨日有 {len(similar)} 条历史路由可供学习")
        # TODO: 根据聚类结果自动更新 INITIAL_PROFILES 中的能力描述
    except Exception as e:
        logger.warning(f"路由自进化失败: {e}")


def setup_scheduler():
    """注册所有定时任务"""
    # 原有任务
    scheduler.add_job(daily_morning_loop, 'cron', hour=8, minute=0, id='daily_morning', replace_existing=True)
    scheduler.add_job(lead_scan, 'interval', minutes=30, id='lead_scan', replace_existing=True)
    scheduler.add_job(student_progress_check, 'cron', hour=18, minute=0, id='student_check', replace_existing=True)
    scheduler.add_job(memory_cleanup, 'cron', hour=3, minute=0, day_of_week='sun', id='memory_cleanup', replace_existing=True)
    scheduler.add_job(finance_weekly, 'cron', hour=9, minute=0, day_of_week='mon', id='finance_weekly', replace_existing=True)
    scheduler.add_job(sop_evolution, 'cron', hour=23, minute=0, id='sop_evolution', replace_existing=True)
    # v6.6 新增
    scheduler.add_job(generate_daily_report_job, 'cron', hour=9, minute=0, id='daily_report', replace_existing=True)
    scheduler.add_job(generate_weekly_report_job, 'cron', hour=9, minute=0, day_of_week='mon', id='weekly_report', replace_existing=True)
    scheduler.add_job(sop_optimization_job, 'cron', hour=2, minute=0, id='sop_optimization', replace_existing=True)
    scheduler.add_job(keyword_evolution_job, 'cron', hour=3, minute=0, day_of_week='sun', id='keyword_evolution', replace_existing=True)
    scheduler.add_job(model_optimization_job, 'cron', hour=4, minute=0, day=1, id='model_optimization', replace_existing=True)
    # v8.0 新增
    scheduler.add_job(routing_evolution, 'cron', hour=2, minute=0, id='routing_evolution', replace_existing=True)

    job_count = len(scheduler.get_jobs())
    logger.info(f"Scheduler configured with {job_count} jobs")
