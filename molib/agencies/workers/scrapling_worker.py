"""墨研竞情 · Scrapling Worker — Web抓取、自适应解析、并发爬虫

基于 Scrapling v0.4.7 (D4Vinci/Scrapling) 封装，提供三大核心能力：
  - web_fetch()    单页抓取（支持 Fetcher 同步 / AsyncFetcher 异步）
  - scrape()       自适应解析（基于 Selector 的 CSS/XPath 提取 + adaptive 模式）
  - crawl()        并发爬虫（基于 Spider 框架）

可作为 Molib Research 子公司的辅助 Worker 使用。
"""

from .base import SubsidiaryWorker, Task, WorkerResult

# ── 工具函数（可直接被 CLI 或别的模块调用）────────────────────────────────────


def web_fetch(
    url: str,
    *,
    async_mode: bool = False,
    impersonate: str = "chrome",
    headless: bool = True,
    timeout: int = 30,
    method: str = "GET",
    **kwargs,
) -> dict:
    """单页抓取：返回页面 HTML/text + 元数据。

    底层用 Scrapling 的 Fetcher（静态请求，curl_cffi 浏览器指纹模拟）。
    设置 async_mode=True 用 AsyncFetcher（异步上下文）。

    Returns:
        {"url": ..., "status": ..., "text": ..., "html": ..., "headers": {..}}
    """
    if async_mode:
        import asyncio
        from scrapling import AsyncFetcher

        async def _fetch():
            f = AsyncFetcher()
            f.configure(headless=headless, timeout=timeout)
            resp = await f.get(url, impersonate=impersonate, **kwargs)
            return _resp_to_dict(resp)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_fetch())
        finally:
            loop.close()
    else:
        from scrapling import Fetcher

        f = Fetcher()
        f.configure(headless=headless, timeout=timeout)
        resp = f.get(url, impersonate=impersonate, **kwargs)
        return _resp_to_dict(resp)


def _resp_to_dict(resp) -> dict:
    """将 Scrapling Response 转为可序列化 dict。Scrapling Response 继承自 Selector。"""
    result = {
        "url": resp.url,
        "status": resp.status,
        "reason": getattr(resp, "reason", ""),
        "encoding": resp.encoding if hasattr(resp, "encoding") else "",
    }
    # 提取文本
    try:
        result["text"] = resp.get_all_text(separator="\n", strip=True) or ""
    except Exception:
        result["text"] = str(resp.text) if hasattr(resp, "text") and resp.text else ""
    # 取 title
    try:
        t = resp.find("title")
        result["title"] = t.text_content() if t is not None else ""
    except Exception:
        result["title"] = ""
    # 尝试提取正文摘要 (去除 HTML 标签后的纯文本)
    try:
        for sel in ("article", "main", ".content", "#content", "body"):
            el = resp.find(sel)
            if el is not None:
                result["summary"] = el.get_all_text(separator="\n", strip=True)[:2000]
                break
    except Exception:
        pass
    return result


def scrape(
    html_or_url: str,
    *,
    css: str | None = None,
    xpath: str | None = None,
    adaptive: bool = False,
    extract_all: bool = True,
    **kwargs,
) -> dict:
    """自适应解析：基于 Scrapling Selector 从 HTML 提取结构化数据。

    Args:
        html_or_url: HTML 字符串或 URL（自动检测）
        css: CSS 选择器（可选）
        xpath: XPath 选择器（与 css 二选一，推荐 css）
        adaptive: 是否启用 Scrapling 自适应定位（当页面结构变化时自动修正）
        extract_all: True 返回所有匹配，False 只返回第一个

    Returns:
        {"selector": ..., "matches": [...], "count": N, "adaptive": bool}
    """
    from scrapling import Selector

    # 如果是 URL 而非 HTML 全文，先抓取
    if html_or_url.startswith(("http://", "https://")):
        fetched = web_fetch(html_or_url)
        html_str = fetched.get("html") or fetched.get("text", "")
    else:
        html_str = html_or_url

    sel = Selector(html_str)

    if css:
        elements = sel.css(css, adaptive=adaptive)
    elif xpath:
        elements = sel.xpath(xpath, adaptive=adaptive)
    else:
        # 默认提取全部文本
        text = sel.get_all_text(separator="\n", strip=True)
        return {"selector": "all_text", "matches": [str(text)], "count": 1, "adaptive": False}

    matches = []
    for el in elements:
        item = {
            "text": str(el.text) if el.text else "",
            "html": str(el.html_content) if hasattr(el, "html_content") else "",
            "tag": el.tag if hasattr(el, "tag") else "",
            "attrib": dict(el.attrib) if hasattr(el, "attrib") else {},
        }
        matches.append(item)
        if not extract_all:
            break

    return {
        "selector": css or xpath or "",
        "matches": matches,
        "count": len(matches),
        "adaptive": adaptive,
    }


def crawl(
    start_urls: list[str],
    *,
    allowed_domains: list[str] | None = None,
    max_pages: int = 10,
    concurrent: int = 4,
    extract_css: str | None = None,
    impersonate: str = "chrome",
    obey_robots: bool = False,
    output_file: str | None = None,
) -> dict:
    """并发爬虫：基于 Scrapling Spider 框架进行多页面抓取。

    使用示例：
        result = crawl(["https://example.com"], max_pages=5, extract_css="h2 a")

    Args:
        start_urls: 起始 URL 列表
        allowed_domains: 允许爬取的域名（默认自动从 start_urls 提取）
        max_pages: 最多爬取页数
        concurrent: 并发请求数
        extract_css: 可选，每页提取的 CSS 选择器
        impersonate: 浏览器指纹（默认 chrome）
        obey_robots: 是否遵守 robots.txt
        output_file: 可选，输出 JSON 文件路径

    Returns:
        {"items": [...], "stats": {...}, "paused": bool}
    """
    from scrapling.fetchers import FetcherSession
    from scrapling.spiders import Spider, Request

    if allowed_domains is None:
        from urllib.parse import urlparse

        allowed_domains = {urlparse(u).netloc for u in start_urls}

    class QuickSpider(Spider):
        name = "molib_scrapling_spider"
        start_urls = start_urls
        allowed_domains = set(allowed_domains) if allowed_domains else set()
        robots_txt_obey = obey_robots
        concurrent_requests = concurrent

        def configure_sessions(self, manager):
            manager.add(
                "default",
                FetcherSession(impersonate=impersonate, timeout=30),
                default=True,
            )

        async def parse(self, response):
            page_data = {
                "url": response.url,
                "status": response.status,
                "title": str(response.find("title").text) if response.find("title") else "",
            }
            if extract_css:
                extracted = []
                for el in response.css(extract_css):
                    extracted.append({
                        "text": str(el.text) if el.text else "",
                        "href": el.attrib.get("href", "") if hasattr(el, "attrib") else "",
                    })
                page_data["extracted"] = extracted
            else:
                page_data["text"] = str(response.get_all_text(separator="\n", strip=True))

            yield page_data

    spider = QuickSpider()
    result = spider.start()

    items = list(result.items) if hasattr(result, "items") else []
    stats = result.stats.to_dict() if hasattr(result, "stats") else {}

    if output_file and items:
        result.items.to_json(output_file)

    return {
        "items": items[:max_pages] if max_pages else items,
        "stats": stats,
        "paused": result.paused,
        "total_scraped": len(items),
    }


# ── Worker 类（墨研竞情 · Scrapling）──────────────────────────────────────


class ScraplingWorker(SubsidiaryWorker):
    worker_id = "scrapling"
    worker_name = "墨研Scrapling"
    description = "基于 Scrapling 的 Web 抓取、自适应解析与并发爬虫"
    oneliner = "无感浏览器指纹模拟 · 自适应解析器 · 并发 Spider 爬虫框架"

    async def execute(self, task: Task, context: dict | None = None) -> WorkerResult:
        try:
            action = task.payload.get("action", "fetch")
            url = task.payload.get("url", "")
            html = task.payload.get("html", "")
            css_selector = task.payload.get("css")
            xpath_selector = task.payload.get("xpath")
            adaptive = task.payload.get("adaptive", False)
            async_mode = task.payload.get("async_mode", False)
            impersonate = task.payload.get("impersonate", "chrome")
            start_urls = task.payload.get("start_urls", [url] if url else [])
            max_pages = task.payload.get("max_pages", 10)
            concurrent = task.payload.get("concurrent", 4)
            extract_css = task.payload.get("extract_css")
            allowed_domains = task.payload.get("allowed_domains")
            output_file = task.payload.get("output_file")

            if action == "fetch":
                if not url:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status="error",
                        output={"error": "需要 --url 参数"},
                    )
                output = web_fetch(
                    url,
                    async_mode=async_mode,
                    impersonate=impersonate,
                    **task.payload.get("fetch_kwargs", {}),
                )

            elif action == "scrape":
                if not html and not url:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status="error",
                        output={"error": "需要 --html 或 --url 参数"},
                    )
                source = html if html else url
                output = scrape(
                    source,
                    css=css_selector,
                    xpath=xpath_selector,
                    adaptive=adaptive,
                    extract_all=task.payload.get("extract_all", True),
                )

            elif action == "crawl":
                if not start_urls:
                    return WorkerResult(
                        task_id=task.task_id,
                        worker_id=self.worker_id,
                        status="error",
                        output={"error": "需要 --start-urls 参数（逗号分隔）"},
                    )
                output = crawl(
                    start_urls,
                    allowed_domains=allowed_domains,
                    max_pages=max_pages,
                    concurrent=concurrent,
                    extract_css=extract_css,
                    impersonate=impersonate,
                    obey_robots=task.payload.get("obey_robots", False),
                    output_file=output_file,
                )

            else:
                output = {"error": f"未知操作: {action}，支持: fetch, scrape, crawl"}

            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="success",
                output=output,
            )

        except Exception as e:
            return WorkerResult(
                task_id=task.task_id,
                worker_id=self.worker_id,
                status="error",
                output={"error": str(e)},
            )
