---
name: zoom-out
description: "Code comprehension: understand the big picture of a codebase before making changes. Maps module structure, data flow, entry points, and key abstractions so the agent can reason about impact. Use when onboarding to an unfamiliar codebase, before making cross-cutting changes, or when the agent needs context about how everything fits together."
version: 1.0.0
source: https://github.com/mattpocock/skills (56K stars)
metadata:
  hermes:
    tags: [code-comprehension, onboarding, architecture, exploration, impact-analysis, software-development, code-review]
---

# Zoom Out — Big-Picture Code Comprehension

## Purpose

Before making changes to a codebase, understand how everything fits together. This skill guides the agent through systematic exploration: mapping the module landscape, understanding data flows, identifying key abstractions, and tracing dependency chains. It prevents the "fix one thing, break three others" problem.

## When to Use

- Entering an unfamiliar codebase for the first time
- Before making changes that span multiple modules or layers
- Reviewing a PR that touches many files — understand the impact
- Answering "how does X work?" questions
- Planning an architectural change — know what you'll affect
- Onboarding a new team member (document findings for future reference)

## When NOT to Use

- You already know the codebase intimately
- The change is isolated to a single, well-understood file
- Quick syntax fixes or typo corrections
- The user asks a specific, narrow question about a single function
- Emergency hotfixes where speed is critical and the fix is known

## Exploration Protocol

### Phase 1: Surface-Level Scan

Start broad, then narrow:

1. **Directory structure**: What are the top-level directories? What does each contain? What naming conventions are used?
2. **Package manifest**: Read `package.json`, `Cargo.toml`, `setup.py`, `go.mod` — what are the key dependencies?
3. **Entry points**: Find `main()`, `index.js`, `app.ts`, route definitions — where does execution begin?
4. **Configuration**: How is the app configured? Environment variables? Config files? CLI flags?
5. **Build and test setup**: How do you build, run, and test? Read relevant config files and scripts.

### Phase 2: Module Map

Map the architecture:

- **Layers**: What are the architectural layers? (e.g., routes → controllers → services → repositories → database)
- **Modules/domains**: What are the bounded contexts or feature modules?
- **Dependencies between modules**: Which modules depend on which? Use import analysis.
- **Shared code**: What utilities, types, constants are shared across modules?
- **External integrations**: What external services, APIs, or databases does the system talk to?

### Phase 3: Data Flow Tracing

Pick a key user action and trace it end-to-end:

- **Entry point**: Where does the request/event enter the system?
- **Transformation**: How is data validated, transformed, and enriched?
- **Persistence**: Where and how is data stored? What schemas?
- **Response**: How does data flow back to the user/client?
- **Side effects**: What else happens? (events emitted, caches updated, logs written)

### Phase 4: Key Abstractions

Identify the central concepts:

- **Core domain models**: What are the primary entities and value objects?
- **Interfaces/contracts**: What are the key interfaces that modules depend on?
- **Design patterns in use**: Repository, Factory, Strategy, Observer, etc. — what patterns are used and where?
- **Error handling strategy**: How are errors propagated, logged, and surfaced?
- **Testing patterns**: How are tests structured? Mocks, fixtures, integration tests?

### Phase 5: Impact Analysis

Before making a change, trace its blast radius:

- **What depends on this code?** — Find all callers, importers, and consumers
- **What does this code depend on?** — Find all dependencies, APIs, and data stores
- **What tests cover this area?** — Identify relevant test suites
- **What data or state might be affected?** — Database migrations, config changes, API contracts

## Questions to Answer

After zooming out, you should be able to answer:

1. What is this codebase's primary purpose?
2. How is it structured at a high level?
3. Where does new feature code typically go?
4. How does data flow through the system?
5. What are the key abstractions and design patterns?
6. What are the most coupled or fragile areas?
7. How is the system tested?
8. What external systems does it depend on?

## Output Format

```markdown
## Zoom Out: [Codebase/Project Name]

### Overview
[2-3 sentence summary of what this codebase does]

### Architecture
[Layers/modules diagram in text]

### Key Modules
| Module | Purpose | Depends On | Depended By |
|--------|---------|------------|-------------|
| auth/ | Authentication & authorization | db/, config/ | All modules |
| api/ | HTTP routes & middleware | auth/, services/ | — |
| ... | ... | ... | ... |

### Data Flow (Example: User Login)
```
Client → POST /login → auth middleware
  → AuthService.authenticate()
    → UserRepository.findByEmail() → Database
    → PasswordHasher.verify()
    → TokenService.generate() → JWT
  → Response with token
```

### Key Abstractions
- **User**: [description]
- **Repository<T>**: [description of generic data access pattern]
- ...

### Dependencies
| Dependency | Version | Purpose |
|-----------|---------|---------|
| express | ^4.18 | HTTP framework |
| ... | ... | ... |

### Fragile Areas (High Risk)
- [Module/File] — [Why it's risky]
- ...

### Change Impact: [Proposed Change]
- **Files to modify**: [list]
- **Tests to update**: [list]
- **Side effects to watch for**: [list]
```

## Notes

- **Don't read every file** — sample strategically: entry points, key modules, tests
- **Follow the imports** — they reveal the real dependency structure
- **Tests are documentation** — they show how the code is meant to be used
- **Look for ADRs** (Architecture Decision Records) in `docs/adr/` or similar
- **Save zoom-out results** for future reference if exploring a codebase you'll work on regularly
- **Pair with `/grill-me`** after zooming out to plan implementation

---

*Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) — "zoom-out" skill.*
