"""
墨麟AIOS 社交推送工具 — SocialPushTool
========================================
支持多平台同步发布、定时发布、状态检查与跨平台格式转换。

参考项目：
- Coze Studio (20.7K⭐): 多平台发布/部署工作流
- weblate (5.8K⭐): MT 引擎抽象层设计
"""

import uuid
import time
import copy
import threading
from datetime import datetime, timedelta
from typing import Any

from .platform_client import PlatformClient


class SocialPushTool:
    """社交推送工具。

    集成 PlatformClient 实现：
    - batch_publish:   多平台同步发布（格式适配 + 频率控制）
    - schedule_post:   定时发布（队列管理 + 冲突检测）
    - check_post_status: 批量检查发布状态
    - cross_platform_format: 跨平台内容格式转换
    """

    # ── 频率控制配置（单位：秒） ─────────────────────────────
    RATE_LIMITS = {
        PlatformClient.PLATFORM_XIAOHONGSHU: {"min_interval": 300, "daily_limit": 10},   # 5分钟/条，日限10
        PlatformClient.PLATFORM_WECHAT:     {"min_interval": 86400, "daily_limit": 1},   # 24小时/条，日限1
        PlatformClient.PLATFORM_WEIBO:      {"min_interval": 60, "daily_limit": 100},    # 1分钟/条，日限100
        PlatformClient.PLATFORM_XIANYU:     {"min_interval": 120, "daily_limit": 50},    # 2分钟/条，日限50
    }

    # ── 内容格式适配器 ──────────────────────────────────────
    FORMAT_ADAPTERS = {
        "markdown_to_plain": {
            "description": "Markdown 转纯文本",
            "patterns": [
                (r"\*\*(.+?)\*\*", r"\1"),          # **bold**
                (r"\*(.+?)\*", r"\1"),               # *italic*
                (r"##*\s*(.+)", r"\1"),              # ## headers
                (r"\[(.+?)\]\(.+?\)", r"\1"),        # [text](url)
                (r"!\[.+?\]\(.+?\)", ""),            # ![alt](img)
                (r">\s*(.+)", r"\1"),                # blockquote
                (r"`{1,3}[^`]*`{1,3}", ""),          # inline code / code block
                (r"[-*+]\s", ""),                    # list markers
                (r"\n{3,}", "\n\n"),                 # excessive newlines
            ],
        },
        "weibo_shorten": {
            "description": "微博字数截断 + 摘要链接",
            "max_length": 2000,
            "append_link": True,
        },
        "xiaohongshu_emojify": {
            "description": "小红书 Emoji 增强",
            "add_emoji_prefix": True,
        },
    }

    def __init__(self, api_key: str | None = None, debug: bool = False):
        """
        Args:
            api_key: 可选的 API 密钥
            debug: 调试模式（跳过延迟等）
        """
        self.client = PlatformClient(api_key=api_key, debug=debug)
        self.debug = debug
        self._schedule_queue: list[dict] = []
        self._schedule_lock = threading.Lock()
        self._publish_timestamps: dict[str, list[datetime]] = {
            p: [] for p in self.RATE_LIMITS
        }

    # ═══════════════════════════════════════════════════════════
    #  1. 多平台同步发布
    # ═══════════════════════════════════════════════════════════

    def batch_publish(self, content: dict | str, platforms: list[str]) -> list[dict]:
        """多平台同步发布。

        自动进行：
        - 内容格式适配（针对各平台特征）
        - 频率控制（检查日限与间隔）
        - 错误隔离（单平台失败不影响其他）

        Args:
            content: 要发布的内容（dict 或 str）
            platforms: 目标平台列表，如 ["xiaohongshu", "weibo", "wechat"]

        Returns:
            list[dict]: 各平台发布结果，顺序与 platforms 一致
        """
        results: list[dict] = []
        errors: list[str] = []

        # 去重 + 校验平台
        unique_platforms = list(dict.fromkeys(p.lower().strip() for p in platforms))
        supported = list(self.RATE_LIMITS.keys())

        for platform in unique_platforms:
            if platform not in supported:
                errors.append(f"不支持的平台: {platform}")
                continue

            # 频率控制检查
            rate_check = self._check_rate_limit(platform)
            if not rate_check["allowed"]:
                results.append({
                    "platform": platform,
                    "status": "rate_limited",
                    "error": rate_check["reason"],
                    "timestamps": {"created": datetime.now().isoformat()},
                })
                continue

            # 格式适配 + 发布
            try:
                adapted = self.cross_platform_format(content, platform)
                result = self.client.route_to_platform(adapted, platform)
                results.append(result)

                # 记录发布成功时间戳
                if result.get("status") == PlatformClient.STATUS_PUBLISHED:
                    self._record_publish(platform)

            except Exception as e:
                results.append({
                    "platform": platform,
                    "status": "error",
                    "error": str(e),
                    "timestamps": {"created": datetime.now().isoformat()},
                })

        # 附加报告
        summary = self._batch_summary(results)
        return {
            "results": results,
            "summary": summary,
            "errors": errors if errors else None,
            "total_platforms": len(unique_platforms),
            "success_count": summary["success"],
            "failed_count": summary["failed"] + summary["rate_limited"],
            "timestamps": {"created": datetime.now().isoformat()},
        }

    def _batch_summary(self, results: list[dict]) -> dict:
        """生成批量发布摘要"""
        success = sum(1 for r in results if r.get("status") == PlatformClient.STATUS_PUBLISHED)
        failed = sum(1 for r in results if r.get("status") in (PlatformClient.STATUS_FAILED, "error"))
        reviewing = sum(1 for r in results if r.get("status") == PlatformClient.STATUS_REVIEWING)
        blocked = sum(1 for r in results if r.get("status") == PlatformClient.STATUS_BLOCKED)
        rate_limited = sum(1 for r in results if r.get("status") == "rate_limited")
        return {
            "total": len(results),
            "success": success,
            "failed": failed,
            "reviewing": reviewing,
            "blocked": blocked,
            "rate_limited": rate_limited,
        }

    # ═══════════════════════════════════════════════════════════
    #  2. 定时发布
    # ═══════════════════════════════════════════════════════════

    def schedule_post(
        self,
        content: dict | str,
        platforms: list[str],
        schedule_time: str,
    ) -> dict:
        """定时发布（含队列管理、冲突检测）。

        将任务加入队列，由后台调度器按计划执行。
        支持 ISO 格式时间字符串。

        Args:
            content: 发布内容
            platforms: 目标平台列表
            schedule_time: 定时时间，ISO 格式 (如 "2026-05-05T22:00:00")

        Returns:
            dict: 包含 task_id, status, queue_info, conflict_check 的结构化结果
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        now = datetime.now()

        # 解析目标时间
        try:
            target_time = datetime.fromisoformat(schedule_time)
        except (ValueError, TypeError):
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"无效的时间格式: {schedule_time}，请使用 ISO 格式 (如 2026-05-05T22:00:00)",
                "timestamps": {"created": now.isoformat()},
            }

        # 校验时间
        if target_time <= now:
            return {
                "task_id": task_id,
                "status": "failed",
                "error": f"定时时间必须晚于当前时间: {target_time} <= {now}",
                "timestamps": {"created": now.isoformat()},
            }

        # 冲突检测
        conflict_check = self._detect_conflicts(platforms, target_time)

        task = {
            "task_id": task_id,
            "content": copy.deepcopy(content) if isinstance(content, dict) else content,
            "platforms": list(dict.fromkeys(p.lower().strip() for p in platforms)),
            "schedule_time": target_time.isoformat(),
            "created_at": now.isoformat(),
            "status": "scheduled",
            "conflicts": conflict_check,
        }

        with self._schedule_lock:
            self._schedule_queue.append(task)

        return {
            "task_id": task_id,
            "status": "scheduled",
            "platforms": task["platforms"],
            "schedule_time": target_time.isoformat(),
            "queue_position": len(self._schedule_queue),
            "conflict_check": conflict_check,
            "timestamps": {
                "created": now.isoformat(),
                "scheduled_for": target_time.isoformat(),
            },
        }

    def _detect_conflicts(self, platforms: list[str], target_time: datetime) -> dict:
        """检测在目标时间是否存在平台冲突"""
        conflicts = []
        window_start = target_time - timedelta(minutes=30)
        window_end = target_time + timedelta(minutes=30)

        with self._schedule_lock:
            for task in self._schedule_queue:
                if task["status"] not in ("scheduled",):
                    continue
                try:
                    task_time = datetime.fromisoformat(task["schedule_time"])
                except (ValueError, TypeError):
                    continue
                if window_start <= task_time <= window_end:
                    overlapping = set(task["platforms"]) & set(platforms)
                    if overlapping:
                        conflicts.append({
                            "conflicting_task_id": task["task_id"],
                            "overlapping_platforms": list(overlapping),
                            "task_time": task["schedule_time"],
                        })

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "severity": "high" if len(conflicts) > 1 else ("low" if conflicts else "none"),
        }

    def get_scheduled_tasks(self, status: str | None = None) -> list[dict]:
        """查看定时任务队列。

        Args:
            status: 筛选状态 (scheduled / in_progress / completed / failed)，None 返回全部

        Returns:
            list[dict]: 任务列表
        """
        with self._schedule_lock:
            if status:
                return [t for t in self._schedule_queue if t["status"] == status]
            return list(self._schedule_queue)

    def cancel_scheduled_task(self, task_id: str) -> dict:
        """取消定时任务。

        Args:
            task_id: 任务 ID

        Returns:
            dict: 操作结果
        """
        with self._schedule_lock:
            for task in self._schedule_queue:
                if task["task_id"] == task_id and task["status"] == "scheduled":
                    task["status"] = "cancelled"
                    return {
                        "task_id": task_id,
                        "status": "cancelled",
                        "message": "定时任务已取消",
                        "timestamps": {"cancelled": datetime.now().isoformat()},
                    }
        return {
            "task_id": task_id,
            "status": "not_found",
            "error": f"未找到可取消的任务: {task_id}",
        }

    # ═══════════════════════════════════════════════════════════
    #  3. 批量检查发布状态
    # ═══════════════════════════════════════════════════════════

    def check_post_status(self, post_ids: list[str], platform: str) -> dict:
        """批量检查发布状态。

        模拟真实平台的状态查询，返回每条内容的审核/发布状态。

        Args:
            post_ids: 待检查的发布 ID 列表
            platform: 目标平台

        Returns:
            dict: 包含各 ID 的状态详情及统计
        """
        if not post_ids:
            return {
                "platform": platform,
                "results": [],
                "summary": {"total": 0, "published": 0, "reviewing": 0, "blocked": 0, "unknown": 0},
                "timestamps": {"checked": datetime.now().isoformat()},
            }

        results = []
        now = datetime.now()
        import random
        import hashlib

        for pid in post_ids:
            # 优先从历史记录中获取
            history_item = None
            for h in self.client._history:
                if h["id"] == pid and h["platform"] == platform:
                    history_item = h
                    break

            if history_item:
                results.append({
                    "id": pid,
                    "platform": platform,
                    "status": history_item["status"],
                    "url": history_item.get("url", ""),
                    "stats": history_item.get("stats", {}),
                    "checked_at": now.isoformat(),
                })
            else:
                # 模拟未知 ID 的查询结果
                seed = int(hashlib.md5(pid.encode()).hexdigest()[:8], 16)
                rng = random.Random(seed)
                status_roll = rng.random()
                if status_roll < 0.7:
                    status = PlatformClient.STATUS_PUBLISHED
                elif status_roll < 0.9:
                    status = PlatformClient.STATUS_REVIEWING
                else:
                    status = PlatformClient.STATUS_BLOCKED

                results.append({
                    "id": pid,
                    "platform": platform,
                    "status": status,
                    "url": f"https://{platform}.com/post/{pid}" if status == PlatformClient.STATUS_PUBLISHED else None,
                    "stats": {},
                    "checked_at": now.isoformat(),
                })

        summary = {
            "total": len(results),
            "published": sum(1 for r in results if r["status"] == PlatformClient.STATUS_PUBLISHED),
            "reviewing": sum(1 for r in results if r["status"] == PlatformClient.STATUS_REVIEWING),
            "blocked": sum(1 for r in results if r["status"] == PlatformClient.STATUS_BLOCKED),
            "draft": sum(1 for r in results if r["status"] == PlatformClient.STATUS_DRAFT),
            "failed": sum(1 for r in results if r["status"] == PlatformClient.STATUS_FAILED),
            "unknown": sum(1 for r in results if r["status"] not in (
                PlatformClient.STATUS_PUBLISHED, PlatformClient.STATUS_REVIEWING,
                PlatformClient.STATUS_BLOCKED, PlatformClient.STATUS_DRAFT,
                PlatformClient.STATUS_FAILED,
            )),
        }

        return {
            "platform": platform,
            "results": results,
            "summary": summary,
            "timestamps": {"checked": now.isoformat()},
        }

    # ═══════════════════════════════════════════════════════════
    #  4. 跨平台内容格式转换
    # ═══════════════════════════════════════════════════════════

    def cross_platform_format(self, content: dict | str, target_platform: str) -> dict:
        """跨平台内容格式转换。

        参考 weblate 的 MT 引擎抽象层设计，将通用内容适配到目标平台格式。
        支持链式转换（如 Markdown → 小红书风格文本）。

        Args:
            content: 原始内容（dict 或 str）
            target_platform: 目标平台标识

        Returns:
            dict: 适配后的内容
        """
        # 标准化输入
        if isinstance(content, str):
            text = content
            extra = {}
        else:
            text = content.get("text", content.get("content", ""))
            extra = {k: v for k, v in content.items() if k not in ("text", "content")}

        platform = target_platform.lower().strip()

        # 通用处理链
        pipeline = self._get_format_pipeline(platform)

        adapted_text = text
        for transform in pipeline:
            try:
                adapted_text = transform(adapted_text)
            except Exception:
                continue  # 单步转换失败不影响后续

        # 平台特有字段
        adapted = {"text": adapted_text, **extra}

        if platform == PlatformClient.PLATFORM_WEIBO:
            adapted["text"] = self._weibo_format(adapted_text)
        elif platform == PlatformClient.PLATFORM_XIAOHONGSHU:
            adapted = self._xiaohongshu_format(adapted_text, adapted)
        elif platform == PlatformClient.PLATFORM_WECHAT:
            adapted = self._wechat_format(adapted_text, adapted)
        elif platform == PlatformClient.PLATFORM_XIANYU:
            adapted = self._xianyu_format(adapted_text, adapted)

        adapted["_adapted_for"] = platform
        adapted["_original_length"] = len(text)
        adapted["_adapted_length"] = len(adapted.get("text", ""))
        return adapted

    def _get_format_pipeline(self, platform: str) -> list:
        """获取平台的格式转换管道"""
        pipelines = {
            PlatformClient.PLATFORM_WEIBO: [
                self._md_to_plain,
                self._strip_excessive_newlines,
            ],
            PlatformClient.PLATFORM_XIAOHONGSHU: [
                self._md_to_plain,
                self._add_emoji_prefix,
            ],
            PlatformClient.PLATFORM_WECHAT: [
                # 公众号保留 HTML/Markdown
                lambda t: t,
            ],
            PlatformClient.PLATFORM_XIANYU: [
                self._md_to_plain,
                self._strip_excessive_newlines,
            ],
        }
        return pipelines.get(platform, [lambda t: t])

    def _md_to_plain(self, text: str) -> str:
        """Markdown 转纯文本"""
        import re
        rules = self.FORMAT_ADAPTERS["markdown_to_plain"]["patterns"]
        result = text
        for pattern, replacement in rules:
            result = re.sub(pattern, replacement, result)
        return result.strip()

    def _strip_excessive_newlines(self, text: str) -> str:
        """压缩多余换行"""
        import re
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def _add_emoji_prefix(self, text: str) -> str:
        """添加 Emoji 前缀（小红书风格）"""
        lines = text.split("\n")
        if not lines:
            return text
        # 首行加 Emoji
        emojis = ["📌", "✨", "🌟", "💡", "📣", "🔥", "💪", "🎯"]
        import hashlib
        idx = int(hashlib.md5(text.encode()).hexdigest()[0], 16) % len(emojis)
        lines[0] = f"{emojis[idx]} {lines[0]}"
        return "\n".join(lines)

    def _weibo_format(self, text: str) -> str:
        """微博格式：字数限制 + 截断"""
        max_len = self.FORMAT_ADAPTERS["weibo_shorten"]["max_length"]
        if len(text) <= max_len:
            return text
        return text[: max_len - 20] + "...\n🔗 查看全文链接"

    def _xiaohongshu_format(self, text: str, adapted: dict) -> dict:
        """小红书格式：Emoji 增强 + 标签"""
        adapted["text"] = self._add_emoji_prefix(text)
        if "tags" not in adapted:
            adapted["tags"] = []
        return adapted

    def _wechat_format(self, text: str, adapted: dict) -> dict:
        """公众号格式：保留 HTML + 适配"""
        adapted["text"] = text
        if "title" not in adapted:
            # 从文本首行提取标题
            first_line = text.split("\n")[0][:64]
            adapted["title"] = first_line if first_line else "墨麟AIOS 发布"
        if "author" not in adapted:
            adapted["author"] = "墨麟AIOS"
        return adapted

    def _xianyu_format(self, text: str, adapted: dict) -> dict:
        """闲鱼格式：纯文本 + 商品描述"""
        adapted["text"] = self._md_to_plain(text)
        if "price" not in adapted:
            adapted["price"] = 0
        if "condition" not in adapted:
            adapted["condition"] = "全新"
        return adapted

    # ═══════════════════════════════════════════════════════════
    #  频率控制
    # ═══════════════════════════════════════════════════════════

    def _check_rate_limit(self, platform: str) -> dict:
        """检查平台的频率限制"""
        limits = self.RATE_LIMITS.get(platform, {})
        now = datetime.now()

        timestamps = self._publish_timestamps.get(platform, [])

        # 清理过期记录（超过24小时）
        cutoff = now - timedelta(hours=24)
        timestamps = [t for t in timestamps if t > cutoff]
        self._publish_timestamps[platform] = timestamps

        # 检查日限
        daily_limit = limits.get("daily_limit", float("inf"))
        if len(timestamps) >= daily_limit:
            return {
                "allowed": False,
                "reason": f"{platform} 已达日发布上限 ({daily_limit})",
                "remaining": 0,
                "reset_at": (timestamps[0] + timedelta(hours=24)).isoformat(),
            }

        # 检查间隔
        min_interval = limits.get("min_interval", 0)
        if timestamps and not self.debug:
            last_pub = timestamps[-1]
            elapsed = (now - last_pub).total_seconds()
            if elapsed < min_interval:
                wait = min_interval - elapsed
                return {
                    "allowed": False,
                    "reason": f"{platform} 发布间隔为 {min_interval}s，还需等待 {wait:.0f}s",
                    "remaining": daily_limit - len(timestamps),
                    "next_available_at": (last_pub + timedelta(seconds=min_interval)).isoformat(),
                }

        return {
            "allowed": True,
            "remaining": daily_limit - len(timestamps),
            "reason": "",
        }

    def _record_publish(self, platform: str):
        """记录一次发布"""
        if platform not in self._publish_timestamps:
            self._publish_timestamps[platform] = []
        self._publish_timestamps[platform].append(datetime.now())

    def get_rate_limit_status(self, platform: str | None = None) -> dict:
        """查询各平台的频率限制状态

        Args:
            platform: 平台标识，None 返回全部

        Returns:
            dict: 各平台的频率状态
        """
        if platform:
            platforms = [platform]
        else:
            platforms = list(self.RATE_LIMITS.keys())

        status = {}
        for p in platforms:
            limits = self.RATE_LIMITS.get(p, {})
            timestamps = self._publish_timestamps.get(p, [])
            now = datetime.now()
            cutoff = now - timedelta(hours=24)
            recent = [t for t in timestamps if t > cutoff]

            daily_limit = limits.get("daily_limit", float("inf"))
            min_interval = limits.get("min_interval", 0)

            status[p] = {
                "published_today": len(recent),
                "daily_limit": daily_limit,
                "remaining_today": max(0, daily_limit - len(recent)),
                "min_interval_seconds": min_interval,
                "last_published": recent[-1].isoformat() if recent else None,
            }

        return status
