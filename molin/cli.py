#!/usr/bin/env python3
"""
墨麟 Hermes OS CLI — 一人公司操作系统命令行入口

Usage:
    molin ceo strategy          # 生成战略决策
    molin ceo review            # 审查上周业绩
    molin content xhs <主题>     # 生成小红书内容
    molin content video <主题>   # 生成视频内容
    molin content seo <关键词>   # 生成SEO内容
    molin publish <平台>         # 发布内容到指定平台
    molin intel trends          # 查看趋势洞察
    molin intel monitor         # 运行监控
    molin xianyu list           # 生成闲鱼商品列表
    molin xianyu publish        # 发布闲鱼商品
    molin business bp <项目>    # 生成商业计划书
    molin business prd <产品>   # 生成PRD
    molin swarm run <任务>      # 启动蜂群执行任务
    molin learn                 # 运行自学习循环
    molin serve                 # 启动Web仪表盘
    molin schedule list         # 查看定时任务
    molin schedule run <id>     # 手动执行定时任务
    molin health                # 系统健康检查
"""

import argparse
import sys
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        prog="molin",
        description="墨麟 Hermes OS — AI一人公司操作系统",
        epilog="Powered by Hermes Agent | moye-tech",
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # ── CEO 战略层 ──
    ceo = sub.add_parser("ceo", help="CEO战略决策")
    ceo_sub = ceo.add_subparsers(dest="action")
    ceo_sub.add_parser("strategy", help="生成战略决策")
    ceo_sub.add_parser("review", help="审查业绩")

    # ── 内容工厂 ──
    content = sub.add_parser("content", help="内容生成")
    content_sub = content.add_subparsers(dest="action")
    xhs = content_sub.add_parser("xhs", help="小红书内容")
    xhs.add_argument("topic", nargs="?", default="", help="主题")
    video = content_sub.add_parser("video", help="视频内容")
    video.add_argument("topic", nargs="?", default="", help="主题")
    seo = content_sub.add_parser("seo", help="SEO内容")
    seo.add_argument("keyword", nargs="?", default="", help="关键词")

    # ── 发布引擎 ──
    pub = sub.add_parser("publish", help="内容发布")
    pub.add_argument("platform", help="平台: xiaohongshu/zhihu/weibo/wechat/juejin/x")

    # ── 情报系统 ──
    intel = sub.add_parser("intel", help="情报系统")
    intel_sub = intel.add_subparsers(dest="action")
    intel_sub.add_parser("trends", help="趋势洞察")
    intel_sub.add_parser("monitor", help="运行监控")

    # ── 闲鱼自动化 ──
    xianyu = sub.add_parser("xianyu", help="闲鱼自动化")
    xianyu_sub = xianyu.add_subparsers(dest="action")
    xianyu_sub.add_parser("list", help="生成商品列表")
    xianyu_sub.add_parser("publish", help="发布商品")

    # ── 商业引擎 ──
    biz = sub.add_parser("business", help="商业引擎")
    biz_sub = biz.add_subparsers(dest="action")
    bp = biz_sub.add_parser("bp", help="商业计划书")
    bp.add_argument("project", nargs="?", default="", help="项目名称")
    prd = biz_sub.add_parser("prd", help="产品需求文档")
    prd.add_argument("product", nargs="?", default="", help="产品名称")

    # ── 蜂群引擎 ──
    swarm = sub.add_parser("swarm", help="蜂群编排")
    swarm_sub = swarm.add_subparsers(dest="action")
    swarm_run = swarm_sub.add_parser("run", help="执行蜂群任务")
    swarm_run.add_argument("task", nargs="?", default="", help="任务描述")

    # ── 自学习 ──
    sub.add_parser("learn", help="自学习循环")

    # ── 服务 ──
    sub.add_parser("serve", help="启动Web仪表盘")

    # ── 调度 ──
    sched = sub.add_parser("schedule", help="定时任务管理")
    sched_sub = sched.add_subparsers(dest="action")
    sched_sub.add_parser("list", help="查看定时任务")
    sched_run = sched_sub.add_parser("run", help="手动执行")
    sched_run.add_argument("job_id", help="任务ID")

    # ── 健康检查 ──
    sub.add_parser("health", help="系统健康检查")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # Route to handler
    handler_map = {
        ("ceo", "strategy"): "agents.ceo:run_strategy",
        ("ceo", "review"): "agents.ceo:run_review",
        ("content", "xhs"): "content.xiaohongshu:generate",
        ("content", "video"): "content.video:generate",
        ("content", "seo"): "content.seo:generate",
        ("intel", "trends"): "intelligence.trends:run",
        ("intel", "monitor"): "intelligence.monitor:run",
        ("xianyu", "list"): "publish.xianyu:list_products",
        ("xianyu", "publish"): "publish.xianyu:publish",
        ("business", "bp"): "business.bp:generate",
        ("business", "prd"): "business.prd:generate",
        ("swarm", "run"): "agents.swarm:run",
        ("publish",): "publish.social_push:publish",
    }

    key = (args.command, getattr(args, "action", None))
    module_path = handler_map.get(key)
    if key == ("publish",):
        module_path = handler_map[("publish",)]

    if module_path:
        print(f"🔧 墨麟启动: {module_path}")
        print(f"📦 模块已就绪，等待 Hermes Agent 调度执行...")
        # In production, this delegates to Hermes Agent's tool system
        print("✅ 请通过 Hermes Agent 接口调用此模块")
    else:
        print(f"⚠️  未知命令: molin {args.command}")
        if hasattr(args, 'action'):
            print(f"   使用 'molin {args.command} --help' 查看子命令")
        else:
            print(f"   使用 'molin --help' 查看所有命令")


if __name__ == "__main__":
    main()
