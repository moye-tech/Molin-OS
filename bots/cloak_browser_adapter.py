"""
Cloak Browser Adapter — 反检测浏览器适配器
===========================================
封装 cloakbrowser.launch()，与 browser_agent.py 兼容。

提供与 browser_agent.py 相同的命令接口:
  - search: 搜索查询
  - navigate: 导航到 URL
  - screenshot: 截取页面截图
  - click: 点击页面元素
  - health: 健康检查

附加能力:
  - --stealth 参数: 启用 cloakbrowser 反检测指纹伪装
  - 自动检测 cloakbrowser 可用性，降级到 playwright

Usage:
    python3 -m bots.cloak_browser_adapter search --query "火花思维" --stealth
    python3 -m bots.cloak_browser_adapter navigate --url "https://example.com"
    python3 -m bots.cloak_browser_adapter screenshot --url "https://example.com" --output shot.png
    python3 -m bots.cloak_browser_adapter click --url "https://example.com" --selector ".btn"
    python3 -m bots.cloak_browser_adapter health
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

logger = logging.getLogger("cloak_browser_adapter")

# ── CloakBrowser 可用性检测 ────────────────────────────────────────────

CLOAK_AVAILABLE: bool = False
CLOAK_MODULE: Any = None

try:
    import cloakbrowser
    CLOAK_MODULE = cloakbrowser
    CLOAK_AVAILABLE = True
except ImportError:
    pass

# ── Playwright 备用检测 ─────────────────────────────────────────────────

PLAYWRIGHT_AVAILABLE: bool = False
try:
    import playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

# ── 数据模型 ────────────────────────────────────────────────────────────


@dataclass
class CloakBrowserResult:
    """统一的结构化返回，与 browser_agent.py 的 BrowserAgentResult 兼容。"""

    success: bool = False
    command: str = ""
    url: str = ""
    result: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    total_duration_ms: float = 0.0
    stealth_used: bool = False
    backend: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} {self.command} | {self.url or '-'} | {self.total_duration_ms:.0f}ms | {self.backend}"


# ── 核心适配器 ──────────────────────────────────────────────────────────


class CloakBrowserAdapter:
    """封装 cloakbrowser.launch()，提供简洁的浏览器操作接口。

    与 browser_agent.py 的命令签名兼容:
      - search(query, stealth, ...)
      - navigate(url, stealth, ...)
      - screenshot(url, output, stealth, ...)
      - click(url, selector, stealth, ...)
      - health()
    """

    def __init__(self, stealth: bool = True):
        self.stealth = stealth

        if CLOAK_AVAILABLE:
            self.backend = "cloakbrowser"
            logger.info("CloakBrowser detected — using stealth browser")
        elif PLAYWRIGHT_AVAILABLE:
            self.backend = "playwright"
            logger.info("CloakBrowser not found — falling back to Playwright")
        else:
            self.backend = "simulated"
            logger.warning("No browser library found — running in simulated mode")

    def _build_browser_kwargs(self) -> dict[str, Any]:
        """Build kwargs for browser launch."""
        kwargs: dict[str, Any] = {"headless": True}
        if self.stealth and self.backend == "cloakbrowser":
            kwargs["stealth_args"] = True
            kwargs["humanize"] = True
        return kwargs

    async def _launch_browser(self):
        """Launch browser and return (browser, page)."""
        if self.backend == "cloakbrowser":
            browser = CLOAK_MODULE.launch(**self._build_browser_kwargs())
            context = await browser.new_context()
            page = await context.new_page()
            return browser, page

        elif self.backend == "playwright":
            from playwright.async_api import async_playwright
            p = await async_playwright().start()
            launch_kwargs = {"headless": True}
            if self.stealth:
                launch_kwargs["args"] = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ]
            browser = await p.chromium.launch(**launch_kwargs)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            return browser, page

        # Simulated fallback
        return None, None

    async def search(self, query: str, max_results: int = 5) -> CloakBrowserResult:
        """Execute a web search and extract results."""
        t0 = time.time()
        result = CloakBrowserResult(
            command="search",
            stealth_used=self.stealth,
            backend=self.backend,
        )

        if self.backend != "simulated":
            browser, page = await self._launch_browser()
            try:
                search_url = f"https://www.baidu.com/s?wd={query}"
                logger.info(f"Navigating to search: {search_url}")
                await page.goto(search_url, wait_until="networkidle", timeout=15000)
                await asyncio.sleep(1)

                title = await page.title()
                content = await page.content()
                # Extract visible text snippets
                snippets = await page.eval_on_selector_all(
                    "div.c-abstract, span.content-right_8Zs40",
                    "elements => elements.map(e => e.textContent.trim())",
                )
                results_list = [s for s in snippets if s.strip()][:max_results]

                result.success = True
                result.url = search_url
                result.result = f"Found {len(results_list)} results for '{query}'"
                result.data = {
                    "query": query,
                    "page_title": title,
                    "results_count": len(results_list),
                    "results": results_list,
                }
                logger.info(f"Search completed: {result.result}")
            except Exception as e:
                result.errors.append(str(e))
                result.result = f"Search failed: {e}"
                logger.error(f"Search error: {e}")
            finally:
                if browser:
                    await browser.close()
        else:
            # Simulated mode
            await asyncio.sleep(0.3)
            result.success = True
            result.result = f"[Simulated] Search for '{query}'"
            result.data = {
                "query": query,
                "results_count": 3,
                "results": [
                    f"结果1: {query} - 相关页面描述",
                    f"结果2: {query} - 更多信息",
                    f"结果3: 关于{query}的最新动态",
                ],
            }

        result.total_duration_ms = (time.time() - t0) * 1000
        return result

    async def navigate(self, url: str) -> CloakBrowserResult:
        """Navigate to a URL and extract page info."""
        t0 = time.time()
        result = CloakBrowserResult(
            command="navigate",
            url=url,
            stealth_used=self.stealth,
            backend=self.backend,
        )

        if self.backend != "simulated":
            browser, page = await self._launch_browser()
            try:
                logger.info(f"Navigating to: {url}")
                await page.goto(url, wait_until="networkidle", timeout=20000)
                await asyncio.sleep(0.5)

                title = await page.title()
                content_len = len(await page.content())
                visible_text = await page.evaluate(
                    "document.body.innerText.substring(0, 2000)"
                )

                result.success = True
                result.result = f"Navigated to {url} — {title}"
                result.data = {
                    "url": url,
                    "page_title": title,
                    "content_length": content_len,
                    "visible_text_preview": visible_text[:500],
                }
                logger.info(f"Navigation completed: {title}")
            except Exception as e:
                result.errors.append(str(e))
                result.result = f"Navigation failed: {e}"
            finally:
                if browser:
                    await browser.close()
        else:
            await asyncio.sleep(0.2)
            result.success = True
            result.result = f"[Simulated] Navigated to {url}"
            result.data = {
                "url": url,
                "page_title": f"Simulated - {url.split('//')[-1].split('/')[0]}",
                "content_length": 0,
            }

        result.total_duration_ms = (time.time() - t0) * 1000
        return result

    async def screenshot(self, url: str, output: str = "") -> CloakBrowserResult:
        """Take a screenshot of the given URL."""
        t0 = time.time()
        result = CloakBrowserResult(
            command="screenshot",
            url=url,
            stealth_used=self.stealth,
            backend=self.backend,
        )

        if self.backend != "simulated":
            browser, page = await self._launch_browser()
            try:
                logger.info(f"Taking screenshot of: {url}")
                await page.goto(url, wait_until="networkidle", timeout=20000)
                await asyncio.sleep(1)

                if not output:
                    ts = int(time.time())
                    output = f"cloak_screenshot_{ts}.png"

                out_path = Path(output)
                out_path.parent.mkdir(parents=True, exist_ok=True)

                await page.screenshot(path=str(out_path), full_page=True)
                file_size = out_path.stat().st_size

                result.success = True
                result.result = f"Screenshot saved to {output} ({file_size} bytes)"
                result.data = {
                    "url": url,
                    "screenshot_path": str(out_path.absolute()),
                    "file_size_bytes": file_size,
                }
                logger.info(f"Screenshot saved: {out_path} ({file_size} bytes)")
            except Exception as e:
                result.errors.append(str(e))
                result.result = f"Screenshot failed: {e}"
            finally:
                if browser:
                    await browser.close()
        else:
            await asyncio.sleep(0.3)
            output = output or f"cloak_screenshot_{int(time.time())}.png"
            result.success = True
            result.result = f"[Simulated] Screenshot saved to {output}"
            result.data = {
                "url": url,
                "screenshot_path": output,
                "file_size_bytes": 0,
            }

        result.total_duration_ms = (time.time() - t0) * 1000
        return result

    async def click(self, url: str, selector: str) -> CloakBrowserResult:
        """Navigate to URL and click the specified element."""
        t0 = time.time()
        result = CloakBrowserResult(
            command="click",
            url=url,
            stealth_used=self.stealth,
            backend=self.backend,
        )

        if self.backend != "simulated":
            browser, page = await self._launch_browser()
            try:
                logger.info(f"Navigating to {url} and clicking '{selector}'")
                await page.goto(url, wait_until="networkidle", timeout=20000)
                await asyncio.sleep(0.5)

                # Try to click the selector
                element = await page.query_selector(selector)
                if element:
                    await element.click()
                    await asyncio.sleep(0.5)
                    new_url = page.url
                    result.success = True
                    result.result = f"Clicked '{selector}' on {url}"
                    result.data = {
                        "url": url,
                        "selector": selector,
                        "new_url": new_url,
                        "clicked": True,
                    }
                    logger.info(f"Clicked element '{selector}', navigated to: {new_url}")
                else:
                    result.errors.append(f"Selector '{selector}' not found")
                    result.result = f"Element '{selector}' not found"
                    result.data = {"url": url, "selector": selector, "clicked": False}
            except Exception as e:
                result.errors.append(str(e))
                result.result = f"Click failed: {e}"
            finally:
                if browser:
                    await browser.close()
        else:
            await asyncio.sleep(0.2)
            result.success = True
            result.result = f"[Simulated] Clicked '{selector}' on {url}"
            result.data = {
                "url": url,
                "selector": selector,
                "clicked": True,
            }

        result.total_duration_ms = (time.time() - t0) * 1000
        return result

    def health(self) -> dict[str, Any]:
        """Check availability of cloakbrowser and dependencies."""
        checks: dict[str, Any] = {
            "cloakbrowser": False,
            "playwright": False,
            "browser_launch": False,
            "stealth_available": False,
            "errors": [],
            "adapter": "cloak_browser_adapter",
        }

        # Check cloakbrowser
        if CLOAK_AVAILABLE:
            try:
                checks["cloakbrowser"] = True
                checks["cloakbrowser_version"] = getattr(CLOAK_MODULE, "__version__", "unknown")
                checks["stealth_available"] = True
            except Exception as e:
                checks["errors"].append(f"cloakbrowser error: {e}")

        # Check playwright
        if PLAYWRIGHT_AVAILABLE:
            try:
                import playwright
                checks["playwright"] = True
                checks["playwright_version"] = playwright.__version__
            except Exception as e:
                checks["errors"].append(f"playwright error: {e}")

        # Test browser launch
        if CLOAK_AVAILABLE:
            try:
                browser = CLOAK_MODULE.launch(headless=True)
                if browser:
                    browser.close()
                    checks["browser_launch"] = True
            except Exception as e:
                checks["errors"].append(f"Browser launch failed: {e}")

        all_ok = checks["cloakbrowser"] or checks["playwright"]
        checks["status"] = "available" if all_ok else "simulated_only"
        checks["note"] = (
            "CloakBrowser provides stealth anti-detection. "
            "Without it, falls back to Playwright or simulated mode."
        )
        return checks


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Cloak Browser Adapter — 反检测浏览器适配器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search
    p_search = subparsers.add_parser("search", help="搜索查询")
    p_search.add_argument("--query", "-q", type=str, required=True, help="搜索关键词")
    p_search.add_argument("--max-results", type=int, default=5, help="最大结果数")
    p_search.add_argument("--stealth", action="store_true", help="启用反检测指纹伪装")
    p_search.add_argument("--output", "-o", type=str, default="", help="输出文件路径 (JSON)")

    # navigate
    p_nav = subparsers.add_parser("navigate", help="导航到 URL")
    p_nav.add_argument("--url", "-u", type=str, required=True, help="目标 URL")
    p_nav.add_argument("--stealth", action="store_true", help="启用反检测指纹伪装")
    p_nav.add_argument("--output", "-o", type=str, default="", help="输出文件路径 (JSON)")

    # screenshot
    p_ss = subparsers.add_parser("screenshot", help="截取页面截图")
    p_ss.add_argument("--url", "-u", type=str, required=True, help="目标 URL")
    p_ss.add_argument("--output", "-o", type=str, default="", help="截图保存路径")
    p_ss.add_argument("--stealth", action="store_true", help="启用反检测指纹伪装")

    # click
    p_click = subparsers.add_parser("click", help="点击页面元素")
    p_click.add_argument("--url", "-u", type=str, required=True, help="目标 URL")
    p_click.add_argument("--selector", "-s", type=str, required=True, help="CSS 选择器")
    p_click.add_argument("--stealth", action="store_true", help="启用反检测指纹伪装")
    p_click.add_argument("--output", "-o", type=str, default="", help="输出文件路径 (JSON)")

    # health
    p_health = subparsers.add_parser("health", help="检查系统可用性")
    p_health.add_argument("--output", "-o", type=str, default="", help="输出文件路径 (JSON)")

    # verbose
    parser.add_argument("--verbose", "-v", action="store_true", help="启用详细日志")

    args = parser.parse_args()

    if args.verbose or os.environ.get("CLOAK_DEBUG"):
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if not args.command:
        parser.print_help()
        return

    stealth = getattr(args, "stealth", False)
    adapter = CloakBrowserAdapter(stealth=stealth)

    async def run():
        if args.command == "search":
            result = await adapter.search(args.query, args.max_results)
        elif args.command == "navigate":
            result = await adapter.navigate(args.url)
        elif args.command == "screenshot":
            result = await adapter.screenshot(args.url, args.output)
        elif args.command == "click":
            result = await adapter.click(args.url, args.selector)
        elif args.command == "health":
            checks = adapter.health()
            print(json.dumps(checks, ensure_ascii=False, indent=2))
            if args.output:
                Path(args.output).write_text(
                    json.dumps(checks, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            sys.exit(0 if checks.get("status") != "error" else 1)
            return
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        # Output result
        output = result.to_dict()
        print(json.dumps(output, ensure_ascii=False, indent=2))

        if args.output:
            Path(args.output).write_text(
                json.dumps(output, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        sys.exit(0 if result.success else 1)

    asyncio.run(run())


if __name__ == "__main__":
    main()
