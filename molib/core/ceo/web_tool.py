"""网络搜索/抓取工具 — Playwright 无头浏览器搜索 + LLM 联网搜索代理（双引擎）"""

from __future__ import annotations

import re
import os
import asyncio
import subprocess
import httpx
from datetime import date
from typing import Any
from loguru import logger
from molib.core.tools.registry import BaseTool, ToolResult

PLAYWRIGHT_AVAILABLE = False
CHROMIUM_PATH = None

# 查找 Chromium 二进制
for _candidate in [
    os.path.expanduser("~/.cache/ms-playwright/chromium-1148/chrome-linux/chrome"),
    "/root/.cache/ms-playwright/chromium-1148/chrome-linux/chrome",
    "/home/hermes/.cache/ms-playwright/chromium-1148/chrome-linux/chrome",
]:
    if os.path.exists(_candidate):
        CHROMIUM_PATH = _candidate
        break

try:
    from playwright.async_api import async_playwright
    if CHROMIUM_PATH:
        PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass

MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_TOKENS", "10000"))


def _truncate(text: str, model: str = None) -> str:
    """根据模型能力截断文本。DeepSeek 模型使用更大上下文窗口。"""
    if model and model.startswith("deepseek-"):
        limit = max(MAX_CONTEXT_CHARS, 200000)
        return text[:limit]
    return text[:10000]


logger.info(f"WebTool: Playwright={'available' if PLAYWRIGHT_AVAILABLE else 'unavailable'}, "
            f"Chromium={CHROMIUM_PATH or 'not found'}")


class WebTool(BaseTool):
    name = "web_tool"
    description = "网络搜索和网页抓取。search 使用无头浏览器搜索 Bing，fetch 抓取单个网页内容。"
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["fetch", "search"], "description": "操作类型"},
            "url": {"type": "string", "description": "目标 URL（fetch 时需要）"},
            "query": {"type": "string", "description": "搜索关键词（search 时需要）"},
        },
        "required": ["action"],
    }

    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def execute(self, action: str, url: str = None, query: str = None, **kwargs) -> ToolResult:
        try:
            if action == "fetch":
                if not url:
                    return ToolResult(success=False, error="url is required for fetch")
                if PLAYWRIGHT_AVAILABLE:
                    return await self._fetch_via_browser(url)
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(url, headers={"User-Agent": self.UA})
                    resp.raise_for_status()
                    text = _truncate(resp.text)
                    return ToolResult(success=True, output=text, metadata={"url": url, "status": resp.status_code})

            elif action == "search":
                if not query:
                    return ToolResult(success=False, error="query is required for search")
                # L1: Playwright 无头浏览器搜索（绕过验证码）
                if PLAYWRIGHT_AVAILABLE:
                    result = await self._search_via_browser(query)
                    if result.success:
                        return result
                    logger.warning(f"Playwright 浏览器搜索失败: {result.error}")
                # L2: LLM 联网搜索代理
                logger.info(f"回退到 LLM 联网搜索: {query}")
                return await self._search_via_llm(query)

            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    # ── Chrome 进程管理 ──────────────────────────

    async def _launch_chrome_via_cdp(self, timeout: float = 10.0):
        """启动 Chromium 子进程，通过 CDP 连接 Playwright"""
        chrome_proc = await asyncio.create_subprocess_exec(
            CHROMIUM_PATH,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-crashpad",
            "--disable-dev-shm-usage",
            "--remote-debugging-port=0",
            "--user-data-dir=/tmp/chrome-cdp-{}".format(os.getpid()),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 轮询 stderr 获取 DevTools WebSocket URL
        ws_url = None
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            line = await asyncio.wait_for(chrome_proc.stderr.readline(), timeout=timeout)
            if not line:
                break
            decoded = line.decode(errors="replace")
            match = re.search(r"ws://[^\s]+", decoded)
            if match:
                ws_url = match.group(0)
                break

        if not ws_url:
            chrome_proc.kill()
            await chrome_proc.wait()
            raise RuntimeError("无法获取 Chrome DevTools URL")

        # 通过 CDP 连接 Playwright
        playwright = await async_playwright().__aenter__()
        browser = await playwright.chromium.connect_over_cdp(ws_url)
        return playwright, browser, chrome_proc

    # ── Playwright 浏览器抓取 ──────────────────────

    async def _fetch_via_browser(self, url: str) -> ToolResult:
        playwright = None
        chrome_proc = None
        try:
            playwright, browser, chrome_proc = await self._launch_chrome_via_cdp()

            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            pages = context.pages
            page = pages[0] if pages else await context.new_page()

            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            text = await page.inner_text("body")
            html = await page.content()

            return ToolResult(success=True, output=_truncate(text), metadata={
                "url": url, "source": "playwright", "html_length": len(html),
            })
        except Exception as e:
            return ToolResult(success=False, error=f"Playwright fetch 失败: {e}")
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if playwright:
                try:
                    await playwright.__aexit__(None, None, None)
                except Exception:
                    pass
            if chrome_proc:
                try:
                    chrome_proc.kill()
                    await chrome_proc.wait()
                except Exception:
                    pass

    # ── Playwright 浏览器搜索 ──────────────────────

    async def _search_via_browser(self, query: str) -> ToolResult:
        """Playwright 无头浏览器搜索 Bing，绕过验证码"""
        playwright = None
        chrome_proc = None
        try:
            playwright, browser, chrome_proc = await self._launch_chrome_via_cdp()

            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            pages = context.pages
            page = pages[0] if pages else await context.new_page()

            await page.goto(
                f"https://www.bing.com/search?q={query}&setlang=zh-Hans",
                timeout=20000,
                wait_until="domcontentloaded",
            )
            await page.wait_for_timeout(2000)
            content = await page.content()

            results = self._parse_bing(content)
            if not results:
                return ToolResult(success=False, error="Bing 搜索结果解析为空（可能触发验证码）")

            output = "\n".join(f"{i}. {r['title']}\n   {r['snippet']}\n   {r['url']}"
                             for i, r in enumerate(results, 1))
            return ToolResult(success=True, output=output, metadata={
                "query": query, "source": "Bing (Playwright)", "result_count": len(results),
                "date": date.today().isoformat(),
            })
        except Exception as e:
            return ToolResult(success=False, error=f"Playwright 搜索失败: {e}")
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass
            if playwright:
                try:
                    await playwright.__aexit__(None, None, None)
                except Exception:
                    pass
            if chrome_proc:
                try:
                    chrome_proc.kill()
                    await chrome_proc.wait()
                except Exception:
                    pass

    # ── LLM 联网搜索代理 ──────────────────────────

    async def _search_via_llm(self, query: str) -> ToolResult:
        """通过 LLM 联网搜索（阿里云百炼 enable_search）"""
        try:
            from molib.core.ceo.model_router import ModelRouter
            router = ModelRouter()

            system = (
                f"你是一个专业的网络搜索助手。当前日期：{date.today().isoformat()}。"
                f"请根据用户的搜索查询，返回全面、准确、最新的搜索结果摘要。"
                f"请以结构化格式返回：1) 核心摘要 2) 关键发现列表 3) 信息来源说明"
            )
            llm_result = await router.call_async(
                prompt=f"搜索查询：{query}\n请搜索并返回关于此查询的最新、最准确的信息。",
                system=system,
                task_type="research",
                enable_search=True,
            )
            text = llm_result.get("text", "")
            if text:
                return ToolResult(success=True, output=text, metadata={
                    "query": query,
                    "source": f"LLM search via {llm_result.get('model', 'unknown')}",
                    "date": date.today().isoformat(),
                })
            return ToolResult(success=False, error="LLM 搜索未返回结果")
        except Exception as e:
            return ToolResult(success=False, error=f"LLM 搜索失败: {e}")

    # ── HTML 解析 ─────────────────────────────────

    def _parse_bing(self, html: str) -> list:
        results = []
        blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL)
        for block in blocks[:10]:
            title_m = re.search(r'<h2[^>]*><a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.DOTALL)
            snippet_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.DOTALL)
            if title_m:
                title = re.sub(r'<.*?>', '', title_m.group(2)).strip()
                snippet = re.sub(r'<.*?>', '', snippet_m.group(1)).strip() if snippet_m else ""
                if title:
                    results.append({"title": title, "url": title_m.group(1), "snippet": snippet})
        return results
