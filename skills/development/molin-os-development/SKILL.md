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

**CRITICAL — async CLI commands:** NEVER call `asyncio.run()` inside a `cmd_xxx()` that's registered in `sync_commands`. `run()` itself is async, so `cmd_xxx` is called from within an already-running event loop — nesting `asyncio.run()` inside it raises `RuntimeError: asyncio.run() cannot be called from a running event loop`.

**Fix:** Make the command function `async def` and register it in `async_commands`:
```python
# ❌ Wrong — crash: asyncio.run() inside running event loop
def cmd_design(args):          # registered in sync_commands
    ...
    return asyncio.run(_run()) # RuntimeError!

# ✅ Right — async function in async_commands
async def cmd_design(args):    # registered in async_commands
    ...
    return await _run()        # natural await, no nested loop
```

**Symptom:** `RuntimeError: asyncio.run() cannot be called from a running event loop` + `RuntimeWarning: coroutine was never awaited`.

**Pattern:** When a new CLI command needs to `await` anything (Worker.execute, API calls, etc.), always make it async and register in `async_commands`. Keep sync-only commands (stdlib dict returns) in `sync_commands`.

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
6. **"继续" = exhaustive** — When user says "继续", push ALL remaining tasks to completion: check system state, deploy services, verify, commit. Don't stop at one action.
7. **Restart from scratch when user pushes back** — If user provides a new document or corrects the approach, re-assess the entire system state. Don't assume previous partial work is still valid.

### External Project Assessment Framework

See `references/open-design-assessment.md` for the full 4-phase methodology:
1. Information gathering (web_search + web_extract + git clone), 2. 4-dimension scoring (architecture/capability/deployment/maintenance), 3. 3-option integration path (transplant/bridge/deploy), 4. Actionable day-plan.
6. **"继续" = exhaustive** — When user says "继续", push ALL remaining tasks to completion: check system state, deploy services, verify, commit. Don't stop at one action.

### Upgrade Document → Implementation Pipeline

When user sends an HTML upgrade document (molin-os-v2-upgrade-map.html, molin-os-content-feishu-upgrade.html, etc.):

```
Phase 1: System scan — grep/pip list/find all relevant files, assess current state
Phase 2: GAP analysis — map document recommendations against reality
Phase 3: Parallel implementation — highest-impact+lowest-effort items first
Phase 4: Verification — import test + functional test for each new module
Phase 5: Commit + push — git add -A && git commit && git push
```

Key patterns proven in v2.5:
- **Free model tier (OpenRouter `:free` suffix)**: Used as Ollama alternative for cost routing. Models: mistral-small-3.1-24b, qwen3-8b, gemma-3-4b, llama-4-scout. Rotate to spread rate limits.
- **API Key injection**: Extract from config.yaml → write to ~/.hermes/.env → EnvLoader auto-loads into os.environ
- **Three-tier backend**: Cloud API (DashScope) → Local light (moviepy+ffmpeg) → Local heavy (MPT/Docker)
- **FeishuCardRouter**: 5 card types + decision tree + keyword trigger sets — solves "when to use card vs text"

### EnvLoader Pattern

**Problem:** .env API keys not visible in Python subprocesses (os.environ.get() returns empty).

**Solution:** `molib/shared/env_loader.py` — auto-loads on import, caches to avoid reload.

```python
from molib.shared.env_loader import load_dotenv, get_env
load_dotenv()  # Inject all ~/.hermes/.env vars into os.environ
key = get_env("DASHSCOPE_API_KEY")  # Safe access with .env loading
```

**When to use:** Every bot/*.py and every molib module that reads API keys via os.environ should call `load_dotenv()` at module top.

## Reference Files

- `references/content-upgrade-workflow.md` — Content/capability upgrade document → implementation pipeline (v2.5, 2026-05-11)
- `references/worker-activation-pattern.md` — From SKILL.md-only to working code+CLI (2026-05-10)
- `references/worker-v2-migration-pattern.md` — Batch upgrade to SmartSubsidiaryWorker + collaboration injection (2026-05-10)
- `references/external-integration-pattern.md` — Lazy-import dict-return fallback-chain pattern for heavy GitHub deps (2026-05-11)
- `references/firecrawl-v2-migration.md` — Firecrawl v2 API breaking changes: Document objects, scrape_url→scrape (2026-05-11)
- `references/github-arsenal.md` — 47+ GitHub projects mapped to 20 subsidiaries, P1/P2/P3 priorities (2026-05-11)
- `references/plan-b-pure-python-fallback.md` — 方案2: when network blocks external tools, create pure Python equivalents (2026-05-11)
- `references/gap-driven-upgrade-workflow.md` — GAP分析→并行实现→验证→提交 的系统升级流水线 + OpenRouter 免费模型路由作为 Ollama 替代 (2026-05-11)
- `references/service-activation-pattern.md` — MPT/ComfyUI/MuseTalk/LivePortrait 本地服务激活清单 + API Key 从 config.yaml 注入 .env 模式 (2026-05-11)
- `references/node-daemon-bridge.md` — Node.js daemon bridge pattern: Open Design v0.6.0 deployment, API catalog, corepack/pnpm workarounds, LLM pipeline (2026-05-11)
- `references/smart-dispatcher-routing-pattern.md` — SmartDispatcher COLLAB_RULES substring matching gotcha + bidirectional keyword strategy (2026-05-11)
- `references/open-design-assessment.md` — 外部GitHub项目评估框架 (4维度×3集成方案) + Open Design 34K★实例 (2026-05-11)

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

## Node.js Daemon Bridge Pattern

When integrating a Node.js project that runs as a local daemon (Express/Next.js server), use HTTP API bridging from Python workers:

```
Molin-OS (Python)                  Open Design (Node.js)
  └─ Worker (designer.py)            └─ daemon (Express :55888)
       ├─ _od_api_get(path)  ──GET──→  /api/skills/:id
       ├─ _od_api_get(path)  ──GET──→  /api/design-systems/:id
       ├─ LLM generates HTML          (stateless — daemon is passive)
       └─ _od_api_post(path) ──POST──→ /api/artifacts/save → preview URL
```

**Corepack/pnpm workarounds (critical — every Node.js daemon project):**

```bash
# Problem 1: corepack enable fails without sudo
# Fix: use corepack directly without enabling
corepack pnpm@<version> install           # ✅ no sudo needed
corepack pnpm@<version> --version         # ✅ verify

# Problem 2: pnpm tools-dev version check rejects corepack-managed pnpm
# Fix: use system pnpm directly — --pm-on-fail flag consumed by pnpm exec layer
pnpm tools-dev start daemon               # ✅ system pnpm handles version dispatch
```

**Worker integration recipe:**

```python
# 1. Static API helpers (stdlib only — urllib, no requests)
@staticmethod
def _od_api_get(path: str) -> dict | None:
    req = Request(f"{DAEMON_URL}{path}")
    req.add_header("Accept", "application/json")
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

# 2. Action → skill mapping (declarative, extensible)
ACTION_SKILL_MAP = {
    "landing_page": "saas-landing",
    "dashboard": "dashboard",
    "pitch_deck": "html-ppt-pitch-deck",
}

# 3. LLM generation pipeline
#    GET skill definition + design system → build system prompt →
#    LLM generates HTML → POST /api/artifacts/save → preview URL
```

**Key insight:** The daemon is *passive* — it stores skills/design-systems/artifacts but does NOT generate content. The agent (Hermes LLM) generates HTML code following the skill specification, then saves it back to the daemon for preview. The daemon provides: skill definitions, design system tokens (color/font/spacing), artifact persistence, and lint checks.

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
| External bridges v2.2 | `molib/infra/external/` | — | — | 12模块: gpt-researcher/firecrawl/browser-use/crawl4ai/diffusers/fish-speech/fal-flux/storm/nemo-guardrails/n8n-rest/langgraph-chain/seedx-translate |
| `feishu_card_router.py` ⭐ v2.5 | `molib/shared/publish/` | 200 | — | FeishuCardRouter: 5种卡片场景(T1-T5)决策树 + 4组关键词触发 + 治理级别路由 |
| `reference_engine.py` ⭐ v2.5 | `molib/shared/content/` | 280 | — | crawl4ai 爆款对标写作: 6种标题公式 + 情绪词库 + 平台写作规范 + 离线降级 |
| `cosyvoice_tts.py` ⭐ v2.5 | `molib/shared/tts/` | 380 | — | CosyVoice v3 TTS: 零样本声音克隆 + 18方言 + 情绪控制 + 4后端降级链 |
| `digital_human.py` ⭐ v2.5 | `molib/content/` | 520 | — | 数字人口播: TTS→MuseTalk唇形同步→LivePortrait→MoviePy 三阶段流水线 |
| `video_processor.py` ⭐ v2.5 | `molib/content/` | 390 | — | MoviePy 胶水层: 多平台适配 + 字幕 + BGM + 智能切片 |
| `memory_layer.py` ⭐ v2.5 | `molib/shared/` | 280 | `mem0ai` | 双层记忆: mem0用户级 + ExperienceVault任务级, DeepSeek/OpenRouter embedding |
| `observability.py` ⭐ v2.5 | `molib/shared/` | 250 | `langfuse` | Langfuse追踪: @observe_worker装饰器, 自动捕获耗时/token/异常 |
| `fault_tolerance.py` ⭐ v2.5 | `molib/shared/` | 300 | `prefect` | Prefect断点续跑: WorkerChain崩溃后从上次成功步骤继续, 指数退避重试 |
| `env_loader.py` ⭐ v2.5 | `molib/shared/` | 80 | stdlib | 统一.env→os.environ加载, 解决子进程API key不可见问题 |
| `designer.py` ⭐ v2.2 | `molib/agencies/workers/` | 270 | — | Open Design v0.6.0 daemon bridge (149设计系统×134技能) + FLUX.2生图 + 14个快捷action (landing_page/dashboard/pitch_deck/...) |
| `voice_actor_worker.py` ⭐ | `molib/agencies/workers/` | 115 | — | macOS say + ffmpeg (墨声配音升级) |
| `data_analyst_worker.py` ⭐ | `molib/agencies/workers/` | 100 | — | MolibAnalytics + CocoIndex (墨测数据升级) |
| `crm_worker.py` ⭐ | `molib/agencies/workers/` | 130 | — | MolibDB (墨域CRM升级, twenty CRM 20K★ 替代) |
| `larksuite_cli` ⭐ v2.5 | `npm global @larksuite/cli` | — | `lark-cli` (25+命令: im/calendar/docs/base/sheets/task/approval/mail/drive 等 17 个业务域) | Node.js v24.14.0 (Lark/Feishu 官方CLI, Agent-Native, MIT, 200+命令) |

## ComfyUI Hardware Constraint (verified 2026-05-11)

**M2 8GB is below the 16GB practical minimum.** Hardware check result:
```
GPU: Apple M2 — 8.0 GB unified memory
Verdict: cloud → comfy-cloud
• SD1.5 may work; SDXL/Flux will swap or OOM.
```

**Decision:** Use Comfy Cloud API ($0 free tier) or DashScope qwen-image-2.0-pro for image generation. The existing ComfyUI skill at `~/.hermes/skills/creative/comfyui/` supports both local and cloud via `scripts/hardware_check.py` → `scripts/comfyui_setup.sh`.

## System Audit Workflow

When the user requests a system audit ("梳理", "标准化", "清理冗余"), run this 6-phase pipeline:

```
Phase 1: Git sync — stash local → pull origin → pop + resolve conflicts
Phase 2: Audit — __pycache__ count, empty dirs, broken symlinks, $HOME literal dirs, .gitignore overreach
Phase 3: Clean — rm -rf __pycache__, rmdir empty refs dirs, delete broken paths
Phase 4: Import test — importlib all key modules, verify CLI health
Phase 5: Standardize — fix .gitignore rules, restore accidentally-ignored source files
Phase 6: Commit + push — git add, commit with audit summary, push origin
```

### Audit checklist

```bash
# __pycache__
find . -type d -name '__pycache__' -not -path './.git/*' | wc -l

# Empty directories (exclude .git internals)
find . -type d -empty -not -path './.git/*' -not -path '*/.git/*'

# Literal $HOME paths (BUG — $HOME not expanded)
find . -maxdepth 2 -name '$HOME' -type d 2>/dev/null

# .gitignore overreach (py files incorrectly ignored)
git ls-files --others --exclude-standard -i | grep '\.py$' | grep -v '__pycache__'

# Check WHY a file is ignored
git check-ignore -v path/to/file.py
```

### .gitignore pitfalls (from audit session)

| Bad rule | Why | Fix |
|:--|:--|:--|
| `**/auth.*` | Matches `auth.py`, `auth.js` source files | `**/auth.json` + `**/auth.env` |
| `*token*` | Matches `token_manager.py`, `token_utils.js` | `**/token.*` + explicit exclude for managers |

**Fix pattern:** narrow the glob to only match credential extensions (`.json`, `.env`, `.key`, `.pem`), and add `!` excludes for known source files.

### \$HOME literal directory BUG

**Symptom:** `find /Users/moye/Molin-OS -maxdepth 2 -name '$HOME'` returns a real directory. The project grows a literal `$HOME/Library/...` tree inside its root.

**Root cause:** A script used single-quoted or un-expanded `$HOME` in a path, creating a literal directory named `$HOME` instead of expanding to `/Users/moye`.

**Fix:** `rm -rf '$HOME'` from project root. Trace source via `grep -r '\$HOME' scripts/`.

## Skip List (vetted, but user may override)

These were evaluated. Do NOT skip them without re-checking current viability:

- **DSPy prompt optimization** — Each iteration costs 10K+ tokens, existing prompts sufficient. RE-EVAL if token costs drop or prompts degrade.
- **夸克 cloud backup** — Already have GitHub + local HDD dual backup. RE-EVAL if one backup target fails.
- **猪八戒 shop automation** — No API documentation, niche platform. RE-EVAL if API becomes available.
- **Complex L2 approval workflow** — Existing L0-L4 governance engine + verbal confirmation sufficient. RE-EVAL if governance violations increase.