---
name: molin-os-development
description: 'Molin-OS module development standards for Mac M2 (8GB RAM, Python 3.11). Covers: stdlib-only pattern, CLI registration in __main__.py, verification snippets, patch pitfalls, module structure, and Mac deployment constraints. Use when creating new molib modules or adding CLI commands to Molin-OS.'
version: 1.0.0
tags:
- molin-os
- development
- mac-m2
- patterns
- cli
related_skills:
- molin-cli
- hermes-skill-adaptation-pipeline
metadata:
  hermes:
    molin_owner: CEO
min_hermes_version: 0.13.0
---

# Molin-OS Module Development Standards

> Mac M2 (8GB RAM, Python 3.11, 169GB disk) — every module must work here first.

## Architecture Principle

```
molib/
├── agencies/        # Business logic (trading_agents, swarm_bridge, handoff)
├── infra/           # Infrastructure (budget_guard, coco_index, event_bus)
│   ├── gateway/     # External service gateways (feishu_card_builder, feishu.py)
│   └── memory/      # Memory system (distiller)
└── __main__.py      # CLI dispatch — ALL new commands registered here
```

**Rule:** New module belongs in `agencies/` if it has business logic; in `infra/` if it's infrastructure/utility.

## Stdlib-Only Pattern

Every new module MUST work with zero external dependencies:

```python
# ✅ Allowed — stdlib only
import json, sqlite3, pathlib, hashlib, logging, urllib.request
from dataclasses import dataclass
from datetime import datetime

# ❌ Forbidden — external deps require explicit justification
# import requests, redis, celery, fastapi, aiohttp, pydantic
```

**Exception:** Only allowed if the module wraps an existing installed framework (e.g., larksuiteoapi in feishu.py, freqtrade in trading strategies).

## Module Structure Template

```python
"""
Module Name — one-line description
===================================
Extended description. Mac M2: <constraint note if any>.

用法:
    python -m molib <command> <subcmd> [--args]
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("molin.<module_name>")

# ── Data Classes ─────────────────────────────────────

@dataclass
class Result:
    ...

# ── Core Class ───────────────────────────────────────

class ModuleName:
    def __init__(self):
        ...

# ── CLI Functions ────────────────────────────────────

def cmd_module_subcommand(args...):
    """CLI entry point."""
    ...

# ── Verification ─────────────────────────────────────

if __name__ == "__main__":
    # Built-in test
    print("✅ Module OK")
```

## CLI Registration Pattern

### 1. Create CLI functions in the module

Export standalone `cmd_<module>_<subcmd>()` functions:

```python
def cmd_index_watch(path: str): ...
def cmd_index_sync(): ...
def cmd_index_stats(): ...
```

### 2. Register in __main__.py

Add a dispatch function that routes subcommands:

```python
def cmd_index(args: list[str]) -> dict:
    """CocoIndex — watch/query/sync/stats"""
    from molib.infra.coco_index import (
        cmd_index_watch, cmd_index_query, cmd_index_sync, cmd_index_stats,
    )
    import io, sys

    if not args:
        return {"error": "子命令: watch | query | sync | stats"}

    subcmd = args[0]
    rest = args[1:]

    # Capture stdout into dict
    old_stdout = sys.stdout
    buf = io.StringIO()
    sys.stdout = buf
    try:
        if subcmd == "watch": ...
        elif subcmd == "query": ...
        # ...
    finally:
        sys.stdout = old_stdout

    return {"output": buf.getvalue()}
```

### 3. Add to dispatch tables

Sync commands (return dict directly):
```python
sync_commands = {
    "health": cmd_health,
    "index": cmd_index,      # ← add here
    "memory": cmd_memory,    # ← add here
    "swarm": cmd_swarm,      # ← add here
}
```

Async commands (return coroutine):
```python
async_commands = {
    "trading": cmd_trading,  # ← add here
    "cost": cmd_cost,        # ← add here
}
```

## Patch Pitfall: __main__.py

**CRITICAL:** When patching `__main__.py`, NEVER let a diff accidentally remove a function header (`def cmd_xxx(...)`). This happens when:

- Using `patch` with old_string that catches the function name but not the `def` line
- Merging code blocks where the new_string drops the function definition
- Always verify with `python -c "import molib.__main__"` after any __main__.py patch

**Safe patch pattern:** Include the full `def ...:` line + docstring in old_string to ensure the patch anchor is unique:

```python
# ✅ Safe — unique anchor
old_string = "def cmd_bitable(args: list[str]) -> dict:\n    \"\"\"飞书多维表格命令 — schema / write / list\"\"\"\n    ..."

# ❌ Dangerous — may match inside another function
old_string = "return bg.get_report()"
```

## Verification Snippet

After creating any module, run:

```bash
cd /Users/moye/Molin-OS && python -c "
from molib.<path>.<module> import <Class>
# Basic instantiation
obj = <Class>()
# Core method test
result = obj.<main_method>(...)
print(f'✅ <Module> OK: {result}')
" 2>&1 | grep -v 'DEBUG\|__pycache'
```

## Mac M2 Deck — What Runs Locally

| Capability | Engine | Status | Cost |
|------------|--------|--------|------|
| TTS (Chinese) | macOS `say` (Tingting/Meijia/Sinji) | ✅ Built-in | Free |
| TTS (50+ voices) | macOS `say -v '?'` | ✅ Built-in | Free |
| Digital human (static) | ffmpeg + say → image+audio→video | ✅ Tier 1 | Free |
| Digital human (lip-sync) | SadTalker + PyTorch MPS | 🔜 Tier 2 | Free (needs `pip install torch`) |
| Video compositing | ffmpeg 8.1.1 | ✅ | Free |
| ML inference (small) | PyTorch MPS (8GB unified) | ⚠️ OK for <2GB models | Free |

## Mac M2 Deployment Constraints

| Resource | Limit | Impact |
|----------|-------|--------|
| RAM | 8 GB unified | No local LLMs, ChromaDB + SQLite OK, Redis too heavy |
| CPU | 8 cores (M2) | Parallel subagents fine, but 3-4 max simultaneously |
| Python | 3.11.15 | No match/case exhaustiveness, no `str | None` syntax |
| Disk | 169 GB free | Plenty for files, not for ML models (>5GB each) |
| OpenSSL | System (3.x) | TLS 1.3 may fail on some endpoints → force TLS 1.2 |

**Mandatory evaluation before any new module:**
1. Does it need cloud services? → Skip if yes, document rationale
2. Memory footprint? → Skip if >500MB peak
3. External deps? → Justify each one in module docstring
4. Better than existing? → If it's not a clear improvement, skip

## Local-First Evaluation Rule

**CRITICAL — learned from session feedback:** Before rejecting any feature as "cloud-only" or "too expensive", exhaust local alternatives first. The user knows their hardware better than you do. When they push back on a skip decision, re-evaluate immediately.

Checklist before marking something as skipped:
1. Can it run with macOS built-in tools? (say, ffmpeg, osascript, shortcuts, spotlight)
2. Can it run with stdlib Python + 1 pip install? (PyTorch MPS for ML tasks)
3. Did you actually TEST the capability, or just assume? → Run the check command
4. Did you ASK the user if they want to skip? → If not, decline with options, not a final decision

## Upgrade Evaluation Framework

**CRITICAL — from session feedback:** Before upgrading or integrating any external design doc, plugin, or feature, run the 4-point evaluation:

| # | Check | If NO → |
|---|-------|---------|
| 1 | **Does it actually run on Mac M2 8GB?** | Skip, or find a local alternative first |
| 2 | **Is it strictly better than what we have?** | Skip. "More code ≠ better" |
| 3 | **Does it need cloud services we don't have?** | Try macOS built-in tools first (say, ffmpeg, osascript) |
| 4 | **Does it add value proportionate to complexity?** | Skip if marginal improvement costs high token/complexity |

**Example from this session:** v6.7 document proposed 4 Token bug fixes that were for a standalone Feishu Bot architecture. Our system uses Hermes Agent built-in Feishu platform — none of the 4 bugs applied. Correct decision: skip, not a "missed opportunity."

**On user pushback:** When the user says "这个部分本地电脑可以实现" — believe them. Re-evaluate. In this session: HeyGen/D-ID was initially skipped as "cloud-only, $50+/mo", but user corrected us — M2 can run SadTalker + PyTorch MPS locally. Result: created Tier 1 (ffmpeg+say, zero dep) and Tier 2 (SadTalker, optional).

## Document-Driven Development

When the user provides design documents (HTML/Markdown), process them systematically:

1. **Extract structure** — Strip HTML tags, identify sections/headings/problems
2. **Separate by applicability** — What applies to our architecture? What doesn't?
3. **Map to existing modules** — Which modules can absorb the upgrade? What's new?
4. **Prioritize by impact** — Fix the UX/pipeline issues first, backend bugs only if they actually affect us
5. **Declare what's skipped AND WHY** — Every skip must have a technical rationale

## Module Catalog

| Module | Location | Lines | CLI | Dependencies |
|--------|----------|-------|-----|--------------|
| `digital_human.py` | `molib/infra/` | 280 | `molib avatar create/list-voices/check` | ffmpeg + macOS say (Tier 1), PyTorch MPS (Tier 2 optional) |
| `feishu_card_builder.py` | `molib/infra/gateway/` | 500 | — | stdlib |
| `feishu_reply_pipeline.py` | `molib/infra/gateway/` | 200 | — | feishu_card_builder |
| `budget_guard.py` | `molib/infra/` | 230 | `molib cost report/check/reset` | stdlib |
| `trading_agents.py` | `molib/agencies/` | 390 | `molib trading signal/analyze/research` | stdlib + urllib |
| `coco_index.py` | `molib/infra/` | 310 | `molib index watch/query/sync/stats` | sqlite3 |
| `feishu_bitable.py` | `molib/infra/` | 280 | `molib bitable schema/write/list` | urllib |
| `distiller.py` | `molib/infra/memory/` | 250 | `molib memory distill/stats` | sqlite3 |
| `feishu_noise_filter.py` | `molib/infra/` | 200 | automatic | re |
| `swarm_bridge.py` | `molib/agencies/` | 568 | `molib swarm list/run/visualize` | stdlib |

## Skip List (vetted, but user may override)

These were evaluated. Do NOT skip them without re-checking current viability:

- **DSPy prompt optimization** — Each iteration costs 10K+ tokens, existing prompts sufficient. RE-EVAL if token costs drop or prompts degrade.
- **夸克 cloud backup** — Already have GitHub + local HDD dual backup. RE-EVAL if one backup target fails.
- **猪八戒 shop automation** — No API documentation, niche platform. RE-EVAL if API becomes available.
- **Complex L2 approval workflow** — Existing L0-L4 governance engine + verbal confirmation sufficient. RE-EVAL if governance violations increase.