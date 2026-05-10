---
name: skill-discovery
description: Systematically research external GitHub repos, evaluate integration value
  for Hermes Agent, and produce tiered adoption roadmaps.
version: 1.0.0
metadata:
  hermes:
    tags:
    - skills
    - evaluation
    - research
    - integration
    - github
    related_skills:
    - swarm-engine
    - karpathy-coding-principles
    - hermes-agent-skill-authoring
    - self-learning-loop
    molin_owner: CEO
min_hermes_version: 0.13.0
---

# Skill Discovery & Evaluation

When the user drops a list of GitHub repos (bulk URLs, curated list, "can we use these"), systematically evaluate each and produce a tiered integration roadmap. Do NOT evaluate one-by-one sequentially — batch and parallelize.

## Triggers

- User shares 3+ GitHub URLs asking "can we use/integrate these"
- User asks "what skills should I install" or "find good skills for Hermes"
- User wants to assess external projects for compatibility
- User uploads a zip file containing a project to evaluate (unzip → list structure → read key files → assess)

## Workflow

### Phase 1: Categorize

Group the repos by type before researching:

| Category | Examples |
|----------|----------|
| Skills/KB (directly convertible) | SKILL.md collections, curated lists |
| Best Practices/Guides | Dotfiles, CLAUDE.md, workflow docs |
| Tools/CLI (executable) | CLI tools, browser automation |
| Agent Frameworks | Competitor agents (OpenClaw, Codex CLI) |
| Already Covered | Memory systems (Hermes has built-in), the platform itself |

### Phase 2: Parallel Research

Split into batches of 3-4 repos per `delegate_task` call. For each repo gather:
- Stars, last commit date, language
- README summary (first ~80 lines)
- Whether it explicitly mentions Hermes/OpenClaw/SKILL.md compatibility
- Production readiness signals (tests, CI, release tags, community)

### Phase 3: Handle Failures

**Clone timeouts (most common):** Large repos (>100MB) or slow network cause 600s timeouts in subagents.

**Escalation path (follow in order):**

Fix 1 — sparse checkout (solves ~80% of timeout cases):
```bash
git clone --depth 1 --filter=blob:none --sparse <repo-url> <dir>
cd <dir>
git sparse-checkout set README.md 'key-dir/*'
```
Skips large binary assets (SVGs, GIFs, images) that bloat clone time.

Fix 2 — direct terminal clone (faster than subagent):
When delegate_task itself times out, run the clone as a direct terminal command with `timeout=60` or `timeout=120`. Direct terminal is typically 3-5x faster than subagent terminal for network-bound operations.

Fix 3 — GitHub API tree listing (no clone needed):
If git clones fail entirely (network issues), use the GitHub API to discover files:
```bash
curl -s 'https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1' | python3 -c \
  "import sys,json; d=json.load(sys.stdin); \
   [print(p['path']) for p in d.get('tree',[]) if p['path'].endswith('.md')][:60]"
```
Then fetch individual files from raw.githubusercontent.com. This bypasses git entirely.

Fix 4 — README-only evaluation (last resort):
If even API tree listing times out, fetch only the README:
```bash
curl -sL 'https://raw.githubusercontent.com/<owner>/<repo>/main/README.md' | head -200
```

**Triple-timeout rule:** If delegate_task times out 3 consecutive times on the same task category, stop using subagents for that task. Switch to direct tools (terminal, execute_code, write_file).

### Phase 4: Tiered Assessment → Aggressive Absorption

### Phase 4: Tiered Assessment → Aggressive Absorption

**Core philosophy: 进化不是净化，是吸收。** The user wants maximum capability expansion, not a curated reading list. Default stance: **convert unless there's a hard reason not to.** When the user says "进化", they mean "make the system more capable by absorbing everything useful."

Assign each repo to one of three tiers:

| Tier | Label | Criteria | Action |
|------|-------|----------|--------|
| 🔥 Tier 1 | 立即转化 | Has Hermes install path, SKILL.md format, or trivially convertible. | **Convert immediately** — write SKILL.md in the same pass |
| 🟡 Tier 2 | 主动吸收 | Valuable concepts/patterns but needs format conversion or isn't directly pluggable. | **Convert anyway** — distill the concept into a Hermes skill. Don't just bookmark it. |
| 🔴 Tier 3 | 硬跳过 | Competitor framework (already covered), deprecated/404, legally risky (hacking tools, ToS violations, reverse-engineered IP), empty repos. | Skip with one-line reason. Only skip when there's a genuine blocker. |

**Key change from v1:** Tier 2 is no longer "参考学习" — it's "主动吸收". If TradingAgents has a great multi-agent financial analysis pattern, don't just note it. Create a `trading-agents` skill that teaches the agent that pattern. If MiroFish has swarm prediction, make it a `mirofish-trends` skill. The user wants MORE capabilities, not a curated reading list.

### Phase 5: Produce Roadmap

Output a phased integration plan:

```
Phase 1 (today):     Install the 2-3 fire-and-forget items
Phase 2 (this week): Convert the high-value skill collections
Phase 3 (reference): Bookmark for learning, no immediate action
```

### Phase 6: Batch Skill Import

When importing 20+ skills from an external repo, use `execute_code` with a batch curl + write_file loop. See `references/batch-import-technique.md` for the full code pattern.

Key principles:
- **Fetch from raw.githubusercontent.com, not git clone** — faster and immune to clone timeouts
- **Use `execute_code` not `delegate_task`** — subagents time out on 50+ file operations; direct execute_code handles them fine
- **Batch size: 8-10 files per curl round** — avoid overwhelming the connection
- **Retry failed files separately** — 10-20% will fail on first pass due to network hiccups
- **Create INDEX.md per skill set** — walk the directories and auto-generate a catalog with descriptions
- **Write SKILL.md with proper Hermes frontmatter** — name, description, version, tags, category, source URL

## Key Rules

- **Always parallelize** — never evaluate repos one-by-one. Use `delegate_task` with batches.
- **Be honest about quality** — call out alpha toys, abandoned repos, and vaporware. User trusts you to filter noise.
- **Convert external skills to Hermes format** — OpenClaw/Claude Code skills often use different conventions. Note format gaps.
- **Check for existing Hermes skills FIRST** — don't reinvent. Hermes already has memory, browser, terminal, delegation built in.
- **Last commit date matters** — anything >6 months stale on a fast-moving platform (Xiaohongshu, browser automation) is likely broken.

### 🧬 Aggressive Absorption Mode (用户说"进化")

When the user says keywords like "进化", "吸收", "集成更多", or "更全能":
- **Convert Tier 2 as well** — don't stop at Tier 1. Tier 2 "仅参考" projects with >5K stars and active maintenance should ALSO be converted to skills.
- **Err on the side of absorption** — a skill capturing a pattern is better than a bookmark.
- **Prioritize by uniqueness** — if the concept doesn't exist in our system, convert it even if format differs.
- **The user's intent is expansion, not curation.** When in doubt, convert.

## Output Format

Present the evaluation as:

```
# N 个项目 × 集成评估报告

## 📊 总览（Tier distribution bar）

## 🔥 Tier 1: 直接集成（X 个）
| # | 项目 | 价值 | 安装方式 |

## 🟡 Tier 2: 主动吸收（X 个）
| 项目 | 价值 | 转换方式 |

## 🔴 Tier 3: 不需要（X 个）
| 项目 | 原因 |

## 🗺️ 推荐路线图
Phase 1 / 2 / 3
```

## Known High-Value Sources

These repos have been vetted and are worth checking when the user wants to expand skills:

| Repo | What | Integration |
|------|------|-------------|
| `sickn33/antigravity-awesome-skills` | 1,443+ SKILL.md files | Mass-convert to Hermes |
| `VoltAgent/awesome-openclaw-skills` | 5,200+ OpenClaw skills | Pattern reference |
| `mvanhorn/last30days-skill` | Social search engine | Has Hermes install path |
| `shanraisshan/claude-code-best-practice` | Coding best practices | Convert to skill |
| `phuryn/pm-skills` | 65 PM skills | Convert to skill set |
| `msitarzewski/agency-agents` | AI agent personalities | Convert to skill set |
| `moye-tech/molin-ai-intelligent-system` | 一人公司AI系统 (CEO→Manager→Worker), 20 subsidiaries, Xianyu/Xiaohongshu automation | Convert key prompts/workers to Hermes skills |
| `paperclipai/paperclip` | 62K-star company OS — org charts, goals, budgets, heartbeats, governance | Convert core patterns to skills |
| `ruvnet/ruflo` | 37K-star multi-agent swarm orchestration (Claude Code plugin) | Architecture reference — swarm patterns, self-learning |

## Phase 7: Monetization Assessment

When the user asks "can we make money with these", add a monetization phase:

1. Map system capabilities to market demand categories
2. Research pricing (per unit, per hour) for each category
3. Rank by: profit margin × demand × competition × system fit
4. Produce ready-to-publish listings with optimized titles, descriptions, and tags
5. Include execution roadmap: signup → listing → fulfillment workflow

Known high-value monetization channels:
- 猪八戒 (Zhubajie): Freelance marketplace for PM docs, business plans, coding
- 闲鱼 (Xianyu): Service listings — resume optimization, PPT, copywriting, AI art
- 小红书 (Xiaohongshu): Content creation, account management services

## Reference Files

- `references/evaluated-repos-2026-05-03.md` — Full evaluation results from the 25-project session (24 repos + Molin AI zip). Includes tier assignments for all projects, Molin integration analysis, Ruflo assessment, and the Xianyu monetization strategy
- `references/freelance-marketplace-analysis.md` — Xianyu/PigBajie monetization analysis with listing templates

## Pitfalls

- **Don't recommend OpenClaw itself** — it's a Hermes competitor. Users sometimes confuse the ecosystem.
- **GitHub Token security**: When the user provides a `ghp_*` token or credentials, use them for the immediate search but WARN the user to rotate the token afterward. Tokens exposed in chat logs are a security breach. Never store tokens in memory or skills.
- **Physical file moves are risky**: Hermes discovers skills by walking the filesystem. Moving directories can break nested structures with `__init__.py`. Preferred approach: update YAML `category:` field in-place. Only move files for genuine archival (→ `_archived/`).
- **Xiaohongshu/Chinese platform tools decay fast** — anti-bot measures evolve weekly. A tool last updated 6+ months ago is probably useless.
- **"Has Hermes support in README" doesn't mean it works** — verify the install path actually exists and the format is compatible.
- **Star count isn't quality** — some excellent niche repos have <10 stars. Judge by content, not popularity.
- **Clone timeouts on large repos** — Repos with embedded SVGs/GIFs/images can exceed 600s subagent timeout. Always use `--depth 1 --filter=blob:none --sparse` when cloning for evaluation. If even that fails, evaluate from README-only via `curl -sL`.
- **Don't batch too many repos in one delegate_task** — 3-4 per subagent call is the sweet spot.
- **3 consecutive timeouts → change approach** — When the same tool-call pattern fails 3 times with timeouts, Hermes may trigger a same_tool_failure_warning and refuse further calls. Switch from delegate_task to direct terminal/execute_code immediately.
- **execute_code f-string escaping** — When using execute_code with Python f-strings containing shell commands, avoid backslashes inside f-string expressions. Pre-construct strings or use os.environ instead.
- **Backup before restructuring** — When the user says "开始" on a skill-system refactoring (merges, moves, archivals), always back up first: `cp -r ~/.hermes/skills ~/.hermes/skills_backup_$(date +%Y%m%d_%H%M)`. The user explicitly expects this. Restructuring without backup is negligent.
- **Avoid physical file moves for skill reorganization** — Hermes discovers skills by walking the filesystem. Moving files can break `__init__.py` and nested structures. Preferred approach: update YAML `category:` field in-place. Only move files for genuine archival (→ `_archived/`).