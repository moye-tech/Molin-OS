"""
飞书进度卡片订阅器 — Redis Pub/Sub 监听 + 卡片实时更新（Feature 1）
独立线程运行，不阻塞飞书 Bot 主循环
"""

import os
import json
import time
import asyncio
import threading
from typing import Dict, Optional
from loguru import logger

_active_subscriber: Optional["ProgressSubscriber"] = None


class ProgressSubscriber:
    """Redis Pub/Sub 进度事件订阅器"""

    def __init__(self):
        self._redis = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._pubsub = None
        # 状态缓存: task_id → {message_id, current_step, agencies, step_results}
        self._task_state: Dict[str, dict] = {}

    def start(self) -> None:
        """在独立线程中启动订阅"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="feishu-progress"
        )
        self._thread.start()
        logger.info("ProgressSubscriber 已启动")

    def stop(self) -> None:
        self._running = False
        if self._pubsub:
            try:
                self._pubsub.close()
            except Exception:
                pass
        logger.info("ProgressSubscriber 已停止")

    def _connect_redis(self):
        try:
            import redis
            self._redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD", ""),
                decode_responses=True,
            )
            self._pubsub = self._redis.pubsub()
            self._pubsub.subscribe("feishu_progress")
            logger.info("ProgressSubscriber 已连接 Redis")
        except Exception as e:
            logger.error(f"ProgressSubscriber Redis 连接失败: {e}")
            self._redis = None

    def _run_loop(self) -> None:
        self._connect_redis()
        if not self._redis:
            return
        logger.info("ProgressSubscriber 开始监听 feishu_progress")
        while self._running:
            try:
                msg = self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg is None or msg["type"] != "message":
                    continue
                self._handle_event(msg["data"])
            except Exception as e:
                logger.warning(f"ProgressSubscriber 监听异常: {e}")
                time.sleep(5)
                self._connect_redis()

    def _handle_event(self, raw: str) -> None:
        try:
            event = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return

        task_id = event.get("task_id", "")
        message_id = event.get("message_id", "")
        current_step = event.get("current_step", 0)

        # 更新状态缓存
        state = self._task_state.setdefault(task_id, {
            "message_id": message_id,
            "current_step": 0,
            "agencies": [],
            "step_results": {},
        })
        state["message_id"] = message_id
        state["current_step"] = current_step
        agency = event.get("agency", "")
        status = event.get("status", "")
        if agency and status:
            state["step_results"][agency] = status
            if agency not in state["agencies"]:
                state["agencies"].append(agency)

        eta = event.get("eta_seconds", 120)
        total = event.get("total_steps", 6)

        # 异步调用飞书 PATCH API
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self._update_card(
                    message_id, current_step, task_id,
                    state["agencies"], state["step_results"],
                    eta // 60, total,
                )
            )
            loop.close()
        except Exception as e:
            logger.warning(f"进度卡片更新失败: {e}")

    async def _update_card(self, message_id, current_step, task_id,
                           agencies, step_results, eta_min, total):
        from molib.integrations.feishu.progress_card import update_progress_card
        await update_progress_card(
            message_id=message_id,
            current_step=current_step,
            task_id=task_id,
            description="",
            agencies=agencies,
            step_results=step_results,
            eta_minutes=eta_min,
            total_steps=total,
        )

    def register_task(self, task_id: str, message_id: str,
                      agencies: Optional[list] = None) -> None:
        """注册任务状态，供订阅器跟踪"""
        self._task_state[task_id] = {
            "message_id": message_id,
            "current_step": 0,
            "agencies": agencies or [],
            "step_results": {},
        }


def get_subscriber() -> Optional[ProgressSubscriber]:
    global _active_subscriber
    return _active_subscriber


def start_progress_subscriber() -> None:
    global _active_subscriber
    if _active_subscriber is None:
        _active_subscriber = ProgressSubscriber()
    _active_subscriber.start()


def stop_progress_subscriber() -> None:
    global _active_subscriber
    if _active_subscriber:
        _active_subscriber.stop()
