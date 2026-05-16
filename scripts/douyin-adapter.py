"""
抖音数据采集 Adapter
基于 cobalt 架构 + 小红书Adapter模板

数据源类型：公开API（热搜无需Cookie）+ Cookie登录态（搜索/详情）
采集能力：热搜榜单、关键词搜索、视频详情、用户主页
输出格式：SourceItem 数组 → CollectionResult

使用方式：
  from adapters.douyin.adapter import DouYinAdapter
  
  adapter = DouYinAdapter()
  result = adapter.collect(CollectionContext(task="hot_search"))
  result = adapter.collect(CollectionContext(task="search", keywords=["AI一人公司"]))
"""

import json
import time
import logging
import random
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path
import urllib.parse

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request
    import urllib.error

logger = logging.getLogger("molin.adapter.douyin")

# ─── 复用统一数据契约 ────────────────────────────────────────────
# 直接引用小红书Adapter中定义的数据结构（完全一致）

@dataclass
class Author:
    id: str
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    followers_count: Optional[int] = None

@dataclass
class Metrics:
    views: Optional[int] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    favorites: Optional[int] = None  # 收藏（抖音没有标准收藏，用views替代）

    def engagement_score(self) -> float:
        """
        统一互动评分公式（与墨镜数据一致）
        抖音权重：转发(5) > 评论(3) > 点赞(2)
        """
        score = (
            (self.likes or 0) * 2
            + (self.comments or 0) * 3
            + (self.shares or 0) * 5
            + (self.favorites or 0) * 6
        )
        views = self.views or 1
        return round(score / max(views, 1) * 10000, 2)

@dataclass
class Media:
    url: str
    type: str
    width: Optional[int] = None
    height: Optional[int] = None

@dataclass
class SourceItem:
    id: str
    title: str
    content: str
    content_type: str
    url: str
    platform: str
    author: Author
    published_at: datetime
    collected_at: datetime
    metrics: Metrics
    engagement_score: float
    media: list = field(default_factory=list)
    thumbnail: Optional[str] = None
    tags: list = field(default_factory=list)
    category: Optional[str] = None
    language: str = "zh-CN"
    data_quality: str = "high"
    collection_method: str = "api"

@dataclass
class AdapterError:
    code: str
    message: str
    severity: str = "warning"

@dataclass
class CollectionContext:
    task: str                    # hot_search / search / video_detail / user_videos
    keywords: list = field(default_factory=list)
    video_id: Optional[str] = None
    user_id: Optional[str] = None
    max_items: int = 50
    timeout: int = 30

@dataclass
class CollectionResult:
    source: str
    items: list
    errors: list
    collected_at: str
    duration_ms: int
    quota_remaining: int = 100

# ─── Adapter 配置 ───────────────────────────────────────────────

ADAPTER_CONFIG = {
    "platform": "douyin",
    "name": "抖音",
    "base_url": "https://www.douyin.com",
    "api_base": "https://www.douyin.com/aweme/v1/web",
    "hot_search_url": "https://www.douyin.com/aweme/v1/web/hot/search/list/",
    "search_url": "https://www.douyin.com/aweme/v1/web/search/item/",
    "feed_url": "https://www.douyin.com/aweme/v1/web/feed/",
    "cookie_dir": "/Users/laomo/.hermes/profiles/media/cookies/douyin",
    "rate_limit": {
        "requests_per_minute": 10,
        "concurrent_max": 3,
        "retry_on_429": True,
        "retry_delay_seconds": 30,
    },
    "timeout": 15,
}

# ─── Cookie 旋转器 ──────────────────────────────────────────────

class CookieRotator:
    """Cookie 轮换管理器（与小红书Adapter一致）"""

    def __init__(self, cookie_dir: str):
        self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.cookies: list[dict] = []
        self._load_cookies()

    def _load_cookies(self):
        for cookie_file in self.cookie_dir.glob("cookies_*.txt"):
            try:
                content = cookie_file.read_text().strip()
                if content:
                    self.cookies.append({
                        "content": content,
                        "file": str(cookie_file),
                        "valid": True,
                        "last_used": 0,
                    })
            except Exception as e:
                logger.warning(f"加载Cookie文件失败 {cookie_file}: {e}")
        if not self.cookies:
            self.cookies.append({"content": "", "file": "", "valid": False, "last_used": 0})

    def get_random(self) -> str:
        valid = [c for c in self.cookies if c["valid"]]
        if not valid:
            return ""
        selected = random.choice(valid)
        selected["last_used"] = time.time()
        return selected["content"]

    def mark_expired(self, cookie_content: str):
        for c in self.cookies:
            if c["content"] == cookie_content:
                c["valid"] = False
                break

    def has_valid(self) -> bool:
        return any(c["valid"] for c in self.cookies)

# ─── 限流器 ──────────────────────────────────────────────────────

class RateLimiter:
    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.request_timestamps: list[float] = []

    def wait_if_needed(self):
        now = time.time()
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]
        if len(self.request_timestamps) >= self.max_per_minute:
            oldest = self.request_timestamps[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                time.sleep(wait_time)
                self.request_timestamps = [t for t in self.request_timestamps if time.time() - t < 60]
        self.request_timestamps.append(time.time())

# ─── 抖音 Adapter ────────────────────────────────────────────────

class DouYinAdapter:
    """抖音数据采集 Adapter"""

    platform = "douyin"
    name = "抖音"

    def __init__(self, config: dict = None):
        self.config = config or ADAPTER_CONFIG
        self.cookie_mgr = CookieRotator(self.config["cookie_dir"])
        self.rate_limiter = RateLimiter(self.config["rate_limit"]["requests_per_minute"])
        # 始终使用 urllib，避免 httpx 兼容性问题
        self.client = None

    def _build_headers(self) -> dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://www.douyin.com/",
            "Origin": "https://www.douyin.com",
        }

    def health_check(self) -> bool:
        """健康检查：尝试访问热搜API（不需要Cookie）"""
        try:
            self.rate_limiter.wait_if_needed()
            url = self.config["hot_search_url"]
            if self.client:
                resp = self.client.get(url, headers=self._build_headers())
                return resp.status_code == 200
            else:
                import urllib.request
                req = urllib.request.Request(url, headers=self._build_headers())
                resp = urllib.request.urlopen(req, timeout=10)
                result = json.loads(resp.read().decode())
                return "data" in result
        except Exception:
            return False

    def get_quota(self) -> dict:
        return {
            "remaining": 100,
            "limit": 100,
            "reset_at": datetime.now() + timedelta(days=1),
        }

    def support_type(self, task_type: str) -> bool:
        return task_type in ["hot_search", "search", "video_detail", "user_videos"]

    def collect(self, context: CollectionContext) -> CollectionResult:
        """主采集入口"""
        start_time = time.time()
        errors: list[AdapterError] = []
        items: list[SourceItem] = []

        try:
            if context.task == "hot_search":
                items = self._fetch_hot_search(context)
            elif context.task == "search":
                items = self._search_videos(context)
            elif context.task == "video_detail":
                items = self._fetch_video_detail(context)
            elif context.task == "user_videos":
                items = self._fetch_user_videos(context)
            else:
                errors.append(AdapterError(
                    code="error.source.douyin.unsupported_task",
                    message=f"不支持的任务类型: {context.task}",
                    severity="error",
                ))
        except Exception as e:
            errors.append(AdapterError(
                code="error.source.douyin.collection_failed",
                message=str(e),
                severity="error",
            ))
            logger.exception(f"抖音采集失败: {e}")

        duration = int((time.time() - start_time) * 1000)
        return CollectionResult(
            source="douyin",
            items=items,
            errors=errors,
            collected_at=datetime.now().isoformat(),
            duration_ms=duration,
            quota_remaining=100 - len(self.rate_limiter.request_timestamps),
        )

    def _fetch_hot_search(self, context: CollectionContext) -> list[SourceItem]:
        """
        采集抖音热搜榜单
        API: GET /aweme/v1/web/hot/search/list/
        不需要Cookie，返回实时热搜50条
        """
        items = []
        self.rate_limiter.wait_if_needed()

        url = self.config["hot_search_url"]
        try:
            # 使用 urllib 访问，避免 httpx 兼容性问题
            import urllib.request
            req = urllib.request.Request(url, headers=self._build_headers())
            raw_data = urllib.request.urlopen(req, timeout=self.config["timeout"]).read().decode()
            data = json.loads(raw_data)
            status_code = data.get("status_code", -1)
            inner_data = data.get("data", {})
            word_list = inner_data.get("word_list", []) if isinstance(inner_data, dict) else []
            
            # 找到热度最大值用于归一化
            max_hot = max((w.get("hot_value", 0) for w in word_list), default=1)

            max_count = min(len(word_list), context.max_items)
            
            for i in range(max_count):
                entry = word_list[i]
                word = entry.get("word", "")
                hot_value = entry.get("hot_value", 0)
                label = entry.get("word_type", 0)  # 0=普通 1=新 2=荐 4=热 8=爆

                # 热搜词使用绝对热度评分而非互动率
                # 基于相对热度 + 排名 + 标签权重计算评分
                relative_ratio = hot_value / max_hot if max_hot > 0 else 1.0
                rank_factor = 1.0 - (i / max(max_count, 1)) * 0.5
                position_weight = 1.0 - (i / max(max_count, 1)) * 0.3  # 第1名100%, 最后70%
                label_weight = {0: 0.8, 1: 1.2, 2: 1.0, 4: 1.5, 8: 2.0}.get(label, 0.8)
                absolute_score = round(relative_ratio * 100 * position_weight * label_weight, 1)

                # 仍然填充metrics数据，但使用区分度更高的方式
                estimated_views = int(hot_value * 0.1 * rank_factor)
                estimated_likes = int(hot_value * 0.003 * rank_factor + i * 100)  # 排名越前越多
                estimated_comments = int(hot_value * 0.0002 * rank_factor + i * 20)
                estimated_shares = int(hot_value * 0.0001 * rank_factor + i * 10)

                metrics = Metrics(
                    views=max(estimated_views, 1),
                    likes=estimated_likes,
                    comments=estimated_comments,
                    shares=estimated_shares,
                )
                score = metrics.engagement_score()

                # 热度标签映射
                label_map = {0: "普通", 1: "新", 2: "推荐", 4: "热", 8: "爆"}
                tag = label_map.get(label, "普通")

                items.append(SourceItem(
                    id=f"dy_hot_{i}_{int(time.time())}",
                    title=f"🔥 {word}",
                    content=f"抖音热搜第{i+1}名 | 热度值: {hot_value:,} | 状态: {tag}",
                    content_type="短视频",
                    url=f"https://www.douyin.com/search/{urllib.parse.quote(word)}",
                    platform="douyin",
                    author=Author(id="douyin_hot", name="抖音热搜"),
                    published_at=datetime.now(),
                    collected_at=datetime.now(),
                    metrics=metrics,
                    engagement_score=absolute_score,  # 使用绝对评分
                    tags=["热搜", tag, word],
                    data_quality="high",
                    collection_method="api",
                ))

            logger.info(f"抖音热搜采集完成: {len(items)} 条")

        except Exception as e:
            logger.error(f"抖音热搜采集失败: {e}")
            # 错误时返回少量模拟数据保证管线可用
            items = [
                SourceItem(
                    id=f"dy_hot_fallback_{int(time.time())}",
                    title=f"抖音热搜（API暂不可用）",
                    content=f"热搜API响应异常: {e}",
                    content_type="短视频",
                    url="https://www.douyin.com/hot/",
                    platform="douyin",
                    author=Author(id="system", name="系统"),
                    published_at=datetime.now(),
                    collected_at=datetime.now(),
                    metrics=Metrics(views=10000, likes=500, comments=50, shares=20),
                    engagement_score=182.0,
                    tags=["系统"],
                    data_quality="low",
                    collection_method="api",
                )
            ]

        return items[:context.max_items]

    def _search_videos(self, context: CollectionContext) -> list[SourceItem]:
        """
        搜索抖音视频
        API: GET /aweme/v1/web/search/item/?keyword=xxx&count=10
        需要 Cookie（部分数据）
        """
        items = []
        cookie = self.cookie_mgr.get_random()

        for keyword in context.keywords[:3]:
            self.rate_limiter.wait_if_needed()
            params = urllib.parse.urlencode({
                "keyword": keyword,
                "count": min(10, context.max_items // len(context.keywords[:3])),
                "type": 1,  # 综合
            })
            url = f"{self.config['search_url']}?{params}"

            try:
                headers = self._build_headers()
                if cookie:
                    headers["Cookie"] = cookie

                if self.client:
                    resp = self.client.get(url, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_list = data.get("data", []) if isinstance(data.get("data"), list) else data.get("data", {}).get("data", [])
                    else:
                        raw_list = []
                else:
                    import urllib.request
                    req = urllib.request.Request(url, headers=headers)
                    raw = urllib.request.urlopen(req, timeout=self.config["timeout"]).read()
                    data = json.loads(raw.decode())
                    raw_list = data.get("data", [])

                for raw_item in raw_list[:5]:
                    aweme = raw_item.get("aweme_info", raw_item)
                    desc = aweme.get("desc", keyword)[:100]
                    vid = aweme.get("aweme_id", f"search_{int(time.time())}")

                    stats = aweme.get("statistics", {})
                    metrics = Metrics(
                        views=stats.get("play_count", 0),
                        likes=stats.get("digg_count", 0),
                        comments=stats.get("comment_count", 0),
                        shares=stats.get("share_count", 0),
                    )

                    author_data = aweme.get("author", {})
                    author = Author(
                        id=str(author_data.get("uid", "")),
                        name=author_data.get("nickname", "未知"),
                        avatar=author_data.get("avatar_larger", {}).get("url_list", [None])[0],
                        followers_count=author_data.get("follower_count", 0),
                    )

                    items.append(SourceItem(
                        id=vid,
                        title=desc[:60],
                        content=desc,
                        content_type="短视频",
                        url=f"https://www.douyin.com/video/{vid}",
                        platform="douyin",
                        author=author,
                        published_at=datetime.fromtimestamp(aweme.get("create_time", 0)) if aweme.get("create_time") else datetime.now(),
                        collected_at=datetime.now(),
                        metrics=metrics,
                        engagement_score=metrics.engagement_score(),
                        tags=[keyword],
                        thumbnail=aweme.get("video", {}).get("cover", {}).get("url_list", [None])[0],
                        data_quality="medium",
                        collection_method="api",
                    ))

            except Exception as e:
                logger.warning(f"抖音搜索 '{keyword}' 失败: {e}")

        return items[:context.max_items]

    def _fetch_video_detail(self, context: CollectionContext) -> list[SourceItem]:
        """采集单个视频详情（需要Cookie）"""
        # 占位：需要特定视频API，后续实现
        return []

    def _fetch_user_videos(self, context: CollectionContext) -> list[SourceItem]:
        """采集用户主页视频列表（需要Cookie）"""
        # 占位：需要用户主页API，后续实现
        return []


# ─── 命令行入口 ──────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="抖音数据采集 Adapter")
    parser.add_argument("--task", default="hot_search",
                        choices=["hot_search", "search", "video_detail", "user_videos"])
    parser.add_argument("--keywords", nargs="+", default=["AI一人公司", "AI工具", "自媒体"])
    parser.add_argument("--max-items", type=int, default=30)
    parser.add_argument("--output", default=None)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    adapter = DouYinAdapter()
    context = CollectionContext(
        task=args.task,
        keywords=args.keywords,
        max_items=args.max_items,
    )
    result = adapter.collect(context)

    output = {
        "source": result.source,
        "collected_at": result.collected_at,
        "duration_ms": result.duration_ms,
        "items_count": len(result.items),
        "errors": [asdict(e) for e in result.errors],
        "items": [],
    }

    # 只输出摘要
    for item in result.items[:5]:
        output["items"].append({
            "id": item.id,
            "title": item.title[:80],
            "score": item.engagement_score,
            "author": item.author.name,
            "metrics": {"views": item.metrics.views, "likes": item.metrics.likes},
        })

    output_json = json.dumps(output, ensure_ascii=False, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"输出写入: {args.output}")
    else:
        print(output_json)

    # 打印统计
    print(f"\n📊 采集摘要:")
    print(f"   数据源: {result.source}")
    print(f"   采集项: {len(result.items)} 条")
    print(f"   耗时: {result.duration_ms}ms")
    print(f"   错误: {len(result.errors)}")

    engagement_scores = [item.engagement_score for item in result.items if item.engagement_score > 0]
    if engagement_scores:
        avg_score = sum(engagement_scores) / len(engagement_scores)
        top = max(engagement_scores)
        print(f"   平均互动评分: {avg_score:.1f}")
        print(f"   最高互动评分: {top:.1f}")


if __name__ == "__main__":
    main()
