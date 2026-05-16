"""
Bilibili 数据采集 Adapter
基于公开API采集热门视频、关键词搜索、视频详情

可用API（无需Cookie）：
  - 本周热门：GET /x/web-interface/popular (10条/页)
  - 搜索综合：GET /x/web-interface/search/all/v2 (多类型搜索)
  - 视频详情：GET /x/web-interface/view (aid或bvid)
  - 热搜建议：GET /x/web-interface/search/default/search_words

输出格式：统一 SourceItem 数据契约
"""

import json
import time
import logging
import random
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

logger = logging.getLogger("molin.adapter.bilibili")

# ─── 统一数据契约 ────────────────────────────────────────────────

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
    favorites: Optional[int] = None  # B站收藏 = coins

    def engagement_score(self) -> float:
        """统一互动评分公式"""
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
    task: str                    # popular / search / video_detail
    keywords: list = field(default_factory=list)
    video_id: Optional[str] = None
    max_items: int = 20
    timeout: int = 15

@dataclass
class CollectionResult:
    source: str
    items: list
    errors: list
    collected_at: str
    duration_ms: int
    quota_remaining: int = 100

# ─── 配置 ────────────────────────────────────────────────────────

ADAPTER_CONFIG = {
    "platform": "bilibili",
    "name": "B站",
    "api_base": "https://api.bilibili.com/x/web-interface",
    "popular_url": "https://api.bilibili.com/x/web-interface/popular",
    "search_url": "https://api.bilibili.com/x/web-interface/search/all/v2",
    "view_url": "https://api.bilibili.com/x/web-interface/view",
    "trending_url": "https://api.bilibili.com/x/web-interface/search/default/search_words",
    "rate_limit": {
        "requests_per_minute": 20,   # B站API限制较宽松
        "concurrent_max": 5,
        "retry_on_429": True,
        "retry_delay_seconds": 10,
    },
    "timeout": 10,
}


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


class BiliBiliAdapter:
    """Bilibili 数据采集 Adapter"""

    platform = "bilibili"
    name = "B站"

    def __init__(self, config: dict = None):
        self.config = config or ADAPTER_CONFIG
        self.rate_limiter = RateLimiter(self.config["rate_limit"]["requests_per_minute"])

    def _build_headers(self) -> dict:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
        }

    def _request(self, url: str, headers: dict = None) -> dict:
        """发送HTTP请求并解析JSON"""
        h = self._build_headers()
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, headers=h)
        resp = urllib.request.urlopen(req, timeout=self.config["timeout"])
        data = json.loads(resp.read().decode())
        code = data.get("code", -1)
        if code != 0:
            raise Exception(f"B站API返回错误 code={code}: {data.get('message','?')}")
        return data.get("data", {})

    def health_check(self) -> bool:
        """通过访问热门API检查服务状态"""
        try:
            url = self.config["popular_url"] + "?pn=1&ps=1"
            self._request(url)
            return True
        except Exception:
            return False

    def get_quota(self) -> dict:
        return {
            "remaining": 100,
            "limit": 100,
            "reset_at": datetime.now() + timedelta(days=1),
        }

    def support_type(self, task_type: str) -> bool:
        return task_type in ["popular", "search", "video_detail", "hot_search"]

    def collect(self, context: CollectionContext) -> CollectionResult:
        start_time = time.time()
        errors: list[AdapterError] = []
        items: list[SourceItem] = []

        try:
            if context.task == "popular":
                items = self._fetch_popular(context)
            elif context.task == "search":
                items = self._search_videos(context)
            elif context.task == "video_detail":
                items = self._fetch_video_detail(context)
            elif context.task == "hot_search":
                items = self._fetch_hot_search(context)
            else:
                errors.append(AdapterError(
                    code="error.source.bilibili.unsupported_task",
                    message=f"不支持的任务类型: {context.task}",
                    severity="error",
                ))
        except Exception as e:
            errors.append(AdapterError(
                code="error.source.bilibili.collection_failed",
                message=str(e),
                severity="error",
            ))
            logger.exception(f"B站采集失败: {e}")

        duration = int((time.time() - start_time) * 1000)
        return CollectionResult(
            source="bilibili",
            items=items,
            errors=errors,
            collected_at=datetime.now().isoformat(),
            duration_ms=duration,
            quota_remaining=100 - len(self.rate_limiter.request_timestamps),
        )

    def _fetch_popular(self, context: CollectionContext) -> list[SourceItem]:
        """采集本周热门视频"""
        items = []
        self.rate_limiter.wait_if_needed()

        url = f"{self.config['popular_url']}?pn=1&ps={min(context.max_items, 50)}"
        data = self._request(url)
        video_list = data.get("list", [])

        for item in video_list[:context.max_items]:
            stat = item.get("stat", {})
            owner = item.get("owner", {})
            title = item.get("title", "")
            bvid = item.get("bvid", "")

            metrics = Metrics(
                views=stat.get("view", 0),
                likes=stat.get("like", 0),
                comments=stat.get("reply", 0),
                shares=stat.get("share", stat.get("forward", 0)),
                favorites=stat.get("coin", 0),  # B站硬币≈收藏
            )

            author = Author(
                id=str(owner.get("mid", "")),
                name=owner.get("name", "未知"),
                avatar=owner.get("face", None),
            )

            items.append(SourceItem(
                id=bvid or f"bili_pop_{int(time.time())}",
                title=title[:80],
                content=item.get("desc", "")[:200],
                content_type="视频",
                url=f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                platform="bilibili",
                author=author,
                published_at=datetime.fromtimestamp(item.get("pubdate", 0)),
                collected_at=datetime.now(),
                metrics=metrics,
                engagement_score=metrics.engagement_score(),
                thumbnail=item.get("pic", None),
                tags=[f"分区:{item.get('tname', '')}"] if item.get('tname') else [],
                category=item.get("tname", None),
                data_quality="high",
                collection_method="api",
            ))

        logger.info(f"B站热门采集完成: {len(items)} 条")
        return items

    def _fetch_hot_search(self, context: CollectionContext) -> list[SourceItem]:
        """采集B站热搜词（搜索默认推荐词）"""
        items = []
        self.rate_limiter.wait_if_needed()

        try:
            data = self._request(self.config["trending_url"])
            trending_list = data.get("list", [])
            for i, entry in enumerate(trending_list[:context.max_items]):
                keyword = entry.get("keyword", "")
                if not keyword:
                    continue

                items.append(SourceItem(
                    id=f"bili_hot_{i}_{int(time.time())}",
                    title=f"🔍 {keyword}",
                    content=f"B站热搜词 #{i+1}",
                    content_type="搜索词",
                    url=f"https://search.bilibili.com/all?keyword={urllib.parse.quote(keyword)}",
                    platform="bilibili",
                    author=Author(id="bilibili_hot", name="B站热搜"),
                    published_at=datetime.now(),
                    collected_at=datetime.now(),
                    metrics=Metrics(views=10000 - i * 200, likes=0, comments=0, shares=0),
                    engagement_score=max(100 - i * 3, 10),
                    tags=["热搜", keyword],
                    data_quality="medium",
                    collection_method="api",
                ))
        except Exception as e:
            logger.warning(f"B站热搜建议API不可用: {e}")
            # 如果热搜建议不可用，降级为搜索关键词
            for i, keyword in enumerate(context.keywords[:5]):
                items.append(SourceItem(
                    id=f"bili_hot_fallback_{i}",
                    title=f"🔍 {keyword}（B站搜索）",
                    content="",
                    content_type="搜索词",
                    url=f"https://search.bilibili.com/all?keyword={urllib.parse.quote(keyword)}",
                    platform="bilibili",
                    author=Author(id="system", name="系统"),
                    published_at=datetime.now(),
                    collected_at=datetime.now(),
                    metrics=Metrics(views=5000, likes=0, comments=0, shares=0),
                    engagement_score=50.0,
                    tags=[keyword],
                    data_quality="low",
                    collection_method="api",
                ))

        return items

    def _search_videos(self, context: CollectionContext) -> list[SourceItem]:
        """搜索B站视频"""
        items = []

        for keyword in context.keywords[:3]:
            self.rate_limiter.wait_if_needed()
            url = f"{self.config['search_url']}?keyword={urllib.parse.quote(keyword)}"
            try:
                data = self._request(url)
                sections = data.get("result", [])

                for section in sections:
                    section_items = section.get("data", [])
                    if not isinstance(section_items, list) or len(section_items) == 0:
                        continue

                    for entry in section_items[:min(5, context.max_items)]:
                        aid = entry.get("aid", 0)
                        bvid = entry.get("bvid", "")
                        play = entry.get("play", 0)
                        pubdate = entry.get("pubdate", 0)

                        metrics = Metrics(
                            views=play,
                            likes=entry.get("like", 0),
                            comments=entry.get("danmaku", 0),
                            shares=entry.get("share", 0),
                        )

                        items.append(SourceItem(
                            id=urllib.parse.quote(str(aid or bvid or f"search_{int(time.time())}")),
                            title=entry.get("title", "?")[:80].replace("<em class=\"keyword\">", "").replace("</em>", ""),
                            content=entry.get("description", "")[:200],
                            content_type="视频",
                            url=f"https://www.bilibili.com/video/{bvid}" if bvid else "",
                            platform="bilibili",
                            author=Author(
                                id=str(entry.get("mid", "")),
                                name=entry.get("author", "未知"),
                            ),
                            published_at=datetime.fromtimestamp(pubdate) if pubdate else datetime.now(),
                            collected_at=datetime.now(),
                            metrics=metrics,
                            engagement_score=metrics.engagement_score(),
                            thumbnail=entry.get("pic", None),
                            tags=[keyword],
                            data_quality="medium",
                            collection_method="api",
                        ))

            except Exception as e:
                logger.warning(f"B站搜索 '{keyword}' 失败: {e}")

        return items[:context.max_items]

    def _fetch_video_detail(self, context: CollectionContext) -> list[SourceItem]:
        """采集单个视频详情"""
        if not context.video_id:
            return []

        self.rate_limiter.wait_if_needed()
        # 支持aid或bvid
        if context.video_id.startswith("BV"):
            url = f"{self.config['view_url']}?bvid={context.video_id}"
        else:
            url = f"{self.config['view_url']}?aid={context.video_id}"

        try:
            data = self._request(url)
            stat = data.get("stat", {})
            owner = data.get("owner", {})
            title = data.get("title", "")

            metrics = Metrics(
                views=stat.get("view", 0),
                likes=stat.get("like", 0),
                comments=stat.get("reply", 0),
                shares=stat.get("share", 0),
                favorites=stat.get("favorite", 0),
            )

            return [SourceItem(
                id=data.get("bvid", context.video_id),
                title=title[:80],
                content=data.get("desc", "")[:200],
                content_type="视频",
                url=f"https://www.bilibili.com/video/{data.get('bvid', '')}",
                platform="bilibili",
                author=Author(
                    id=str(owner.get("mid", "")),
                    name=owner.get("name", "未知"),
                    avatar=owner.get("face", None),
                ),
                published_at=datetime.fromtimestamp(data.get("pubdate", 0)),
                collected_at=datetime.now(),
                metrics=metrics,
                engagement_score=metrics.engagement_score(),
                thumbnail=data.get("pic", None),
                tags=[data.get("tname", "")],
                category=data.get("tname", None),
                data_quality="high",
                collection_method="api",
            )]
        except Exception as e:
            logger.warning(f"B站视频详情采集失败: {e}")
            return []


# ─── 命令行入口 ──────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="B站数据采集 Adapter")
    parser.add_argument("--task", default="popular",
                        choices=["popular", "search", "video_detail", "hot_search"])
    parser.add_argument("--keywords", nargs="+", default=["AI一人公司", "AI工具", "编程"])
    parser.add_argument("--video-id", default=None)
    parser.add_argument("--max-items", type=int, default=20)
    parser.add_argument("--output", default=None)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    adapter = BiliBiliAdapter()
    context = CollectionContext(
        task=args.task,
        keywords=args.keywords,
        video_id=args.video_id,
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
    for item in result.items[:5]:
        output["items"].append({
            "id": item.id,
            "title": item.title[:80],
            "score": item.engagement_score,
            "author": item.author.name,
            "metrics": {
                "views": item.metrics.views,
                "likes": item.metrics.likes,
                "comments": item.metrics.comments,
            },
        })

    output_json = json.dumps(output, ensure_ascii=False, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"输出写入: {args.output}")
    else:
        print(output_json)

    print(f"\n📊 采集摘要:")
    print(f"   数据源: {result.source}")
    print(f"   采集项: {len(result.items)} 条")
    print(f"   耗时: {result.duration_ms}ms")
    print(f"   错误: {len(result.errors)}")


if __name__ == "__main__":
    main()
