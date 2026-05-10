"""
墨麟OS — Browser-Use 集成 (⭐50k)
===================================
AI驱动的浏览器自动化，支持视觉+DOM双模式操作。

用法:
    from molib.infra.external.browser_use import execute_browser_task
    result = await execute_browser_task("打开闲鱼搜索iPhone 15")

集成点:
  - Ecommerce Worker: 闲鱼商品自动上架、价格监控
  - BD Worker: LinkedIn/小红书潜在客户信息采集
"""

from __future__ import annotations

import asyncio
from typing import Optional


async def execute_browser_task(
    task: str,
    model: str = "deepseek-chat",
    headless: bool = True,
    max_steps: int = 15,
) -> dict:
    """
    执行自然语言描述的浏览器自动化任务。

    Args:
        task: 自然语言任务描述
        model: 使用的LLM模型
        headless: 是否无头模式
        max_steps: 最大操作步数

    Returns:
        {"task": str, "result": str, "steps": int, "status": str}
    """
    try:
        from browser_use import Agent as BrowserAgent
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=model,
            base_url="https://api.deepseek.com/v1",
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        )

        agent = BrowserAgent(
            task=task,
            llm=llm,
            use_vision=True,
        )

        result = await asyncio.wait_for(
            agent.run(max_steps=max_steps), timeout=300
        )

        return {
            "task": task,
            "result": str(result)[:5000],
            "steps": getattr(result, "number_of_steps", max_steps),
            "status": "success",
            "source": "browser-use",
        }

    except ImportError:
        return {"task": task, "error": "browser-use not installed", "status": "unavailable"}
    except asyncio.TimeoutError:
        return {"task": task, "error": "Browser task timed out (300s)", "status": "timeout"}
    except Exception as e:
        return {"task": task, "error": str(e), "status": "error"}


async def scrape_product_info(platform: str, search_keyword: str) -> dict:
    """
    抓取电商平台商品信息。
    支持: 闲鱼(xianyu)、淘宝(taobao)
    """
    tasks = {
        "xianyu": f"打开闲鱼网页版(2.taobao.com)搜索'{search_keyword}'，提取前5个商品的价格、标题、卖家信息",
        "taobao": f"打开淘宝搜索'{search_keyword}'，提取前5个商品的价格、标题、销量",
    }
    task_desc = tasks.get(platform, tasks["xianyu"])
    return await execute_browser_task(task_desc, max_steps=20)


import os  # noqa: E402 (lazy for browser_use usage)
