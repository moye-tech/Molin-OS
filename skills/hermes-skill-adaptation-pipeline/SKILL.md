---
name: hermes-skill-adaptation-pipeline
description: "Adapt external GitHub projects (Claude Code skills, Python frameworks, CLI tools) into Hermes Agent skills. Covers: condensing multi-file skill sets into single orchestrator SKILL.md, wrapping installed frameworks, creating reference/template files, patching downstream docs like molin-company-structure, and pushing to repo. Use when integrating external repos (not built for Hermes) into the Hermes OS skill system."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, adaptation, integration, hermes-os, conversion]
    related_skills: [skill-discovery, hermes-agent-skill-authoring, batch-yaml-frontmatter-injection, readme-standardization]
    molin_owner: CEO
---

# Hermes Skill Adaptation Pipeline

## Overview

When absorbing external GitHub projects into Hermes OS, the projects come in different forms:
- **Claude Code skill sets** — 5-15 individual SKILL.md files with orchestrator, designed for `~/.claude/skills/`
- **Python frameworks** — pip-installable tools like freqtrade with CLI commands and config files
- **CLI tools** — single-binary or script-based tools
- **Knowledge/SOP repos** — collections of markdown documentation and templates

This skill defines the **condensation + wrapping** pattern: convert multi-file external repos into single, well-structured Hermes skills.

## When to Use

- You're integrating a repo that has **10+ separate skill files** that need condensing
- You're wrapping a **pip-installable framework** as a Hermes agent capability
- You need to **patch downstream docs** (molin-company-structure, system overview) after integration
- You're adapting skills from **another agent ecosystem** (Claude Code, OpenClaw, Cursor)

## The Adaptation Recipe

### Pattern A: Condense Multi-File Skill Sets → Single Orchestrator

External skill repos (e.g., `ai-legal-claude` with 13 skills) use a design where each command has its own SKILL.md. For Hermes, condense all into one orchestrator-style SKILL.md:

```markdown
---
name: my-adapted-skill
description: "Summary <<250 chars covering ALL capabilities. Use when: <triggers>."
---
# Title

## Overview
[Covers ALL sub-capabilities in a table]

## When to Use
[Bullet triggers for each sub-command]

## Workflow
[Core orchestration flow — e.g., parallel agents → aggregation → report]

## Commands Guide
[One section per sub-capability with:
- Purpose
- Input format
- Process steps
- Output description
]

## Key Reference Tables
[Risk matrices, grading systems, category lists — moved from external files]

## Pitfalls
[External-specific + Hermes-specific pitfalls combined]

## Verification Checklist
```

**When to do this vs. separate skills:**
- ONE orchestrator if: the sub-capabilities are all called via the same trigger pattern and share data formats/scores
- SEPARATE skills if: each sub-capability has completely different triggers, data sources, and output formats

### Pattern B: Wrap Installed Python Frameworks

For pip-installable tools (like freqtrade), create a skill that:

```markdown
---
name: skill-name
---

## Quick Start
[Install command, init, first-run steps]

## Complete Command Reference
[All CLI commands with their purpose, example usage, and output format]

## Common Workflows
[End-to-end recipes: "do X → then Y → then Z"]

## Reference Tables
[Key parameters, scoring systems, configuration examples]

## Best Practices / Pitfalls
[Common mistakes, edge cases, performance tips]
```

**Key difference from Pattern A:** These skills teach the *agent* how to use the tool, they don't replace the tool. Include exact command syntax, expected output patterns, and error interpretation.

### Pattern C: Framework with Supporting Files

Add references and templates as child files:

```
skills/<name>/
├── SKILL.md                    # Main orchestrator
├── references/
│   ├── checklists.md           # Contract checklists, compliance lists
│   └── taxonomy.md             # Category hierarchies, scoring systems
└── templates/
    └── report-template.md      # Output templates with placeholders
```

## GitHub Clone Fallback Strategy

Git clone from GitHub often times out (TLS/network issues). Use this fallback:

```bash
# Primary: git clone (fast path)
git clone https://github.com/owner/repo.git --depth 1

# Fallback: GitHub API readme (when git times out >30s)
curl -sL "https://api.github.com/repos/owner/repo/readme" | \
  python3 -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# Read specific file from repo
curl -sL "https://api.github.com/repos/owner/repo/contents/path/to/file" | \
  python3 -c "import sys,json,base64; d=json.load(sys.stdin); print(base64.b64decode(d['content']).decode())"

# List repo contents
curl -sL "https://api.github.com/repos/owner/repo/contents/" | \
  python3 -c "import sys,json; [print(i['name'],i['type']) for i in json.load(sys.stdin)]"
```

**When to use:** If `git clone` doesn't return within 30s, switch to API. The API has rate limits (60 req/hr unauthenticated) but for README + 2-3 key files it's sufficient.

### Pattern D: Zero-Dependency Weave

Some skills don't need external projects at all — they weave together existing Hermes tools and skills into a new workflow:

```markdown
# Example: Zero-dep skill weaves existing Hermes tools
## Core capabilities → mapped to Hermes primitives:
- FAQ knowledge base → memory + session_search
- Auto-reply templates → skill commands with intent routing
- Ticket management → todo system (P0-P3 priority)
- Satisfaction surveys → clarify + template messages
- Platform messaging → send_message + xianyu-automation
- Compliance checks → molin-legal (GDPR/CCPA)
- Multi-platform publishing → social-push-publisher
- SEO optimization → seo-machine
- Video localization → ffmpeg-video-engine
```

**When to use this pattern:** When there's no good external tool for the job (e.g., Chinese customer service is all heavy deployment). The skill becomes a *workflow orchestrator* that chains existing capabilities.

**Key difference from Patterns A-C:** The skill is NOT wrapping an external project. It's documenting an integration pattern that already exists in the Hermes OS ecosystem. The value is in the workflow — the sequence, the data flow between tools, and the edge-case handling.

## Parallel Skill Creation with delegate_task

For batch integration (3-5 skills at once), use delegate_task to CREATE skills in parallel:

```python
# Each subagent creates one complete skill
tasks = [
    {"goal": "Create skill-A from project-X", "context": "..."},
    {"goal": "Create skill-B from project-Y", "context": "..."},
    {"goal": "Create skill-C (zero-dep weave)", "context": "..."},
]
# All run concurrently. Each writes a complete SKILL.md to ~/.hermes/skills/
# Benefits: parallel I/O, isolated context, no cross-contamination
# After all complete: sync to repo, update downstream docs, push
```

**When to use:** 3+ skills to create, each with distinct source material (different repos, different patterns). Don't use for 1-2 skills — the overhead of delegation (context setup, result aggregation) isn't worth it.

## Downstream Patching

After creating the skill, always update:

### 1. molin-company-structure
- Patch the subsidiary entry: update `molin_owner`, add skill reference, boost T-tier if applicable
- Add to startup priority list under the subsidiary

### 2. System overview docs
- Update skill count, subsidiary table, and "Remaining gaps" section
- Add integration notes (star count, source repo, key features)

### 3. Memory
- Save the integration as a compact memory entry: source repo + star count + key capabilities + what changed (T-tier boost, skill count, GitHub commit hash)
- Total memory: ≤350 chars per integration entry

### 4. Gap Analysis document
- Mark the gap as resolved (where applicable)

## Reference: ai-legal-claude Adaption (Example)

**Source:** zubair-trabzada/ai-legal-claude ⭐1.2k — 13 SKILL.md files (legal-review, legal-risks, legal-nda, legal-privacy, legal-compliance, legal-terms, legal-compare, legal-plain, legal-negotiate, legal-missing, legal-freelancer, legal-agreement, legal-report-pdf) + 5 agent files + 1 orchestrator

**Adaptation:** Condensed to 1 `molin-legal/SKILL.md` (7.1KB) + 1 reference + 1 template

**Key decisions:**
- Single orchestrator because all skills share the risk scoring system (1-10), contract templates, and are triggered by `/legal` prefix
- 5-agent parallelization pattern preserved via `delegate_task` in Hermes
- Risk scoring matrix (11 categories) and contract safety score (0-100, A+~F) moved to reference tables in the main SKILL.md
- Legal disclaimer pattern preserved on every output

## Reference: Freqtrade Adaption (Example)

**Source:** freqtrade/freqtrade ⭐34k+ — Python framework, CLI tool

**Adaptation:** Wrapped as 1 `molin-trading/SKILL.md` (7KB)

**Key decisions:**
- Installed via `pip install --break-system-packages freqtrade` (freqtrade v2026.4)
- Verified with `freqtrade --help` — 20+ subcommands exposed
- Full command reference included (6 core workflows: init → data → backtest → hyperopt → visualize → trade)
- Strategy development section: minimal class template, common indicator table (RSI/MACD/SMA/EMA/Bollinger/ATR), stop-loss patterns
- Pitfalls from real trading: overfitting, future function, slippage, fees, small-sample validation
- Noted: requires exchange API keys for real trading; config created via `freqtrade new-config`

## Common Pitfalls

1. **Git clone timeout** — Don't keep retrying. Switch to GitHub API within 30s. `curl api.github.com/repos/owner/repo/readme` is the fastest path to understanding a project
2. **Forgetting to verify the install worked** — Always run `--help` or a test command after pip install
3. **Not creating refs/templates** — External repos often have useful checklists, templates, and reference tables; don't lose them by only writing the SKILL.md
4. **Over-condensing** — If sub-capabilities have different triggers and data sources, split into separate skills
5. **Missing the orchestrator pattern** — For skill-set repos, the orchestrator (the routing layer) is the most important file to preserve
6. **Skipping downstream docs** — molin-company-structure and system docs are the system's source of truth; out-of-date docs = broken mental model
7. **Not checking for test contracts/samples** — Repos like ai-legal-claude come with `sample-contract.pdf` or `generate_sample_contract.py` — use these to verify the system works end-to-end
8. **Parallel creation without explicit context** — `delegate_task` subagents have NO memory of the parent conversation. Pass ALL relevant info (exact file paths, YAML frontmatter format, star counts, owner name, install commands) in the context field. The 300-500 char summary is worth it.

## Verification Checklist

- [ ] Project cloned/installed and verified working
- [ ] Hermes SKILL.md created with proper frontmatter, molin_owner, description
- [ ] All sub-capabilities documented (not just the main one)
- [ ] References and templates copied/adapted (if applicable)
- [ ] molin-company-structure updated (T-tier, skill reference, products)
- [ ] System documentation updated
- [ ] Gap analysis updated (if applicable)
- [ ] GitHub commit + push
- [ ] Memory updated (compact, ≤350 chars)
