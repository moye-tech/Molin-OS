"""
墨麟AIOS 平台客户端 — PlatformClient
======================================
模拟多平台内容发布客户端，支持：
- 小红书（草稿 → 审核 → 发布 → 统计）
- 微信公众号（文章推送、预览链接、定时发布）
- 微博（图文、话题标签）
- 闲鱼（商品上架）
- 自动路由适配

参考项目：
- Coze Studio (20.7K⭐): 发布/部署到多平台
"""

import uuid
import time
import copy
import hashlib
from datetime import datetime, timedelta
from typing import Any


class PlatformClient:
    """多平台内容发布客户端。

    模拟各平台 API 行为，返回结构化发布结果。
    """

    # ── 平台标识常量 ──────────────────────────────────────────
    PLATFORM_XIAOHONGSHU = "xiaohongshu"
    PLATFORM_WECHAT = "wechat"
    PLATFORM_WEIBO = "weibo"
    PLATFORM_XIANYU = "xianyu"

    # ── 发布状态常量 ──────────────────────────────────────────
    STATUS_DRAFT = "draft"
    STATUS_REVIEWING = "reviewing"
    STATUS_PUBLISHED = "published"
    STATUS_BLOCKED = "blocked"
    STATUS_FAILED = "failed"

    # ── 平台配置 ──────────────────────────────────────────────
    PLATFORM_CONFIGS = {
        PLATFORM_XIAOHONGSHU: {
            "name": "小红书",
            "max_images": 18,
            "max_text_length": 1000,
            "supports_video": True,
            "requires_review": True,
            "review_time_seconds": (30, 180),
        },
        PLATFORM_WECHAT: {
            "name": "微信公众号",
            "max_images": 10,
            "max_text_length": 50000,
            "supports_video": True,
            "requires_review": True,
            "review_time_seconds": (60, 600),
        },
        PLATFORM_WEIBO: {
            "name": "微博",
            "max_images": 18,
            "max_text_length": 2000,
            "supports_video": True,
            "requires_review": False,
            "review_time_seconds": (0, 0),
        },
        PLATFORM_XIANYU: {
            "name": "闲鱼",
            "max_images": 9,
            "max_text_length": 5000,
            "supports_video": False,
            "requires_review": True,
            "review_time_seconds": (10, 60),
        },
    }

    def __init__(self, api_key: str | None = None, debug: bool = False):
        """
        Args:
            api_key: 可选的 API 密钥，用于模拟鉴权
            debug: 调试模式，跳过模拟延迟
        """
        self.api_key = api_key or f"molib_pk_{hashlib.md5(str(time.time()).encode()).hexdigest()[:12]}"
        self.debug = debug
        self._history: list[dict] = []  # 发布历史

    # ═══════════════════════════════════════════════════════════
    #  1. 小红书发布
    # ═══════════════════════════════════════════════════════════

    def xiaohongshu_publish(self, post_data: dict) -> dict:
        """模拟小红书图文/视频发布流程。

        流程: 草稿创建 → 内容审核 → 发布上架 → 数据统计

        Args:
            post_data: 发布数据，支持字段:
                - title (str): 标题
                - content (str): 正文内容
                - images (list[str]): 图片路径列表
                - video (str | None): 视频路径
                - tags (list[str]): 话题标签
                - location (str | None): 定位
                - schedule_time (str | None): 定时发布时间 (ISO格式)

        Returns:
            dict: 包含 id, status, platform, stats, urls, timestamps 的结构化结果
        """
        post_id = self._gen_id("xhs")
        now = datetime.now()

        # 内容校验
        errors = self._validate_content(post_data, self.PLATFORM_XIAOHONGSHU)
        if errors:
            return self._error_result(post_id, self.PLATFORM_XIAOHONGSHU, errors)

        # Step 1: 创建草稿
        draft = self._create_draft(post_id, post_data)
        self._record_step(post_id, self.STATUS_DRAFT, "草稿创建完成")

        # Step 2: 审核流程
        review_time = self._simulate_review(self.PLATFORM_XIAOHONGSHU)
        review_result = self._simulate_review_result(post_data)
        self._record_step(post_id, self.STATUS_REVIEWING, f"内容审核中 ({review_time}s)")

        if not review_result["passed"]:
            return {
                "id": post_id,
                "platform": self.PLATFORM_XIAOHONGSHU,
                "status": self.STATUS_BLOCKED,
                "reason": review_result["reason"],
                "draft": draft,
                "timestamps": {
                    "created": now.isoformat(),
                    "review_start": now.isoformat(),
                    "failed": (now + timedelta(seconds=review_time)).isoformat(),
                },
            }

        # Step 3: 发布
        publish_url = f"https://xiaohongshu.com/explore/{post_id}"
        self._record_step(post_id, self.STATUS_PUBLISHED, "发布成功")

        # Step 4: 统计模拟
        stats = self._simulate_stats()

        result = {
            "id": post_id,
            "platform": self.PLATFORM_XIAOHONGSHU,
            "platform_name": "小红书",
            "status": self.STATUS_PUBLISHED,
            "title": post_data.get("title", ""),
            "url": publish_url,
            "share_url": publish_url + "?share=1",
            "stats": stats,
            "draft": draft,
            "review_info": {
                "passed": True,
                "review_time_seconds": review_time,
            },
            "timestamps": {
                "created": now.isoformat(),
                "review_start": now.isoformat(),
                "published": (now + timedelta(seconds=review_time)).isoformat(),
            },
        }
        self._history.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    #  2. 微信公众号推送
    # ═══════════════════════════════════════════════════════════

    def wechat_push(self, article_data: dict) -> dict:
        """模拟微信公众号文章推送。

        Args:
            article_data: 文章数据，支持字段:
                - title (str): 文章标题
                - author (str | None): 作者
                - content (str): 文章正文 (支持HTML)
                - cover_image (str | None): 封面图片
                - digest (str | None): 摘要
                - is_original (bool): 是否原创
                - original_url (str | None): 原文链接
                - need_open_comment (bool): 是否开启评论
                - schedule_time (str | None): 定时发布时间 (ISO格式)

        Returns:
            dict: 包含 id, status, preview_url, urls, stats 的结构化结果
        """
        post_id = self._gen_id("wx")
        now = datetime.now()

        errors = self._validate_content(article_data, self.PLATFORM_WECHAT)
        if errors:
            return self._error_result(post_id, self.PLATFORM_WECHAT, errors)

        # 创建草稿
        draft = self._create_draft(post_id, article_data)
        self._record_step(post_id, self.STATUS_DRAFT, "图文草稿创建完成")

        # 审核
        review_time = self._simulate_review(self.PLATFORM_WECHAT)
        review_result = self._simulate_review_result(article_data)
        self._record_step(post_id, self.STATUS_REVIEWING, f"内容审核中 ({review_time}s)")

        if not review_result["passed"]:
            return {
                "id": post_id,
                "platform": self.PLATFORM_WECHAT,
                "status": self.STATUS_BLOCKED,
                "reason": review_result["reason"],
                "draft": draft,
                "timestamps": {
                    "created": now.isoformat(),
                    "failed": (now + timedelta(seconds=review_time)).isoformat(),
                },
            }

        # 发布
        article_url = f"https://mp.weixin.qq.com/s/{post_id}"
        preview_url = f"https://mp.weixin.qq.com/s/{post_id}?preview=1"
        self._record_step(post_id, self.STATUS_PUBLISHED, "群发成功")

        stats = self._simulate_stats(wechat_extra=True)
        is_scheduled = "schedule_time" in article_data

        result = {
            "id": post_id,
            "platform": self.PLATFORM_WECHAT,
            "platform_name": "微信公众号",
            "status": self.STATUS_PUBLISHED,
            "title": article_data.get("title", ""),
            "url": article_url,
            "preview_url": preview_url,
            "is_scheduled": is_scheduled,
            "scheduled_time": article_data.get("schedule_time"),
            "stats": stats,
            "draft": draft,
            "review_info": {
                "passed": True,
                "review_time_seconds": review_time,
            },
            "timestamps": {
                "created": now.isoformat(),
                "published": (now + timedelta(seconds=review_time)).isoformat(),
                "scheduled": article_data.get("schedule_time", ""),
            },
        }
        self._history.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    #  3. 微博发布
    # ═══════════════════════════════════════════════════════════

    def weibo_post(self, content: dict | str) -> dict:
        """模拟微博内容发布（含图文、话题标签）。

        Args:
            content: 发布内容，可以是:
                - str: 纯文本内容
                - dict: 结构化内容，支持字段:
                    - text (str): 正文
                    - images (list[str]): 图片路径列表
                    - topics (list[str]): 话题标签 (如 ["AI", "科技"])
                    - at_users (list[str]): @用户列表
                    - visible (str): 可见性 (public/friends/private)

        Returns:
            dict: 包含 id, status, url, stats, topics 的结构化结果
        """
        post_id = self._gen_id("wb")
        now = datetime.now()

        # 标准化输入
        if isinstance(content, str):
            content = {"text": content, "images": [], "topics": []}

        text = content.get("text", "")
        images = content.get("images", [])
        topics = content.get("topics", [])

        # 内容校验
        if not text or len(text.strip()) == 0:
            return self._error_result(post_id, self.PLATFORM_WEIBO, ["微博正文不能为空"])

        cfg = self.PLATFORM_CONFIGS[self.PLATFORM_WEIBO]
        if len(text) > cfg["max_text_length"]:
            return self._error_result(
                post_id, self.PLATFORM_WEIBO,
                [f"微博正文超出长度限制 ({len(text)}/{cfg['max_text_length']})"],
            )
        if len(images) > cfg["max_images"]:
            return self._error_result(
                post_id, self.PLATFORM_WEIBO,
                [f"图片数量超出限制 ({len(images)}/{cfg['max_images']})"],
            )

        # 格式化话题标签
        topic_str = " ".join(f"#{t}#" for t in topics) if topics else ""
        formatted_text = text
        if topic_str:
            formatted_text = f"{text}\n{topic_str}"

        # @用户
        at_users = content.get("at_users", [])
        if at_users:
            at_str = " ".join(f"@{u}" for u in at_users)
            formatted_text = f"{formatted_text}\n{at_str}"

        # 微博无需审核（模拟）
        publish_url = f"https://weibo.com/{post_id}"
        self._record_step(post_id, self.STATUS_PUBLISHED, "发布成功")

        stats = self._simulate_stats()
        stats["likes"] = stats.pop("views", 0) // 10  # 模拟赞数

        result = {
            "id": post_id,
            "platform": self.PLATFORM_WEIBO,
            "platform_name": "微博",
            "status": self.STATUS_PUBLISHED,
            "text": formatted_text,
            "url": publish_url,
            "images": images,
            "topics": topics,
            "at_users": at_users,
            "visible": content.get("visible", "public"),
            "stats": {
                "views": stats.get("views", 0),
                "likes": stats.get("likes", 0),
                "reposts": stats.get("shares", 0),
                "comments": stats.get("comments", 0),
            },
            "timestamps": {
                "created": now.isoformat(),
                "published": now.isoformat(),
            },
        }
        self._history.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    #  4. 闲鱼商品上架
    # ═══════════════════════════════════════════════════════════

    def xianyu_list(self, product_data: dict) -> dict:
        """模拟闲鱼商品上架。

        参考 XianYuApis 发布格式，支持一口价和拍卖模式。

        Args:
            product_data: 商品数据，支持字段:
                - title (str): 商品标题
                - description (str): 商品描述
                - price (float): 价格（元）
                - original_price (float | None): 原价
                - images (list[str]): 商品图片
                - category (str): 商品分类
                - condition (str): 新旧程度 (全新/几乎全新/轻微使用/明显使用)
                - tags (list[str]): 标签
                - location (dict | None): 发货地 {"city": "上海", "district": "浦东"}
                - delivery_method (str): 发货方式 (express/face_to_face)
                - auction (bool): 是否拍卖模式
                - min_bid (float | None): 起拍价（拍卖模式）

        Returns:
            dict: 包含 id, status, url, stats 的结构化结果
        """
        post_id = self._gen_id("xy")
        now = datetime.now()

        errors = self._validate_content(product_data, self.PLATFORM_XIANYU)
        if errors:
            return self._error_result(post_id, self.PLATFORM_XIANYU, errors)

        # 价格校验
        price = product_data.get("price", 0)
        if price <= 0:
            return self._error_result(post_id, self.PLATFORM_XIANYU, ["商品价格必须大于 0"])

        # 创建商品草稿
        draft = self._create_draft(post_id, product_data)
        self._record_step(post_id, self.STATUS_DRAFT, "商品草稿创建完成")

        # 审核
        review_time = self._simulate_review(self.PLATFORM_XIANYU)
        self._record_step(post_id, self.STATUS_REVIEWING, f"商品审核中 ({review_time}s)")

        # 闲鱼审核通常较快，模拟通过
        publish_url = f"https://2.taobao.com/item/{post_id}.htm"
        self._record_step(post_id, self.STATUS_PUBLISHED, "商品上架成功")

        stats = self._simulate_stats()
        stats["favorites"] = stats.pop("shares", 0)  # 收藏代替分享

        result = {
            "id": post_id,
            "platform": self.PLATFORM_XIANYU,
            "platform_name": "闲鱼",
            "status": self.STATUS_PUBLISHED,
            "title": product_data.get("title", ""),
            "price": price,
            "original_price": product_data.get("original_price"),
            "url": publish_url,
            "category": product_data.get("category", "其他"),
            "condition": product_data.get("condition", "全新"),
            "images": product_data.get("images", []),
            "is_auction": product_data.get("auction", False),
            "location": product_data.get("location"),
            "delivery_method": product_data.get("delivery_method", "express"),
            "stats": stats,
            "draft": draft,
            "review_info": {
                "passed": True,
                "review_time_seconds": review_time,
            },
            "timestamps": {
                "created": now.isoformat(),
                "published": (now + timedelta(seconds=review_time)).isoformat(),
            },
        }
        self._history.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    #  5. 自动路由适配
    # ═══════════════════════════════════════════════════════════

    def route_to_platform(self, content: dict | str, platform: str) -> dict:
        """根据平台自动适配内容格式并发布。

        参考 Coze Studio 的多平台部署设计，自动进行格式转换。

        Args:
            content: 通用内容（dict 或 str）
            platform: 目标平台标识（xiaohongshu / wechat / weibo / xianyu）

        Returns:
            dict: 对应平台的发布结果
        """
        platform = platform.lower().strip()

        if isinstance(content, str):
            content = {"text": content}

        # 平台路由映射
        router = {
            self.PLATFORM_XIAOHONGSHU: self._route_to_xiaohongshu,
            self.PLATFORM_WECHAT: self._route_to_wechat,
            self.PLATFORM_WEIBO: self._route_to_weibo,
            self.PLATFORM_XIANYU: self._route_to_xianyu,
        }

        adapter = router.get(platform)
        if not adapter:
            return {
                "id": None,
                "platform": platform,
                "status": self.STATUS_FAILED,
                "error": f"不支持的平台: {platform}。支持: {list(router.keys())}",
                "timestamps": {"created": datetime.now().isoformat()},
            }

        adapted_content = adapter(content)
        return adapted_content

    def _route_to_xiaohongshu(self, content: dict) -> dict:
        """适配到小红书格式"""
        post_data = {
            "title": content.get("title", content.get("text", "")[:50]),
            "content": content.get("text", content.get("content", "")),
            "images": content.get("images", []),
            "tags": content.get("tags", content.get("topics", [])),
            "location": content.get("location"),
        }
        return self.xiaohongshu_publish(post_data)

    def _route_to_wechat(self, content: dict) -> dict:
        """适配到微信公众号格式"""
        article_data = {
            "title": content.get("title", content.get("text", "")[:64]),
            "content": content.get("text", content.get("content", "")),
            "cover_image": content.get("cover_image", content.get("images", [None])[0]),
            "author": content.get("author", "墨麟AIOS"),
            "digest": content.get("digest", ""),
        }
        return self.wechat_push(article_data)

    def _route_to_weibo(self, content: dict) -> dict:
        """适配到微博格式"""
        return self.weibo_post({
            "text": content.get("text", content.get("content", "")),
            "images": content.get("images", []),
            "topics": content.get("tags", content.get("topics", [])),
        })

    def _route_to_xianyu(self, content: dict) -> dict:
        """适配到闲鱼格式"""
        product_data = {
            "title": content.get("title", content.get("text", "")[:30]),
            "description": content.get("text", content.get("description", "")),
            "price": content.get("price", 0),
            "original_price": content.get("original_price"),
            "images": content.get("images", []),
            "category": content.get("category", "其他"),
            "condition": content.get("condition", "全新"),
        }
        return self.xianyu_list(product_data)

    # ═══════════════════════════════════════════════════════════
    #  内部工具方法
    # ═══════════════════════════════════════════════════════════

    def get_history(self, platform: str | None = None) -> list[dict]:
        """获取发布历史。

        Args:
            platform: 筛选平台，None 返回全部

        Returns:
            list[dict]: 发布历史记录列表
        """
        if platform:
            return [h for h in self._history if h["platform"] == platform]
        return list(self._history)

    def _gen_id(self, prefix: str) -> str:
        """生成唯一发布 ID"""
        return f"{prefix}_{uuid.uuid4().hex[:16]}"

    def _validate_content(self, data: dict, platform: str) -> list[str]:
        """校验内容基本完整性"""
        errors = []
        if not data:
            errors.append("发布数据不能为空")
            return errors

        cfg = self.PLATFORM_CONFIGS.get(platform, {})
        text = str(data.get("text", data.get("content", data.get("title", ""))))
        images = data.get("images", [])

        if not text.strip() and platform != self.PLATFORM_XIANYU:
            errors.append("内容正文不能为空")
        if images and len(images) > cfg.get("max_images", 99):
            errors.append(f"图片数量超出限制 ({len(images)}/{cfg['max_images']})")
        if len(text) > cfg.get("max_text_length", 99999):
            errors.append(f"内容长度超出限制 ({len(text)}/{cfg['max_text_length']})")
        return errors

    def _create_draft(self, post_id: str, data: dict) -> dict:
        """创建发布草稿"""
        return {
            "draft_id": f"draft_{post_id}",
            "content_snapshot": copy.deepcopy(data),
            "created_at": datetime.now().isoformat(),
        }

    def _simulate_review(self, platform: str) -> int:
        """模拟审核耗时"""
        cfg = self.PLATFORM_CONFIGS.get(platform, {})
        min_t, max_t = cfg.get("review_time_seconds", (0, 0))
        if self.debug:
            return 0
        return int(min_t + (max_t - min_t) * (hashlib.md5(str(time.time()).encode()).hexdigest()[0], 16) % 100 / 100)

    def _simulate_review_result(self, data: dict) -> dict:
        """模拟审核结果 (90% 通过率)"""
        import random
        passed = random.random() < 0.9
        if passed:
            return {"passed": True, "reason": ""}
        reasons = [
            "内容包含敏感词，请修改后重新提交",
            "图片不符合社区规范",
            "标题含有违禁词",
            "内容重复度过高，建议原创",
        ]
        return {"passed": False, "reason": random.choice(reasons)}

    def _simulate_stats(self, wechat_extra: bool = False) -> dict:
        """模拟发布后的数据统计"""
        import random
        stats = {
            "views": random.randint(100, 5000),
            "likes": random.randint(10, 500),
            "shares": random.randint(1, 100),
            "comments": random.randint(0, 50),
        }
        if wechat_extra:
            stats["read_rate"] = round(random.uniform(0.3, 0.9), 2)
            stats["favorites"] = random.randint(1, 100)
        return stats

    def _error_result(self, post_id: str, platform: str, errors: list[str]) -> dict:
        """构造错误返回"""
        return {
            "id": post_id,
            "platform": platform,
            "status": self.STATUS_FAILED,
            "errors": errors,
            "timestamps": {"created": datetime.now().isoformat()},
        }

    def _record_step(self, post_id: str, status: str, message: str):
        """记录发布步骤日志"""
        entry = {
            "post_id": post_id,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }
        if not hasattr(self, "_steps"):
            self._steps = []
        self._steps.append(entry)

    def get_steps(self, post_id: str | None = None) -> list[dict]:
        """获取发布步骤日志"""
        if post_id:
            return [s for s in getattr(self, "_steps", []) if s["post_id"] == post_id]
        return list(getattr(self, "_steps", []))
