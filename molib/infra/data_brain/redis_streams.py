"""
Redis Streams 客户端 v6.6
实现数据大脑的事件流处理
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from loguru import logger
import redis.asyncio as aioredis
from redis.exceptions import ResponseError as RedisResponseError

from ..memory.memory_manager import get_memory_manager, MemoryScenario


class RedisStreamsClient:
    """Redis Streams 客户端，用于处理事件流和实时分析"""

    def __init__(self, redis_host: str = "redis", redis_port: int = 6379,
                 redis_password: str = None, stream_prefix: str = "hermes"):
        """
        初始化Redis Streams客户端

        Args:
            redis_host: Redis主机地址
            redis_port: Redis端口
            redis_password: Redis密码
            stream_prefix: 流名称前缀
        """
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_password = redis_password
        self.stream_prefix = stream_prefix
        self.redis = None
        self.memory_manager = None

        # 流名称定义
        self.STREAM_EVENTS = f"{stream_prefix}_events"  # 通用事件流
        self.STREAM_DECISIONS = f"{stream_prefix}_decisions"  # 决策事件流
        self.STREAM_ALERTS = f"{stream_prefix}_alerts"  # 告警事件流
        self.STREAM_METRICS = f"{stream_prefix}_metrics"  # 指标流

        # 消费者组名称
        self.CONSUMER_GROUP_DATA_BRAIN = "data_brain"
        self.CONSUMER_GROUP_ALERTS = "alerts"
        self.CONSUMER_GROUP_MONITORING = "monitoring"

        # 流最大长度（防止无限增长）
        self.STREAM_MAX_LEN = 10000

        logger.info(f"Redis Streams客户端初始化: {redis_host}:{redis_port}")

    async def connect(self):
        """连接到Redis服务器"""
        if self.redis is None:
            connection_kwargs = {
                "host": self.redis_host,
                "port": self.redis_port,
            }
            if self.redis_password:
                connection_kwargs["password"] = self.redis_password

            self.redis = await aioredis.from_url(
                f"redis://{self.redis_host}:{self.redis_port}",
                password=self.redis_password,
                decode_responses=True
            )

            # 创建消费者组（如果不存在）
            await self._create_consumer_groups()

            logger.info("Redis Streams连接成功")

    async def _create_consumer_groups(self):
        """创建必要的消费者组"""
        streams = [
            self.STREAM_EVENTS,
            self.STREAM_DECISIONS,
            self.STREAM_ALERTS,
            self.STREAM_METRICS
        ]

        for stream in streams:
            try:
                # 检查流是否存在
                stream_info = await self.redis.xinfo_stream(stream)
                # 流存在，检查消费者组
                groups = await self.redis.xinfo_groups(stream)
                group_names = [group['name'] for group in groups]

                # 创建缺失的消费者组
                if self.CONSUMER_GROUP_DATA_BRAIN not in group_names:
                    await self.redis.xgroup_create(
                        stream, self.CONSUMER_GROUP_DATA_BRAIN, id="0", mkstream=True
                    )
                    logger.debug(f"创建消费者组: {self.CONSUMER_GROUP_DATA_BRAIN} for {stream}")

            except RedisResponseError as e:
                # 流不存在，创建流和消费者组
                if "no such key" in str(e).lower():
                    await self.redis.xgroup_create(
                        stream, self.CONSUMER_GROUP_DATA_BRAIN, id="0", mkstream=True
                    )
                    logger.debug(f"创建流和消费者组: {stream} with {self.CONSUMER_GROUP_DATA_BRAIN}")
                else:
                    logger.warning(f"检查流 {stream} 时出错: {e}")

    async def publish_event(self, event_type: str, event_data: Dict[str, Any],
                          stream: str = None) -> str:
        """
        发布事件到Redis Stream

        Args:
            event_type: 事件类型
            event_data: 事件数据
            stream: 目标流名称（默认使用通用事件流）

        Returns:
            str: 事件ID
        """
        await self.connect()

        if stream is None:
            stream = self.STREAM_EVENTS

        event_payload = {
            "event_type": event_type,
            "timestamp": time.time(),
            "data": event_data,
            "source": "data_brain",
        }

        # 添加事件到流
        message_id = await self.redis.xadd(
            stream,
            event_payload,
            maxlen=self.STREAM_MAX_LEN,
            approximate=True
        )

        logger.debug(f"发布事件到 {stream}: {event_type} [{message_id}]")
        return message_id

    async def publish_decision(self, decision_data: Dict[str, Any]) -> str:
        """发布决策事件到决策流"""
        return await self.publish_event(
            event_type="decision",
            event_data=decision_data,
            stream=self.STREAM_DECISIONS
        )

    async def publish_alert(self, alert_type: str, alert_data: Dict[str, Any],
                          severity: str = "medium") -> str:
        """发布告警到告警流"""
        alert_data["severity"] = severity
        alert_data["alert_time"] = time.time()

        return await self.publish_event(
            event_type=alert_type,
            event_data=alert_data,
            stream=self.STREAM_ALERTS
        )

    async def publish_metric(self, metric_name: str, metric_value: float,
                           tags: Dict[str, str] = None) -> str:
        """发布指标到指标流"""
        metric_data = {
            "metric": metric_name,
            "value": metric_value,
            "tags": tags or {}
        }

        return await self.publish_event(
            event_type="metric",
            event_data=metric_data,
            stream=self.STREAM_METRICS
        )

    async def consume_events(self, consumer_group: str, consumer_name: str,
                           stream: str = None, count: int = 10,
                           block_ms: int = 5000) -> List[Dict[str, Any]]:
        """
        从流中消费事件

        Args:
            consumer_group: 消费者组名称
            consumer_name: 消费者名称
            stream: 流名称（默认使用通用事件流）
            count: 每次读取的最大消息数
            block_ms: 阻塞等待时间（毫秒）

        Returns:
            List[Dict[str, Any]]: 事件列表
        """
        await self.connect()

        if stream is None:
            stream = self.STREAM_EVENTS

        try:
            # 读取待处理消息
            messages = await self.redis.xreadgroup(
                groupname=consumer_group,
                consumername=consumer_name,
                streams={stream: ">"},  # ">" 表示只读取新消息
                count=count,
                block=block_ms
            )

            if not messages:
                return []

            events = []
            for stream_name, message_list in messages:
                for message_id, message_data in message_list:
                    event = {
                        "id": message_id,
                        "stream": stream_name,
                        "data": message_data
                    }
                    events.append(event)

                    # 确认消息已处理
                    await self.redis.xack(stream_name, consumer_group, message_id)

            return events

        except Exception as e:
            logger.error(f"消费事件时出错: {e}")
            return []

    async def process_decision_stream(self) -> List[Dict[str, Any]]:
        """
        处理决策流中的新决策
        用于实时分析和触发后续操作
        """
        events = await self.consume_events(
            consumer_group=self.CONSUMER_GROUP_DATA_BRAIN,
            consumer_name="decision_processor",
            stream=self.STREAM_DECISIONS,
            count=20,
            block_ms=1000
        )

        processed_decisions = []
        for event in events:
            try:
                decision_data = json.loads(event["data"].get("data", "{}"))
                event_type = event["data"].get("event_type", "")

                # 决策处理逻辑
                processed_decision = {
                    "id": event["id"],
                    "type": event_type,
                    "data": decision_data,
                    "processed_at": time.time(),
                    "analysis": await self._analyze_decision(decision_data)
                }

                processed_decisions.append(processed_decision)

                # 记录到记忆系统
                await self._store_to_memory(processed_decision)

                logger.info(f"处理决策: {event_type} [{event['id']}]")

            except Exception as e:
                logger.error(f"处理决策事件时出错: {e}")

        return processed_decisions

    async def _analyze_decision(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析决策数据"""
        analysis = {
            "roi_impact": 0.0,
            "risk_level": "low",
            "recommendations": [],
            "confidence": 0.7
        }

        # 简单的ROI影响分析
        if "roi" in decision_data:
            roi = decision_data["roi"]
            if roi > 3.0:
                analysis["roi_impact"] = 1.0
                analysis["risk_level"] = "low"
                analysis["recommendations"].append("高ROI决策，建议扩大规模")
            elif roi > 1.5:
                analysis["roi_impact"] = 0.5
                analysis["risk_level"] = "medium"
                analysis["recommendations"].append("中等ROI，建议优化测试")
            else:
                analysis["roi_impact"] = 0.1
                analysis["risk_level"] = "high"
                analysis["recommendations"].append("低ROI，建议谨慎评估")

        # 置信度分析
        if "confidence" in decision_data:
            analysis["confidence"] = decision_data["confidence"]

        return analysis

    async def _store_to_memory(self, processed_data: Dict[str, Any]):
        """存储处理后的数据到记忆系统"""
        if self.memory_manager is None:
            self.memory_manager = await get_memory_manager()

        try:
            await self.memory_manager.store(
                key=f"stream_decision_{processed_data['id'].replace('-', '_')}",
                data=processed_data,
                scenario=MemoryScenario.TRANSACTIONAL,
                metadata={
                    "source": "redis_streams",
                    "processed_at": processed_data["processed_at"],
                    "analysis_confidence": processed_data["analysis"]["confidence"]
                }
            )
        except Exception as e:
            logger.warning(f"存储到记忆系统失败: {e}")

    async def get_stream_stats(self) -> Dict[str, Any]:
        """获取流统计信息"""
        await self.connect()

        stats = {}
        streams = [
            self.STREAM_EVENTS,
            self.STREAM_DECISIONS,
            self.STREAM_ALERTS,
            self.STREAM_METRICS
        ]

        for stream in streams:
            try:
                info = await self.redis.xinfo_stream(stream)
                stats[stream] = {
                    "length": info["length"],
                    "groups": len(info.get("groups", [])),
                    "last_generated_id": info["last-generated-id"],
                    "first_entry": info.get("first-entry", {}),
                    "last_entry": info.get("last-entry", {})
                }
            except Exception as e:
                stats[stream] = {"error": str(e)}

        return stats

    async def cleanup_old_messages(self, max_age_hours: int = 24):
        """
        清理旧消息
        基于时间的消息清理（简化实现）
        """
        await self.connect()

        streams = [
            self.STREAM_EVENTS,
            self.STREAM_DECISIONS,
            self.STREAM_ALERTS,
            self.STREAM_METRICS
        ]

        for stream in streams:
            try:
                # 使用XTRIM命令基于最大长度清理
                # Redis Streams不支持基于时间的直接清理，但我们可以依赖最大长度设置
                logger.debug(f"清理流: {stream} (保持最近 {self.STREAM_MAX_LEN} 条消息)")
            except Exception as e:
                logger.warning(f"清理流 {stream} 时出错: {e}")

    async def close(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Redis Streams连接已关闭")


# 全局单例实例
_streams_client = None


async def get_streams_client() -> RedisStreamsClient:
    """获取Redis Streams客户端单例"""
    global _streams_client
    if _streams_client is None:
        import os
        _streams_client = RedisStreamsClient(
            redis_host=os.getenv("REDIS_HOST", "redis"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            redis_password=os.getenv("REDIS_PASSWORD"),
            stream_prefix=os.getenv("REDIS_STREAM_PREFIX", "hermes")
        )
        await _streams_client.connect()
    return _streams_client