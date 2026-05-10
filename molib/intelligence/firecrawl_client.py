"""
墨麟OS — Firecrawl 网页采集客户端
墨研竞情核心模块。通过 python -m molib intel <command> 调用。

SDK: firecrawl-py v4.25.2 | Docs: https://docs.firecrawl.dev
"""
import json
import os
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from firecrawl import Firecrawl
except ImportError:
    print("❌ firecrawl-py 未安装。运行: pip install firecrawl-py", file=sys.stderr)
    sys.exit(1)


def _get_client() -> Firecrawl:
    """获取 Firecrawl 客户端，自动读取环境变量。"""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    api_url = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev")
    if not api_key:
        # 尝试从 .env 文件读取
        env_file = Path.home() / ".hermes" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("FIRECRAWL_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not api_key:
        raise ValueError(
            "❌ FIRECRAWL_API_KEY 未设置。\n"
            "获取免费 Key: https://firecrawl.dev/\n"
            "设置: echo 'FIRECRAWL_API_KEY=fc-xxx' >> ~/.hermes/.env"
        )
    return Firecrawl(api_key=api_key, api_url=api_url)


# ── 公共 API ──

def scrape(url: str, formats: List[str] = None, only_main: bool = True,
           wait_for: int = 0, mobile: bool = False,
           proxy: str = None, block_ads: bool = False,
           json_output: bool = True) -> Dict[str, Any]:
    """
    抓取单个 URL。
    
    用法: python -m molib intel scrape --url "https://example.com"
    """
    fc = _get_client()
    opts = {"formats": formats or ["markdown", "html"], "only_main_content": only_main}
    if wait_for:
        opts["wait_for"] = wait_for
    if mobile:
        opts["mobile"] = True
    if proxy:
        opts["proxy"] = proxy
    if block_ads:
        opts["block_ads"] = True

    result = fc.v1.scrape_url(url, **opts)
    out = {
        "url": url,
        "title": getattr(result.metadata, "title", "") if result.metadata else "",
        "markdown": result.markdown[:5000] if result.markdown else "",
        "html_length": len(result.html or ""),
        "status": result.metadata.status_code if result.metadata else None,
    }
    if json_output:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(result.markdown or "")
    return out


def crawl(url: str, max_pages: int = 50, max_depth: int = 3,
          exclude_paths: List[str] = None, include_paths: List[str] = None,
          wait: bool = True) -> Dict[str, Any]:
    """
    爬取整个网站。

    用法: python -m molib intel crawl --url "https://docs.example.com" --max-pages 50
    """
    fc = _get_client()
    opts = {
        "max_pages": max_pages,
        "max_depth": max_depth,
        "scrape_options": {"formats": ["markdown"], "only_main_content": True},
    }
    if exclude_paths:
        opts["exclude_paths"] = exclude_paths
    if include_paths:
        opts["include_paths"] = include_paths

    job = fc.v1.crawl_url(url, **opts)
    print(json.dumps({"job_id": job.job_id, "url": url, "max_pages": max_pages}, ensure_ascii=False))

    if wait:
        print(f"⏳ 等待爬取完成... (Job: {job.job_id})", file=sys.stderr)
        result = fc.v1.wait_for_crawl(job.job_id, poll_interval=10)
        pages = []
        for p in result.pages:
            pages.append({
                "url": p.url,
                "title": getattr(p, "title", ""),
                "markdown_preview": (p.markdown or "")[:500],
            })
        out = {
            "job_id": job.job_id,
            "total_pages": len(pages),
            "pages": pages[:20],  # 仅返回前20页预览
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        _save_relay("crawl", out)
        return out
    return {"job_id": job.job_id, "status": "started"}


def crawl_status(job_id: str) -> Dict[str, Any]:
    """查询爬取任务状态。"""
    fc = _get_client()
    status = fc.v1.check_crawl_status(job_id)
    return {"job_id": job_id, "status": str(status)}


def search(query: str, limit: int = 10, country: str = None,
           lang: str = None, time_range: str = None,
           scrape_results: bool = False) -> List[Dict[str, Any]]:
    """
    搜索网络内容。

    用法: python -m molib intel search --query "AI agent trends 2026" --limit 10
    """
    fc = _get_client()
    opts = {"limit": limit}
    if country:
        opts["search_options"] = opts.get("search_options", {})
        opts["search_options"]["country"] = country
    if lang:
        opts.setdefault("search_options", {})["lang"] = lang
    if time_range:
        opts.setdefault("search_options", {})["tbs"] = time_range
    if scrape_results:
        opts["scrape_options"] = {"formats": ["markdown"], "only_main_content": True}

    results = fc.v1.search(query, **opts)
    items = []
    for r in results:
        items.append({
            "title": getattr(r, "title", ""),
            "url": getattr(r, "url", ""),
            "description": getattr(r, "description", ""),
            "markdown": (getattr(r, "markdown", "") or "")[:1000],
        })
    out = {"query": query, "total": len(items), "results": items}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    _save_relay("search", out)
    return items


def batch_scrape(urls: List[str], max_concurrency: int = 5) -> Dict[str, Any]:
    """批量抓取多个 URL。"""
    fc = _get_client()
    batch = fc.v1.async_batch_scrape_urls(
        urls,
        formats=["markdown"],
        max_concurrency=max_concurrency,
        only_main_content=True
    )
    print(f"Batch ID: {batch.batch_id}, URLs: {len(urls)}", file=sys.stderr)
    results = fc.v1.get_batch_scrape_results(batch.batch_id)
    items = []
    for r in results:
        items.append({
            "url": r.url,
            "markdown": (r.markdown or "")[:1000],
        })
    out = {"batch_id": batch.batch_id, "total": len(items), "results": items}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return out


def deep_research(topic: str, max_depth: int = 3, max_urls: int = 50) -> Dict[str, Any]:
    """深度研究：多轮搜索 + 综合分析。"""
    fc = _get_client()
    result = fc.v1.deep_research(topic, max_depth=max_depth, max_urls=max_urls)
    out = {
        "topic": topic,
        "summary": getattr(result, "summary", ""),
        "sources": getattr(result, "sources", []),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    _save_relay("research", out)
    return out


def map_site(url: str) -> List[str]:
    """获取网站 URL 地图。"""
    fc = _get_client()
    sitemap = fc.v1.map_url(url)
    urls = list(sitemap.urls)
    print(json.dumps({"url": url, "total_urls": len(urls)}, ensure_ascii=False))
    return urls


# ── 辅助 ──

def _save_relay(kind: str, data: Dict[str, Any]) -> None:
    """保存采集结果到 relay/ 目录供下游消费。"""
    relay_dir = Path.home() / ".hermes" / "molin" / "relay"
    relay_dir.mkdir(parents=True, exist_ok=True)
    output_file = relay_dir / f"firecrawl_{kind}_{_today()}.json"
    output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"📁 已保存: {output_file}", file=sys.stderr)


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


# ── CLI ──

def _cli():
    """命令行入口: python -m molib intel firecrawl <command>"""
    import argparse
    parser = argparse.ArgumentParser(description="墨麟OS Firecrawl 采集客户端")
    sub = parser.add_subparsers(dest="command")

    # scrape
    p = sub.add_parser("scrape", help="抓取单个URL")
    p.add_argument("--url", required=True)
    p.add_argument("--formats", nargs="+", default=["markdown"])
    p.add_argument("--only-main", type=bool, default=True)
    p.add_argument("--wait-for", type=int, default=0)
    p.add_argument("--mobile", action="store_true")
    p.add_argument("--proxy")
    p.add_argument("--no-json", dest="json_output", action="store_false")

    # crawl
    p = sub.add_parser("crawl", help="爬取全站")
    p.add_argument("--url", required=True)
    p.add_argument("--max-pages", type=int, default=50)
    p.add_argument("--max-depth", type=int, default=3)
    p.add_argument("--no-wait", dest="wait", action="store_false")

    # search
    p = sub.add_parser("search", help="搜索")
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--country")
    p.add_argument("--lang")

    # batch
    p = sub.add_parser("batch", help="批量抓取")
    p.add_argument("--urls", nargs="+", required=True)

    # research
    p = sub.add_parser("research", help="深度研究")
    p.add_argument("--topic", required=True)
    p.add_argument("--max-depth", type=int, default=3)

    # map
    p = sub.add_parser("map", help="站点地图")
    p.add_argument("--url", required=True)

    # status
    p = sub.add_parser("status", help="查询爬取状态")
    p.add_argument("--job-id", required=True)

    args = parser.parse_args()
    cmd = args.command
    if cmd == "scrape":
        scrape(args.url, formats=args.formats, only_main=args.only_main,
               wait_for=args.wait_for, mobile=args.mobile, proxy=args.proxy,
               json_output=args.json_output)
    elif cmd == "crawl":
        crawl(args.url, max_pages=args.max_pages, max_depth=args.max_depth, wait=args.wait)
    elif cmd == "search":
        search(args.query, limit=args.limit, country=args.country, lang=args.lang)
    elif cmd == "batch":
        batch_scrape(args.urls)
    elif cmd == "research":
        deep_research(args.topic, max_depth=args.max_depth)
    elif cmd == "map":
        map_site(args.url)
    elif cmd == "status":
        print(json.dumps(crawl_status(args.job_id), ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
