# 方案2 Pattern: Pure Python Fallback

> Canonical source: `molin-os-development` skill → Mac M2 Network Constraints section
> Applied session: 2026-05-11 (ComfyUI Tier 3 blocked → diffusers方案2)

## When to Apply方案2

Network blocks external tool installation → create pure Python alternative instead of fighting the network:

- `git clone` times out (GitHub CDN)
- `pip install` SSL read timeout (PyPI)
- `brew install` hangs
- Binary downloads truncated (9-byte files)

## Pattern Steps

1. **Identify core capability** — what does the external tool actually DO?
2. **Find Python stdlib equivalent** — sqlite3 for DB, smtplib for email, pathlib for fs
3. **If stdlib insufficient, use pip-installable pure Python lib** — diffusers for image gen, not ComfyUI clone
4. **Preserve same CLI interface** — `molib comfy generate --prompt ...` works whether ComfyUI or diffusers
5. **Graceful fallback** — if neither方案2 nor original works, return clear error with install instructions

## Proven Examples

| Original | Blocked By | 方案2 | Stars |
|----------|-----------|-------|-------|
| PocketBase 54K★ | Go binary download truncated | `molib_db.py` — SQLite CRUD + auth | ✅ |
| listmonk 15K★ | brew install timeout | `molib_mail.py` — SMTP + list mgmt | ✅ |
| MedusaJS 27K★ | Node + PostgreSQL heavy | `molib_order.py` — order lifecycle | ✅ |
| Umami 23K★ | git clone timeout | `molib_analytics.py` — pageview tracking | ✅ |
| ComfyUI 60K★ | git clone CDN truncated | `molib_comfy.py` v2.0 — diffusers MPS | ✅ |
| Kill Bill 4K★ | Java runtime heavy | `molib_order.py` (invoice engine) | ✅ |
| NocoBase 12K★ | Node + DB heavy | `molib_db.py` (collection CRUD + auth) | ✅ |

## Network Workarounds (tried in order)

1. Direct `pip install` with 120s timeout
2. Tsinghua mirror: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`
3. Shallow clone: `git clone --depth 1`
4. If all fail → 方案2 pure Python fallback

## Post-install Dependency Conflicts

Some packages (browser-use, gpt-researcher) pin conflicting versions of shared deps (openai, requests). After installing:
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple "openai<3,>=2.36" "requests<3,>=2.33" "rich<15,>=14.3.3"
```
Accept dependency conflict warnings — imports work fine.
