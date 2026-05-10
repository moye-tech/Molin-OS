---

name: triage
description: "Issue and bug management: categorize, prioritize, and assign issues with clear severity levels and action plans. Use when faced with a queue of bug reports, feature requests, or support tickets that need systematic evaluation and routing."
version: 1.0.0
source: https://github.com/mattpocock/skills (56K stars)
metadata:
  hermes:
    tags: [triage, bug-management, issue-tracking, prioritization, categorization, software-development, project-management]
    molin_owner: 墨码（软件工坊）
---

# Triage — Issue Categorization and Prioritization

## Purpose

This skill provides a systematic framework for evaluating, categorizing, and prioritizing issues — whether they're bug reports, feature requests, or support tickets. The goal is to route each issue to the right person with the right priority and enough context to act on it.

## When to Use

- Processing a backlog of un-triaged issues
- Evaluating a new bug report or feature request
- Running a triage meeting and need a structured approach
- Determining what to fix in the next sprint vs. defer
- Assessing the severity of a production incident
- Helping a team establish a triage process

## When NOT to Use

- The issue is already well-categorized and prioritized
- Trivial issues that don't need formal assessment (typos, obvious quick fixes)
- The user just wants a direct answer to a question, not a process
- Issues that should be closed immediately (spam, duplicates, won't-fix)

## Triage Protocol

### Step 1: Quick Validation

Before deep analysis, validate the issue exists at all:

- **Is it real?** Can you reproduce it or verify the request is legitimate?
- **Is it a duplicate?** Check for existing issues reporting the same thing
- **Is it actionable?** Does it contain enough information to act on?
  - If not, tag as `needs-info` and ask the reporter for specifics
- **Is it in scope?** Does this belong in this project or should it be redirected?

### Step 2: Categorize

Assign the issue to the right category:

| Category | Examples | Description |
|----------|----------|-------------|
| **Bug** | Crash, wrong output, data loss | Something that worked is now broken |
| **Feature Request** | New endpoint, new UI component | Something new that doesn't exist yet |
| **Enhancement** | Performance improvement, better UX | Improving something that already works |
| **Technical Debt** | Refactoring, dependency updates | Code quality work with no user-facing change |
| **Documentation** | Missing docs, wrong examples | Documentation issues |
| **Security** | Vulnerability, data exposure | Security-sensitive issues |
| **Question/Support** | "How do I...?" | Usage questions, not code changes |

### Step 3: Assess Severity (Bugs)

Use a clear severity scale:

| Severity | Label | Definition | Example |
|----------|-------|------------|---------|
| **S0 — Critical** | `severity:critical` | System down, data loss, security breach, revenue-blocking | Production outage, PII leak |
| **S1 — High** | `severity:high` | Major feature broken, no workaround, affects most users | Login broken for all users |
| **S2 — Medium** | `severity:medium` | Feature partially broken, workaround exists, affects some users | Export CSV fails for >1000 rows |
| **S3 — Low** | `severity:low` | Cosmetic issue, edge case, minimal user impact | Button misaligned on IE11 |
| **S4 — Trivial** | `severity:trivial` | Typo, visual glitch, no functional impact | Misleading comment in code |

### Step 4: Assess Priority (All Issues)

Priority combines severity with business context:

| Priority | Label | When to Use |
|----------|-------|-------------|
| **P0 — Now** | `priority:now` | Drop everything. Blocks release or causes active harm. |
| **P1 — Next Sprint** | `priority:high` | Important for near-term goals. Should be in the next sprint. |
| **P2 — Soon** | `priority:medium` | Valuable but not urgent. Schedule in the next 2-4 sprints. |
| **P3 — Later** | `priority:low` | Nice to have. No timeline commitment. |
| **P4 — Backlog** | `priority:backlog` | Valid but no plans to work on it. Revisit during planning. |

Priority ≠ Severity. A low-severity bug might be high-priority if it blocks a key customer's workflow. A high-severity bug might be lower priority if it only affects an unused feature.

### Step 5: Estimate Effort

Rough effort estimate to help with sprint planning:

| Size | Label | Guideline |
|------|-------|-----------|
| **XS** | `effort:xs` | < 1 hour — typo fix, config change |
| **S** | `effort:s` | 1-4 hours — small fix, simple feature |
| **M** | `effort:m` | 1-3 days — feature with a few components |
| **L** | `effort:l` | 3-10 days — multi-sprint feature |
| **XL** | `effort:xl` | > 10 days — needs breakdown into smaller issues |

### Step 6: Assign and Route

- **Assign to a person** if ownership is clear
- **Assign to a team/tag** if the right person isn't clear
- **Tag with component/label** to indicate which part of the system
- **Link related issues** — duplicates, blockers, dependencies

### Step 7: Set Expectations

For each issue, communicate:

- **What happens next** — Will this be investigated? Fixed? Discussed?
- **When** — This sprint? Next quarter? Not planned?
- **What the reporter can do** — Provide more info? Test a fix? Wait?

## Triage Checklist

For each issue, answer these questions:

```
□ Is the issue valid? (not spam, not a duplicate, in scope)
□ Is there enough information to act? (if not → needs-info)
□ What category? (bug/feature/enhancement/tech-debt/docs/security)
□ If bug: What severity? (S0-S4)
□ What priority? (P0-P4, considering business context)
□ Estimated effort? (XS-XL)
□ Who should own this? (person, team, or unassigned)
□ Are there related issues to link?
□ What should the reporter expect next?
```

## Triage Output Format

For a batch of issues:

```markdown
## Triage Results: [Date / Sprint / Milestone]

### Critical (S0-S1, P0-P1) — Action Now
| # | Issue | Severity | Priority | Assignee | Action |
|---|-------|----------|----------|-----------|--------|
| 123 | Login broken in prod | S0 | P0 | @alice | Fix now |
| 456 | Payment double-charge | S1 | P0 | @bob | Investigate |

### High Priority (P1) — Next Sprint
| # | Issue | Severity | Priority | Assignee | Action |
|---|-------|----------|----------|-----------|--------|
| 789 | Export timeout >10k rows | S2 | P1 | @carol | Sprint 24 |

### Needs Triage / Needs Info
| # | Issue | Missing Info | Action |
|---|-------|-------------|--------|
| 234 | "App is slow" | No repro steps, no metrics | Ask reporter for details |

### Deferred (P3-P4) — Later
| # | Issue | Reason |
|---|-------|--------|
| 567 | Dark mode toggle | Low user demand, revisit Q4 |

### Closed
| # | Issue | Reason |
|---|-------|--------|
| 890 | Duplicate of #123 | Merged |
```

## Notes

- **Be honest about priorities** — don't label everything P0 or nothing gets done
- **Communicate decisions** — reporters deserve to know why their issue was deferred
- **Regular triage cadence** — weekly is ideal; stale backlogs are demoralizing
- **Document triage criteria** — make sure the team agrees on severity/priority definitions
- **Automate where possible** — label bots, stale-issue closers, duplicate detection
- **The goal is clarity, not bureaucracy** — keep the process lightweight

---

*Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) — "triage" skill.*
