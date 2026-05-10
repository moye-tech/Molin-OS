"""
Web Browser External Tool (Playwright / Lightpanda Integration)
为 墨麟Worker 提供无头浏览器能力，支持抓取动态渲染的网页内容和基础的 UI 交互。
"""
from typing import Dict, Any
from loguru import logger
from molib.integrations.adapters.tool_adapter import ExternalToolAdapter

PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


class WebBrowserTool(ExternalToolAdapter):
    def __init__(self):
        super().__init__(tool_name="lightpanda_browser")
        self.register_command("fetch_page", self._fetch_page)
        self.register_command("extract_text", self._extract_text)
        logger.info(f"WebBrowserTool initialized (playwright={'available' if PLAYWRIGHT_AVAILABLE else 'fallback'}).")

    async def _fetch_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """加载网页并返回渲染后的页面信息"""
        url = params.get("url")
        if not url:
            raise ValueError("URL parameter is required")

        timeout_ms = params.get("timeout_ms", 15000)
        logger.debug(f"[Browser] Fetching {url}")

        if PLAYWRIGHT_AVAILABLE:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, timeout=timeout_ms)
                    content = await page.content()
                    title = await page.title()
                    await browser.close()
                return {
                    "url": url,
                    "status": 200,
                    "page_title": title,
                    "html_length": len(content),
                    "html_snippet": content[:2000],
                }
            except Exception as e:
                logger.error(f"[Browser] Playwright error: {e}")
                return {"status": "error", "url": url, "message": str(e)[:300]}

        # 回退：轻量 HTTP 请求
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url)
            return {
                "url": url,
                "status": resp.status_code,
                "page_title": self._extract_title_from_html(resp.text),
                "html_length": len(resp.text),
                "html_snippet": resp.text[:2000],
            }
        except Exception as e:
            logger.error(f"[Browser] HTTP fallback error: {e}")
            return {"status": "error", "url": url, "message": str(e)[:300]}

    async def _extract_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """使用无头浏览器提取页面正文"""
        url = params.get("url")
        selector = params.get("selector", "body")
        logger.debug(f"[Browser] Extracting text from {url}")

        if PLAYWRIGHT_AVAILABLE:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, timeout=15000)
                    text = await page.inner_text(selector)
                    await browser.close()
                return {"url": url, "selector": selector, "extracted_text": text[:3000]}
            except Exception as e:
                return {"status": "error", "url": url, "message": str(e)[:300]}

        # 回退
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url)
            return {"url": url, "selector": selector,
                    "extracted_text": self._extract_title_from_html(resp.text)}
        except Exception as e:
            return {"status": "error", "url": url, "message": str(e)[:300]}

    @staticmethod
    def _extract_title_from_html(html: str) -> str:
        import re
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else "(no title)"


_web_browser_tool = WebBrowserTool()

def get_web_browser() -> WebBrowserTool:
    return _web_browser_tool
