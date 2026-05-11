# Content Layer Upgrade Workflow (v2.5)

> Pattern extracted from 2026-05-11 session: `molin-os-content-feishu-upgrade.html` → full implementation.

## Workflow

When the user provides a content/capability upgrade document:

```
1. Read full document (all sections)
2. Scan current system state (what exists vs what's claimed)
3. Build gap matrix: P1/P2/P3 × exists_working / exists_broken / missing
4. Implement in priority order, parallel where independent:
   a. P1 This week: highest leverage, lowest effort first
   b. P1 This month: new capabilities with clear ROI
   c. P2 This month: activate existing dormant integrations
   d. P3 Next month: heavy GPU deps, defer
5. Verify all imports in one shot
6. Commit with structured message linking to document sections
```

## Assessment Template

For each proposed upgrade:
- **Name**: What the document calls for
- **Current state**: Check file exists, service running, pip installed
- **Action needed**: Create new module / activate dormant / configure API key
- **Dependency check**: pip list, curl health check, env var check
- **Risk**: Network/GPU/Docker dependency that may fail on M2

## Example: 2026-05-11 Session

| Dimension | Doc Proposal | System State | Implemented |
|-----------|-------------|-------------|-------------|
| FeishuCardRouter | New module | No file existed | ✅ `feishu_card_router.py` |
| crawl4ai | pip install + integrate | crawl4ai 0.8.6 installed | ✅ `reference_engine.py` + ContentWriter patch |
| CosyVoice v3 | TTS upgrade | tts_generator.py exists, API-only | ✅ `cosyvoice_tts.py` (4-backend fallback) |
| MuseTalk+LivePortrait | New digital human | No service running | ✅ `digital_human.py` (API pre-configured) |
| MoviePy glue layer | Video post-processing | moviepy 2.2.1 installed | ✅ `video_processor.py` |
| MoneyPrinterTurbo | Activate local service | MPT not running | ⚠️ Documented, BACKENDS priority set |
| ComfyUI | Activate local image gen | ComfyUI not running | ⚠️ Documented, API endpoint pre-configured |

## Key Pattern: "代码就绪，服务待启动"

When a GitHub project requires local GPU/Docker:
- Write the integration module NOW (API endpoints, fallback chains, health checks)
- Document the activation command in the module's status check
- Tag as "code-ready, service-pending" in the commit
- This lets the system work the moment the service starts, vs. needing another dev cycle
