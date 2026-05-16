"""
小红书数据采集 Adapter
基于 cobalt 架构的4层URL处理链 + 统一响应契约

数据源类型：Cookie登录态（浏览器Cookie）
采集能力：热词搜索、笔记详情、用户主页、搜索建议
输出格式：SourceItem 数组 → CollectionResult

使用方式：
  from adapters.xiaohongshu.adapter import XiaoHongShuAdapter
  
  adapter = XiaoHongShuAdapter()
  result = adapter.collect(CollectionContext(
      task="hot_topics",
      keywords=["AI一人公司", "AI工具", "副业"]
  ))
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

# 尝试导入httpx，如果没有则使用urllib
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False
    import urllib.request
    import urllib.error

logger = logging.getLogger("molin.adapter.xiaohongshu")

# ─── 统一响应契约（符合 adapter-architecture.md 定义） ─────────────────

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
    favorites: Optional[int] = None   # 收藏/保存（小红书关键指标）

    def engagement_score(self) -> float:
        """
        统一互动评分公式（与墨镜数据一致）
        权重：收藏/保存(6) > 分享(5) > 评论(3) > 点赞(2)
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
    type: str  # image / video
    width: Optional[int] = None
    height: Optional[int] = None

@dataclass
class SourceItem:
    id: str
    title: str
    content: str
    content_type: str          # 图文/视频/帖子
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
    data_quality: str = "high"   # high / medium / low
    collection_method: str = "api"

@dataclass
class AdapterError:
    code: str
    message: str
    severity: str = "warning"  # warning / error / critical

@dataclass
class CollectionContext:
    task: str                    # hot_topics / search / detail / user
    keywords: list = field(default_factory=list)
    note_id: Optional[str] = None
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

# ─── Adapter 配置 ─────────────────────────────────────────────

ADAPTER_CONFIG = {
    "platform": "xiaohongshu",
    "name": "小红书",
    "base_url": "https://www.xiaohongshu.com",
    "api_base": "https://edith.xiaohongshu.com",
    "search_url": "https://www.xiaohongshu.com/search_result",
    "cookie_dir": "/Users/laomo/.hermes/profiles/media/cookies/xiaohongshu",
    "rate_limit": {
        "requests_per_minute": 5,
        "concurrent_max": 2,
        "retry_on_429": True,
        "retry_delay_seconds": 30,
    },
    "timeout": 30,
}


class CookieRotator:
    """Cookie 轮换管理器（借鉴 cobalt）"""

    def __init__(self, cookie_dir: str):
        self.cookie_dir = Path(cookie_dir)
        self.cookie_dir.mkdir(parents=True, exist_ok=True)
        self.cookies: list[dict] = []
        self._load_cookies()

    def _load_cookies(self):
        """从文件加载多组 Cookie"""
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
            logger.info("未找到Cookie文件，将使用免登录模式")
            # 创建一个占位记录
            self.cookies.append({
                "content": "",
                "file": "",
                "valid": False,
                "last_used": 0,
            })

    def get_random(self) -> str:
        """获取一个随机 Cookie"""
        valid_cookies = [c for c in self.cookies if c["valid"]]
        if not valid_cookies:
            return ""
        selected = random.choice(valid_cookies)
        selected["last_used"] = time.time()
        return selected["content"]

    def mark_expired(self, cookie_content: str):
        """标记某个Cookie已过期"""
        for c in self.cookies:
            if c["content"] == cookie_content:
                c["valid"] = False
                logger.warning(f"Cookie已过期: {c['file']}")
                break

    def has_valid(self) -> bool:
        return any(c["valid"] for c in self.cookies)


class RateLimiter:
    """限流器"""

    def __init__(self, max_per_minute: int):
        self.max_per_minute = max_per_minute
        self.request_timestamps: list[float] = []

    def wait_if_needed(self):
        """如果超过限流阈值，等待到下一个可用时刻"""
        now = time.time()
        # 清理1分钟前的记录
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]

        if len(self.request_timestamps) >= self.max_per_minute:
            # 计算需要等待的时间
            oldest = self.request_timestamps[0]
            wait_time = 60 - (now - oldest)
            if wait_time > 0:
                logger.info(f"限流中，等待 {wait_time:.1f} 秒")
                time.sleep(wait_time)
                # 清理并重试
                self.request_timestamps = [t for t in self.request_timestamps if time.time() - t < 60]

        self.request_timestamps.append(time.time())


class XiaoHongShuAdapter:
    """小红书数据采集 Adapter"""

    platform = "xiaohongshu"
    name = "小红书"

    def __init__(self, config: dict = None):
        self.config = config or ADAPTER_CONFIG
        self.cookie_mgr = CookieRotator(self.config["cookie_dir"])
        self.rate_limiter = RateLimiter(self.config["rate_limit"]["requests_per_minute"])

        if HAS_HTTPX:
            self.client = httpx.Client(
                timeout=self.config["timeout"],
                follow_redirects=True,
                headers=self._build_headers(),
            )
        else:
            self.client = None

    def _build_headers(self) -> dict:
        """构造浏览器风格请求头"""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.xiaohongshu.com/",
            "Origin": "https://www.xiaohongshu.com",
        }

    def health_check(self) -> bool:
        """健康检查：验证Cookie是否有效（通过访问搜索页）"""
        if not self.cookie_mgr.has_valid():
            logger.info("小红书Cookie未配置，使用占位模式")
            return False
        
        try:
            cookie = self.cookie_mgr.get_random()
            cookie_str = self._format_cookie(cookie) if cookie else ""
            if not cookie_str:
                return False
                
            headers = self._build_headers()
            headers["Cookie"] = cookie_str
            
            url = self.config["base_url"] + "/search_result?keyword=AI"
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=10)
            
            html = resp.read().decode("utf-8", errors="replace")
            valid = resp.status == 200 and len(html) > 10000
            if valid:
                logger.info("小红书Cookie有效 ✅")
            return valid
        except Exception as e:
            logger.warning(f"小红书健康检查失败: {e}")
            return False

    def _format_cookie(self, cookie_content: str) -> str:
        """将多行Cookie格式化为单行HTTP Cookie头"""
        lines = [line.strip() for line in cookie_content.split("\n") if line.strip() and "=" in line]
        return "; ".join(lines)

    def get_quota(self) -> dict:
        """返回配额状态"""
        return {
            "remaining": 100,
            "limit": 100,
            "reset_at": datetime.now() + timedelta(days=1),
        }

    def support_type(self, task_type: str) -> bool:
        """支持的任务类型"""
        return task_type in ["hot_topics", "search", "note_detail", "user_notes"]

    def collect(self, context: CollectionContext) -> CollectionResult:
        """主采集入口"""
        start_time = time.time()
        errors: list[AdapterError] = []
        items: list[SourceItem] = []

        try:
            if context.task == "hot_topics":
                items = self._fetch_hot_topics(context)
            elif context.task == "search":
                items = self._search_notes(context)
            elif context.task == "note_detail":
                items = self._fetch_note_detail(context)
            elif context.task == "user_notes":
                items = self._fetch_user_notes(context)
            else:
                errors.append(AdapterError(
                    code="error.source.xiaohongshu.unsupported_task",
                    message=f"不支持的任务类型: {context.task}",
                    severity="error",
                ))

        except Exception as e:
            errors.append(AdapterError(
                code="error.source.xiaohongshu.collection_failed",
                message=str(e),
                severity="error",
            ))
            logger.exception(f"小红书采集失败: {e}")

        duration = int((time.time() - start_time) * 1000)

        return CollectionResult(
            source="xiaohongshu",
            items=items,
            errors=errors,
            collected_at=datetime.now().isoformat(),
            duration_ms=duration,
            quota_remaining=100 - len(self.rate_limiter.request_timestamps),
        )

    def _fetch_hot_topics(self, context: CollectionContext) -> list[SourceItem]:
        """采集热门话题/搜索结果"""
        items = []
        keywords = context.keywords or ["AI一人公司", "AI工具", "副业", "自媒体创业"]

        for keyword in keywords[:3]:  # 最多搜索3个关键词
            self.rate_limiter.wait_if_needed()
            try:
                batch = self._search_single_keyword(keyword, context.max_items // len(keywords))
                items.extend(batch)
                logger.info(f"小红书搜索 '{keyword}' 获取到 {len(batch)} 条结果")
            except Exception as e:
                logger.warning(f"小红书搜索 '{keyword}' 失败: {e}")

        # 去重（按note_id）
        seen = set()
        unique_items = []
        for item in items:
            if item.id not in seen:
                seen.add(item.id)
                unique_items.append(item)

        return unique_items[:context.max_items]

    def _search_single_keyword(self, keyword: str, limit: int) -> list[SourceItem]:
        """搜索单个关键词"""
        # 由于小红书没有公开API，这里构建search_url
        # 实际请求会通过Web搜索+html解析或自有API
        # 目前返回模拟结构让管线先跑起来，后续接入真实数据源
        params = urllib.parse.urlencode({"keyword": keyword, "sort": "general"})
        url = f"{self.config['search_url']}?{params}"

        items = []
        # 占位：此处接入真实采集逻辑
        # 当前返回占位数据，结构完整可被下游消费
        items.append(SourceItem(
            id=f"placeholder_xhs_{int(time.time())}",
            title=f"小红书热词搜索结果：{keyword}",
            content=f"关键词 '{keyword}' 的热门笔记摘要，待接入真实数据源",
            content_type="图文",
            url=url,
            platform="xiaohongshu",
            author=Author(id="system", name="系统"),
            published_at=datetime.now(),
            collected_at=datetime.now(),
            metrics=Metrics(views=1000, likes=50, comments=10, shares=5, favorites=20),
            engagement_score=0.0,
            tags=[keyword],
            data_quality="low",
            collection_method="public",
        ))
        return items

    def _fetch_note_detail(self, context: CollectionContext) -> list[SourceItem]:
        """采集笔记详情"""
        if not context.note_id:
            return []

        url = f"{self.config['base_url']}/explore/{context.note_id}"
        self.rate_limiter.wait_if_needed()

        # 占位实现
        return [SourceItem(
            id=context.note_id,
            title=f"笔记 {context.note_id}",
            content="详情待接入真实数据源",
            content_type="图文",
            url=url,
            platform="xiaohongshu",
            author=Author(id="", name="未知"),
            published_at=datetime.now(),
            collected_at=datetime.now(),
            metrics=Metrics(),
            engagement_score=0.0,
            data_quality="low",
            collection_method="public",
        )]

    def _fetch_user_notes(self, context: CollectionContext) -> list[SourceItem]:
        """采集用户笔记列表"""
        # 占位
        return []


# ─── 命令行入口 ────────────────────────────────────────────────

def main():
    """命令行调用入口"""
    import argparse

    parser = argparse.ArgumentParser(description="小红书数据采集 Adapter")
    parser.add_argument("--task", default="hot_topics",
                        choices=["hot_topics", "search", "note_detail", "user_notes"])
    parser.add_argument("--keywords", nargs="+", default=["AI一人公司", "AI工具", "副业"])
    parser.add_argument("--note-id", default=None)
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--output", default=None,
                        help="输出文件路径，默认打印到stdout")

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    adapter = XiaoHongShuAdapter()
    context = CollectionContext(
        task=args.task,
        keywords=args.keywords,
        note_id=args.note_id,
        max_items=args.max_items,
    )

    result = adapter.collect(context)

    output = {
        "source": result.source,
        "collected_at": result.collected_at,
        "duration_ms": result.duration_ms,
        "items_count": len(result.items),
        "errors": [asdict(e) for e in result.errors],
        "items": [asdict(item) for item in result.items],
    }

    output_json = json.dumps(output, ensure_ascii=False, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"输出写入: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
