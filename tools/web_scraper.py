#!/usr/bin/env python3
"""
墨麟OS · 智能网页抓取工具
策略：
  1. 优先使用 crawl4ai（本地，零成本，M1原生）
  2. crawl4ai失败或内容不足时，自动fallback到 Firecrawl API
  3. 所有Agent通过此统一接口调用，无需关心底层引擎
  
用法：
  # 命令行
  python3.11 tools/web_scraper.py https://example.com
  python3.11 tools/web_scraper.py https://example.com --engine firecrawl
  
  # Python调用
  from tools.web_scraper import scrape
  result = await scrape("https://example.com")
"""
import asyncio
import sys
import os
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path.home() / "Molin-OS" / ".env")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
MIN_CONTENT_LENGTH = 200  # 内容少于200字符则视为失败，触发fallback


async def scrape_with_crawl4ai(url: str) -> str:
    """使用crawl4ai本地爬取（零成本，M1原生）"""
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=url,
                bypass_cache=True,
                remove_overlay_elements=True,
            )
            if result.success and result.markdown:
                return result.markdown
            return ""
    except ImportError:
        print("⚠️  crawl4ai未安装，切换到Firecrawl")
        return ""
    except Exception as e:
        print(f"⚠️  crawl4ai失败: {e}，切换到Firecrawl")
        return ""


def scrape_with_firecrawl_cli(url: str) -> str:
    """使用Firecrawl CLI命令行工具"""
    try:
        result = subprocess.run(
            ["firecrawl", "scrape", url, "--format", "markdown"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
        return ""
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"⚠️  Firecrawl CLI失败: {e}")
        return ""


async def scrape_with_firecrawl_api(url: str) -> str:
    """使用Firecrawl Python SDK（API调用）"""
    if not FIRECRAWL_API_KEY:
        return ""
    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        result = app.scrape_url(url, params={"formats": ["markdown"]})
        return result.get("markdown", "") if isinstance(result, dict) else ""
    except ImportError:
        return scrape_with_firecrawl_cli(url)
    except Exception as e:
        print(f"⚠️  Firecrawl API失败: {e}")
        return ""


async def scrape(url: str, engine: str = "auto", min_length: int = MIN_CONTENT_LENGTH) -> str:
    """
    智能网页抓取，自动选择最优引擎
    Args:
        url: 目标URL
        engine: "auto"（自动）| "crawl4ai"（强制本地）| "firecrawl"（强制API）
        min_length: 内容最小长度，低于此值触发fallback
    Returns:
        str: Markdown格式的网页内容
    """
    content = ""

    if engine in ("auto", "crawl4ai"):
        content = await scrape_with_crawl4ai(url)
        if len(content) >= min_length:
            print(f"✅ crawl4ai抓取成功: {len(content)}字符")
            return content

    if engine in ("auto", "firecrawl") or len(content) < min_length:
        if engine == "auto":
            print("⏳ crawl4ai内容不足，切换到Firecrawl...")
        content = await scrape_with_firecrawl_api(url)
        if len(content) >= min_length:
            print(f"✅ Firecrawl抓取成功: {len(content)}字符")
            return content

    if not content:
        print(f"❌ 所有引擎均失败，URL: {url}")

    return content


async def batch_scrape(urls: list[str], engine: str = "auto") -> dict[str, str]:
    """批量抓取多个URL（并发执行）"""
    tasks = [scrape(url, engine) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {
        url: (result if isinstance(result, str) else "")
        for url, result in zip(urls, results)
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="墨麟OS智能网页抓取工具")
    parser.add_argument("url", help="要抓取的URL")
    parser.add_argument("--engine", choices=["auto", "crawl4ai", "firecrawl"],
                        default="auto", help="指定抓取引擎（默认auto）")
    parser.add_argument("--output", help="输出文件路径（默认打印到终端）")
    args = parser.parse_args()

    result = asyncio.run(scrape(args.url, args.engine))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ 结果已保存到: {args.output}")
    else:
        print(result)
