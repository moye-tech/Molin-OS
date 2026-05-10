"""浏览器自动化工具 — 迁移自 external/hermes-agent/tools/browser_tool.py"""

from __future__ import annotations

import httpx
from typing import Any
from molib.core.tools.registry import BaseTool, ToolResult


class BrowserTool(BaseTool):
    name = "browser_tools"
    description = "浏览器操作。支持 navigate（访问网页）、screenshot（获取页面截图描述）。"
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["navigate"], "description": "操作类型"},
            "url": {"type": "string", "description": "目标 URL"},
        },
        "required": ["action", "url"],
    }

    async def execute(self, action: str, url: str, **kwargs) -> ToolResult:
        try:
            if action == "navigate":
                # 轻量级浏览器：用 httpx 获取页面
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                }
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    text = resp.text[:15000]
                    return ToolResult(
                        success=True,
                        output=text,
                        metadata={"url": url, "status": resp.status_code, "title": self._extract_title(text)},
                    )
            return ToolResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    @staticmethod
    def _extract_title(html: str) -> str:
        import re
        match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else "Unknown"
