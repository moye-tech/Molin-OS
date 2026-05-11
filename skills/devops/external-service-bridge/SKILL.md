---
name: external-service-bridge
description: 'Deploy and bridge external polyglot services (Node.js, Go, Rust, etc.) alongside Molin-OS. Covers: evaluation, deployment, API discovery, resource verification, and Worker→HTTP bridge design. Use when integrating an external daemon/service that runs as its own process (not pip-installable Python).'
version: 1.0.0
metadata:
  hermes:
    tags:
    - integration
    - deployment
    - nodejs
    - polyglot
    - bridge
    related_skills:
    - hermes-skill-adaptation-pipeline
    - setup-hermes-enhancement-repo
    - molin-os-development
    molin_owner: CEO
---

# External Service Bridge

## Overview

When Molin-OS needs to use an external service written in a non-Python language (Node.js, Go, Rust, etc.), the integration pattern is fundamentally different from pip-installable Python tools. The service runs as its own process, and Molin-OS communicates via HTTP API or subprocess CLI.

This skill defines the **evaluate → deploy → probe → bridge** pipeline for external polyglot services.

## When to Use

- User shares a GitHub repo written in Node.js/TypeScript/Go/Rust and asks "can this strengthen Molin-OS?"
- You need to run an external daemon alongside Molin-OS as a sidecar service
- You're designing a Worker → HTTP API bridge pattern
- The service has its own package manager (pnpm/npm/cargo/go mod) and runtime, separate from Python

**Do NOT use this skill for:**
- Python packages (pip install → `hermes-skill-adaptation-pipeline`)
- Hermes Agent enhancement repos (`setup-hermes-enhancement-repo`)
- Pure CLI tools with no daemon (subprocess call, no bridge needed)

## Pipeline

### Phase 1: Evaluate

Before any deployment, score the project against Molin-OS constraints:

```
Score table (each 0-10):
• Capability gap fill — does it fill a missing layer in Molin-OS?
• Skill library value — how many new capabilities does it add?
• M1 8GB fit — memory footprint estimate
• Network dependency — can it run offline after install?
• Integration complexity — how hard to bridge with Molin-OS?
• License — Apache 2.0/MIT preferred, GPL cautiously
```

**Hard blockers (auto-reject):**
- Requires Docker (M1 8GB can't run Docker well)
- Requires cloud service with no local fallback
- Estimated memory > 2GB RSS
- Requires GPU
- Paid/proprietary license without free tier

**Presentation format:**
1. Lead with conclusion (YES/NO/CONDITIONAL)
2. Architecture match score (1-10)
3. Specific capability gains (per dimension, with scores)
4. Deployment risks (with severity: 🔴🟠🟡)
5. Recommended integration approach (with options A/B/C)
6. Phased execution plan (Day 1-4)

### Phase 2: Deploy

#### Step 1: Clone
```bash
mkdir -p ~/Projects
cd ~/Projects
git clone <repo-url> --depth 1
```

#### Step 2: Check environment
```bash
# Verify Node.js version matches package.json engines
node --version
# Check package manager availability
which pnpm npm
```

#### Step 3: Handle proxy
**CRITICAL: Kill proxy before npm/pnpm install.** Clash Party proxy (127.0.0.1:7890) often slows or breaks npm downloads. Verify:
```bash
env | grep -i proxy  # Should be empty
```
If proxy vars are set, unset them or use the `--proxy` flag with the proxy address, not env vars.

#### Step 4: Install dependencies

**Node.js with pnpm:**
```bash
# macOS corepack quirk: corepack enable needs sudo
# Workaround: call corepack directly
corepack pnpm@<version> install
```
See `references/pnpm-corepack-pitfalls.md` for macOS-specific quirks (corepack sudo, version mismatch, proxy interference).

#### Step 5: Start daemon
Follow the project's AGENTS.md or README for the correct launch command. For monorepos:
```bash
pnpm tools-dev start daemon    # or equivalent
pnpm tools-dev status daemon    # verify
```

#### Step 6: Verify resource usage
```bash
ps -p <pid> -o pid,rss,pcpu,comm
```
- RSS < 200MB → green light
- RSS 200-500MB → yellow (monitor)
- RSS > 500MB → red (reconsider on M1 8GB)

### Phase 3: API Discovery

External services rarely document their full API. Discover it:

```bash
# Method 1: grep Express/Fastify routes
grep -n "app\.\(get\|post\|put\|delete\)(" <server-file>

# Method 2: Probe endpoints
curl -s http://127.0.0.1:<port>/api/health
curl -s http://127.0.0.1:<port>/api/skills | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d))"

# Method 3: Check for auto-detection features
curl -s http://127.0.0.1:<port>/api/agents
curl -s http://127.0.0.1:<port>/api/active
```

Document all discovered endpoints with their response shapes. Save to `references/<service>-api.md`.

### Phase 4: Design Bridge

The bridge pattern:

```
Molin-OS (Python)
  └─ Worker (molib/agencies/workers/<name>.py)
       └─ async def _call_daemon(self, endpoint, payload) -> dict
            └─ aiohttp.ClientSession → http://127.0.0.1:<port>/api/...
                 └─ External Daemon (Node.js/Go/Rust)
                      └─ Returns JSON response
```

**Bridge module template:**
```python
# molib/agencies/workers/<name>.py
import aiohttp
from typing import Optional

class <Name>Bridge:
    def __init__(self, base_url: str = "http://127.0.0.1:55888"):
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        if self._session is None:
            self._session = aiohttp.ClientSession()

    async def health(self) -> dict:
        await self._ensure_session()
        async with self._session.get(f"{self.base_url}/api/health") as resp:
            return await resp.json()

    async def list_skills(self) -> list:
        await self._ensure_session()
        async with self._session.get(f"{self.base_url}/api/skills") as resp:
            data = await resp.json()
            return data.get("skills", [])

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
```

**Phase-gated approach:** Do NOT write the full Worker on Day 1. Verify the daemon is stable first. Write the bridge module incrementally as you discover the real API.

### Phase 5: Lifecycle Management

```bash
# Start
cd ~/Projects/<project> && pnpm tools-dev start daemon

# Status
cd ~/Projects/<project> && pnpm tools-dev status

# Stop
cd ~/Projects/<project> && pnpm tools-dev stop daemon

# Logs
tail -f ~/Projects/<project>/.tmp/tools-dev/default/logs/daemon/latest.log
```

Consider adding to Molin-OS startup sequence if critical.

## Reference: Open Design (Example)

**Source:** nexu-io/open-design ⭐34K, Apache 2.0, TypeScript/Next.js
**Path:** ~/Projects/open-design
**Daemon:** http://127.0.0.1:55888, 161MB RSS
**Resources:** 149 design systems + 134 skills + 16 auto-detected agents

See `references/open-design-api.md` for the full discovered API (50+ endpoints across skills, projects, artifacts, agents, deploy, MCP, etc.).

## Common Pitfalls

1. **Proxy interference** — Clash Party proxy (127.0.0.1:7890) can slow npm/pnpm to timeout. Always check `env | grep proxy` before install. Direct connection is faster for bulk downloads.
2. **Corepack permission on macOS** — `corepack enable` writes to `/usr/local/bin/pnpm` which needs sudo. Use `corepack pnpm@version <cmd>` directly without enable.
3. **pnpm version mismatch** — When package.json specifies a different pnpm version than system, `corepack pnpm@version` runs the right version but internal version checks see the system version. Use system pnpm directly for `tools-dev` scripts, corepack only for install.
4. **Assuming API endpoints** — Don't guess `/api/skills/run` or similar. Grep the source code for actual routes. The API shape is always project-specific.
5. **Skipping resource check** — Always check RSS before committing to long-running daemon. 161MB is fine on M1 8GB; 500MB+ is not.
6. **pnpm install timeout** — If install hangs, the proxy is the #1 suspect. Kill proxy, unset env vars, retry.
7. **npm global bin path** — The user's pnpm is at `~/.npm-global/bin/pnpm`. Corepack-managed pnpm may conflict. Prefer corepack for the pinned version.
8. **Full-stack vs daemon-only** — Most external services have a web UI component. On M1 8GB, run daemon-only mode. The web UI (Next.js dev server) can consume 300-500MB extra.

## Verification Checklist

- [ ] Repo cloned to ~/Projects/
- [ ] Dependencies installed without proxy interference
- [ ] Daemon started and health check passes (`{"ok":true}`)
- [ ] RSS < 500MB (ideally < 200MB)
- [ ] All API endpoints discovered and documented
- [ ] Bridge module skeleton created (health + list working)
- [ ] Lifecycle commands documented (start/stop/status/logs)
- [ ] Memory updated with deployment state
