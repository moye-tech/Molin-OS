---
name: improve-codebase-architecture
description: 'Systematic code quality and architecture improvement: identify structural
  issues, propose targeted refactors, and create an incremental improvement plan.
  Use when reviewing existing code for maintainability, reducing technical debt, or
  preparing for a feature that requires architectural changes.'
version: 1.0.0
source: https://github.com/mattpocock/skills (56K stars)
metadata:
  hermes:
    tags:
    - refactoring
    - architecture
    - code-quality
    - technical-debt
    - maintainability
    - software-development
    - code-review
    molin_owner: 墨码（软件工坊）
min_hermes_version: 0.13.0
---

# Improve Codebase Architecture

## Purpose

This skill guides a systematic assessment of codebase architecture and quality, producing an actionable improvement plan. The agent analyzes structure, identifies problems, and proposes refactors — prioritized for maximum impact with minimal risk.

## When to Use

- Onboarding to a new codebase and assessing its health
- Preparing for a significant feature that requires architectural changes
- Addressing growing technical debt that's slowing the team down
- After a rapid development phase — cleanup and consolidation
- Before scaling: will this architecture hold under 10x load/users?

## When NOT to Use

- Small, isolated changes that don't affect architecture
- Rewrite-everything proposals (this skill favors incremental improvement)
- Greenfield projects (nothing to improve yet)
- When the team has no appetite for refactoring right now
- Performance-only investigations (use `/diagnose` instead)

## Architecture Assessment Protocol

### Phase 1: Map the Current Architecture

First, understand what exists:

- **Directory structure**: How are files organized? Does the structure communicate intent?
- **Module dependencies**: What imports what? Identify core modules, utility modules, and leaf modules.
- **Data flow**: How does data move through the system? Database → service → controller → view?
- **Entry points**: API routes, CLI commands, event handlers — where does execution begin?
- **Configuration**: How is the system configured? Environment variables, config files, service discovery?
- **External dependencies**: What libraries, services, and APIs does the system depend on?

### Phase 2: Identify Architectural Smells

Look for these structural problems:

| Smell | What to Look For |
|---|---|
| **God modules** | Files > 500 lines handling too many concerns |
| **Circular dependencies** | A imports B, B imports A (or longer cycles) |
| **Shotgun surgery** | Changing one feature requires touching 10+ files |
| **Rigidity** | Small changes cascade into many other changes |
| **Fragility** | Changes in one place break unrelated things |
| **Immobility** | Components can't be reused because they're too coupled |
| **Needless complexity** | Over-engineering — patterns that add more complexity than they solve |
| **Opacity** | Code that's hard to understand at a glance |
| **Duplication** | Same logic in multiple places with slight variations |
| **Wrong abstraction** | An abstraction that doesn't fit, forcing workarounds |
| **Hidden coupling** | Components that depend on implicit behavior of others |
| **Feature envy** | A method that uses another class's data more than its own |

### Phase 3: Prioritize Improvements

Rate each issue on two dimensions:

- **Impact**: How much does this slow down development or cause bugs? (High/Medium/Low)
- **Effort**: How much work to fix? (High/Medium/Low)

Focus on **High Impact + Low Effort** items first, then High Impact + Medium Effort.

### Phase 4: Design the Target Architecture

For each identified problem, describe:

- **Current state**: What's wrong and why it matters
- **Target state**: What should it look like?
- **Transition plan**: Incremental steps to get there without breaking things
- **Risk mitigation**: How to validate correctness during the transition

### Phase 5: Create the Improvement Roadmap

Organize into phases:

```
Phase 1 (Quick Wins — this sprint):
- [ ] Extract ConfigService from god module app.ts
- [ ] Break circular dep between User and Order modules

Phase 2 (Structural — next 2 sprints):
- [ ] Introduce Repository pattern for data access
- [ ] Consolidate 3 duplicate validation functions into shared lib

Phase 3 (Strategic — this quarter):
- [ ] Split monolith into bounded contexts
- [ ] Introduce event-driven communication between modules
```

## Refactoring Principles

1. **Boy Scout Rule**: Leave the code better than you found it
2. **Incremental over big-bang**: Each refactor step should leave the system in a working state
3. **Test coverage first**: Add characterization tests before refactoring
4. **One refactor at a time**: Don't mix structural changes — isolate each transformation
5. **Parallel change pattern**: Build the new alongside the old, switch over, remove old
6. **Strangler Fig pattern**: Gradually replace pieces of a legacy system

## Output Format

```markdown
## Architecture Assessment: [Project/Module Name]

### Current Architecture Summary
[2-3 paragraph overview of how the system is structured]

### Identified Issues (ranked by Impact/Effort)

| # | Issue | Type | Impact | Effort | Priority |
|---|-------|------|--------|--------|----------|
| 1 | God module: app.ts (800 lines) | God Module | High | Medium | P0 |
| 2 | User/Order circular dependency | Circular Dep | High | Low | P0 |
| 3 | Duplicate auth logic in 4 places | Duplication | Medium | Low | P1 |
| ... | ... | ... | ... | ... | ... |

### Improvement Roadmap

#### Phase 1: Quick Wins
- **Issue 1**: [Specific refactor steps]
- **Issue 2**: [Specific refactor steps]

#### Phase 2: Structural Improvements
- ...

### Target Architecture
[Description of desired end state + transition strategy]
```

## Notes

- **Never propose a full rewrite** — always favor incremental improvement
- **Respect the existing style** — consistency beats personal preference
- **Measure before and after** — use metrics (complexity, coupling, test coverage) to show progress
- **Document decisions** — write ADRs for significant architectural choices
- **Pair this skill with `/zoom-out`** to first understand the big picture

---

*Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) — "improve-codebase-architecture" skill.*