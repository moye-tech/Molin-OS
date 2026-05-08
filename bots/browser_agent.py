#!/usr/bin/env python3
"""
browser-use Hermes Agent 集成模块

封装 browser-use (v0.12.6+) 为 CLI 子命令和 Python 工具函数。
支持: navigate / search / extract / screenshot / click

用法:
    # 子命令模式（推荐）
    python -m bots.browser_agent navigate --url "https://example.com" --task "点击第一个按钮"
    python -m bots.browser_agent search --query "browser-use python" --max-results 5
    python -m bots.browser_agent extract --url "https://example.com" --fields "标题,价格"
    python -m bots.browser_agent screenshot --url "https://example.com" --output ./page.png
    python -m bots.browser_agent click --url "https://example.com" --selector "#submit"

    # 旧版自由任务模式（向后兼容）
    python -m bots.browser_agent "搜索 Hacker News 今日热门" --max-steps 15

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
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

# ── 路径锚点 ──────────────────────────────────────────
_HERMES_HOME = Path.home() / ".hermes"
_HERMES_ENV = _HERMES_HOME / ".env"
_WORKSPACE_ENV = Path.home() / "hermes-os" / ".env"

# ── 日志 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("browser_agent")


# ── 加载环境变量 ──────────────────────────────────────
def load_env() -> None:
    """从 ~/.hermes/.env 或 ~/hermes-os/.env 加载配置到 os.environ。"""
    env_paths = [_HERMES_ENV, _WORKSPACE_ENV]
    loaded = False
    try:
        from dotenv import load_dotenv  # noqa: PLC0415

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(str(env_path), override=False)
                logger.info("Loaded env from %s", env_path)
                loaded = True
    except ImportError:
        pass

    if not loaded:
        logger.warning("No .env file found; falling back to existing env vars")


def get_api_key() -> tuple[str, str, str]:
    """
    读取 API key 和 base_url。

    Returns:
        (api_key, base_url, provider_name)
        如果 key 不存在或为占位符 (***) 则返回空字符串。
    """
    # 1) OpenRouter 优先
    or_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    or_base = os.environ.get("OPENROUTER_BASE_URL", "").strip()
    if or_key and or_key != "***":
        base = or_base or "https://openrouter.ai/api/v1"
        return or_key, base, "openrouter"

    # 2) DeepSeek
    ds_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not ds_key or ds_key == "***":
        ds_key = os.environ.get("DEEPSEEK_KEY", "").strip()
    ds_base = os.environ.get("DEEPSEEK_BASE_URL", "").strip()
    if ds_key and ds_key != "***":
        base = ds_base or "https://api.deepseek.com/v1"
        return ds_key, base, "deepseek"

    # 3) 通用 API_KEY
    gen_key = os.environ.get("API_KEY", "").strip()
    gen_base = os.environ.get("API_BASE_URL", "").strip()
    if gen_key and gen_key != "***":
        base = gen_base or "https://api.deepseek.com/v1"
        return gen_key, base, "generic"

    return "", "", ""


# ── 加载 env ──────────────────────────────────────────
load_env()


# ── LLM 工厂 ──────────────────────────────────────────
def build_llm() -> Any:
    """
    构造 browser-use 可用的 LLM 实例。

    Returns:
        ChatDeepSeek 实例

    Raises:
        ValueError: 未找到有效的 API key
    """
    api_key, base_url, provider = get_api_key()
    if not api_key:
        raise ValueError(
            "No valid API key found. Set one of these in .env:\n"
            "  OPENROUTER_API_KEY=sk-...\n"
            "  DEEPSEEK_API_KEY=sk-...\n"
            "  API_KEY=sk-..."
        )

    from browser_use.llm.deepseek.chat import ChatDeepSeek  # noqa: PLC0415

    logger.info("Using LLM provider=%s base_url=%s", provider, base_url)
    return ChatDeepSeek(
        model="deepseek-chat",
        api_key=api_key,
        base_url=base_url,
        temperature=0.0,
    )


# ── Browser 工厂 ──────────────────────────────────────
import atexit
import subprocess
import urllib.request
import json as _json
import time
from pathlib import Path

# 全局 Chromium 进程/端口管理
_CHROME_PROC: Any = None
_CHROME_PORT: int | None = None


def _find_chrome_path() -> Path:
    """找到 playwright 安装的 Chromium 可执行文件。"""
    candidates = [
        Path.home() / ".cache/ms-playwright/chromium-1217/chrome-linux64/chrome",
        Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome",
        Path("/usr/bin/chromium"),
        Path("/usr/bin/chromium-browser"),
        Path("/usr/bin/google-chrome"),
    ]
    for c in candidates:
        if c.exists():
            return c
    # glob 匹配版本号
    import glob
    matches = sorted(glob.glob(str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome")))
    if matches:
        return Path(matches[-1])
    raise FileNotFoundError("未找到 Chromium 可执行文件。运行: playwright install chromium")


def _start_chrome_cdp(headless: bool = True, port: int = 0) -> tuple[subprocess.Popen, int, str]:
    """手动启动 Chromium 带 --remote-debugging-port，返回 (进程, 端口, CDP WebSocket URL)。"""
    global _CHROME_PROC, _CHROME_PORT
    
    chrome_path = _find_chrome_path()
    actual_port = _CHROME_PORT or (port if port else 9222)
    
    # 如果已有运行的 chrome 进程，直接复用
    if _CHROME_PROC and _CHROME_PROC.poll() is None:
        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{actual_port}/json/version", timeout=3)
            data = _json.loads(resp.read().decode())
            ws_url = data.get("webSocketDebuggerUrl", "")
            if ws_url:
                logger.info("♻️ 复用已有 Chrome 进程: port=%d", actual_port)
                return _CHROME_PROC, actual_port, ws_url
        except Exception:
            logger.info("旧 Chrome 进程不可用，重新启动")
            _kill_chrome()
    
    cmd = [
        str(chrome_path),
        "--headless" if headless else "",
        f"--remote-debugging-port={actual_port}",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-setuid-sandbox",
        "--no-first-run",
        "--disable-extensions",
    ]
    cmd = [c for c in cmd if c]  # 去掉空字符串
    
    logger.info("🚀 启动 Chrome (CDP port=%d): %s", actual_port, chrome_path.name)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    # 等待 CDP 就绪
    for attempt in range(20):
        time.sleep(0.5)
        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{actual_port}/json/version", timeout=3)
            data = _json.loads(resp.read().decode())
            ws_url = data.get("webSocketDebuggerUrl", "")
            if ws_url:
                _CHROME_PROC = proc
                _CHROME_PORT = actual_port
                atexit.register(_kill_chrome)
                logger.info("✅ Chrome 就绪: %s", ws_url[:60])
                return proc, actual_port, ws_url
        except Exception:
            continue
    
    proc.kill()
    raise RuntimeError(f"Chrome 启动超时 (port={actual_port})")


def _kill_chrome():
    """清理 Chrome 进程。"""
    global _CHROME_PROC
    if _CHROME_PROC and _CHROME_PROC.poll() is None:
        try:
            _CHROME_PROC.terminate()
            _CHROME_PROC.wait(timeout=5)
        except Exception:
            _CHROME_PROC.kill()
        _CHROME_PROC = None


def build_browser(headless: bool = True, proxy: str | None = None) -> Any:
    """构造 browser-use BrowserSession 实例。
    
    绕过 browser-use v0.12.6 BrowserSession.start() 事件总线超时bug。
    方案：手动启动 Chromium + --remote-debugging-port → 获取 CDP URL → 传入 BrowserSession。
    BrowserSession 收到 cdp_url 后直接 connect()，不走内部 LaunchEvent → Watchdog 路径。
    """
    _, _, cdp_url = _start_chrome_cdp(headless=headless)
    logger.info("🔗 连接 CDP: %s", cdp_url[:60])
    
    from browser_use.browser.session import BrowserSession  # type: ignore  # noqa: PLC0415
    
    kwargs: dict[str, Any] = {
        "cdp_url": cdp_url,
        "headless": headless,
    }
    if proxy:
        kwargs["proxy"] = {"server": proxy}
    session = BrowserSession(**kwargs)
    return session


# ── 结果数据模型 ──────────────────────────────────────
@dataclass
class BrowserAgentResult:
    """browser_agent() 的结构化返回。"""

    success: bool = False
    task: str = ""
    final_result: str = ""
    extracted_content: list[str] = field(default_factory=list)
    steps: int = 0
    errors: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    total_duration_sec: float = 0.0
    action_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def summary(self) -> str:
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
    browser: Any = None,
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
    use_vision : bool
        是否启用视觉理解（默认 True）。
    model : str | None
        覆盖 LLM 模型名称。
    save_conversation : str | None
        保存完整对话历史到路径。
    proxy : str | None
        浏览器代理地址。
    llm : Any | None
        外部传入的 LLM 实例（若提供则跳过自动构建）。
    browser : Any | None
        外部传入的 Browser 实例（若提供则跳过自动构建）。

    Returns
    -------
    BrowserAgentResult
    """
    result = BrowserAgentResult(task=task)

    async def _run() -> BrowserAgentResult:
        nonlocal result

        # 1. 构建 LLM
        _llm = llm if llm is not None else build_llm()
        if model is not None:
            _llm.model = model  # type: ignore[union-attr]

        # 2. 构造 Agent
        from browser_use import Agent  # noqa: PLC0415

        agent_kwargs: dict[str, Any] = {
            "task": task,
            "llm": _llm,
            "use_vision": use_vision,
            "max_failures": 3,
            "max_actions_per_step": 5,
        }
        if save_conversation:
            agent_kwargs["save_conversation_path"] = save_conversation
            agent_kwargs["generate_gif"] = True
        if browser is not None:
            # browser 现在是 BrowserSession 实例（通过 CDP 连接）
            agent_kwargs["browser_session"] = browser

        agent = Agent(**agent_kwargs)

        # 3. 执行
        logger.info("Starting browser agent: %s", task[:80])
        history = await agent.run(max_steps=max_steps)

        # 4. 提取结果
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


# ── 快捷子命令函数 ────────────────────────────────────

def cmd_navigate(args: argparse.Namespace) -> BrowserAgentResult:
    """导航到 URL 并执行可选任务。"""
    task = args.task or f"Navigate to {args.url} and describe the page"
    return browser_agent(
        task=task,
        max_steps=args.max_steps,
        headless=args.headless,
        use_vision=not args.no_vision,
        model=args.model,
        proxy=args.proxy,
    )


def cmd_search(args: argparse.Namespace) -> BrowserAgentResult:
    """在搜索引擎中搜索并提取结果。"""
    task = (
        f"Search for '{args.query}' on a search engine and extract "
        f"{args.max_results} results with titles and links"
    )
    return browser_agent(
        task=task,
        max_steps=args.max_steps,
        headless=args.headless,
        use_vision=not args.no_vision,
        model=args.model,
        proxy=args.proxy,
    )


def cmd_extract(args: argparse.Namespace) -> BrowserAgentResult:
    """从页面提取结构化数据。"""
    fields_str = args.fields or "all visible text"
    task = (
        f"Navigate to {args.url}, extract the following fields: {fields_str}. "
        f"Return the extracted data in a structured format."
    )
    return browser_agent(
        task=task,
        max_steps=args.max_steps,
        headless=args.headless,
        use_vision=not args.no_vision,
        model=args.model,
        proxy=args.proxy,
    )


def cmd_screenshot(args: argparse.Namespace) -> BrowserAgentResult:
    """截取页面截图。"""
    from browser_use import Browser  # noqa: PLC0415

    async def _screenshot() -> BrowserAgentResult:
        browser = Browser(headless=args.headless)
        try:
            page = await browser.get_current_page()
            await browser.navigate_to(args.url)
            await asyncio.sleep(2)  # wait for page load
            screenshot_data = await browser.take_screenshot()
            output = args.output or f"screenshot_{int(time.time())}.png"
            if isinstance(screenshot_data, bytes):
                Path(output).write_bytes(screenshot_data)
            elif isinstance(screenshot_data, str):
                import base64
                data = base64.b64decode(screenshot_data)
                Path(output).write_bytes(data)
            else:
                output = str(screenshot_data)
            result = BrowserAgentResult(
                success=True,
                task=f"Screenshot of {args.url}",
                final_result=f"Screenshot saved to {output}",
                urls=[args.url],
            )
            return result
        finally:
            await browser.close()

    return asyncio.run(_screenshot())


def cmd_click(args: argparse.Namespace) -> BrowserAgentResult:
    """在页面上点击指定元素。"""
    task = (
        f"Navigate to {args.url}. Find and click the element matching "
        f"'{args.selector}' or described as '{args.task or args.selector}'. "
        f"Then describe what happened."
    )
    return browser_agent(
        task=task,
        max_steps=args.max_steps,
        headless=args.headless,
        use_vision=not args.no_vision,
        model=args.model,
        proxy=args.proxy,
    )


def cmd_health(args: argparse.Namespace | None = None) -> dict[str, Any]:
    """检查 browser-use 和 playwright 是否可正常使用。"""
    checks: dict[str, Any] = {
        "browser_use": False,
        "playwright": False,
        "browser_launch": False,
        "api_key_configured": False,
        "errors": [],
    }

    # 1) 检查 browser-use import
    try:
        from browser_use import Agent, Browser  # noqa: PLC0415, F811
        from browser_use.llm.deepseek.chat import ChatDeepSeek  # noqa: PLC0415, F401

        checks["browser_use"] = True
        try:
            from importlib.metadata import version
            checks["browser_use_version"] = version("browser-use")
        except Exception:
            checks["browser_use_version"] = "unknown"
    except Exception as e:
        checks["errors"].append(f"browser-use import failed: {e}")

    # 2) 检查 playwright
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        checks["playwright"] = True
    except Exception as e:
        checks["errors"].append(f"playwright import failed: {e}")

    # 3) 尝试启动浏览器（无头）
    if checks["playwright"]:
        try:
            from playwright.sync_api import sync_playwright  # noqa: PLC0415

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto("about:blank")
                title = page.title()
                browser.close()
            checks["browser_launch"] = True
            checks["browser_info"] = f"Chromium launched OK, title='{title}'"
        except Exception as e:
            checks["errors"].append(f"browser launch failed: {e}")

    # 4) 检查 API key
    api_key, base_url, provider = get_api_key()
    if api_key:
        checks["api_key_configured"] = True
        checks["api_provider"] = provider
        checks["api_base_url"] = base_url
    else:
        checks["errors"].append("No valid API key configured in .env")

    checks["all_ok"] = (
        checks["browser_use"]
        and checks["playwright"]
        and checks["browser_launch"]
    )

    return checks


# ── CLI 入口 ──────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="browser-use Hermes Agent 集成 — 浏览器自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s navigate --url https://example.com\n"
            "  %(prog)s search --query \"browser-use\" --max-results 5\n"
            "  %(prog)s extract --url https://example.com --fields \"标题,价格\"\n"
            "  %(prog)s screenshot --url https://example.com --output ./page.png\n"
            "  %(prog)s click --url https://example.com --selector \"#submit\"\n"
            "  %(prog)s health\n"
            "  %(prog)s \"自由任务描述\" --max-steps 20\n"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # ── navigate ──
    nav = subparsers.add_parser("navigate", help="导航到 URL")
    nav.add_argument("--url", type=str, required=True, help="目标 URL")
    nav.add_argument("--task", type=str, default="", help="在页面上执行的任务")
    _add_common_args(nav)

    # ── search ──
    search = subparsers.add_parser("search", help="搜索并提取结果")
    search.add_argument("--query", type=str, required=True, help="搜索关键词")
    search.add_argument("--max-results", type=int, default=5, help="最大结果数")
    _add_common_args(search)

    # ── extract ──
    ext = subparsers.add_parser("extract", help="提取页面结构化数据")
    ext.add_argument("--url", type=str, required=True, help="目标 URL")
    ext.add_argument("--fields", type=str, default="", help="要提取的字段（逗号分隔）")
    _add_common_args(ext)

    # ── screenshot ──
    ss = subparsers.add_parser("screenshot", help="截取页面截图")
    ss.add_argument("--url", type=str, required=True, help="目标 URL")
    ss.add_argument("--output", type=str, default=None, help="保存路径")
    ss.add_argument("--headless", action="store_true", default=True)
    ss.add_argument("--no-headless", action="store_false", dest="headless")

    # ── click ──
    clk = subparsers.add_parser("click", help="点击页面元素")
    clk.add_argument("--url", type=str, required=True, help="目标 URL")
    clk.add_argument("--selector", type=str, default="", help="CSS 选择器")
    clk.add_argument("--task", type=str, default="", help="点击任务描述")
    _add_common_args(clk)

    # ── health ──
    subparsers.add_parser("health", help="检查 browser-use 和 playwright 状态")

    return parser


def _add_common_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--max-steps", type=int, default=20, help="最大操作步数（默认 20）"
    )
    subparser.add_argument(
        "--headless", action="store_true", default=True, help="启用无头模式（默认）"
    )
    subparser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="显示浏览器界面",
    )
    subparser.add_argument(
        "--no-vision",
        action="store_true",
        default=False,
        help="禁用视觉理解（节省 tokens）",
    )
    subparser.add_argument(
        "--model", type=str, default=None, help="覆盖 LLM 模型名称"
    )
    subparser.add_argument(
        "--proxy", type=str, default=None, help="浏览器代理地址"
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数，兼容旧版自由任务模式。

    策略：
    1. 如果第一个参数是已知子命令 → 使用子命令解析
    2. 如果第一个参数不是子命令且不以 '-' 开头 → 视为自由任务
    3. 否则 → 显示 help
    """
    parser = _build_parser()

    if not argv:
        parser.print_help()
        sys.exit(1)

    # 检测是否是自由任务模式（非子命令且不以 - 开头）
    known_commands = {"navigate", "search", "extract", "screenshot", "click", "health"}
    first_arg = argv[0]

    if first_arg not in known_commands and not first_arg.startswith("-"):
        # 自由任务模式
        old_parser = argparse.ArgumentParser()
        old_parser.add_argument("task", type=str, nargs="?", default="")
        old_parser.add_argument("--max-steps", type=int, default=20)
        old_parser.add_argument("--headless", action="store_true", default=True)
        old_parser.add_argument("--no-headless", action="store_false", dest="headless")
        old_parser.add_argument("--save", type=str, default=None)
        old_parser.add_argument("--json", action="store_true", default=False)
        old_parser.add_argument("--model", type=str, default=None)
        old_parser.add_argument("--proxy", type=str, default=None)
        old_parser.add_argument("--no-vision", action="store_true", default=False)
        old_args = old_parser.parse_args(argv)
        return argparse.Namespace(
            command="task",
            task=old_args.task,
            max_steps=old_args.max_steps,
            headless=old_args.headless,
            no_vision=old_args.no_vision,
            model=old_args.model,
            proxy=old_args.proxy,
            save=old_args.save,
            json_output=old_args.json,
        )

    # 子命令模式
    return parser.parse_args(argv)


def main() -> int:
    """CLI 入口。"""
    args = _parse_args(sys.argv[1:] if len(sys.argv) > 1 else None)

    # ── health 子命令 ──
    if args.command == "health":
        checks = cmd_health()
        print(json.dumps(checks, ensure_ascii=False, indent=2))
        return 0 if checks.get("all_ok") else 1

    # ── 各子命令分发 ──
    command_map = {
        "navigate": cmd_navigate,
        "search": cmd_search,
        "extract": cmd_extract,
        "screenshot": cmd_screenshot,
        "click": cmd_click,
    }

    if args.command in command_map:
        result = command_map[args.command](args)
        # 输出
        if getattr(args, "json_output", False):
            print(result.to_json())
        else:
            print("\n" + "=" * 60)
            print(f"  Task: {result.task}")
            print(f"  Status: {'✅ Success' if result.success else '❌ Failed'}")
            print(f"  Steps: {result.steps}")
            print(f"  Duration: {result.total_duration_sec:.1f}s")
            print(f"  URLs: {len(result.urls)} visited")
            if result.final_result:
                print(f"\n  Final Result:\n    {result.final_result[:500]}")
            if result.errors:
                print(f"\n  Errors ({len(result.errors)}):")
                for e in result.errors[:5]:
                    print(f"    - {e}")
            print("=" * 60)
        return 0 if result.success else 1

    # ── task 子命令（旧版自由任务模式） ──
    if args.command == "task" and args.task:
        result = browser_agent(
            task=args.task,
            max_steps=args.max_steps,
            headless=args.headless,
            use_vision=not args.no_vision,
            model=args.model,
            save_conversation=getattr(args, "save", None),
            proxy=args.proxy,
        )
        if getattr(args, "json_output", False):
            print(result.to_json())
        else:
            print(result.summary() if result.success else result.to_json())
        return 0 if result.success else 1

    # 无有效命令
    print("Error: no valid command or task provided. Use --help for usage.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
