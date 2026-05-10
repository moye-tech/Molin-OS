from pathlib import Path
import json
import asyncio
import time
from typing import Dict, Any, List
from loguru import logger

from molib.infra.memory.sqlite_client import SQLiteClient
from molib.core.ceo.model_router import ModelRouter
from molib.utils.alerts import send_alert
from .redis_streams import get_streams_client

PROMPT_PATH = Path(__file__).resolve().parent / 'prompts' / 'analysis.txt'


class DataBrain:
    def __init__(self):
        self.db = SQLiteClient()
        self.router = ModelRouter()
        self.system_prompt = PROMPT_PATH.read_text(encoding='utf-8') if PROMPT_PATH.exists() else ''
        self.streams_client = None
        self._streams_initialized = False

    async def _init_streams(self):
        """初始化Redis Streams客户端"""
        if not self._streams_initialized:
            try:
                import os
                if os.getenv("REDIS_STREAMS_ENABLED", "true").lower() == "true":
                    self.streams_client = await get_streams_client()
                    logger.info("Redis Streams客户端初始化完成")
                else:
                    logger.info("Redis Streams已禁用")
                self._streams_initialized = True
            except Exception as e:
                logger.error(f"Redis Streams初始化失败: {e}")
                self.streams_client = None

    async def publish_decision_event(self, decision_data: Dict[str, Any]):
        """发布决策事件到Redis Stream"""
        await self._init_streams()
        if self.streams_client:
            try:
                await self.streams_client.publish_decision(decision_data)
                logger.debug(f"发布决策事件: {decision_data.get('action', 'unknown')}")
            except Exception as e:
                logger.warning(f"发布决策事件失败: {e}")

    async def publish_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """发布指标到Redis Stream"""
        await self._init_streams()
        if self.streams_client:
            try:
                await self.streams_client.publish_metric(metric_name, value, tags)
            except Exception as e:
                logger.warning(f"发布指标失败: {e}")

    async def process_realtime_events(self) -> List[Dict[str, Any]]:
        """处理实时事件流"""
        await self._init_streams()
        if not self.streams_client:
            return []

        try:
            # 处理决策流
            decisions = await self.streams_client.process_decision_stream()

            # 处理其他事件流
            # 这里可以添加更多事件处理逻辑

            return decisions
        except Exception as e:
            logger.error(f"处理实时事件时出错: {e}")
            return []

    async def analyze_daily(self) -> dict:
        data = await self.db.get_daily_summary()
        full_input = f"今日业务数据：{json.dumps(data, ensure_ascii=False)}"

        # 发布每日指标到Redis Stream
        await self.publish_metric("daily_leads", data.get("leads", 0), {"type": "daily_summary"})
        await self.publish_metric("daily_revenue", data.get("total_revenue", 0), {"type": "daily_summary"})
        await self.publish_metric("daily_api_cost", data.get("api_cost", 0), {"type": "daily_summary"})

        result = await self.router.call_async(
            prompt=full_input,
            system=self.system_prompt,
            task_type='data_analysis',
            team='data',
        )

        try:
            text = result['text']
            s, e = text.find('{'), text.rfind('}') + 1
            analysis = json.loads(text[s:e])
            alerts = analysis.get('alerts') or []
            if alerts:
                await send_alert('Data Brain 告警', '\n'.join(alerts), 'warning')

            # 发布分析结果到Redis Stream
            analysis_event = {
                "analysis_type": "daily",
                "data": data,
                "insights": analysis.get("insights", []),
                "alerts": alerts,
                "timestamp": time.time()
            }
            await self.publish_metric("analysis_completed", 1, {"type": "daily_analysis"})

            return analysis
        except Exception as exc:
            logger.error(f"DataBrain analyze failed: {exc}")

            # 发布错误事件到Redis Stream
            error_event = {
                "error": str(exc),
                "data": data,
                "timestamp": time.time()
            }
            if self.streams_client:
                try:
                    await self.streams_client.publish_event("analysis_error", error_event)
                except Exception as e:
                    logger.warning(f"发布错误事件失败: {e}")

            return {'error': str(exc)}

    async def get_stream_stats(self) -> Dict[str, Any]:
        """获取流统计信息"""
        await self._init_streams()
        if self.streams_client:
            try:
                return await self.streams_client.get_stream_stats()
            except Exception as e:
                logger.error(f"获取流统计信息失败: {e}")
                return {"error": str(e)}
        return {"status": "redis_streams_disabled"}

    async def realtime_analysis_loop(self, interval_seconds: int = 60):
        """实时分析循环（后台任务）"""
        logger.info("启动实时分析循环")
        while True:
            try:
                # 处理实时事件
                events = await self.process_realtime_events()

                if events:
                    logger.info(f"处理了 {len(events)} 个实时事件")

                    # 基于事件进行实时分析
                    for event in events:
                        if event.get("type") == "decision":
                            await self._analyze_decision_realtime(event)

                # 发布系统健康指标
                await self.publish_metric("data_brain_health", 1, {"component": "analytics"})

            except Exception as e:
                logger.error(f"实时分析循环出错: {e}")
                await self.publish_metric("data_brain_error", 1, {"error": str(e)})

            await asyncio.sleep(interval_seconds)

    async def _analyze_decision_realtime(self, decision_event: Dict[str, Any]):
        """实时分析决策事件"""
        try:
            decision_data = decision_event.get("data", {})
            action = decision_data.get("action", "unknown")
            roi = decision_data.get("roi", 0)

            # 简单的实时分析逻辑
            if action == "GO" and roi > 3.0:
                # 高ROI决策，可以触发自动扩展
                logger.info(f"检测到高ROI决策: ROI={roi}")
                await self.publish_metric("high_roi_decision", 1, {"roi": roi})

            elif action == "NO_GO" and roi < 1.0:
                # 低ROI决策，需要进一步分析
                logger.info(f"检测到低ROI决策: ROI={roi}")
                await self.publish_metric("low_roi_decision", 1, {"roi": roi})

        except Exception as e:
            logger.error(f"实时分析决策事件时出错: {e}")
