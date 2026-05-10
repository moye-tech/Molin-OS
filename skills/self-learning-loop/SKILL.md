---

name: self-learning-loop
description: Auto-reflect on completed tasks, extract lessons learned, and automatically update or create skills. The system gets smarter with every use — inspired by Ruflo's self-learning memory architecture.
version: 1.0.0
tags: [self-learning, auto-improve, reflection, memory, skills, optimization]
category: software-development
related_skills: [skill-discovery, agentic-engineering, swarm-orchestration]
metadata:
  hermes:
    inspired_by: https://github.com/ruvnet/ruflo
    upstream_fork: https://github.com/moye-tech/ruflo
    stars: 38000
    concepts: [self-learning, experience-crystallization, auto-skill-creation, reflection-loops, q-learning-routing, self-optimizing-orchestration]
    ruflo_integrated:
      - Q-Learning Router: 学习最优任务分配策略，每次决策后自动调优
      - EWC++ (Elastic Weight Consolidation): 学新知识不忘旧经验
      - ReasoningBank: 模式库，重复使用的模式自动沉淀
      - Self-Optimizing Loop: 每次编排后自动评估并调整策略
    molin_owner: CEO
---

# Self-Learning Loop — 自学习回路

After every complex task, automatically extract lessons learned and crystallize them into reusable skills. The system improves with every use.

## Core Concept

```
Complete Task
    │
    ▼
Reflect: What worked? What failed? What surprised me?
    │
    ▼
Extract: Concrete do's and don'ts
    │
    ▼
Crystallize: Save as skill or update existing skill
    │
    ▼
Next time: Skill auto-loads, avoiding the same mistakes
```

## When to Trigger

**Always run after:**
- Tasks with 5+ tool calls
- Tasks where you had to retry or fix errors
- Tasks the user corrected you on
- Tasks where you discovered a better approach
- Complex multi-step workflows that succeeded

**Skip for:**
- Trivial one-off queries
- Simple information lookups
- Tasks under 3 tool calls

## The Reflection Protocol

After completing a complex task, silently run this checklist:

### 1. Identify Learning Moments

```
□ Did I make a wrong assumption? → What assumption and what was correct?
□ Did I hit an error or failure? → What caused it and how did I fix it?
□ Did the user correct me? → What correction and why?
□ Did I discover a better approach? → What approach and why is it better?
□ Was there a reusable pattern? → What pattern?
```

### 2. Classify the Lesson

| Type | Example | Action |
|------|---------|--------|
| **Pitfall** | "apt-get needs -y flag in non-interactive mode" | Update relevant skill |
| **Pattern** | "Use delegate_task for multi-file refactors" | Create/update workflow skill |
| **Command** | "ffmpeg -i input.mp4 -vf scale=1080:-1 output.mp4" | Save as skill reference |
| **Correction** | "User prefers Chinese responses" | Save to memory |
| **Environment** | "Python 3.10 is installed, not 3.12" | Save to memory |

### 3. Decide: Memory or Skill?

```
Is it a fact about the user/environment?
    → Use memory tool (target: 'user' or 'memory')

Is it a reusable procedure/workflow?
    → Create or update a skill

Is it a one-time correction?
    → Use memory tool

Is it a pattern that applies to future similar tasks?
    → Create/update a skill
```

## Auto-Skill Creation

When you discover a new workflow pattern, create a skill immediately:

```python
# Check if a matching skill already exists
skill_view(name="related-skill-name")

# If it exists but is incomplete/wrong → patch it
skill_manage(
    action="patch",
    name="related-skill-name",
    old_string="old incorrect instruction",
    new_string="corrected instruction"
)

# If no skill exists → offer to create one
clarify(
    question=f"I discovered a reusable pattern for {pattern_description}. Save as a skill?",
    choices=["Yes, save it", "No, just note it", "Save and also update memory"]
)
```

## Learning Log (Internal)

Maintain a mental log of recent lessons. After every 5 learning events, review:

```
Recent Lessons:
1. [Task] Building FastAPI app → apt-get needs -y flag
2. [Task] Xiaohongshu research → Reddit r/China has better AI tool discussions
3. [Task] PRD writing → Clients prefer tables over paragraphs
4. [Task] Git operations → Always check branch before committing
5. [Task] PM proposal → Include SWOT always gets higher win rate
```

If 3+ lessons cluster around the same domain → time to create a dedicated skill.

## Crystallization Examples

### Before (raw experience)
> "I tried to install dependencies but apt-get hung waiting for confirmation"

### After (crystallized skill update)
> Add to relevant skill:
> ```diff
> + ## Pitfall
> + - **apt-get hangs**: In non-interactive mode, always use `-y` flag:
> +   `apt-get install -y <package>`
> ```

### Before (raw experience)
> "The client on 猪八戒 asked for market analysis but really wanted competitor comparison"

### After (crystallized skill)
> Add to `pm-create-prd` or `agent-sales-proposal-strategist`:
> ```diff
> + ## 猪八戒接单技巧
> + - 客户说「市场分析」时，实际想要的是「竞品对比表」
> + - 附加一个可视化对比图表，中标率提升 40%
> ```

## Real Example: User Correction → Skill Philosophy Change

During the Molin/Ruflo integration session (2026-05-04), the user corrected a fundamental approach:

**User said**: "我说的是进化，就是集成更多的东西，让你更全能"
**What I was doing**: Filtering repos into Tier 1/2/3, only converting Tier 1
**Correction decoded**: "Don't filter. ABSORB EVERYTHING USEFUL. Tier 2 is not 参考 — it's 主动转化."

**Crystallized into `skill-discovery`**: Phase 4 renamed from "Tiered Assessment" to "Tiered Assessment → Aggressive Absorption". Tier 2 changed from "参考学习" to "主动吸收" with mandatory conversion. The default stance flipped from "evaluate then decide" to "convert unless blocked."

**Why this matters**: This was not a tactical correction (wrong command, wrong tool). It was a **strategic philosophy correction** — the user wanted the system to be more aggressive in capability expansion, not more curated. Memory records "用户偏好吸收式进化", but the SKILL.md encodes the new behavior so future evaluation sessions default to aggressive absorption.

During a 24-repo batch evaluation session (尹建业, 2026-05-03), the self-learning loop ran in real time:

1. **Problem**: Large repo clones kept timing out (600s subagent limit)
2. **Lesson extracted**: Progressive fallback strategy (sparse clone → API tree → raw fetch)
3. **Crystallized**: `skill-discovery` auto-patched its own failure-handling section
4. **Future sessions**: Next batch evaluation automatically uses sparse checkout first

This is the loop functioning correctly — the system gets measurably better at its job with each session.

## Real Example: Claude Code Source Analysis → Tool Development Pattern

During the Claude Code decompiled codebase analysis (2026-05-04):

1. **Problem**: The Claude Code repo had 61 tools with complex feature-gating patterns that weren't immediately obvious from just listing files
2. **Discoveries**:
   - Three-layer feature flag system (Bun build-time MACRO → env-var USER_TYPE → GrowthBook remote A/B)
   - SQLite-backed task system with 6 distinct tools (not just 1)
   - LSP integration gated behind `ENABLE_LSP_TOOL` env var
3. **Crystallized into skills**:
   - `hermes-tool-development` — captured the SQLite test isolation pattern, tool registration methods, and feature-gating approaches
   - Updated memory with Claude Code analysis findings

**Lesson for the loop**: When analyzing an external codebase, look for patterns (registration, testing, gating) that can be extracted as reusable skills for your own codebase. Don't just note "cool feature X" — note *how* they built it so you can replicate the approach.

Same session, the loop caught three more patterns:

1. **闲鱼变现模板模式**: After analyzing 12 freelancing categories, created 6 ready-to-publish listing templates with optimized copy. Crystallized into `skill-discovery` as Phase 7 (Monetization Assessment).

2. **记忆双写模式**: When a lesson is both a procedure AND an environment fact, save to BOTH memory and skill. Example: "Clone strategy" → memory (environment quirk) + skill-discovery pitfall (procedural fix).

3. **Zip 文件评估**: New input format — user can upload zip files containing projects to evaluate. Process: unzip → list structure → read key files (README, prompts, configs) → assess integration value. Added to `skill-discovery` triggers.

## Reference Files

## Integration with Swarm + Skill Discovery

After a swarm task completes OR after a batch skill-discovery evaluation:

```
Task/Evaluation Complete → Synthesize Results
    │
    ▼
Self-Learning Loop Triggered
    │
    ├── Agent A failed on X → Extract pitfall → Update skill
    ├── Agent B found clever approach Y → Extract pattern → Create skill
    ├── Overall workflow was efficient → Crystallize template
    └── User corrected the approach → HIGHEST PRIORITY → Update governing skill immediately
```

**User corrections are the #1 learning signal.** When the user says "don't just filter, absorb everything" — that's not a memory entry, that's a skill philosophy update. Patch the governing skill (skill-discovery, in this case) immediately. Memory records the fact; the skill encodes the new behavior.

## Anti-Patterns

1. **Over-crystallization** — Not every sentence is a skill. Only crystallize when the lesson would save significant time next time.
2. **Stale skills** — If a skill causes errors, patch it immediately. Don't let bad skills accumulate.
3. **Memory bloat** — Don't save task progress. Save only durable facts and patterns.
4. **Imperial memory** — Memory is for facts. Skills are for procedures. Don't put procedures in memory.
5. **Restructuring without backup** — Before any bulk operation on the skills directory (merge, move, archive), always run: `cp -r ~/.hermes/skills ~/.hermes/skills_backup_$(date +%Y%m%d_%H%M)`. This costs seconds and prevents catastrophe.

## Quick Decision Flow

```
Task completed with lessons learned
    │
    ├── User corrected me?
    │   └── memory(action='add', target='user', content="Prefers X over Y")
    │
    ├── Discovered a new command/flag/workflow?
    │   └── Patch existing skill OR create new skill
    │
    ├── Hit an error that will recur?
    │   └── Add "Pitfall" section to relevant skill
    │
    ├── Found a better approach than what skills currently say?
    │   └── skill_manage(action='patch', ...)
    │
    └── None of the above?
        └── No action needed (not everything needs saving)
```
