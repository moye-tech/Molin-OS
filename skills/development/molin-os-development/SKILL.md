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

## Python 3.11 Pitfall: TypeVar Compatibility + `from __future__` Placement

**FOUND AND FIXED 2026-05-10 (twice — MolinDB session + v2.0 migration):**

### Root cause: `TypeVar | dict` is invalid in Python 3.11

Python 3.11 does not support the `X | Y` union syntax when `X` is a `TypeVar`. The fix is `from __future__ import annotations`, which makes ALL annotations lazy strings — but it must be placed correctly.

**Symptom:** `TypeError: unsupported operand type(s) for |: 'TypeVar' and 'type'` — entire worker subsystem blocked.

**Affected file:** `molib/agencies/workers/base.py` line 13: `payload: T | dict = field(default_factory=dict)`

### Placement: `from __future__` MUST be first statement

**Fix:**
```python
# ❌ Wrong — SyntaxError
"""docstring"""
from abc import ABC
from __future__ import annotations  # SyntaxError: must be at beginning!

# ❌ Wrong — ImportError (3.11 can't parse T | dict)
from abc import ABC
from dataclasses import dataclass
T = TypeVar("T")
class Task(Generic[T]):
    payload: T | dict  # TypeError!

# ✅ Correct — works (__future__ MUST be line 1, before docstring)
from __future__ import annotations
"""docstring"""
from abc import ABC
from dataclasses import dataclass
```

**Verification:**
```bash
# Line 2 must be __future__
head -3 molib/agencies/workers/base.py
# Expected: line 1 = from __future__ import annotations, line 2 = docstring
```

## Mac M2 Network Constraints

**CRITICAL — GitHub downloads >10MB reliably fail** on this machine. Symptoms: 9-byte truncated files, timeout, "truncated gzip input". This affects: git clone, curl -L release downloads, brew install (from source).

### Proxy Workaround (Clash Party / Mihomo)

**Clash Party is installed and running** on this Mac (`/Applications/Clash Party.app`). It wraps Mihomo (Clash Meta) as sidecar:

| Setting | Value |
|---------|-------|
| HTTP/SOCKS proxy | `http://127.0.0.1:7890` |
| SOCKS port | `7891` |
| Mixed port | `7890` |
| TUN device | `utun1500` (system-level VPN) |
| Control socket | `/tmp/mihomo-party-501-5151.sock` |
| Working dir | `~/Library/Application Support/mihomo-party/work` |
| Config | `~/Library/Application Support/mihomo-party/work/config.yaml` |
| Subscription mgmt | `~/Library/Application Support/mihomo-party/profile.yaml` |

**Verified working** (2026-05-11):
```bash
# pip through proxy — bypasses PyPI SSL timeouts
pip install --proxy http://127.0.0.1:7890 gpt-researcher browser-use

# curl through proxy
curl -x http://127.0.0.1:7890 https://httpbin.org/ip
# → {"origin": "109.61.127.153"}  (HK exit IP)
```

**When network operations fail (SSL timeout, connection reset), retry with `--proxy http://127.0.0.1:7890` or `export https_proxy=http://127.0.0.1:7890`.**

### Proven Workaround: Pure Python Fallback

When a popular tool's binary download fails due to network, create a pure-Python stdlib equivalent:

| Original | Stars | Problem | Molib Fallback | Status |
|----------|-------|---------|----------------|--------|
| PocketBase | 54K | Go binary download truncated | `molib_db.py` — SQLite CRUD + auth | ✅ |
| listmonk | 15K | brew install timeout | `molib_mail.py` — SMTP + list management | ✅ |
| MedusaJS | 27K | Node + PostgreSQL too heavy | `molib_order.py` — order lifecycle + invoice | ✅ |
| Umami | 23K | git clone timeout | `molib_analytics.py` — pageview tracking + stats | ✅ |
| Kill Bill | 4K | Java runtime too heavy | `molib_order.py` (invoice engine) | ✅ |
| NocoBase | 12K | Node + DB too heavy | `molib_db.py` (collection CRUD + auth) | ✅ |

### What DOES download reliably

- **PyTorch CPU wheels** from `download.pytorch.org` — works with 120s timeout. Install recipe:
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
  ```
- **npm packages** via npx — works for small packages (n8n worked at 2.19.5)
- **Small GitHub files** (<1MB) — curl works
- **PyPI packages** — pip install usually works, but large ones (~500MB+) may fail

### Network Decision Flow

```
New external tool needed?
├── Can we download the binary? (<1MB, not from GitHub releases)
│   └── YES → download + wrap with molib module
├── Can we `pip install` it?
│   └── YES → install + wrap
├── Can we `npm/npx` it?
│   └── YES → use + wrap
└── NO → Create pure Python stdlib equivalent
    └── This is the MolibDB/MolibMail/MolibOrder pattern
## Mac M2 Deck — What Runs Locally

| Capability | Engine | Status | Cost |
|------------|--------|--------|------|
| AI image generation | diffusers (方案2) + PyTorch MPS 2.11.0 | ✅ Tier 2 MPS ✅, 方案2 (diffusers sd-turbo/sd-1.5/sdxl-turbo) active. Tier 3 ComfyUI clone blocked by network → skipped in favor of纯Python方案2. | Free |
| TTS (50+ voices) | macOS `say -v '?'` | ✅ Built-in | Free |
| Digital human (static) | ffmpeg + say → image+audio→video | ✅ Tier 1 | Free |
| Digital human (lip-sync) | SadTalker + PyTorch MPS | 🔜 Tier 2 | Free (`pip install torch` ✅ done 2026-05-10) |
| Video compositing | ffmpeg 8.1.1 | ✅ | Free |
| AI image generation | ComfyUI + PyTorch MPS 2.11.0 | ⚠️ Tier 2 MPS ✅, Tier 3 (ComfyUI repo clone) blocked by network — shallow clone also fails (Connection reset by peer) | |
| ML inference (small) | PyTorch MPS 2.11.0 (8GB unified) | ✅ Installed 2026-05-10 via `pip install torch --index-url https://download.pytorch.org/whl/cpu` | Free |
| Workflow automation | n8n 2.19.5 (npx) | ✅ Available on-demand (`npx n8n`) | 200MB RAM (temporary) |
| Email marketing | MolibMail (SMTP stdlib) | ✅ No external binary needed | Free |
| Order management | MolibOrder (SQLite) | ✅ No external binary needed | Free |
| Analytics | MolibAnalytics (SQLite) | ✅ No external binary needed | Free |
| Unified backend | MolibDB (SQLite: collection/record/auth) | ✅ No external binary needed | Free |
| Revenue pipeline | MolibDB + MolibMail + MolibOrder + MolibAnalytics | ✅ 4 SQLite files, <30MB total | Free |
| Speech recognition | MolibSTT (ffprobe metadata + whisper optional) | ✅ Tier 1+2, Tier 3 needs `pip install openai-whisper` | Free |
| CRM pipeline | MolibDB-backed CRM (6-stage pipeline) | ✅ No external binary needed | Free |

## Mac M2 Deployment Constraints

| Resource | Limit | Impact |
|----------|-------|--------|
| RAM | 8 GB unified | No local LLMs, ChromaDB + SQLite OK, Redis too heavy |
| CPU | 8 cores (M2) | Parallel subagents fine, but 3-4 max simultaneously |
| Python | 3.11.15 | No match/case exhaustiveness, no `str | None` syntax |
| Disk | 169 GB free | Plenty for files, not for ML models (>5GB each) |
| OpenSSL | System (3.x) | TLS 1.3 may fail on some endpoints → force TLS 1.2 |

### Hard Constraints (User Explicit — 2026-05-11)

**NO Docker.** User explicitly rejected Docker-based solutions. Find pure Python or macOS native alternatives for everything. Skip projects that require Docker (RAGFlow, OpenHands) unless user explicitly requests otherwise.

**NO local LLM / Ollama.** User explicitly rejected local LLM deployment. Skip ollama, skip downloading 7B+ models. Use cloud API alternatives: Fish-Speech API for TTS (not local CosyVoice), DashScope for translation (not local Seed-X), DeepSeek API for LLM tasks.

**API-First for heavy compute.** When a task requires GPU or >3GB models, use cloud APIs: fal.ai for FLUX.2 image generation, Fish Audio for TTS, DashScope for translation/vision. Reserve local MPS for lightweight inference only (diffusers sd-turbo, small PyTorch models).

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

## Reference Files

- `references/worker-activation-pattern.md` — From SKILL.md-only to working code+CLI (2026-05-10)
- `references/worker-v2-migration-pattern.md` — Batch upgrade to SmartSubsidiaryWorker + collaboration injection (2026-05-10)
- `references/external-integration-pattern.md` — Lazy-import dict-return fallback-chain pattern for heavy GitHub deps (2026-05-11)
- `references/firecrawl-v2-migration.md` — Firecrawl v2 API breaking changes: Document objects, scrape_url→scrape (2026-05-11)
- `references/github-arsenal.md` — 47+ GitHub projects mapped to 20 subsidiaries, P1/P2/P3 priorities (2026-05-11)
- `references/plan-b-pure-python-fallback.md` — 方案2: when network blocks external tools, create pure Python equivalents (2026-05-11)

## Mac M2 Pip Timeout → Tsinghua Mirror / Clash Proxy

**PyPI direct downloads frequently time out** on this machine (read timeout after 15s, 4 retries all fail). Two proven workarounds:

```bash
# Option A: Tsinghua mirror (国内直连)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple gpt-researcher browser-use playwright

# Option B: Clash Party proxy (经香港出口)
pip install --proxy http://127.0.0.1:7890 diffusers accelerate safetensors
```

**When to use mirror:** Any `pip install` that shows `ReadTimeoutError` on first attempt — try mirror first (faster, no proxy overhead).
**When to use proxy:** Mirror fails or package not available on mirror — use Clash proxy.

**Post-install dependency fix:** Some packages (e.g., `browser-use 0.12.6`) pin exact versions of shared deps (`openai==2.16.0`, `requests==2.32.5`) that conflict with Hermes Agent. After installing, restore Hermes deps:

```bash
pip install --proxy http://127.0.0.1:7890 "openai<3,>=2.36" "requests<3,>=2.33" "rich<15,>=14.3.3"
```

Accept the pip dependency conflict warnings — the code imports fine.

## Non-Invasive Enhancement Pattern

**Rule:** When enhancing large existing modules (500+ lines), create a WRAPPER rather than modifying the original. This was proven on RAGEngine (568 lines):

```python
# ❌ Wrong — modify 568-line file, risk breakage
# rag_engine.py — add HyDE + BM25 directly

# ✅ Right — create wrapper
# hybrid_retriever.py — imports RAGEngine, adds HyDE + BM25 on top
```

This pattern applies to all shared/infra modules. The wrapper:
- Imports the original class
- Adds new functionality in a separate class/function
- Returns unified results
- Doesn't change the original's API or behavior

## External Integration Module Pattern

When integrating GitHub open-source projects (pypi packages or cloud APIs), use `molib/infra/external/`:

```python
"""Module docstring with GitHub stars count and Worker integration points."""
from __future__ import annotations

async def main_function(param: str) -> dict:
    """Always return dict. Never raise — return error dict."""
    try:
        from heavy_dep import Client  # lazy import — only on first call
        client = Client()
        result = client.do_work(param)
        return {"data": result, "status": "success", "source": "name"}
    except ImportError:
        return {"error": "not installed. Run: pip install x", "status": "unavailable"}
    except Exception as e:
        return {"error": str(e), "status": "error"}
```

**Rules:**
- All functions return `dict` — never raise exceptions
- Lazy import all heavy deps inside functions — don't import at module level
- Always provide `"status"` key: "success" | "error" | "unavailable" | "timeout" | "no_api_key"
- Always provide `"source"` key for tracing
- Fallback chain: cloud API → local alternative → macOS built-in → LLM fallback → mock
- File path: `molib/infra/external/<project_name>.py`

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
| `molib_db.py` ⭐ | `molib/infra/` | 370 | `molib db collection/record/auth/stats` | sqlite3 (PocketBase 54K★ 替代) |
| `molib_mail.py` ⭐ | `molib/infra/` | 350 | `molib mail list/subscriber/campaign/stats` | smtplib (listmonk 15K★ 替代) |
| `molib_order.py` ⭐ | `molib/infra/` | 380 | `molib order create/list/invoice/stats` | sqlite3 (MedusaJS 27K★ + KillBill 4K★ 替代) |
| `molib_analytics.py` ⭐ | `molib/infra/` | 200 | `molib analytics track/stats/top-pages` | sqlite3 (Umami 23K★ 替代) |
| `molib_comfy.py` | `molib/infra/` | 418 | `molib comfy check/generate/models/preload/img2img` | PyTorch MPS + diffusers (方案2: 纯Python替代 ComfyUI 60K★, sd-turbo/sd-1.5/sdxl-turbo) |
| `molib_flow.py` ⭐ | `molib/infra/` | 80 | `molib flow check/start/compare` | npx n8n (55K★ 桥) |
| `molib_stt.py` ⭐ | `molib/infra/` | 130 | `molib stt check/transcribe` | ffmpeg (Whisper 替代) |
| External bridges v2.2 | `molib/infra/external/` | 行 | — | 12模块: gpt-researcher/firecrawl/browser-use/crawl4ai/diffusers/fish-speech/fal-flux/storm/nemo-guardrails/n8n-rest/langgraph-chain/seedx-translate |
| `designer_worker.py` ⭐ | `molib/agencies/workers/` | 100 | — | PyTorch MPS (墨图设计升级) |
| `voice_actor_worker.py` ⭐ | `molib/agencies/workers/` | 115 | — | macOS say + ffmpeg (墨声配音升级) |
| `data_analyst_worker.py` ⭐ | `molib/agencies/workers/` | 100 | — | MolibAnalytics + CocoIndex (墨测数据升级) |
| `crm_worker.py` ⭐ | `molib/agencies/workers/` | 130 | — | MolibDB (墨域CRM升级, twenty CRM 20K★ 替代) |

## Skip List (vetted, but user may override)

These were evaluated. Do NOT skip them without re-checking current viability:

- **DSPy prompt optimization** — Each iteration costs 10K+ tokens, existing prompts sufficient. RE-EVAL if token costs drop or prompts degrade.
- **夸克 cloud backup** — Already have GitHub + local HDD dual backup. RE-EVAL if one backup target fails.
- **猪八戒 shop automation** — No API documentation, niche platform. RE-EVAL if API becomes available.
- **Complex L2 approval workflow** — Existing L0-L4 governance engine + verbal confirmation sufficient. RE-EVAL if governance violations increase.