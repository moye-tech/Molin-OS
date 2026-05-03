---
name: karpathy-coding-principles
description: "Apply Andrej Karpathy's four LLM coding principles: think before coding, simplicity first, surgical changes, goal-driven execution. Load when the user asks for coding tasks, refactoring, or bug fixing."
version: 1.0.0
author: Hermes Agent (adapted from forrestchang/andrej-karpathy-skills)
license: MIT
metadata:
  hermes:
    tags: [coding-principles, simplicity, surgical-editing, goal-driven, karpathy, quality]
    related_skills: [test-driven-development, systematic-debugging, writing-plans, plan, requesting-code-review]
---

# Karpathy Coding Principles

## Overview

Four principles derived from [Andrej Karpathy's observations on LLM coding pitfalls](https://x.com/karpathy/status/2015883857489522876). LLMs tend to make wrong assumptions silently, overcomplicate code, make orthogonal edits, and lack goal-orientation. These principles directly counter each of those failure modes.

**Core insight:** LLMs are exceptionally good at looping until they meet specific goals. Don't tell them what to do — give them success criteria and let them iterate.

## When to Use

**Always load for:**
- Writing new code or features
- Refactoring or simplifying existing code
- Bug fixes in non-trivial codebases
- Multi-step implementation tasks

**Use judgment (skip the full rigor) for:**
- Simple typo fixes or one-liner corrections
- Purely informational requests (no code changes)
- When user explicitly asks for speed over caution

## The Four Principles

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

LLMs often pick an interpretation silently and run with it. This principle forces explicit reasoning before any code is written:

- **State assumptions explicitly** — If anything is ambiguous, name your interpretation before acting on it. Say "I'm assuming X" rather than silently encoding X into the implementation.
- **Present multiple interpretations** — When a request could mean A or B, present both and ask. Don't pick silently just because one seems more likely.
- **Push back when warranted** — If a simpler approach exists, if the request has hidden complexity, or if there's a better way to achieve the goal, say so before implementing.
- **Stop when confused** — If you don't fully understand the request, the codebase, or the domain, name what's unclear and ask. Confusion that goes unnamed becomes bugs.

**Red flags that you're violating this principle:**
- You wrote code based on an assumption you didn't state
- The user corrects your interpretation after seeing the code
- You implemented something and later thought "oh, they probably meant..."

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

Combat the LLM tendency toward overengineering and bloated abstractions:

- **No features beyond what was asked.** If the user says "add validation for email," don't also add validation for phone, name, and address.
- **No abstractions for single-use code.** A one-off function with a generic-sounding name that's called exactly once is a smell.
- **No "flexibility" or "configurability" that wasn't requested.** Don't parameterize things "in case they need it later."
- **No error handling for impossible scenarios.** Handle expected errors, not hypothetical ones.
- **If 200 lines could be 50, rewrite it.** Err on the side of shorter. Delete dead code you created — don't leave commented-out blocks.

**The simplicity test:** Would a senior engineer reviewing this say "this is overcomplicated"? If yes, simplify before showing it.

**Counter-examples:**
- ❌ Adding a `ValidatorFactory` with strategy pattern when a single `validate_email()` function suffices
- ❌ Creating a `BaseWidget extends ConfigurableComponent` for a one-off UI element
- ✅ One function, clear name, does exactly what's needed

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code, be precise. Every changed line should trace directly to the user's request:

- **Don't "improve" adjacent code, comments, or formatting.** Those improvements introduce unrelated risk and make diffs harder to review.
- **Don't refactor things that aren't broken.** Even if you'd structure it differently, that's not the task.
- **Match existing style, even if you'd do it differently.** Consistency with the codebase matters more than your preference.
- **If you notice unrelated dead code, mention it — don't delete it.** The user can decide whether to remove it.
- **Remove only imports/variables/functions that YOUR changes made unused.** Don't clean up pre-existing dead code unless explicitly asked.

**The surgical test:** Can you point to every changed line and explain how it serves the user's request? If a line changed because "it looked better" or "while I was there," remove it from the diff.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform imperative tasks into verifiable goals. This is where LLMs truly shine:

| Instead of... | Transform to... |
|---|---|
| "Add validation" | "Write tests for invalid inputs, then make them pass" |
| "Fix the bug" | "Write a test that reproduces the bug, then make it pass" |
| "Refactor X" | "Ensure all existing tests pass before and after the refactor" |
| "Add a feature" | "Define acceptance criteria, write tests, implement until green" |

**For multi-step tasks, state a plan with verification at each step:**

```
1. [Step description] → verify: [specific check]
2. [Step description] → verify: [specific check]
3. [Step description] → verify: [specific check]
```

**Strong vs. weak success criteria:**

- ❌ Weak: "make it work" — ambiguous, can't verify
- ❌ Weak: "improve the code" — subjective, no check
- ✅ Strong: "all 12 existing tests pass, plus 3 new tests for edge cases"
- ✅ Strong: "`npm test` exits 0 and the form submits without console errors"
- ✅ Strong: "the API returns 200 for valid input and 400 with `{error: 'Invalid email'}` for bad input"

**The loop:** Write tests → run them (they fail) → implement → run them (they pass) → verify nothing else broke. If something breaks, loop again. The LLM can and should self-correct.

## Common Pitfalls

1. **Skipping the thinking step on "obvious" tasks.** Even simple-sounding requests can hide ambiguity. "Add a login page" — with what auth provider? What fields? What error states? State assumptions first.
2. **Adding "nice-to-have" features.** You're implementing validation and think "I'll add logging too." Don't. Stick to what was asked.
3. **Refactoring as you go.** You're fixing a bug and notice the function could be cleaner. Unless the refactor is necessary for the fix, don't touch it. File it away as a suggestion.
4. **Weak success criteria.** Saying "I'll make sure it works" isn't verifiable. Name the specific test command, expected output, or behavior check.
5. **Not looping on failure.** If a test fails, don't ask the user what to do — analyze the failure, fix it, and re-run. Loop until green or until you've exhausted reasonable attempts.
6. **Hiding assumptions in code.** "I'll just return null if the user isn't found" — did the user want null? An error? A redirect? State the assumption before coding it.

## Verification Checklist

- [ ] Did I state my assumptions before writing code?
- [ ] Did I push back or present alternatives where warranted?
- [ ] Is this the simplest implementation that solves the problem?
- [ ] Did I avoid adding features, abstractions, or error handling that wasn't asked for?
- [ ] Does every changed line trace directly to the user's request?
- [ ] Did I avoid touching adjacent code, comments, or formatting?
- [ ] Are my success criteria specific, testable, and verifiable?
- [ ] Did I run the tests and verify they pass?

## Tradeoff Note

These principles bias toward **caution over speed**. For trivial tasks (simple typo fixes, obvious one-liners), use judgment — not every change needs the full rigor. The goal is reducing costly mistakes on non-trivial work, not slowing down simple tasks.

## Reference

Based on Andrej Karpathy's [original observations](https://x.com/karpathy/status/2015883857489522876) and [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills).
