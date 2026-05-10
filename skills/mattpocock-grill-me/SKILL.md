---
name: grill-me
description: Grilling session that forces the agent to explicitly think through requirements,
  edge cases, tradeoffs, and design decisions BEFORE writing any code. Use when starting
  a new feature, tackling a complex task, or when you need the agent to deeply understand
  what to build before building it. Prevents premature implementation.
version: 1.0.0
source: https://github.com/mattpocock/skills (56K stars)
metadata:
  hermes:
    tags:
    - planning
    - requirements
    - alignment
    - thinking
    - design
    - pre-code
    - software-development
    molin_owner: 墨码（软件工坊）
min_hermes_version: 0.13.0
---

# Grill Me — Pre-Code Alignment Session

## Purpose

Before writing a single line of code, this skill runs a structured grilling session that forces the agent to confront the full scope of the task. The agent must demonstrate deep understanding by answering probing questions about requirements, edge cases, tradeoffs, and implementation strategy — not just jumping to solutions.

## When to Use

- Starting a new feature that has unclear requirements
- Before implementing a complex architectural change
- When the user wants confidence that the agent truly understands the problem
- Before making changes to critical or sensitive code paths

## When NOT to Use

- Trivial, well-understood changes (typo fixes, simple config changes, one-line bugfixes)
- The user has already provided a crystal-clear, exhaustive specification
- Time-critical hotfixes where the fix is already known
- Tasks where the user explicitly says "just do it"

## Grilling Protocol

### Phase 1: Understanding What to Build

Ask and answer these questions before any code:

1. **What exactly are we building?** — Describe the feature/change in one paragraph. No jargon.
2. **Who is this for?** — Which users/customers/systems will interact with this?
3. **What problem does it solve?** — What pain exists today? How will we measure improvement?
4. **What does success look like?** — Define acceptance criteria with concrete, verifiable conditions.

### Phase 2: Edge Cases and Failure Modes

Think through every scenario that could go wrong:

5. **What happens when inputs are empty?** — null, undefined, empty string, empty array, zero
6. **What happens with very large inputs?** — 10,000 items? 1GB file? Infinite stream?
7. **What happens with malformed inputs?** — wrong types, corrupted data, invalid formats
8. **What happens when dependencies fail?** — network timeout, database down, API error, disk full
9. **What about concurrency?** — race conditions, multiple users, parallel requests
10. **What about security?** — injection attacks, auth bypass, data leakage, privilege escalation
11. **What are the performance boundaries?** — latency budget, throughput requirements, memory limits
12. **What about backwards compatibility?** — existing APIs, stored data, user workflows

### Phase 3: Design Decisions and Tradeoffs

Explicitly surface the choices being made:

13. **What are the alternative approaches?** — Name at least 2 different ways to solve this.
14. **Why choose this approach over alternatives?** — What are the explicit tradeoffs (simplicity vs flexibility, speed vs correctness, etc.)?
15. **What libraries/frameworks/dependencies are needed?** — Justify each one. Can we avoid them?
16. **What is the minimal viable implementation?** — What's the simplest thing that could work?
17. **What are we explicitly NOT building?** — Scope boundaries. What will be done later?

### Phase 4: Implementation Strategy

18. **What is the implementation order?** — List the steps in dependency order.
19. **What tests should we write?** — Unit, integration, E2E; happy path AND failure cases.
20. **What documentation needs updating?** — README, API docs, changelog, ADRs.

## Output Format

After grilling, produce a consolidated summary:

```markdown
## Grill Me Summary: [Feature/Task Name]

### What We're Building
[One-paragraph description]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

### Edge Cases Addressed
| Scenario | Handling Strategy |
|----------|-------------------|
| Empty input | ... |
| Large input | ... |
| Network failure | ... |

### Design Decisions
- **Chosen approach**: [approach] because [reasoning]
- **Rejected alternatives**: [list with brief reasons]

### Implementation Plan
1. [Step 1]
2. [Step 2]
...

### Out of Scope
- [Item not being built]
```

## Notes

- Do not write any implementation code during the grilling phase
- If the user pushes back on a question, that's a signal the requirement is unclear
- Save longer grill summaries to `.hermes/plans/` for reference
- This skill pairs well with `/zoom-out` for understanding the existing codebase first

---

*Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) — "grill-me" skill.*