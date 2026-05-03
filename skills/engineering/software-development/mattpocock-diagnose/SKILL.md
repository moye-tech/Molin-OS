---
name: diagnose
description: "Structured debugging protocol: reproduce the issue, isolate the failing component, trace to root cause, THEN propose a fix. Never jumps to fixes without understanding. Use when debugging any bug, error, unexpected behavior, or test failure."
version: 1.0.0
source: https://github.com/mattpocock/skills (56K stars)
metadata:
  hermes:
    tags: [debugging, troubleshooting, root-cause-analysis, bug-fix, diagnosis, software-development]
---

# Diagnose — Structured Debugging Protocol

## Purpose

This skill enforces a rigorous debugging methodology: reproduce → isolate → trace → fix. The agent must NOT jump to code changes until the root cause is definitively identified. Guessing-based fixes create new bugs and waste time.

## When to Use

- Any bug report, error message, or unexpected behavior
- Test failures (CI or local)
- Production incidents where the cause is unclear
- Performance regressions
- "It works on my machine" problems

## When NOT to Use

- The root cause is already known with certainty
- The error message provides an exact, clear fix instruction
- Cosmetic issues that don't affect functionality
- When the user explicitly says "I know the cause, just apply this fix"

## Diagnosis Protocol

### Step 1: Gather Information

Before hypothesizing, collect everything:

- **Error messages**: Exact stack traces, error codes, log lines (copy full text, never summarize)
- **Reproduction steps**: What action triggers it? Can the user reproduce it consistently?
- **Environment**: OS, runtime version, dependency versions, configuration
- **Recent changes**: What changed recently? (code, config, dependencies, infrastructure)
- **Frequency**: Always? Intermittent? Under load? Specific timing?
- **Scope**: Affects all users or specific ones? All environments or specific ones?

### Step 2: Reproduce the Issue

If you cannot reproduce it, you cannot fix it with confidence.

- Attempt to reproduce using the exact steps provided
- Try variations: different data, different timing, different concurrency
- If unable to reproduce, state this clearly and ask for more detail
- Create a minimal reproduction case: the smallest possible code/input that triggers the bug

### Step 3: Isolate the Failing Component

Narrow the scope systematically — NOT by guessing:

- **Binary search through the call stack**: Where exactly does execution diverge from expectation?
- **Log insertion**: Add targeted logging at decision points to trace values
- **Toggle components**: Disable suspected modules one by one to find the culprit
- **Compare with working state**: What's different between working and failing cases?
- **Check assumptions**: Every line of code makes assumptions — verify each one

Isolation questions:
- Is the bug in the input handling, processing logic, or output?
- Is it a data issue or a code issue?
- Is it synchronous or async-related?
- Is it deterministic or race-condition-based?

### Step 4: Trace to Root Cause

The root cause is the WHY, not the WHERE.

Bad: "It crashes at line 42 because `user` is null."
Good: "It crashes at line 42 because `user` is null. `user` is null because `fetchUser` returns null when the auth token expires mid-session, and we don't handle that case."

Use the **5 Whys** technique:
1. Why did the bug manifest? → The API returned 500.
2. Why did the API return 500? → NullPointerException in the handler.
3. Why was there a null? → The database returned null for the user record.
4. Why was the user record null? → The user was soft-deleted but the auth token wasn't invalidated.
5. Why wasn't the auth token invalidated? → The delete-user flow doesn't call the token revocation endpoint.

### Step 5: Propose and Validate the Fix

Only now do we discuss code changes:

- State the root cause clearly: "The root cause is [X] because [Y]"
- Propose the minimal fix: What's the smallest change that addresses the root cause?
- Consider fix-at-source vs fix-at-symptom: Fix the root cause, not the symptom
- Identify side effects: What else might this fix break?
- Add regression prevention: What test would catch this if it recurs?
- Validate: Run the reproduction case — does the fix actually solve it?

### Step 6: Prevent Recurrence

- Add a test that reproduces the exact bug (red → green)
- Check for similar patterns elsewhere in the codebase
- Consider if this reveals a systemic issue (all error handling? all null checks?)

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad |
|---|---|
| Guessing a fix without reproduction | Wastes time, may not actually fix anything |
| Fixing the symptom, not the cause | The bug comes back in a different form |
| Adding more code to handle edge case | May hide the real problem |
| Changing multiple things at once | You won't know which change fixed it |
| Blaming external dependencies immediately | Always verify your own code first |

## Output Format

```
## Diagnosis Report: [Bug Title]

### Reproduction
[Exact steps + minimal reproduction case]

### Isolation
- The bug is in [component/file]
- Not in [components checked and ruled out]

### Root Cause
[Clear statement: X causes Y because Z]

### Fix
[Minimal code change]

### Prevention
- [Test to add]
- [Pattern to check for elsewhere]
```

## Notes

- **Never skip the reproduction step** — if you can't make it happen, you're guessing
- **One change at a time** — validate each hypothesis independently
- **Read the full error, not just the first line** — critical clues are often buried
- When debugging async/concurrent code, add timing/ordering logs
- Save diagnosis reports for complex bugs as future reference

---

*Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) — "diagnose" skill.*
