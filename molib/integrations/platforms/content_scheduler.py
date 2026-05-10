"""
ContentScheduler v6.6 — IP 内容定时发布
生产段(9:00) → 审阅 → 发布段(10:00) → 数据回收 → 反馈优化
"""

from __future__ import annotations

import json
import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger


# ── 数据模型 ──

@dataclass
class ContentDraft:
    draft_id: str
    title: str
    body: str
    platform: str            # xiaohongshu, douyin, wechat, ...
    media_prompt: str = ""   # 配图 Prompt
    tags: List[str] = field(default_factory=list)
    scheduled_time: str = ""  # "10:00"
    status: str = "draft"     # draft, review_pending, approved, published, failed
    created_at: float = field(default_factory=time.time)
    published_at: float = 0
    metrics: Dict[str, int] = field(default_factory=dict)  # reads, likes, shares


@dataclass
class PublishTask:
    draft: ContentDraft
    platform_worker: str     # "XiaohongshuWorker" or "DouyinWorker"
    retry_count: int = 0
    max_retries: int = 3


# ── 调度器 ──

class ContentScheduler:
    """内容定时发布调度器"""

    def __init__(self):
        self._drafts: Dict[str, ContentDraft] = {}
        self._queue: List[PublishTask] = []
        self._published: List[ContentDraft] = []

    # ── 生产段 (9:00) ──

    async def generate_daily_drafts(
        self,
        ceo_input: str = "",
        data_insights: Dict[str, Any] = None,
    ) -> List[ContentDraft]:
        """
        CEO 触发 IP 子公司生成当日内容草稿。

        Args:
            ceo_input: CEO 对当日内容方向的指示
            data_insights: Data 子公司提供的历史表现数据

        Returns:
            生成的草稿列表
        """
        today = datetime.now().strftime("%Y%m%d")
        drafts = []

        # 默认内容模板（实际应由 IP 子公司 LLM 生成）
        platforms = ["xiaohongshu", "douyin"]
        for i, platform in enumerate(platforms):
            draft_id = f"draft_{today}_{platform}_{i}"
            draft = ContentDraft(
                draft_id=draft_id,
                title=f"AI工具推荐 | {today}",
                body=ceo_input or "今日AI工具精选内容",
                platform=platform,
                tags=["AI", "效率", "工具"],
                scheduled_time="10:00",
                status="draft",
            )
            drafts.append(draft)
            self._drafts[draft_id] = draft

        logger.info(f"[ContentScheduler] 生成 {len(drafts)} 条草稿")
        return drafts

    # ── 审阅 ──

    def submit_for_review(self, drafts: List[ContentDraft]) -> List[ContentDraft]:
        """提交审阅，标记为待审核"""
        for d in drafts:
            d.status = "review_pending"
        return drafts

    def approve_draft(self, draft_id: str) -> bool:
        if draft_id in self._drafts:
            self._drafts[draft_id].status = "approved"
            return True
        return False

    def reject_draft(self, draft_id: str, reason: str = "") -> bool:
        if draft_id in self._drafts:
            self._drafts[draft_id].status = "rejected"
            logger.info(f"[ContentScheduler] 草稿被拒: {draft_id}, reason={reason}")
            return True
        return False

    # ── 发布段 (10:00) ──

    def build_publish_queue(self) -> List[PublishTask]:
        """构建发布队列"""
        self._queue = []
        platform_workers = {
            "xiaohongshu": "XiaohongshuWorker",
            "douyin": "DouyinWorker",
        }

        for draft in self._drafts.values():
            if draft.status == "approved" and not draft.published_at:
                worker = platform_workers.get(draft.platform, "GenericWorker")
                self._queue.append(PublishTask(draft=draft, platform_worker=worker))

        logger.info(f"[ContentScheduler] 发布队列: {len(self._queue)} 条待发布")
        return self._queue

    async def publish_draft(self, task: PublishTask) -> Dict[str, Any]:
        """
        发布单条内容到目标平台。

        Returns:
            发布结果 {success, url, screenshot_path, error}
        """
        draft = task.draft

        logger.info(
            f"[ContentScheduler] 发布: {draft.title[:30]} → {draft.platform} "
            f"(worker={task.platform_worker})"
        )

        # 实际发布由 Platform Worker 执行（Playwright 或 API）
        # 这里提供接口框架
        try:
            # 模拟发布成功
            draft.published_at = time.time()
            draft.status = "published"
            self._published.append(draft)

            return {
                "success": True,
                "draft_id": draft.draft_id,
                "platform": draft.platform,
                "published_at": draft.published_at,
                "url": f"https://{draft.platform}.com/post/mock",
            }
        except Exception as e:
            draft.status = "failed"
            return {"success": False, "draft_id": draft.draft_id, "error": str(e)}

    # ── 数据回收 ──

    async def collect_metrics(self) -> Dict[str, Any]:
        """收集已发布内容的数据表现"""
        metrics = {}
        for draft in self._published:
            if draft.published_at > time.time() - 86400 * 7:  # 7天内
                metrics[draft.draft_id] = {
                    "title": draft.title[:50],
                    "platform": draft.platform,
                    "reads": draft.metrics.get("reads", 0),
                    "likes": draft.metrics.get("likes", 0),
                    "shares": draft.metrics.get("shares", 0),
                }
        return metrics

    # ── 定时任务入口 ──

    async def daily_production(self):
        """每日9:00 — CEO触发内容生产"""
        logger.info("[ContentScheduler] 每日内容生产启动")
        drafts = await self.generate_daily_drafts()
        self.submit_for_review(drafts)
        return drafts

    async def daily_publish(self):
        """每日10:00 — 自动发布已审核内容"""
        logger.info("[ContentScheduler] 每日内容发布启动")
        queue = self.build_publish_queue()
        results = []
        for task in queue:
            result = await self.publish_draft(task)
            results.append(result)
        return results


# 全局单例
_scheduler: Optional[ContentScheduler] = None


def get_content_scheduler() -> ContentScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = ContentScheduler()
    return _scheduler
