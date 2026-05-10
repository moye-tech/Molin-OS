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
    python -m molib shop <subcmd> [args]      # 电商（商品+订单+上架）
    python -m molib data <subcmd> [args]      # 数据
    python -m molib proxy <subcmd> [args]     # AI代理（9Router）
    python -m molib scrap <subcmd> [args]    # Scrapling抓取
    python -m molib index <subcmd> [args]   # CocoIndex本地索引(watch/query/sync/stats)
    python -m molib sync <subcmd> [args]     # CocoIndex增量同步
    python -m molib trading <subcmd> [args]  # 量化交易（墨投交易）
    python -m molib plan <subcmd> [args]     # 规划工具（写任务计划）
    python -m molib query "FROM ..."        # MQL 查询引擎（墨脑知识）
    python -m molib manifest validate       # Manifest 标准化验证
    python -m molib swarm list             # Swarm跨子公司通路
    python -m molib swarm run <pattern>    # 运行预定义工作流
    python -m molib swarm visualize        # ASCII流程图
    python -m molib bitable schema         # 飞书多维表格表结构
    python -m molib bitable write <table>  # 飞书多维表格写入记录
    python -m molib bitable list <table>   # 飞书多维表格查询记录
    python -m molib avatar create --text "你好" --image pic.jpg  # 数字人视频(Tier 1: ffmpeg+say)
    python -m molib avatar list-voices     # 列出可用语音
    python -m molib avatar check           # 检测 Tier 1/2 引擎状态
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
        "order status --order-id ID": "订单详情（墨链电商）",
        "order create --title T --source S --value V": "创建订单（墨链电商）",
        "order invoice --order-id ID --customer C": "生成发票（墨链电商）",
        "order payment --invoice-id ID --amount A --method M": "记录支付（墨链电商）",
        "order transition --order-id ID --to STATUS": "推进订单状态（墨链电商）",
        "order stats": "订单统计（墨链电商）",
        "order report": "每日订单报告（墨链电商）",
        "order remind-overdue": "逾期提醒（墨链电商）",
        "pocketbase install": "安装 PocketBase 后端（墨码开发）",
        "pocketbase start": "启动 PocketBase（墨码开发）",
        "pocketbase stop": "停止 PocketBase（墨码开发）",
        "pocketbase status": "查看 PocketBase 状态",
        "pocketbase quick-start": "一键安装+启动+初始化 PocketBase",
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
        "index watch --dir PATH": "开始监听目录文件变更（CocoIndex本地索引）",
        "index query --term TERM": "搜索已索引文件内容",
        "index sync": "全量扫描索引所有监听目录",
        "index stats": "查看索引统计信息",
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
        "bitable schema [table]": "查看飞书多维表格结构",
        "bitable write <table> --json '{...}'": "写入飞书多维表格记录",
        "bitable list <table> [--filter expr]": "查询飞书多维表格记录",
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


def cmd_index(args: list[str]) -> dict:
    """CocoIndex本地索引命令 — watch/query/sync/stats"""
    from molib.infra.coco_index import (
        cmd_index_watch, cmd_index_query, cmd_index_sync, cmd_index_stats,
    )
    import io, sys

    if not args:
        return {"error": "子命令: watch | query | sync | stats"}

    subcmd = args[0]
    rest = args[1:]

    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if subcmd == "watch":
            path = rest[0] if rest else str(Path.home() / "Molin-OS")
            cmd_index_watch(path)
        elif subcmd == "query":
            term = rest[0] if rest else ""
            cmd_index_query(term)
        elif subcmd == "sync":
            cmd_index_sync()
        elif subcmd == "stats":
            cmd_index_stats()
        else:
            return {"error": f"未知子命令: {subcmd}"}
    finally:
        sys.stdout = old_stdout

    return {"output": buf.getvalue()}


def cmd_bitable(args: list[str]) -> dict:
    """飞书多维表格命令 — schema / write / list"""
    from molib.infra.feishu_bitable import (
        cmd_bitable_schema, cmd_bitable_write, cmd_bitable_list,
    )
    import io, sys

    if not args:
        return {"error": "子命令: schema | write | list"}

    subcmd = args[0]
    rest = args[1:]

    table = rest[0] if rest else ""
    app_token = rest[1] if len(rest) > 1 else ""
    table_id = rest[2] if len(rest) > 2 else ""

    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if subcmd == "schema":
            cmd_bitable_schema()
        elif subcmd == "write":
            cmd_bitable_write(table, app_token, table_id)
        elif subcmd == "list":
            cmd_bitable_list(table, app_token, table_id)
        else:
            return {"error": f"未知子命令: {subcmd}"}
    finally:
        sys.stdout = old_stdout

    return {"output": buf.getvalue()}


def cmd_swarm(args: list[str]) -> dict:
    """Swarm Bridge — 跨子公司 Handoff 编排"""
    from molib.agencies.swarm_bridge import SwarmBridge
    import io, sys

    sb = SwarmBridge()

    if not args:
        return {"error": "子命令: list | run | visualize"}

    subcmd = args[0]
    rest = args[1:]

    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if subcmd == "list":
            for h in sb.list_handoffs():
                print(f"  {h.source_agency} → {h.target_agency} ({h.condition})")
            return {"handoffs": len(sb.list_handoffs())}
        elif subcmd == "run":
            pattern = rest[0] if rest else "content_full_pipeline"
            if pattern in sb.SWARM_PATTERNS:
                print(f"⚡ 运行工作流: {pattern}")
                print(f"   步骤: {' → '.join(sb.SWARM_PATTERNS[pattern])}")
            else:
                print(f"未知模式: {pattern}")
                print(f"可用: {list(sb.SWARM_PATTERNS.keys())}")
        elif subcmd == "visualize":
            sb.visualize()
        else:
            return {"error": f"未知子命令: {subcmd}"}
    finally:
        sys.stdout = old_stdout

    return {"output": buf.getvalue()}


def cmd_memory(args: list[str]) -> dict:
    """记忆蒸馏 — distill/stats"""
    from molib.infra.memory.distiller import cmd_memory_distill, cmd_memory_stats
    import io, sys

    if not args:
        return {"error": "子命令: distill | stats"}

    subcmd = args[0]

    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if subcmd == "distill":
            cmd_memory_distill()
        elif subcmd == "stats":
            cmd_memory_stats()
        else:
            return {"error": f"未知子命令: {subcmd}"}
    finally:
        sys.stdout = old_stdout

    return {"output": buf.getvalue()}


def cmd_avatar(args: list[str]) -> dict:
    """数字人视频生成 — create / list-voices / check"""
    from molib.infra.digital_human import (
        cmd_avatar_create, cmd_avatar_list_voices, cmd_avatar_check,
    )

    if not args:
        return {"error": "子命令: create | list-voices | check"}

    subcmd = args[0]
    rest = args[1:]

    text = ""
    image = ""
    voice = ""
    rate = 200
    resolution = "720p"
    lang = ""
    i = 0
    while i < len(rest):
        if rest[i] == "--text" and i + 1 < len(rest):
            text = rest[i + 1]; i += 2
        elif rest[i] == "--image" and i + 1 < len(rest):
            image = rest[i + 1]; i += 2
        elif rest[i] == "--voice" and i + 1 < len(rest):
            voice = rest[i + 1]; i += 2
        elif rest[i] == "--rate" and i + 1 < len(rest):
            rate = int(rest[i + 1]); i += 2
        elif rest[i] == "--resolution" and i + 1 < len(rest):
            resolution = rest[i + 1]; i += 2
        elif rest[i] == "--lang" and i + 1 < len(rest):
            lang = rest[i + 1]; i += 2
        else:
            i += 1

    import io, sys
    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if subcmd == "create":
            cmd_avatar_create(text, image, voice, rate, resolution)
        elif subcmd == "list-voices":
            cmd_avatar_list_voices(lang)
        elif subcmd == "check":
            cmd_avatar_check()
        else:
            return {"error": f"未知子命令: {subcmd}"}
    finally:
        sys.stdout = old_stdout

    return {"output": buf.getvalue()}


# ── MolibDB / MolibMail / MolibOrder ────────────────────────

def cmd_db(args: list[str]) -> dict:
    """统一轻量后端 — collection/record/auth/stats"""
    from molib.infra.molib_db import cmd_db_collection, cmd_db_record, cmd_db_auth, cmd_db_stats
    if not args:
        return cmd_db_stats()
    subcmd = args[0]
    rest = args[1:]
    if subcmd == "collection":
        return cmd_db_collection(rest)
    elif subcmd == "record":
        return cmd_db_record(rest)
    elif subcmd == "auth":
        return cmd_db_auth(rest)
    elif subcmd == "stats":
        return cmd_db_stats()
    return {"error": f"未知: {subcmd}，支持 collection|record|auth|stats"}


def cmd_mail(args: list[str]) -> dict:
    """邮件营销 — list/subscriber/campaign/stats"""
    from molib.infra.molib_mail import cmd_mail_list, cmd_mail_subscriber, cmd_mail_campaign, cmd_mail_stats
    if not args:
        return cmd_mail_stats()
    subcmd = args[0]
    rest = args[1:]
    if subcmd == "list":
        return cmd_mail_list(rest)
    elif subcmd == "subscriber":
        return cmd_mail_subscriber(rest)
    elif subcmd == "campaign":
        return cmd_mail_campaign(rest)
    elif subcmd == "stats":
        return cmd_mail_stats()
    return {"error": f"未知: {subcmd}，支持 list|subscriber|campaign|stats"}


def cmd_order(args: list[str]) -> dict:
    """订单引擎 — create/list/invoice/stats"""
    from molib.infra.molib_order import cmd_order_create, cmd_order_list, cmd_order_invoice, cmd_order_stats
    if not args:
        return cmd_order_stats()
    subcmd = args[0]
    rest = args[1:]
    if subcmd == "create":
        return cmd_order_create(rest)
    elif subcmd == "list":
        return cmd_order_list(rest)
    elif subcmd == "invoice":
        return cmd_order_invoice(rest)
    elif subcmd == "stats":
        return cmd_order_stats()
    return {"error": f"未知: {subcmd}，支持 create|list|invoice|stats"}


def cmd_analytics(args: list[str]) -> dict:
    """轻量分析 — track/stats/top"""
    from molib.infra.molib_analytics import cmd_analytics_track, cmd_analytics_stats, cmd_analytics_top
    if not args:
        return {"error": "子命令: track | stats | top-pages"}
    subcmd = args[0]
    rest = args[1:]
    if subcmd == "track":
        return cmd_analytics_track(rest)
    elif subcmd == "stats":
        return cmd_analytics_stats(rest)
    elif subcmd == "top-pages":
        return cmd_analytics_top(rest)
    return {"error": f"未知: {subcmd}，支持 track|stats|top-pages"}


async def cmd_cost(args: list[str]) -> dict:
    """API成本追踪 — report / check / reset / track"""
    from molib.infra.budget_guard import BudgetGuard
    bg = BudgetGuard()

    if not args or args[0] == "report":
        return bg.get_report()

    if args[0] == "check":
        provider = args[1] if len(args) > 1 else None
        result = bg.check(provider=provider)
        return result

    if args[0] == "reset":
        return bg.reset_daily()

    if args[0] == "track":
        provider = "deepseek"
        model = "deepseek-v4-pro"
        input_tokens = 0
        output_tokens = 0
        images = 0
        i = 1
        while i < len(args):
            if args[i] == "--provider" and i + 1 < len(args):
                provider = args[i + 1]; i += 2
            elif args[i] == "--model" and i + 1 < len(args):
                model = args[i + 1]; i += 2
            elif args[i] == "--input" and i + 1 < len(args):
                input_tokens = int(args[i + 1]); i += 2
            elif args[i] == "--output" and i + 1 < len(args):
                output_tokens = int(args[i + 1]); i += 2
            elif args[i] == "--images" and i + 1 < len(args):
                images = int(args[i + 1]); i += 2
            else:
                i += 1
        cost = bg.track(provider, model, input_tokens, output_tokens, images)
        status = bg.check()
        return {
            "cost": round(cost, 6),
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "images": images,
            "budget_status": status,
        }

    return {"error": f"未知子命令: {args[0]}，支持: report | check [provider] | reset | track"}


async def cmd_trading(args: list[str]) -> dict:
    """TradingAgents-CN — signal/analyze/research（多智能体交易分析）"""
    from molib.agencies.trading_agents import (
        cmd_trading_signal, cmd_trading_analyze, cmd_trading_research,
    )

    if not args:
        return {"error": "子命令: signal | analyze | research"}

    subcmd = args[0]
    rest = args[1:]

    symbol = ""
    market = ""
    ticker = ""
    i = 0
    while i < len(rest):
        if rest[i] == "--symbol" and i + 1 < len(rest):
            symbol = rest[i + 1]; i += 2
        elif rest[i] == "--market" and i + 1 < len(rest):
            market = rest[i + 1]; i += 2
        elif rest[i] == "--ticker" and i + 1 < len(rest):
            ticker = rest[i + 1]; i += 2
        else:
            i += 1

    import io, sys
    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if subcmd == "signal":
            cmd_trading_signal(symbol or "000001", market or "a-share")
        elif subcmd == "analyze":
            cmd_trading_analyze(symbol or "BTC/USDT", market or "crypto")
        elif subcmd == "research":
            cmd_trading_research(ticker or symbol or "BTC")
        else:
            return {"error": f"未知子命令: {subcmd}"}
    finally:
        sys.stdout = old_stdout

    return {"output": buf.getvalue()}


async def cmd_order(args: list[str]) -> dict:
    """订单命令 — create / invoice / payment / list / status / transition / stats / report"""
    if not args:
        return {
            "error": "子命令: create | invoice | payment | list | status | transition | stats | report",
            "examples": {
                "create": 'python -m molib order create --title "项目名" --source direct --value 500',
                "invoice": "python -m molib order invoice --order-id ORD-XXX --customer 客户名",
                "payment": "python -m molib order payment --invoice-id INV-XXX --amount 500 --method wechat",
                "list": "python -m molib order list --status won",
                "status": "python -m molib order status --order-id ORD-XXX",
                "transition": "python -m molib order transition --order-id ORD-XXX --to bidding",
                "stats": "python -m molib order stats",
                "report": "python -m molib order report",
            },
        }

    subcmd = args[0]
    rest = args[1:]

    from molib.agencies.workers.order_worker import OrderWorker
    worker = OrderWorker()

    if subcmd == "create":
        title = ""
        source = "direct"
        description = ""
        value = 0.0
        tags_str = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--title" and i + 1 < len(rest):
                title = rest[i + 1]; i += 2
            elif rest[i] == "--source" and i + 1 < len(rest):
                source = rest[i + 1]; i += 2
            elif rest[i] == "--description" and i + 1 < len(rest):
                description = rest[i + 1]; i += 2
            elif rest[i] == "--value" and i + 1 < len(rest):
                value = float(rest[i + 1]); i += 2
            elif rest[i] == "--tags" and i + 1 < len(rest):
                tags_str = rest[i + 1]; i += 2
            else:
                i += 1
        if not title:
            return {"error": "请指定 --title 参数"}
        tags = [t.strip() for t in tags_str.split(",")] if tags_str else []
        return worker.create_order(
            source=source, title=title, description=description,
            estimated_value=value, tags=tags,
        )

    elif subcmd == "invoice":
        order_id = ""
        customer = ""
        email = ""
        notes = ""
        tax_rate = 0.0
        due_days = 30
        items_json = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--order-id" and i + 1 < len(rest):
                order_id = rest[i + 1]; i += 2
            elif rest[i] == "--customer" and i + 1 < len(rest):
                customer = rest[i + 1]; i += 2
            elif rest[i] == "--email" and i + 1 < len(rest):
                email = rest[i + 1]; i += 2
            elif rest[i] == "--notes" and i + 1 < len(rest):
                notes = rest[i + 1]; i += 2
            elif rest[i] == "--tax-rate" and i + 1 < len(rest):
                tax_rate = float(rest[i + 1]); i += 2
            elif rest[i] == "--due-days" and i + 1 < len(rest):
                due_days = int(rest[i + 1]); i += 2
            elif rest[i] == "--items" and i + 1 < len(rest):
                items_json = rest[i + 1]; i += 2
            else:
                i += 1
        if not order_id:
            return {"error": "请指定 --order-id 参数"}
        items = None
        if items_json:
            try:
                items = json.loads(items_json)
            except json.JSONDecodeError:
                return {"error": "items 参数必须是有效 JSON"}
        return worker.create_invoice(
            order_id=order_id, items=items, customer_name=customer,
            customer_email=email, notes=notes, tax_regime="CN_SMALL",
            due_days=due_days,
        )

    elif subcmd == "payment":
        invoice_id = ""
        amount = 0.0
        method = "unknown"
        note = ""
        order_id = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--invoice-id" and i + 1 < len(rest):
                invoice_id = rest[i + 1]; i += 2
            elif rest[i] == "--amount" and i + 1 < len(rest):
                amount = float(rest[i + 1]); i += 2
            elif rest[i] == "--method" and i + 1 < len(rest):
                method = rest[i + 1]; i += 2
            elif rest[i] == "--note" and i + 1 < len(rest):
                note = rest[i + 1]; i += 2
            elif rest[i] == "--order-id" and i + 1 < len(rest):
                order_id = rest[i + 1]; i += 2
            else:
                i += 1
        if not invoice_id or amount <= 0:
            return {"error": "请指定 --invoice-id 和 --amount 参数"}
        return worker.record_payment(
            invoice_id=invoice_id, amount=amount, method=method,
            note=note,
        )

    elif subcmd == "list":
        status = None
        source = None
        i = 0
        while i < len(rest):
            if rest[i] == "--status" and i + 1 < len(rest):
                status = rest[i + 1]; i += 2
            elif rest[i] == "--source" and i + 1 < len(rest):
                source = rest[i + 1]; i += 2
            else:
                i += 1
        return worker.list_orders(status=status, source=source)

    elif subcmd == "status":
        order_id = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--order-id" and i + 1 < len(rest):
                order_id = rest[i + 1]; i += 2
            else:
                i += 1
        if not order_id:
            return {"error": "请指定 --order-id 参数"}
        return worker.get_order_status(order_id)

    elif subcmd == "transition":
        order_id = ""
        to_status = ""
        i = 0
        while i < len(rest):
            if rest[i] == "--order-id" and i + 1 < len(rest):
                order_id = rest[i + 1]; i += 2
            elif rest[i] == "--to" and i + 1 < len(rest):
                to_status = rest[i + 1]; i += 2
            else:
                i += 1
        if not order_id or not to_status:
            return {"error": "请指定 --order-id 和 --to 参数"}
        return worker.transition_order(order_id, to_status)

    elif subcmd == "stats":
        return worker.stats()

    elif subcmd == "report":
        print(worker.daily_report())
        return {"report": "printed"}

    elif subcmd == "remind-overdue":
        return worker.remind_overdue()

    return {"error": f"未知子命令: {subcmd}"}


def cmd_pocketbase(args: list[str]) -> dict:
    """PocketBase 后端管理 — install | start | stop | restart | status | quick-start"""
    from molib.infra.pocketbase import (
        install, start, stop, restart, status, quick_start,
        is_installed, version, get_client,
    )

    if not args:
        return {
            "error": "子命令: install | start | stop | restart | status | quick-start | health",
            "installed": is_installed(),
            "version": version(),
        }

    subcmd = args[0]

    if subcmd == "install":
        tag = args[1] if len(args) > 1 else None
        return install(tag)
    elif subcmd == "start":
        return start()
    elif subcmd == "stop":
        return stop()
    elif subcmd == "restart":
        return restart()
    elif subcmd == "status":
        return status()
    elif subcmd == "quick-start":
        return quick_start()
    elif subcmd == "health":
        client = get_client()
        return client.health()

    return {"error": f"未知子命令: {subcmd}"}


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
        "index": cmd_index,
        "query": cmd_query,
        "manifest": cmd_manifest,
        "bitable": cmd_bitable,
        "swarm": cmd_swarm,
        "memory": cmd_memory,
        "avatar": cmd_avatar,
        "db": cmd_db,
        "mail": cmd_mail,
        "order": cmd_order,
        "analytics": cmd_analytics,
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
        "order": cmd_order,
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
