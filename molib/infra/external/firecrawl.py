"""
墨麟OS — Firecrawl 集成 (⭐70k)
================================
AI驱动的网页抓取，将任意网页转为干净Markdown/JSON。

用法:
    from molib.infra.external.firecrawl import scrape_url, search_and_scrape
    result = scrape_url("https://example.com/article")
    results = search_and_scrape("AI Agent 趋势 2026", limit=5)

集成点:
  - Research Worker: 竞品文章/行业报告批量抓取
  - ContentWriter: 爆款文章参考抓取，结构分析
"""

from __future__ import annotations

import os
from typing import Optional


def _get_api_key() -> Optional[str]:
    """从环境变量获取 API Key"""
    return os.environ.get("FIRECRAWL_API_KEY") or os.environ.get("FIRECRAWL_KEY")


def scrape_url(url: str, formats: list[str] = None) -> dict:
    """
    抓取单个URL并返回结构化内容。

    Args:
        url: 目标URL
        formats: 输出格式列表 (markdown/html/rawHtml/screenshot/links)

    Returns:
        {"url": str, "markdown": str, "title": str, "links": [...]}
    """
    if not _get_api_key():
        return {
            "url": url,
            "error": "FIRECRAWL_API_KEY not set",
            "status": "no_api_key",
        }

    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=_get_api_key())
        result = app.scrape(url, formats=(formats or ["markdown", "links"]))

        # 处理 firecrawl v2 Document 对象
        if hasattr(result, 'markdown'):
            return {
                "url": url,
                "markdown": result.markdown or "",
                "title": getattr(result.metadata, 'title', '') if result.metadata else '',
                "links": result.links or [],
                "status": "success",
                "source": "firecrawl",
            }
        # 兼容旧版 dict
        data = result.get("data", result) if isinstance(result, dict) else {}
        return {
            "url": url,
            "markdown": data.get("markdown", ""),
            "title": data.get("metadata", {}).get("title", "") if isinstance(data.get("metadata"), dict) else "",
            "links": data.get("links", []),
            "status": "success",
            "source": "firecrawl",
        }

    except ImportError:
        return {"url": url, "error": "firecrawl not installed", "status": "unavailable"}
    except Exception as e:
        return {"url": url, "error": str(e), "status": "error"}


def search_and_scrape(query: str, limit: int = 5, source: str = "web") -> dict:
    """
    搜索并批量抓取结果页面。

    Args:
        query: 搜索关键词
        limit: 最大结果数
        source: 搜索源 (web/news/images)

    Returns:
        {"query": str, "results": [{url, title, markdown}], "count": int}
    """
    if not _get_api_key():
        return {
            "query": query,
            "error": "FIRECRAWL_API_KEY not set",
            "status": "no_api_key",
        }

    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=_get_api_key())

        # 使用 /search 端点 + scrape
        search_result = app.search(query, limit=limit, sources=[source])
        results = []

        items = search_result.get("data", []) if isinstance(search_result, dict) else []
        for item in items[:limit]:
            url = item.get("url", "")
            scraped = scrape_url(url)
            results.append({
                "url": url,
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "content": scraped.get("markdown", "")[:3000],
            })

        return {
            "query": query,
            "results": results,
            "count": len(results),
            "status": "success",
            "source": "firecrawl",
        }

    except ImportError:
        return {"query": query, "error": "firecrawl not installed", "status": "unavailable"}
    except Exception as e:
        return {"query": query, "error": str(e), "status": "error"}


def extract_article_structure(url: str) -> dict:
    """
    提取文章结构（标题层次、关键词、段落分布）。
    用于 ContentWriter 分析爆款文章模式。
    """
    result = scrape_url(url, formats=["markdown"])
    if result.get("status") != "success":
        return result

    markdown = result.get("markdown", "")
    lines = markdown.split("\n")

    headers = []
    keywords = set()
    for line in lines:
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            headers.append({"level": level, "text": line.lstrip("# ").strip()})

    return {
        "url": url,
        "title": result.get("title", ""),
        "headers": headers,
        "total_lines": len(lines),
        "estimated_words": len(markdown.split()),
        "status": "success",
    }
