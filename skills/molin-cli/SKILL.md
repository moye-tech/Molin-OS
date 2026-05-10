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

# Trading
python -m molib trading analyze --market-type crypto --symbol BTC/USDT
python -m molib trading signal --symbol BTC/USDT

# Finance
python -m molib finance record --type expense --amount 100 --note "API"
python -m molib finance report

# Planning
python -m molib plan create --title "任务" --description "描述"
python -m molib plan decompose --plan-id ID

# Handoff
python -m molib handoff list
python -m molib handoff route --task "内容创作"

# Cost
python -m molib cost report
python -m molib cost alert
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

8 cron jobs managed by Hermes scheduler:
- 08:00 墨思情报银行 — intelligence gathering
- 09:00 墨迹内容工厂 — content generation
- 09:00 CEO每日简报 — daily briefing
- 10:00 墨增增长引擎 — growth analysis
- 10:00 每日治理合规 — compliance check
- 12:00 系统状态快照 — system snapshot
- 15/45min 闲鱼消息检测 — xianyu message check
- Fri 10:00 自学习进化 — self-improvement

## Pitfalls

- Never run molib commands in execute_code() — use terminal()
- Always check `python -m molib health` after system changes
- Feishu output must follow molin-markdown CEO style (no markdown formatting)
- Cron jobs deliver to feishu channel oc_94c87f141e118b68c2da9852bf2f3bda
