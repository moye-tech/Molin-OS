---
name: to-prd
description: Convert high-level ideas, feature requests, or vague requirements into
  a structured Product Requirements Document (PRD) with work breakdown. Use when someone
  has a feature idea but needs it formalized into clear, actionable specifications
  with scope, priorities, and implementation phases.
version: 1.0.0
source: https://github.com/mattpocock/skills (56K stars)
metadata:
  hermes:
    tags:
    - prd
    - product-requirements
    - specification
    - planning
    - work-breakdown
    - scoping
    - software-development
    - documentation
    molin_owner: 墨码（软件工坊）
min_hermes_version: 0.13.0
---

# To PRD — Idea to Structured Specification

## Purpose

Transform a raw idea, feature request, or vague requirement into a structured PRD. This skill bridges the gap between "I want X" and "here's exactly what we're building, broken into phases." The output is a document that engineering can execute against.

## When to Use

- A stakeholder says "we should build [X]" without specifics
- A feature request issue is too vague to estimate
- User interview feedback needs to be translated into requirements
- Starting a major feature that needs cross-team alignment
- Converting a brainstorming session into actionable work

## When NOT to Use

- The idea is already fully specified with acceptance criteria
- Trivial changes with obvious scope (bug fixes, minor tweaks)
- Exploratory spikes where uncertainty is too high for a PRD
- The "idea" is actually a refactoring task (use `/improve-codebase-architecture` instead)
- When the user explicitly wants a quick prototype, not a document

## PRD Creation Protocol

### Step 1: Extract and Clarify

Dig into the raw idea:

- **Restate the idea**: Paraphrase what you heard to confirm understanding
- **Ask clarifying questions**:
  - Who is this for? (Personas, roles)
  - What problem does it solve? (Jobs to be done)
  - Why now? What changed?
  - What does success look like?
  - How is this done today? (Workarounds, existing tools)
  - What are the constraints? (Time, budget, technology, compliance)
- **Identify unknowns**: List what we don't know yet and need to discover

### Step 2: Define Scope and Priorities

- **Must have (P0)**: Without this, the feature delivers no value
- **Should have (P1)**: Important but can launch without it
- **Nice to have (P2)**: Adds polish but not essential for launch
- **Won't have (P3)**: Explicitly out of scope for v1

Use the MoSCoW method if appropriate:
- Must have, Should have, Could have, Won't have

### Step 3: Break Down the Work

Decompose the feature into implementable units:

- **Epics**: Large user-facing capabilities (1-4 weeks)
- **User Stories**: "As a [persona], I want [action] so that [benefit]" — each shippable in a sprint
- **Technical Tasks**: Infrastructure, refactoring, performance, testing work
- **Dependencies**: What must be completed before what? External team dependencies?

### Step 4: Define Acceptance Criteria

For each user story, define objective, testable criteria:

- **GIVEN/WHEN/THEN format**: Given [precondition], when [action], then [expected result]
- **Edge cases**: What happens with empty, large, malformed, or concurrent inputs?
- **Error states**: What does the user see when things go wrong?
- **Performance criteria**: Response time, throughput, data volume limits

### Step 5: Estimate and Phase

Organize work into phases:

```
Phase 1 (MVP — 2 sprints):
  - Core functionality that delivers baseline value
  - Must-have features only

Phase 2 (V1.0 — 1 sprint after MVP):
  - Should-have features
  - Polish and edge case handling

Phase 3 (Future):
  - Nice-to-have features
  - Performance optimizations
```

### Step 6: Identify Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Third-party API changes during development | Medium | High | Version-lock API, add integration tests |
| Performance under load unknown | High | Medium | Load test during Phase 1 |
| ... | ... | ... | ... |

## PRD Template

```markdown
# PRD: [Feature Name]

**Status**: Draft | In Review | Approved
**Author**: [Name]
**Date**: [Date]
**Stakeholders**: [Names/Roles]

## Summary
[2-3 sentence executive summary]

## Problem Statement
[What problem are we solving? For whom? Why does it matter?]

## Success Metrics
- [Measurable outcome 1]
- [Measurable outcome 2]

## User Stories

### Epic 1: [Epic Name]
| Priority | Story | Acceptance Criteria | Estimate |
|----------|-------|---------------------|----------|
| P0 | As a [user], I want [action] so that [benefit] | Given/When/Then | S |
| P1 | ... | ... | M |

### Epic 2: [Epic Name]
...

## Scope
**In Scope (v1)**:
- [Feature/component]

**Out of Scope (v1)**:
- [Feature/component — will revisit in v2]

## Technical Considerations
- [Architecture notes, technology choices, constraints]

## Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ... | ... | ... | ... |

## Phases
1. **MVP** (Sprint X-Y): [Scope]
2. **V1.0** (Sprint Z): [Scope]
3. **Future**: [Scope]

## Open Questions
- [Question 1]
- [Question 2]
```

## Notes

- **Start with WHY, not WHAT** — always ground the PRD in the problem
- **Write for primary school graduates** — use simple, accessible language
- **Flag assumptions explicitly** — separate what we know from what we believe
- **Keep it living** — a PRD is not set in stone; update it as you learn
- **Save the PRD**: Write substantial PRDs to file as `PRD-[feature-name].md`

---

*Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) — "to-prd" skill.*