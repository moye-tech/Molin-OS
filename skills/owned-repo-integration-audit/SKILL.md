---
name: owned-repo-integration-audit
description: Audit multiple owned fork/clone repositories against the current Hermes
  system to identify what's already integrated and what's missing. Produces a prioritized
  integration roadmap with effort estimates.
version: 1.0.0
tags:
- gap-analysis
- integration
- codebase-audit
- roadmap
related_skills:
- decompiled-codebase-extraction
- skill-discovery
- codebase-inspection
- github-repo-management
metadata:
  hermes:
    molin_owner: 墨码（软件工坊）
min_hermes_version: 0.13.0
---

# Owned Repository Integration Audit

When the user asks "compare my fork projects with the system to see what's missing," systematically audit each owned repo against the running Hermes system and produce a component-by-component gap analysis.

## When to Use

- User says "看看还有哪些没有集成" (check what's not integrated yet)
- User references multiple fork/clone repos they own (moye-tech/*)
- User wants to know what value each fork project brings to the current system
- You need to produce an integration roadmap for owned repositories

## Workflow

### Phase 1: Discover Local Repos

Find all git repos on the system:

```bash
find /home/ubuntu -maxdepth 3 -name ".git" -type d 2>/dev/null
```

Check each repo's remote to confirm it's a user-owned fork:

```bash
cd <repo> && git remote -v
```

Key repos to look for:
- `moye-tech/claude-code` — Reverse-engineered Claude Code CLI
- `moye-tech/molin-ai-intelligent-system` — 墨麟 AI 智能系统架构参考
- `moye-tech/Molin-OS` — Molin OS 墨麟AI一人公司操作系统
- Any other `moye-tech/*` repos

### Phase 2: Map Each Repo's Structure

For each repo, understand its architecture at two levels:

**Level 1 — Directory/File Structure:**
```bash
find <repo> -maxdepth 2 -type f -o -type d | sort | head -60
```

**Level 2 — Key Modules (depth varies by repo):**

For **claude-code** repos:
```bash
# Tool registry — the complete list
ls src/tools/ 2>/dev/null

# Architecture components
ls src/bridge/ 2>/dev/null  # Remote/Bridge control
ls src/daemon/ 2>/dev/null  # Daemon mode
ls src/remote/ 2>/dev/null  # Remote sessions
ls src/state/ 2>/dev/null   # State management
```

For **molin-ai-intelligent-system** repos:
```bash
# Core CEO/decision/planning
find core/ -maxdepth 2 -name "*.py" | sort

# Worker agencies (the 22 subsidiaries)
ls agencies/workers/

# Infrastructure
find infra/ -maxdepth 2 -name "*.py" | sort

# Integrations / bridges
find integrations/ -maxdepth 2 -name "*.py" | sort

# Other key dirs
ls hermes_fusion/ strategy/ sop/ external/
```

For **Molin-OS** repos:
```bash
# Python modules
find molin/ -name "*.py" | sort

# Available skills
find skills/ -name "*.md" | sort | head -60
```

Use `wc -l` to gauge module size — small files may be stubs or empty.

### Phase 3: Snapshot Current Hermes System

Get the full skills list:

```python
from hermes_tools import terminal
result = terminal("hermes skills list")  # or use skills_list tool
```

Also check available native tools (browser_, terminal, cronjob, etc.) to understand the built-in capability baseline.

### Phase 4: Component-by-Component Cross-Reference

For each component found in Phase 2, classify against current Hermes:

| Status | Meaning |
|:-------|:--------|
| ✅ 已覆盖 | Functionally equivalent — Hermes has it via skill/tool |
| ⚡ 部分 | Partial overlap — concept exists but implementation differs |
| 🔴 未集成 | No equivalent — should be in the integration plan |
| SKIP | Not applicable (OS-specific, deprecated, test code) |

**Classification heuristics:**

**Tool-level comparison** (claude-code tools vs Hermes tools):
- Check if Hermes has a built-in tool with the same function (e.g., `browser_navigate` = `WebBrowserTool`)
- Check for a skill that provides equivalent capability (e.g., `cronjob` tool = `ScheduleCronTool`)
- Claude Code tools that are core (AgentTool, LSPTool) but absent from Hermes = 🔴 HIGH

**Architecture-level comparison** (not tools, but system patterns):
- Feature flags — Hermes has no feature flag system = 🔴 HIGH
- Bridge/Remote control — Hermes has no remote session management = 🔴 HIGH
- Memory systems — compare depth (Hermes has basic memory, but lacks vector DB = ⚡ 部分)
- Event bus — Hermes has no event-driven architecture = 🔴

**Skill-level comparison** (molin-ai-ref workers vs Hermes skills):
- 22 workers map to molin/* skills — check if each has a corresponding skill
- Example: `agencies/workers/ip_worker.py` → `skills/business/molin/ip-content/SKILL.md`

### Phase 5: Categorize Findings

Organize into three source categories:

```
## A. [Repo Name] — [Component count]个组件

### 独有且未集成
[Components with no Hermes equivalent]

### 架构层可参考
[Architectural patterns worth studying, not direct tools]

### 已覆盖
[Components already in Hermes]
```

### Phase 6: Produce Prioritized Roadmap

Rank integration candidates:

| Priority | Label | Effort | Criteria |
|:---------|:------|:-------|:---------|
| 🔥🔥 HIGH | 立即集成 | 1-5天 | Provides new capability, high reuse, low effort |
| 🔥 HIGH | 高价值 | 2-5天 | Significant capability gap, moderate effort |
| ⚡ MEDIUM | 有价值 | 2-7天 | Niche but useful, not urgent |
| 🟢 LOW | 可做可不做 | varies | Edge case, low frequency use |

**Roadmap format:**

```
▎STEP 1: [Name] (X-Y天)
  ├─ Source: [repo/path]
  └─ Approach: [how to integrate]

▎STEP 2: [Name] (X-Y天)
  ...
```

### Phase 7: Update Memory

Save key findings to memory so future sessions can pick up where you left off:

```python
# After completing the audit, save:
# - Which repos were analyzed
# - Priority order determined
# - Any blockers or dependencies discovered
```

Save as memory (not a skill update) since the specific integration state is session-dependent.

## Pitfalls

1. **Don't trust directory names alone** — always check if a file is a stub (3 lines with `export {};` or auto-generated) vs real implementation. Use `wc -l` to spot stubs.
2. **Tools vs architecture distinction** — claude-code has 56 tool directories, but tools like `EnterPlanModeTool` are just UI wrappers around a concept Hermes already has (`plan` skill). The high-value stuff is often NOT in tools/ but in architectural directories (bridge/, daemon/, remote/).
3. **Hermes skills are growing fast** — always refresh the skills list before comparing. What wasn't there last month may exist now (e.g., `native-mcp` skill).
4. **Don't count claude-code's DAEMON/COORDINATOR as "not integrated"** if Hermes has equivalent concepts under different names. Use functional equivalence, not name matching.
5. **Repo may have old Hermes source** — `molin-ai-ref/external/hermes-agent/` is a reference copy of old Hermes, not a component to integrate.
6. **Feature flags in claude-code are 3-layer** — build-time macros (Bun `-d` defines), runtime env vars (`FEATURE_X=1`), and env-less remote gates. Don't report them as a single thing.
7. **Component count tells you surface area** — 35 bridge files = major architecture, 3 daemon files = smaller scope. Use file count + line count to gauge integration effort.

## Templates

### Gap Analysis Table

```
┌──────┬──────────────────────────────┬────────────────────┬──────────┐
│ 组件  │ 功能描述                      │ 当前 Hermes 状态    │ 集成度   │
├──────┼──────────────────────────────┼────────────────────┼──────────┤
│ [name]│ [description]                │ [status]            │ [emoji]  │
└──────┴──────────────────────────────┴────────────────────┴──────────┘
```

### Priority Summary

```
🔥🔥 HIGH:
  1. [Component] [effort] — [why]

🔥 HIGH:
  2. [Component] [effort] — [why]

⚡ MEDIUM:
  3. [Component] [effort] — [why]
```