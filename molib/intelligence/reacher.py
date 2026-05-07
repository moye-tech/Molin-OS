"""墨研竞情 — 社交爬虫（基于Agent-Reach设计模式，零API费）

集成自 Agent-Reach ⭐19K。核心设计模式：
1. Jina Reader 代理：curl https://r.jina.ai/URL → 免费Markdown渲染
2. 第三方CLI工具：twitter-cli, rdt-cli, xhs-cli（已装）
3. 免费第三方API：yt-dlp（字幕）, feedparser（RSS）, GitHub API
4. 直接从平台API爬：V2EX, Bilibili, 雪球
"""

import json
import subprocess
from typing import Optional


async def reach_web(url: str) -> dict:
    """用Jina Reader免费获取网页内容（零API费）"""
    import urllib.request
    try:
        req = urllib.request.Request(
            f"https://r.jina.ai/{url}",
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; Molin-Intel/1.0)",
                "Accept": "text/markdown",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode()
            return {
                "source": url,
                "method": "jina_reader",
                "content_length": len(content),
                "content": content[:3000],
            }
    except Exception as e:
        return {"source": url, "method": "jina_reader", "error": str(e)}


async def reach_github(query: str, limit: int = 10) -> dict:
    """GitHub API搜索（免费，无需token也可）"""
    import urllib.request, json
    try:
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort=stars&per_page={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "Molin-Intel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            items = []
            for r in data.get("items", [])[:limit]:
                items.append({
                    "name": r["full_name"],
                    "stars": r["stargazers_count"],
                    "description": r.get("description", ""),
                    "url": r["html_url"],
                    "language": r.get("language", ""),
                })
            return {"query": query, "total": data.get("total_count", 0), "results": items}
    except Exception as e:
        return {"query": query, "error": str(e)}


async def reach_rss(feed_url: str) -> dict:
    """RSS订阅阅读（纯Python，零依赖）"""
    try:
        import feedparser
        feed = feedparser.parse(feed_url)
        entries = []
        for entry in feed.entries[:10]:
            entries.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:300],
                "published": entry.get("published", ""),
            })
        return {
            "feed_title": feed.feed.get("title", ""),
            "entries_count": len(entries),
            "entries": entries,
        }
    except Exception as e:
        return {"feed_url": feed_url, "error": str(e)}


async def reach_bilibili(keyword: str) -> dict:
    """B站搜索（免费API）"""
    import urllib.request, json, urllib.parse
    try:
        url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={urllib.parse.quote(keyword)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://search.bilibili.com/",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"keyword": keyword, "data": data}
    except Exception as e:
        return {"keyword": keyword, "error": str(e)}
