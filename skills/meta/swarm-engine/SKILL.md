---
name: swarm-engine
description: Unified swarm orchestration engine — decompose complex tasks into role-based parallel agents, execute concurrently, and synthesize results. Merges agentic-engineering patterns, swarm orchestration, and subagent-driven development into one cohesive system.
version: 2.0.0
tags: [swarm, multi-agent, orchestration, parallel, delegation, workflow]
category: meta
related_skills: [molin-ceo-persona, self-learning-loop, archon-workflow, paperclip-company-os]
metadata:
  hermes:
    merged_from: [agentic-engineering, swarm-orchestration, subagent-driven-development]
---

# Swarm Engine — 统一蜂群引擎

## Overview

The unified orchestration engine for Hermes Agent. When a task is too complex for one agent, the Swarm Engine decomposes it into independent sub-tasks, spawns role-specialized agents in parallel, and synthesizes their outputs into a coherent result.

This replaces three separate skills (agentic-engineering, swarm-orchestration, subagent-driven-development) with one cohesive system.

## Core Loop

```
User Goal
    │
    ▼
┌─────────────────┐
│ 1. DECOMPOSE    │ ← CEO Persona: 四层意图理解 + 任务拆解
│ 独立子任务×3-4    │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. ROLE-MATCH   │ ← 7 predefined roles
│ Researcher       │
│ Backend          │
│ Frontend         │
│ Reviewer         │
│ Tester           │
│ Writer           │
│ Analyst          │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. SPAWN        │ ← delegate_task(tasks=[...])
│ 并行执行，各含独立上下文│
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. VERIFY       │ ← Never trust self-reports
│ 检查文件/测试/API │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. SYNTHESIZE   │ ← Combine + resolve conflicts
│ 统一交付物        │
└─────────────────┘
```

## When to Swarm

| Scenario | Swarm Size | Roles |
|----------|-----------|-------|
| Full-stack feature | 3-4 | Backend, Frontend, Test, Review |
| Research + Write | 2-3 | Research, Write, Review |
| Content production | 3-4 | Research, Write, Design, Review |
| Bug investigation | 2 | Debug, Research |
| Data analysis | 2-3 | Extract, Analyze, Visualize |
| Proposal/bid | 2-3 | Research, Write, Review |
| Single fix | 0 | Don't swarm — just do it |

## Integration with Company OS

Swarm Engine handles **tactical** execution (single mission, one shot). For **strategic** continuous operation, combine with Company OS patterns:

| Layer | Tool | Pattern |
|-------|------|---------|
| **Tactical** | `swarm-engine` | One mission → decompose → spawn → synthesize → done |
| **Strategic** | `paperclip-company-os` | Mission → heartbeat → autonomous work → governance → review |

**Example**: The daily morning report heartbeat (cronjob `3aed992deea3`) uses swarm-engine patterns internally but runs on a schedule via Company OS heartbeats. Swarm handles the "how to parallelize this check", Company OS handles the "why check at 9am every day and who approves the result."

```
Mission: "本周小红书内容"
    ├── Researcher → last30days + maigret + world-monitor
    ├── Writer → xiaohongshu-content-engine (5 posts)
    ├── Designer → cover_suggestions for each post
    └── Analyst → quality score + compliance check
```

## 3-Level Delegation

- **Level 1**: Simple task → do it yourself (no swarm)
- **Level 2**: Medium task → 2-agent swarm (eg. Research + Implement)
- **Level 3**: Complex mission → 3-4 agent swarm + synthesis

Never nest more than 2 levels deep.

## Pitfalls

1. **Over-swarming**: Not everything needs a swarm. Single-file fixes don't.
2. **Context starvation**: Each agent knows nothing about your conversation. Pass everything.
3. **Trusting self-reports**: Always verify file creation, test results, API calls.
4. **No cross-talk**: Design tasks to be truly independent.
5. **Timeout management**: Complex agent tasks need 5-10 min each.
