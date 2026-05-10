#!/usr/bin/env python3
"""墨麟 molib CLI — Hermes terminal 工具的执行入口

这是整个系统的"肌肉"层入口。
Hermes（大脑）通过 terminal（神经）调用本 CLI。
本入口将命令分发给对应模块，结果写入 FileEventBus。

用法:
    python -m molib health                   # 系统健康检查
    python -m molib help                      # 命令列表
    python -m molib content <subcmd> [args]   # 内容创作
    python -m molib design <subcmd> [args]    # 设计
    python -m molib video <subcmd> [args]     # 视频
    python -m molib xianyu <subcmd> [args]    # 闲鱼
    python -m molib crm <subcmd> [args]       # 私域
    python -m molib intel <subcmd> [args]     # 情报
    python -m molib finance <subcmd> [args]   # 财务
    python -m molib order <subcmd> [args]     # 订单
    python -m molib data <subcmd> [args]      # 数据
    python -m molib proxy <subcmd> [args]     # AI代理（9Router）
    python -m molib scrap <subcmd> [args]    # Scrapling抓取
    python -m molib sync <subcmd> [args]     # CocoIndex增量同步
    python -m molib trading <subcmd> [args]  # 量化交易（墨投交易）
    python -m molib plan <subcmd> [args]     # 规划工具（写任务计划）
    python -m molib query "FROM ..."        # MQL 查询引擎（墨脑知识）
    python -m molib manifest validate       # Manifest 标准化验证
"""

import sys
import json
import asyncio
from pathlib import Path

from molib import __version__


def cmd_health(args: list[str]) -> dict:
    """系统健康检查 — 快速验证各模块可用性"""
    import importlib

    modules = {
        "molib": "molib",
        "molib.core.engine": "molib.core.engine",
        "molib.ceo": "molib.ceo",
        "molib.agencies": "molib.agencies",
        "molib.xianyu": "molib.xianyu",
    }

    results = {}
    for name, module_path in modules.items():
        try:
            importlib.import_module(module_path)
            results[name] = "✅ ok"
        except Exception as e:
            results[name] = f"❌ {e}"

    # 配置文件检查
    config_dir = Path(__file__).parent.parent / "config"
    config_files = {
        "company.toml": config_dir / "company.toml",
        "moyer-override.toml": config_dir / "moyer-override.toml",
    }
    for name, path in config_files.items():
        results[f"config/{name}"] = "✅ ok" if path.exists() else "❌ missing"

    # molib CLI 自身
    results["molib.cli"] = "✅ ok"
    results["molib.__main__"] = "✅ ok"

    return {
        "status": "ok" if all("❌" not in v for v in results.values()) else "degraded",
        "checks": results,
        "version": "v" + __version__,
        "note": "SOUL.md+AGENTS.md已填写，Hermes现在知道自己是谁",
    }


def cmd_help(args: list[str]) -> dict:
    """显示所有可用命令"""
    commands = {
        "health": "系统健康检查",
        "help": "显示此帮助",
        "content write --topic T --platform P": "创作内容（墨笔文创）",
        "content publish --platform P --draft-id ID": "发布内容（墨笔文创）",
        "design image --prompt P --style S": "生成图片（墨图设计）",
        "video script --topic T --duration D": "生成视频脚本（墨播短视频）",
        "video generate --topic T --engine mpt|pixelle": "全自动生成视频（MPT⭐57K/Pixelle⭐13K）",
        "xianyu reply --msg-id ID --content C": "回复闲鱼消息（墨声客服）",
        "intel reach --url URL": "社交爬虫（基于Agent-Reach⭐19K）",
        "intel trending": "热门趋势（墨研竞情）",
        "intel predict --topic T --context C": "群体智能预测（基于MiroFish⭐59K）",
        "intel save --topic T --summary S": "保存情报（墨研竞情）",
        "intel firecrawl scrape --url URL": "Firecrawl单页抓取→Markdown（墨研竞情）",
        "intel firecrawl search --query Q": "Firecrawl网络搜索（墨研竞情）",
        "intel firecrawl crawl --url URL": "Firecrawl全站爬取（墨研竞情）",
        "intel firecrawl research --topic T": "Firecrawl深度研究（墨研竞情）",
        "scrap fetch --url URL": "Scrapling单页抓取（curl_cffi浏览器指纹模拟）",
        "scrap scrape --html H --css S": "Scrapling自适应解析（CSS/XPath提取）",
        "scrap crawl --start-urls U --max-pages N": "Scrapling并发爬虫（Spider框架）",
        "finance record --type T --amount A --note N": "记账（墨算财务）",
        "finance report": "财务报告（墨算财务）",
        "order list --status S": "订单列表（墨链电商）",
        "crm segment --by B": "用户分群（墨域私域）",
        "proxy start": "启动AI代理（9Router，端口20128）",
        "proxy stop": "停止AI代理",
        "proxy status": "查看AI代理运行状态",
        "proxy providers": "查看已配置的AI供应商",
        "proxy tokens": "查看RTK Token节省统计",
        "sync list": "列出所有CocoIndex同步管道（墨域同步）",
        "sync status": "查看同步管道运行状态",
        "sync run --pipeline NAME": "运行一次管道同步（增量catch-up）",
        "sync start --pipeline NAME": "启动管道后台持续同步",
        "sync stop --pipeline NAME": "停止管道后台同步",
        "trading analyze --market-type crypto --symbol BTC/USDT": "市场分析（墨投交易）",
        "trading backtest --strategy S --period 90d": "回测策略（墨投交易）",
        "trading signal --symbol BTC/USDT --timeframe 1h": "生成交易信号（墨投交易）",
        "trading research --ticker BTC --timeframe 1d": "研究报告（墨投交易）",
        "cost report": "API成本月度报告",
        "cost alert": "检查成本预警",
        "cost daily [N]": "最近N日成本趋势",
        "query \"FROM skills WHERE ...\"": "MQL 结构化查询（墨脑知识引擎）",
        "query --search \"关键词\"": "MQL 全文搜索",
        "query --sources": "列出 MQL 数据源",
        "manifest validate": "验证所有技能的 Manifest 标准",
        "manifest fix": "自动修复缺失的 Manifest 字段",
    }
    return {"commands": commands, "total": len(commands)}


async def cmd_intel(args: list[str]) -> dict:
    """情报命令 — 趋势 + 预测 + 保存"""
    if not args:
        return {"error": "子命令: trending | predict | save"}

    subcmd = args[0]
    rest = args[1:]

    if subcmd == "trending":
        # 趋势信息暂时返回提示信息
        return {
            "action": "trending",
            "message": "趋势分析功能仍在建设中，请使用 predict 进行预测分析",
            "suggestion": 'python -m molib intel predict --topic "AI Agent 趋势"',
        }

    if subcmd == "reach":
        url = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--url" and i + 1 < len(rest):
                url = rest[i + 1]
                i += 2
            else:
                i += 1
        if not url:
            return {"error": "请指定 --url 参数"}
        from molib.intelligence.reacher import reach_web, reach_github, reach_rss
        if "github.com" in url and "/search" in url:
            query = url.split("search?q=")[-1] if "search?q=" in url else url
            result = await reach_github(query)
        elif url.startswith("http"):
            result = await reach_web(url)
        else:
            result = await reach_rss(url)
        return result

    if subcmd == "predict":
        topic = ""
        context = ""
        num_agents = 5

        i = 0
        while i < len(rest):
            if rest[i] == "--topic" and i + 1 < len(rest):
                topic = rest[i + 1]
                i += 2
            elif rest[i] == "--context" and i + 1 < len(rest):
                context = rest[i + 1]
                i += 2
            elif rest[i] == "--agents" and i + 1 < len(rest):
                num_agents = int(rest[i + 1])
                i += 2
            else:
                i += 1

        if not topic:
            return {"error": "请指定 --topic 参数"}
        from molib.intelligence.predictor import predict
        result = await predict(topic, context, num_agents)
        return {
            "action": "prediction",
            "topic": result["topic"],
            "num_agents": result["num_agents"],
            "final_report": result["final_report"],
            "confidence_avg": round(result["confidence_avg"], 2),
        }

    if subcmd == "save":
        topic = ""
        summary = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--topic" and i + 1 < len(rest):
                topic = rest[i + 1]
                i += 2
            elif rest[i] == "--summary" and i + 1 < len(rest):
                summary = rest[i + 1]
                i += 2
            else:
                i += 1
        return {"saved": True, "topic": topic, "summary": summary}

    if subcmd == "firecrawl":
        # Firecrawl 网页采集 — scrape/crawl/search/batch/research/map/status
        from molib.intelligence.firecrawl_client import (
            scrape, crawl, search, batch_scrape, deep_research,
            map_site, crawl_status, _cli
        )
        # 将剩余参数传给 firecrawl_client 的 CLI
        import sys as _sys
        _orig = _sys.argv[:]
        _sys.argv = ["molib intel firecrawl"] + rest
        try:
            _cli()
            return {"firecrawl": "done"}
        except SystemExit:
            return {"firecrawl": "done"}
        finally:
            _sys.argv = _orig

    return {"error": f"未知子命令: {subcmd}"}


async def cmd_video(args: list[str]) -> dict:
    """短视频命令 — 脚本生成 + 视频合成"""
    if not args:
        return {"error": "子命令: script | generate"}

    subcmd = args[0]
    rest = args[1:]

    topic = ""
    engine = "mpt"
    duration = 60

    i = 0
    while i < len(rest):
        if rest[i] == "--topic" and i + 1 < len(rest):
            topic = rest[i + 1]
            i += 2
        elif rest[i] == "--engine" and i + 1 < len(rest):
            engine = rest[i + 1]
            i += 2
        elif rest[i] == "--duration" and i + 1 < len(rest):
            duration = int(rest[i + 1])
            i += 2
        else:
            i += 1

    from molib.agencies.workers.short_video import ShortVideo
    from molib.agencies.workers.base import Task

    if subcmd == "script":
        if not topic:
            return {"error": "请指定 --topic 参数"}
        task = Task(task_id="cli", task_type="video_script",
                    payload={"topic": topic, "mode": "script", "duration": duration})
        worker = ShortVideo()
        result = await worker.execute(task)
        return result.output

    if subcmd == "generate":
        if not topic:
            return {"error": "请指定 --topic 参数"}
        if engine not in ("mpt", "pixelle"):
            return {"error": f"未知引擎: {engine}，可用: mpt, pixelle"}
        task = Task(task_id="cli", task_type="video_generate",
                    payload={"topic": topic, "mode": "generate", "engine": engine, "duration": duration})
        worker = ShortVideo()
        result = await worker.execute(task)
        return result.output

    return {"error": f"未知子命令: {subcmd}"}


async def cmd_proxy(args: list[str]) -> dict:
    """9Router代理命令 — start/stop/status/providers/tokens"""
    from molib.agencies.workers.router9 import cmd_proxy as _proxy
    return await _proxy(args)


async def cmd_scrap(args: list[str]) -> dict:
    """Scrapling 抓取命令 — fetch / scrape / crawl"""
    if not args:
        return {"error": "子命令: fetch | scrape | crawl"}

    subcmd = args[0]
    rest = args[1:]

    url = ""
    html = ""
    css_sel = ""
    xpath_sel = ""
    start_urls = []
    max_pages = 10
    concurrent = 4
    impersonate = "chrome"
    adaptive = False
    async_mode = False
    extract_css = ""
    output_file = ""

    i = 0
    while i < len(rest):
        if rest[i] == "--url" and i + 1 < len(rest):
            url = rest[i + 1]
            i += 2
        elif rest[i] == "--html" and i + 1 < len(rest):
            html = rest[i + 1]
            i += 2
        elif rest[i] == "--css" and i + 1 < len(rest):
            css_sel = rest[i + 1]
            i += 2
        elif rest[i] == "--xpath" and i + 1 < len(rest):
            xpath_sel = rest[i + 1]
            i += 2
        elif rest[i] == "--start-urls" and i + 1 < len(rest):
            start_urls = [u.strip() for u in rest[i + 1].split(",")]
            i += 2
        elif rest[i] == "--max-pages" and i + 1 < len(rest):
            max_pages = int(rest[i + 1])
            i += 2
        elif rest[i] == "--concurrent" and i + 1 < len(rest):
            concurrent = int(rest[i + 1])
            i += 2
        elif rest[i] == "--impersonate" and i + 1 < len(rest):
            impersonate = rest[i + 1]
            i += 2
        elif rest[i] == "--adaptive":
            adaptive = True
            i += 1
        elif rest[i] == "--async":
            async_mode = True
            i += 1
        elif rest[i] == "--extract-css" and i + 1 < len(rest):
            extract_css = rest[i + 1]
            i += 2
        elif rest[i] == "--output" and i + 1 < len(rest):
            output_file = rest[i + 1]
            i += 2
        else:
            i += 1

    from molib.agencies.workers.scrapling_worker import web_fetch, scrape, crawl

    if subcmd == "fetch":
        if not url:
            return {"error": "请指定 --url 参数"}
        result = web_fetch(url, async_mode=async_mode, impersonate=impersonate)
        return {
            "action": "fetch",
            "url": result.get("url"),
            "status": result.get("status", 0),
            "body_length": len(result.get("text", "")),
            "headers": result.get("headers", {}),
        }

    elif subcmd == "scrape":
        if not html and not url:
            return {"error": "请指定 --html 或 --url 参数"}
        source = html if html else url
        result = scrape(
            source,
            css=css_sel or None,
            xpath=xpath_sel or None,
            adaptive=adaptive,
        )
        return result

    elif subcmd == "crawl":
        if not start_urls and not url:
            return {"error": "请指定 --start-urls 参数"}
        if not start_urls and url:
            start_urls = [url]
        result = crawl(
            start_urls,
            max_pages=max_pages,
            concurrent=concurrent,
            extract_css=extract_css or None,
            impersonate=impersonate,
        )
        return result

    return {"error": f"未知子命令: {subcmd}"}


def cmd_sync(args: list[str]) -> dict:
    """同步管道命令 — list/status/run/start/stop（CocoIndex增量同步）"""
    from molib.agencies.workers.cocoindex_sync import cmd_sync as _sync
    return _sync(args)


async def cmd_trading(args: list[str]) -> dict:
    """量化交易命令 — analyze / backtest / signal / research"""
    if not args:
        return {"error": "子命令: analyze | backtest | signal | research"}

    subcmd = args[0]
    rest = args[1:]

    # 解析通用参数
    market_type = ""
    symbol = ""
    strategy = ""
    period = ""
    timeframe = ""
    ticker = ""
    pairs = []

    i = 0
    while i < len(rest):
        if rest[i] == "--market-type" and i + 1 < len(rest):
            market_type = rest[i + 1]
            i += 2
        elif rest[i] == "--symbol" and i + 1 < len(rest):
            symbol = rest[i + 1]
            i += 2
        elif rest[i] == "--strategy" and i + 1 < len(rest):
            strategy = rest[i + 1]
            i += 2
        elif rest[i] == "--period" and i + 1 < len(rest):
            period = rest[i + 1]
            i += 2
        elif rest[i] == "--timeframe" and i + 1 < len(rest):
            timeframe = rest[i + 1]
            i += 2
        elif rest[i] == "--ticker" and i + 1 < len(rest):
            ticker = rest[i + 1]
            i += 2
        elif rest[i] == "--pairs" and i + 1 < len(rest):
            pairs = [p.strip() for p in rest[i + 1].split(",")]
            i += 2
        else:
            i += 1

    from molib.agencies.workers.trading import Trading
    from molib.agencies.workers.base import Task

    if subcmd == "analyze":
        task = Task(
            task_id="cli",
            task_type="analyze_market",
            payload={"market_type": market_type or "crypto", "symbol": symbol or "BTC/USDT"},
        )
        worker = Trading()
        result = await worker.execute(task)
        return result.output

    if subcmd == "backtest":
        task = Task(
            task_id="cli",
            task_type="backtest",
            payload={
                "strategy": strategy or "SampleStrategy",
                "period": period or "90d",
                "pairs": pairs or ["BTC/USDT", "ETH/USDT"],
            },
        )
        worker = Trading()
        result = await worker.execute(task)
        return result.output

    if subcmd == "signal":
        task = Task(
            task_id="cli",
            task_type="signal",
            payload={"symbol": symbol or "BTC/USDT", "timeframe": timeframe or "1h"},
        )
        worker = Trading()
        result = await worker.execute(task)
        return result.output

    if subcmd == "research":
        task = Task(
            task_id="cli",
            task_type="research",
            payload={"ticker": ticker or "BTC", "timeframe": timeframe or "1d"},
        )
        worker = Trading()
        result = await worker.execute(task)
        return result.output

    return {"error": f"未知子命令: {subcmd}"}


async def cmd_cost(args: list[str]) -> dict:
    """API成本追踪 — report / alert / daily / record"""
    from molib.cost import report, check_alerts, get_daily_stats, record as cost_record

    if not args or args[0] == "report":
        stats = report()
        return stats

    if args[0] == "alert":
        alerts = check_alerts()
        return {"alerts": alerts, "healthy": len(alerts) == 0}

    if args[0] == "daily":
        days = int(args[1]) if len(args) > 1 else 7
        trend = get_daily_stats(days=days)
        return {"days": days, "trend": trend}

    if args[0] == "record":
        kwargs = {"model": "unknown", "input_tokens": 0, "output_tokens": 0, "images": 0, "task": ""}
        i = 1
        while i < len(args):
            if args[i] == "--input" and i + 1 < len(args):
                kwargs["input_tokens"] = int(args[i + 1]); i += 2
            elif args[i] == "--output" and i + 1 < len(args):
                kwargs["output_tokens"] = int(args[i + 1]); i += 2
            elif args[i] == "--model" and i + 1 < len(args):
                kwargs["model"] = args[i + 1]; i += 2
            elif args[i] == "--task" and i + 1 < len(args):
                kwargs["task"] = args[i + 1]; i += 2
            elif args[i] == "--images" and i + 1 < len(args):
                kwargs["images"] = int(args[i + 1]); i += 2
            else:
                i += 1
        cost = cost_record(**kwargs)
        return {"cost": cost, **kwargs}

    return {"error": f"未知: {args[0]}，支持: report | alert | daily [N] | record"}


async def cmd_handoff(args: list[str]) -> dict:
    """Handoff自动路由命令 — list / route / history"""
    from molib.agencies.handoff_register import register_all_handoffs
    from molib.agencies.handoff import HandoffManager, HandoffInputData, HandoffError

    register_all_handoffs()

    if not args or args[0] == "list":
        return {"handoffs": HandoffManager.get_manifest()}

    if args[0] == "route":
        task_name = ""
        if "--task" in args:
            idx = args.index("--task")
            task_name = args[idx + 1] if idx + 1 < len(args) else ""
        elif len(args) > 1:
            task_name = args[1]
        if not task_name:
            return {"error": "请指定任务名称: --task <名称> 或 route <名称>"}
        result, record = HandoffManager.route(task_name, HandoffInputData())
        if isinstance(result, HandoffError):
            return {"status": "error", "error": result.message, "code": result.code.value}
        return {"status": "ok", "worker": result.worker_id, "output": str(result.output)[:300]}

    if args[0] == "history":
        limit = 20
        if "--limit" in args:
            idx = args.index("--limit")
            limit = int(args[idx + 1]) if idx + 1 < len(args) else 20
        return {"history": HandoffManager.build_history(limit=limit)}

    return {"error": f"未知子命令: {args[0]}，支持: list | route | history"}


async def cmd_plan(args: list[str]) -> dict:
    """规划工具 — 分解任务为结构化 TODO 列表"""
    from molib.agencies.planning import main as plan_main

    return plan_main(args)


def cmd_query(args: list[str]) -> dict:
    """MQL 查询引擎"""
    from molib.shared.query.cli import main as query_main
    import io

    # 捕获 CLI 输出
    old_argv = sys.argv
    try:
        sys.argv = ["molib-query"] + args
        query_main()
        return {"status": "ok"}
    except SystemExit:
        return {"status": "ok"}
    finally:
        sys.argv = old_argv


def cmd_manifest(args: list[str]) -> dict:
    """Manifest 标准化工具"""
    from molib.core.tools.manifest_validator import main as manifest_main
    import io

    old_argv = sys.argv
    try:
        sys.argv = ["molib-manifest"] + args
        manifest_main()
        return {"status": "ok"}
    except SystemExit:
        return {"status": "ok"}
    finally:
        sys.argv = old_argv


async def run(command: str, args: list[str]) -> dict:
    """分发命令到具体模块"""
    # 同步命令映射（直接返回 dict）
    sync_commands = {
        "health": cmd_health,
        "help": cmd_help,
        "sync": cmd_sync,
        "query": cmd_query,
        "manifest": cmd_manifest,
    }
    # 异步命令映射（返回 coroutine）
    async_commands = {
        "intel": cmd_intel,
        "video": cmd_video,
        "proxy": cmd_proxy,
        "scrap": cmd_scrap,
        "trading": cmd_trading,
        "handoff": cmd_handoff,
        "plan": cmd_plan,
        "cost": cmd_cost,
    }

    if command in sync_commands:
        return sync_commands[command](args)
    elif command in async_commands:
        return await async_commands[command](args)

    return {
        "status": "error",
        "error": f"未知命令: {command}",
        "hint": "使用 `python -m molib help` 查看可用命令",
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "usage": "python -m molib <command> [args...]",
            "hint": "python -m molib help 查看所有命令",
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    command, *args = sys.argv[1:]
    result = asyncio.run(run(command, args))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
