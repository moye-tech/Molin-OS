---

name: decompiled-codebase-extraction
description: Extract architecture, tools, and reusable patterns from decompiled/reverse-engineered codebases. Identify stubbed modules, feature flag systems, tool registries, and integration potential with existing systems.
version: 1.0.0
author: Hermes Agent
tags: [codebase-analysis, architecture, tool-extraction, decompiled-code]
metadata:
  hermes:
    related_skills: [codebase-inspection, github-repo-management]
    molin_owner: CEO
---

# Decompiled Codebase Extraction

Systematic approach to analyze reverse-engineered codebases and extract reusable components.

## When to Use

- User provides a decompiled repo and wants to know what's worth integrating
- You need to compare another system's tools/architecture against Hermes
- User wants integration assessment with dependency mapping

## Analysis Protocol

### Step 1: Initial Scan

Clone the repo, then check for project documentation files like README or any architecture docs:
```bash
head -100 ./target-repo/README.md 2>/dev/null
```

Decompiled repos often ship with annotated docs that explain what was stripped — this is your single most valuable first read.

### Step 2: Find Key Structural Files

**Entrypoint** — how the app starts:
```bash
ls src/entrypoints/ 2>/dev/null
grep -n "Fast-path\|import.*from\|async function main" src/entrypoints/cli.tsx 2>/dev/null | head -20
```

**Tool Registry** — the complete tool list:
```bash
grep -n "import.*Tool from\|getAllBaseTools\|export function getTools" src/tools.ts 2>/dev/null | head -30
```

**Tool Interface** — the Tool type definition:
```bash
grep -n "export type Tool\b\|name\|description\|call\|isEnabled" src/Tool.ts 2>/dev/null | head -20
```

### Step 3: Detect Stubbed Modules

Decompilation often strips implementations. Find stubs by size:
```bash
# Small files are likely stubs
find src/ -name "*.ts" -o -name "*.tsx" | xargs wc -l 2>/dev/null | sort -n | head -30

# Check key directories for stubs
wc -l src/server/*.ts src/bridge/*.ts 2>/dev/null | sort -n | head -10

# Grep for stub markers
grep -rn "stub\|placeholder\|not implemented" src/ --include="*.ts" --include="*.tsx" | head -20
```

A file is a stub if it contains `export {};`, `Auto-generated stub`, or is a minimal `() => ({ stop() {} })` placeholder.

### Step 4: Feature Flag Architecture

Map the layered feature gating system:
```bash
# Layer 1: Build-time macros
grep -B5 -A30 "DEFAULT_BUILD_FEATURES\|DEFAULT_DEV_FEATURES" build.ts scripts/dev.ts 2>/dev/null
grep -A5 "bun:bundle" src/types/internal-modules.d.ts 2>/dev/null

# Layer 2: Runtime env var gates
grep -rn "feature('" src/ --include="*.ts" --include="*.tsx" | grep -v node_modules | head -40

# Layer 3: Remote A/B testing
grep -rn "checkGate\|getFeatureValue\|GrowthBook\|Statsig" src/ --include="*.ts" | head -10
```

### Step 5: Build Comparison Matrix

For each tool in the registry, classify against the target system:

| Priority | Meaning |
|:---------|:--------|
| **P0** | Missing core capability — no equivalent exists |
| **P1** | Valuable add-on — fills a gap but not critical |
| **P2** | Related approach — worth noting different design |
| **Skip** | Full overlap — Hermes already has it |
| **N/A** | Requires original backend — cannot standalone |

### Step 6: Backend Dependency Audit

Check if promising modules can run independently:
```bash
# Check for original-backend API references
grep -rn "anthropic\|claude.ai\|api\." src/bridge/ 2>/dev/null | head -20

# Check for standalone transport layer
ls packages/ 2>/dev/null
find src/ -name "*WebSocket*" -o -name "*transport*" -o -name "*Server*" 2>/dev/null

# Check protocol/types that can be extracted
find src/ -name "*types*" -o -name "*sdkTypes*" | head -10
```

## Pitfalls

1. **Stubs look real until you read them** — always check file sizes. A 3-line file with `export {};` tells you the original was removed.
2. **Dead code elimination hides feature states** — features may have complete source but be entirely stripped at build time if gated by compile-time defines.
3. **Circular dependency hacks are artifacts of decompilation** — don't treat dynamic require() patterns as intentional architecture.
4. **UI components are non-portable** — decompiled CLIs often embed ~150+ React components with custom reconcilers. Skip UI extraction.
5. **Version strings may lag production** — check package.json + defines.ts for version discrepancies.
6. **Internal-only tools marked by USER_TYPE gates** — `USER_TYPE === 'ant'` or similar guards mean the tool needs internal infrastructure not available externally.
7. **Feature flags may exist in source but be 0% rollout** — presence in source != enabled for anyone.

## Report Template

After analysis, produce:

```
# {Repo} Codebase Extraction

## Architecture Overview
- Runtime: ...
- Entry: ...
- Core loop: ...

## Feature Flag System ({N} layers)
- Build-time: {N} flags
- Runtime env var: {N} flags
- Remote: {N} gates

## Tool Comparison ({N} tools)
P0 ({N}): ...
P1 ({N}): ...
Skip ({N}): ...
N/A ({N}): ...

## Extractable Candidates
1. Module X (effort) — approach
2. Module Y (effort) — approach

## Recommendations
- P0 — ...
- P1 — ...
```

## Verification

- Check stub identification by reading file contents, not just sizes
- Confirm feature gates by grepping actual usage patterns
- Verify backend dependency by tracing import chains
