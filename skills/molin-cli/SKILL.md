---
name: molin-cli
description: Operate Molin-OS via the molib CLI. Use when running molib commands, managing Workers, checking system health, or orchestrating Molin-OS operations.
version: 1.0.0
min_hermes_version: 0.13.0
dependencies: [molin-markdown]
tags: [molin-os, cli, molib, operations]
category: infrastructure
---

# Molin CLI Skill

Operate Molin-OS through the `python -m molib` CLI interface.

## Architecture

```
Hermes (brain) → terminal tool (nerve) → python -m molib <cmd> (muscle) → result
```

Never run molib commands in execute_code — always use terminal().

## Core Commands

```bash
# System
python -m molib health                     # Full system health check
python -m molib help                        # List all commands

# Query (MQL)
python -m molib query "FROM skills WHERE category = 'tools' LIMIT 10"
python -m molib query --search "keyword"
python -m molib query --sources

# Manifest
python -m molib manifest validate
python -m molib manifest fix

# Content
python -m molib content write --topic "主题" --platform xhs
python -m molib content publish --platform xhs --draft-id ID

# Intelligence
python -m molib intel trending
python -m molib intel predict --topic "AI Agent"
python -m molib intel firecrawl scrape --url URL

# Xianyu
python -m molib xianyu reply --msg-id ID --content "回复"

# Trading (TradingAgents-CN — multi-agent)
python -m molib trading signal --symbol 000001 --market a-share
python -m molib trading analyze --symbol BTC/USDT --market crypto
python -m molib trading research --ticker 000001

# Finance
python -m molib finance record --type expense --amount 100 --note "API"
python -m molib finance report

# Cost (BudgetGuard — API cost tracking)
python -m molib cost report                # Daily spend breakdown
python -m molib cost check [provider]      # 80% warning / 100% blocked
python -m molib cost reset                 # Reset daily counters

# Planning
python -m molib plan create --title "任务" --description "描述"
python -m molib plan decompose --plan-id ID

# Handoff
python -m molib handoff list
python -m molib handoff route --task "内容创作"

# Swarm (cross-agency orchestration)
python -m molib swarm list                 # List handoff pathways
python -m molib swarm run <pattern>        # Run predefined workflow
python -m molib swarm visualize            # ASCII flow diagram

# Index (CocoIndex — local file sync)
python -m molib index watch --path /path   # Watch directory
python -m molib index query --term "关键词" # Search indexed content
python -m molib index sync                 # Full re-scan
python -m molib index stats                # Index statistics

# Bitable (Feishu multi-dim tables)
python -m molib bitable schema             # Show table schemas
python -m molib bitable write <table>      # Write record (orders/content/finance)

# Memory (distillation engine)
python -m molib memory distill             # Trigger working→semantic distillation
python -m molib memory stats               # Memory system statistics
```

## Worker System

22 Workers mapped to 20 subsidiaries. Route tasks automatically:

```bash
python -m molib handoff route --task "帮我写小红书文案"
# Auto-routes to 墨笔文创 (content_writer.py)

python -m molib handoff route --task "分析BTC趋势"
# Auto-routes to 墨投交易 (trading.py)
```

## Health Check

```bash
python -m molib health
# Returns JSON with all module statuses
```

Check for:
- ✅ ok — module operational
- ❌ error — module broken, need attention

## Cron Jobs

18 cron jobs managed by Hermes scheduler:
- 03:00 墨麟OS系统备份 — dual backup (GitHub + local HDD)
- 06:00 Mon 墨梦记忆蒸馏 — weekly memory consolidation
- 07:00 夸克云盘增量备份 — Quark drive backup
- 07:30 API成本预警 — budget threshold check
- 08:00 墨思情报银行 — intelligence gathering
- 09:00 墨迹内容工厂 — content generation (flywheel baton 2)
- 09:00 CEO每日简报 — daily briefing
- 10:00 墨增增长引擎 — growth analysis (flywheel baton 3)
- 10:00 每日治理合规 — compliance check
- 11:00 内容效果回收分析 — content performance analysis
- 12:00 系统状态快照 — system snapshot
- 14:00 竞品价格内容监控 — competitor monitoring
- 15,45min 9-21h 闲鱼消息检测 — xianyu message check
- 17:00 CEO下班汇总简报 — end-of-day summary
- Every 2h 墨麟OS GitHub双向同步 — repo sync
- Fri 10:00 自学习进化 — self-improvement
- 1st 09:00 月度财务对账 — monthly finance report
- 15th 10:00 技能库健康审计 — skill health audit

## Pitfalls

- Never run molib commands in execute_code() — use terminal()
- Always check `python -m molib health` after system changes
- Feishu output must follow molin-markdown CEO style (no markdown formatting)
- Cron jobs deliver to feishu channel oc_94c87f141e118b68c2da9852bf2f3bda
