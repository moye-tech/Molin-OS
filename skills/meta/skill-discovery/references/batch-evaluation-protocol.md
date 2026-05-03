# Batch Repository Evaluation Protocol

## Standard Flow

```
1. DEDUPLICATE: Check skills_list for already-evaluated repos
2. CATEGORIZE: Group repos by type (skills/tools/frameworks/guides)
3. PARALLEL RESEARCH: 3-4 repos per delegate_task call
4. TIER ASSESSMENT:
   Tier 1: Directly integrable (has Hermes path or compatible SKILL.md)
   Tier 2: Convertible with effort (different format but universal concepts)
   Tier 3: Skip (duplicate, deprecated, legal grey area, offensive tools)
5. CONVERT: Tier 1 immediately, Tier 2 if user says "进化"
6. INDEX: Add to meta/trending-projects or relevant catalog
```

## GitHub API Token Usage

When user provides a token:
```bash
TOKEN="ghp_xxx"
curl -sH "Authorization: token $TOKEN" "https://api.github.com/..."
```

Search patterns:
- `search/repositories?q=KEYWORDS+created:>DATE&sort=stars`
- `users/USER/repos?per_page=20&sort=updated`
- `repos/OWNER/REPO/readme` (base64-encoded content)

⚠️ Warn user to rotate token after session.

## Clone Strategies (Progressive Fallback)

1. `git clone --depth 1 URL` — standard, works for <50MB repos
2. `git clone --depth 1 --filter=blob:none --sparse URL && git sparse-checkout set PATHS` — for large repos
3. `curl -sL 'raw.githubusercontent.com/...' | head -200` — README-only evaluation
4. GitHub API tree listing — no clone needed, but max ~2MB response

## Triple-Timeout Rule

If delegate_task times out 3 consecutive times on the same task category:
1. Switch from delegate_task to direct terminal/execute_code
2. Don't keep retrying the same pattern — Hermes will trigger same_tool_failure_warning
3. Use execute_code with batch curl + write_file for skill conversions

## Conversion Patterns

### From Claude Code skills to Hermes:
- Replace `disable-model-invocation` with `metadata.hermes.auto_load`
- Replace `allowed-tools: Bash(...)` with `metadata.hermes.toolsets`
- Add `category:` field matching our 6-domain system
- Add `source:` attribution

### From OpenClaw skills to Hermes:
- Replace `clawhub install` references with `/skill` references
- Adapt platform-specific commands to Hermes equivalents

## Key Innovation: FFmpeg Video Pipeline

Discovered that with just FFmpeg + Edge-TTS + Pillow (all GPU-free), we can:
1. Generate script → xiaohongshu-content-engine
2. Generate TTS voiceover → edge-tts (free, zh-CN-XiaoxiaoNeural)
3. Compose video → FFmpeg (image slideshow + audio + text overlay + transitions)
4. Output → 1080×1920 MP4 ready for Xiaohongshu

This enables video content creation without any GPU dependency.
