#!/usr/bin/env python3
"""
browser-use Hermes Agent 集成模块

将 browser-use 封装为同步调用的工具函数，供 Hermes Agent 的 tool registry 使用。
支持通过 DeepSeek API（原生或 OpenRouter）驱动浏览器自动化。

用法:
    python browser_agent.py "搜索 Hacker News 今日热门"
    python browser_agent.py "在 GitHub 搜索 browser-use 仓库" --max-steps 15 --save screenshot.png
    python browser_agent.py "查看我的 Gmail 收件箱" --headless

依赖:
    pip install browser-use (v0.12.6+)
    playwright install chromium
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ── 路径锚点 ──────────────────────────────────────────
_HERMES_HOME = Path.home() / ".hermes"
_HERMES_ENV = _HERMES_HOME / ".env"

# ── 日志 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("browser_agent")

# ── 加载环境变量 ──────────────────────────────────────
def _load_env() -> None:
    """加载 Hermes .env 到 os.environ。"""
    try:
        from dotenv import load_dotenv
        if _HERMES_ENV.exists():
            load_dotenv(str(_HERMES_ENV), override=False)
            logger.info("Loaded env from %s", _HERMES_ENV)
    except ImportError:
        logger.warning("python-dotenv not installed; relying on existing env vars")


_load_env()


# ── LLM 工厂 ──────────────────────────────────────────
def _build_llm() -> Any:
    """
    构造 browser-use 可用的 LLM 实例。

    优先级:
      1. OPENROUTER_API_KEY → ChatOpenAI(base_url=openrouter.ai/api/v1)
      2. DEEPSEEK_API_KEY   → ChatDeepSeek (原生 DeepSeek API)
      3. 两种 key 都缺失 → 抛出 ValueError

    Hermes OS 主要走 DeepSeek 原生 API（DEEPSEEK_API_KEY），
    但 OpenRouter 路径保留以支持统一路由的场景。
    """
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    deepseek_key_simple = os.environ.get("DEEPSEEK_KEY", "")

    # OpenRouter 优先（如果已配置）
    if openrouter_key and openrouter_key.strip() and openrouter_key != "***":
        from browser_use.llm.openai.chat import ChatOpenAI  # noqa: PLC0415

        logger.info("Using OpenRouter → %s", "deepseek-chat")
        return ChatOpenAI(
            model="deepseek-chat",
            api_key=openrouter_key.strip(),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.0,
        )

    # DeepSeek 原生 API
    api_key = deepseek_key or deepseek_key_simple
    if api_key and api_key.strip() and api_key != "***":
        from browser_use.llm.deepseek.chat import ChatDeepSeek  # noqa: PLC0415

        base_url = os.environ.get(
            "DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"
        )
        logger.info("Using DeepSeek native → %s", base_url)
        return ChatDeepSeek(
            model="deepseek-chat",
            api_key=api_key.strip(),
            base_url=base_url,
            temperature=0.0,
        )

    raise ValueError(
        "No API key found. Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY in "
        f"{_HERMES_ENV}"
    )


# ── 结果数据模型 ──────────────────────────────────────
@dataclass
class BrowserAgentResult:
    """browser_agent() 的结构化返回。"""

    success: bool = False
    """任务是否成功完成（is_successful()）。"""

    task: str = ""
    """原始任务描述。"""

    final_result: str = ""
    """Agent 的最终文本回答。"""

    extracted_content: list[str] = field(default_factory=list)
    """每一步提取的内容列表。"""

    steps: int = 0
    """实际执行的操作步数。"""

    errors: list[str] = field(default_factory=list)
    """执行中出现的错误消息列表。"""

    urls: list[str] = field(default_factory=list)
    """访问过的 URL 列表。"""

    total_duration_sec: float = 0.0
    """总耗时（秒）。"""

    action_names: list[str] = field(default_factory=list)
    """所有执行过的动作名称。"""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def summary(self) -> str:
        """人类可读的单行摘要。"""
        status = "✅" if self.success else "❌"
        return (
            f"{status} browser_agent | "
            f'"{self.task[:60]}{"..." if len(self.task) > 60 else ""}" | '
            f"{self.steps} steps, {self.total_duration_sec:.1f}s | "
            f'{self.urls[0] if self.urls else "-"}'
        )


# ── 核心函数 ──────────────────────────────────────────
def browser_agent(
    task: str,
    max_steps: int = 20,
    headless: bool = True,
    use_vision: bool = True,
    model: str | None = None,
    save_conversation: str | None = None,
    proxy: str | None = None,
    llm: Any = None,
) -> BrowserAgentResult:
    """
    同步封装：运行 browser-use Agent 完成浏览器自动化任务。

    Parameters
    ----------
    task : str
        自然语言任务描述（必填）。
    max_steps : int
        最大操作步数（默认 20）。
    headless : bool
        是否使用无头浏览器（默认 True）。
    use_vision : bool | str
        是否启用视觉理解（默认 True，可选 "auto"）。
    model : str | None
        覆盖 LLM 模型名称（如 "deepseek-chat"）。
    save_conversation : str | None
        保存完整对话历史到路径。
    proxy : str | None
        浏览器代理地址（如 "http://127.0.0.1:7890"）。
    llm : Any | None
        外部传入的 LLM 实例（若提供则跳过自动构建）。

    Returns
    -------
    BrowserAgentResult
    """
    result = BrowserAgentResult(task=task)

    async def _run() -> BrowserAgentResult:
        nonlocal result

        # 1. 构建 LLM
        _llm = llm if llm is not None else _build_llm()
        if model is not None:
            _llm.model = model  # type: ignore[union-attr]

        # 2. 配置浏览器
        browser_kwargs: dict[str, Any] = {}
        if not headless:
            browser_kwargs["headless"] = False
        if proxy:
            browser_kwargs["proxy"] = {"server": proxy}

        # 3. 构造 Agent
        from browser_use import Agent  # noqa: PLC0415

        agent = Agent(
            task=task,
            llm=_llm,
            use_vision=use_vision,
            save_conversation_path=save_conversation,
            generate_gif=bool(save_conversation),
            max_failures=3,
            max_actions_per_step=5,
        )

        # 4. 执行
        logger.info("Starting browser agent: %s", task[:80])
        history = await agent.run(max_steps=max_steps)

        # 5. 提取结果
        result.success = history.is_successful()
        result.final_result = history.final_result() or ""
        result.extracted_content = history.extracted_content()
        result.steps = history.number_of_steps()
        result.errors = [e for e in history.errors() if e]
        result.urls = history.urls()
        if history.total_duration_seconds():
            result.total_duration_sec = history.total_duration_seconds()
        result.action_names = history.action_names()

        logger.info(result.summary())
        return result

    return asyncio.run(_run())


# ── CLI 入口 ──────────────────────────────────────────
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="browser-use Hermes Agent 集成 — 浏览器自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s \"搜索今日 HN 头条\"\n"
            "  %(prog)s \"登录 GitHub 查看 PR\" --max-steps 15 --no-headless\n"
            "  %(prog)s \"提取知乎热榜\" --save conversation.json --json\n"
        ),
    )
    parser.add_argument("task", type=str, help="浏览器自动化任务描述")
    parser.add_argument(
        "--max-steps", type=int, default=20, help="最大操作步数（默认 20）"
    )
    parser.add_argument(
        "--headless", action="store_true", default=True,
        help="启用无头模式（默认）",
    )
    parser.add_argument(
        "--no-headless", action="store_false", dest="headless",
        help="显示浏览器界面",
    )
    parser.add_argument(
        "--save", type=str, default=None,
        help="保存对话/截图到路径",
    )
    parser.add_argument(
        "--json", action="store_true", default=False,
        help="以 JSON 格式输出结果",
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="覆盖 LLM 模型名称",
    )
    parser.add_argument(
        "--proxy", type=str, default=None,
        help="浏览器代理地址",
    )
    parser.add_argument(
        "--no-vision", action="store_true", default=False,
        help="禁用视觉理解（节省 tokens）",
    )
    return parser.parse_args(argv)


def main() -> int:
    """CLI 入口。"""
    args = _parse_args()
    result = browser_agent(
        task=args.task,
        max_steps=args.max_steps,
        headless=args.headless,
        use_vision=not args.no_vision,
        model=args.model,
        save_conversation=args.save,
        proxy=args.proxy,
    )
    if args.json:
        print(result.to_json())
    else:
        print("\n" + "=" * 60)
        print(f"  Task: {result.task}")
        print(f"  Status: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"  Steps: {result.steps}")
        print(f"  Duration: {result.total_duration_sec:.1f}s")
        print(f"  URLs: {len(result.urls)} visited")
        if result.final_result:
            print(f"\n  Final Result:\n    {result.final_result[:300]}")
        if result.errors:
            print(f"\n  Errors ({len(result.errors)}):")
            for e in result.errors[:5]:
                print(f"    - {e}")
        print("=" * 60)
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
