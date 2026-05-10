---
name: paperclip-company-os
description: Company operating system patterns from Paperclip (62K stars) — org chart,
  goal cascade, heartbeat scheduling, ticket system, budget control, and governance.
  Use when designing autonomous business operations, multi-agent coordination, or
  zero-human workflows.
version: 1.0.0
tags:
- company
- orchestration
- governance
- heartbeat
- budget
- org-chart
- paperclip
category: meta
related_skills:
- molin-ceo-persona
- swarm-engine
- self-learning-loop
metadata:
  hermes:
    source: https://github.com/paperclipai/paperclip
    stars: 62000
    molin_owner: CEO
min_hermes_version: 0.13.0
---

# Paperclip Company OS — 一人公司操作系统

## Overview

Design patterns from Paperclip (62K stars): the open-source orchestration layer for "zero-human companies." Paperclip models a company as an org chart with goals, budgets, heartbeats, and governance — exactly the missing management layer for our system.

**Core insight**: Paperclip doesn't build better agents. It builds a better COMPANY around agents.

## Six Design Patterns

### 1. Company Model (公司 = 组织架构)

Instead of a flat list of skills, structure as a company:

```
CEO (you, the human)
├── COO (molin-ceo-persona) — strategic decisions, task routing
├── Content Division
│   ├── 小红书专员 (xiaohongshu-content-engine)
│   ├── 视频制作 (pixelle-video)
│   └── SEO优化 (seo-machine)
├── Engineering Division
│   ├── 全栈开发 (agent-engineering-backend)
│   ├── 代码审查 (agent-engineering-code-reviewer)
│   └── QA测试 (agent-testing-reality-checker)
├── Growth Division
│   ├── 闲鱼运营 (xianyu-automation)
│   ├── 销售专员 (agent-sales-deal-strategist)
│   └── 营销策略 (agent-marketing-social-media)
├── Business Division
│   ├── 产品经理 (pm-create-prd)
│   ├── 财务分析 (trading-agents)
│   └── 市场研究 (pm-market-sizing)
└── Intelligence Division
    ├── 趋势预测 (mirofish-trends)
    ├── 情报监控 (world-monitor)
    └── OSINT调查 (maigret-osint)
```

Each agent has: Title, Role description, Reporting line, Budget, Approval level.

### 2. Goal Cascade (目标对齐)

Every task traces back to the mission. No orphan work.

```
Mission: "月收入 ¥30,000 的 AI 一人公司"
  ├── Goal 1: 闲鱼月收入 ¥20,000
  │   ├── Task: 上架商业计划书服务
  │   ├── Task: 优化简历服务文案
  │   └── Task: 每日回复客户消息
  ├── Goal 2: 小红书粉丝 5,000
  │   ├── Task: 本周发 5 篇笔记
  │   └── Task: A/B测试标题公式
  └── Goal 3: 猪八戒月收入 ¥10,000
      ├── Task: 每日扫描新项目
      └── Task: 投标 3 个高价值项目
```

When dispatching a task, always include: WHAT to do, WHY it matters (parent goal), HOW to measure success.

### 3. Heartbeat Scheduling (心跳机制)

Agents don't wait to be called — they wake up and work.

```
Daily heartbeat:
  09:00 — world-monitor: check for breaking news
  10:00 — maigret-osint: scan for competitor activity
  12:00 — xianyu-automation: process overnight messages
  18:00 — content division: prepare tomorrow's posts
  22:00 — trading-agents: daily market summary

Weekly heartbeat:
  Monday 09:00 — strategy review: mission progress
  Friday 18:00 — weekly report: revenue, costs, wins/losses

Hourly heartbeat:
  Every 60 min — xianyu: poll for new messages
  Every 3 hours — last30days: trending topics refresh
```

Each heartbeat: wake → check context → act → report → sleep.

### 4. Ticket System (工单追踪)

Every task is a ticket. Every ticket is tracked.

```
Ticket model:
  id: unique identifier
  goal: parent goal this serves
  agent: assigned agent/division
  status: pending | in_progress | done | blocked | cancelled
  created: timestamp
  heartbeat: last activity timestamp
  budget: allocated $/tokens
  spent: actual $/tokens spent
  output: deliverable produced
  audit: key decisions made
```

### 5. Budget Control (成本控制)

Every agent has a budget. When exhausted, they stop — no runaway costs.

```
Budget model (monthly per agent):
  CEO persona:      unlimited (always on)
  Content division: ¥200/month API costs
  Engineering:      ¥500/month (active projects)
  Growth:           ¥100/month (messaging/polling)
  Intelligence:     ¥300/month (searches/analysis)

Rules:
  - Agents track their own token usage
  - Warning at 70% budget consumed
  - Auto-pause at 90% — requires human approval to continue
  - Budget resets on the 1st of each month
```

### 6. Governance (治理)

You're the board. Approve, override, pause, or terminate any agent.

```
Governance levels:
  Level 0 (auto):     Reply to Xianyu messages, post scheduled content
  Level 1 (review):   New business proposals, pricing decisions >¥500
  Level 2 (approve):  New service offerings, major strategy changes
  Level 3 (board):    Mission change, new division creation, budget reallocation

Audit trail:
  - Every decision logs: who, what, why, when, cost
  - Configuration changes are versioned
  - Bad changes can be rolled back
```

## Application to Our System

### Immediate: Company Structure

Map our 6 domains to the company model. Each domain becomes a division with named agents, role descriptions, and reporting lines.

### This Week: Heartbeat Prototype

Implement one daily heartbeat:
- 早上 9 点自动检查闲鱼消息
- 汇总成一句话报告发到飞书

### Next: Goal Cascade

When dispatching any task via swarm-engine, always include the parent goal so agents understand WHY.

### Future: Budget + Ticket

Track token costs per task. Surface when agents are burning budget. Log decisions for audit.

## Key Difference from Swarm Engine

```
Swarm Engine:       "I have a task → spawn agents → get result → done"
Paperclip Company:  "I have a mission → agents work continuously →
                     check in on schedule → report → I govern"
                     
Swarm is TACTICAL (single mission execution).
Paperclip is STRATEGIC (continuous company operation).
```

We need BOTH. Swarm for one-shot complex tasks. Paperclip patterns for ongoing autonomous operations.