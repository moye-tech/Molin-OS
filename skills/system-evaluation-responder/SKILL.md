---
name: system-evaluation-responder
description: "Systematic protocol for digesting external system evaluation reports — map defects to actual vs already-fixed vs real gaps, prioritize fixes against existing roadmap, and execute a batched fix plan. Use when: receiving an architecture review, code audit, third-party evaluation, or diagnostic report about the Hermes OS system."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [evaluation, audit, review, diagnosis, roadmap, planning]
    related_skills: [molin-memory, self-learning-loop, skill-discovery, molin-governance, molin-company-structure]
    molin_owner: CEO
---

# System Evaluation Responder Protocol

## Overview

When you receive a system evaluation report (architecture review, code audit, third-party diagnostic), follow this five-phase protocol. The key insight: **evaluations often compare against an older baseline** — you must first distinguish "already fixed" from "real gaps" before acting.

## Phase 1: Digest & Map

### 1.1 Structure the report

Read the full report. Identify:

- **Scoring dimensions** (architecture, implementation, autonomy, etc.)
- **Specific defect claims** with supporting evidence (code snippets, file paths, metrics)
- **Roadmap/recommendations** (phased or unordered)
- **External assumptions** (what version/baseline they evaluated)

### 1.2 Create a defect mapping table

| # | Defect | Report Evidence | Our Current State | Verdict |
|---|--------|----------------|-------------------|---------|
| 1 | "No persistent memory" | `decisions_log = []` | ✅ Hermes `memory()` tool + session_search | Already fixed |
| 2 | "Self-learning returns []" | `_evaluate()` returns hardcoded dict | ✅ `molin_learn.py` real evaluate→absorb→integrate | Already fixed |
| 3 | "X subsidiary unstaffed" | YAML has no SKILL.md | ✅ `molin-xxx` exists | Already fixed |
| 4 | "Real gap: no vector RAG" | ChromaDB not used | ❌ Need to build `molin-memory` | Real gap |

**Verdict categories:**
- ✅ **Already fixed** — system has addressed this since the report baseline
- ✅ **Misunderstanding** — report misread the architecture (e.g., evaluated old Python prototype vs current Hermes Agent ecosystem)
- ⚠️ **Partially addressed** — concept exists but implementation needs depth
- ❌ **Real gap** — genuine deficiency not yet addressed

### 1.3 Prioritize real gaps

| Priority | Criteria | Example |
|:--------:|----------|---------|
| **P0** | Blocks other subsystems, directly impacts revenue, or makes the system look broken | No persistence, empty self-learning |
| **P1** | High impact, isolated scope, can be done in 1 session | Missing subsidiary skill, single feature gap |
| **P2** | Architectural improvement, multi-session effort | Event bus, OKR automation, self-healing |
| **P3** | Polish, expansion, nice-to-have | MCP serverization, Grafana dashboard |

## Phase 2: Communicate Findings

Present a clear summary to the user showing:

```
## Report Verdict

| Scoring Dimension | Report Score | Reality | Delta |
|-------------------|:------------:|:-------:|:-----:|
| Architecture | 78 | 85 | +7 (better than reported) |
| Implementation | 42 | 72 | +30 (278 skills vs 16) |
| Autonomy | 25 | 55 | +30 (cronjobs + agents working) |

## Defect Status (7 total)
  ✅ Already fixed: 4
  ❌ Real gaps:    3 (P1×2, P2×1)
```

## Phase 3: Execute Fix Plan

For each real gap, execute in priority order. Batch independent fixes into parallel workstreams.

### Real gap patterns and their standard fixes:

| Gap Pattern | Standard Fix | Typical Effort |
|-------------|-------------|----------------|
| No persistence | Build `molin-memory`: ChromaDB + SQLite | 1 session |
| Zero-subsidiary coverage | `molin-xxx` skill: research GitHub projects → absorb → write SKILL.md | 1-3 sessions (batch by subsidiary) |
| Stub self-learning | `molin_learn.py`: evaluate→absorb→integrate→retire scripts + cronjob | 1 session |
| No cross-subsidiary comms | SQLite events table (pub/sub) in `molin-memory` | Added to persistence session |
| No vector RAG | ChromaDB collections per subsidiary + context injection hook | Part of `molin-memory` |
| Stub governance | L0-L3 enforcement in governance skill + SQLite audit log | 1 session |
| No education/customer-service skill | Research GitHub: DeepTutor ⭐23.2k, human-skill-tree ⭐517 → absorb → create skill | 1 session |

## Phase 4: Track Progress

After each fix session, update the defect mapping table. Use commit messages and memory to track:

```
memory(action='replace', target='memory',
  old_text='P3.1 progress...',
  content='P3.1 complete: fixed 3/7 defects. Remaining: P2×1, P3×1. (commit abc1234)')
```

Maintain one master tracking entry in memory, replacing it as progress advances.

## Phase 5: Close the Loop

After all priority gaps are closed, generate a closure report:

```
# 评估报告修复完成报告

## 覆盖率
  总缺陷: 7
  已修复: 7 (100%)
  
## 新增能力
  - molin-memory (ChromaDB + SQLite 双写)
  - molin_learn (四阶段自学习闭环)
  - 5个新 molin-xxx skills (教育/法务/交易/数据/出海/客服/影音)
  
## 系统变化
  技能: 267 → 280
  子公司覆盖: 19/22 → 22/22
  GitHub commit: abc1234..def5678
```

## Reference: This Session's Pattern

During the 2026-05-04 session:
1. Received 1420-line HTML evaluation report from external tool
2. Report scored system: Arch 78, Code 42, Autonomy 25 (avg 45)
3. **Key discovery**: Report evaluated old Python `molin cli.py` prototype (16 SKILL.md), not current Hermes ecosystem (278 skills)
4. 7 defect claims → Only 3 were real gaps after mapping
5. Fixed in order: molin-memory (P1) → molin_learn (P1) → molin-education (P1)
6. Results: 3 sessions, 280 skills, 22/22 subsidiaries covered, all 7 defects closed

## Common Pitfalls

1. **Assuming the evaluation is about the current system** — Reports often evaluate stale artifacts. Always check the baseline date and code version.
2. **Fixing everything the report says** — Some "defects" are intentional design choices (e.g., using Hermes Agent tools vs custom Python). Understand before fixing.
3. **Not checking for pre-existing solutions** — Hermes ecosystem has built-in memory, tools, cron, delegation. Don't rebuild what already exists.
4. **Over-engineering to meet the report's vision** — The evaluation is one perspective. Prioritize fixes that align with user's business goals, not just report scores.
5. **Letting perfect be the enemy of good** — A working SQLite events table > a beautifully designed Redis pub/sub that never gets built.
