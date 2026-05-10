# External Integration Pattern (2026-05-11)

Proven pattern from the GitHub开源武装升级 session: integrating 7 GitHub projects (gpt-researcher ⭐18k, firecrawl ⭐70k, browser-use ⭐50k, CosyVoice ⭐21k, FLUX.2 ⭐20k, STORM ⭐22k, HyDE+BM25) into 10 Workers.

## Directory Structure

```
molib/infra/external/
├── __init__.py              # Doc-only: lists all integrations
├── gpt_researcher.py        # GPT-Researcher (130 lines)
├── firecrawl.py             # Firecrawl scraper (147 lines)
├── browser_use.py           # Browser automation (88 lines)
├── cosyvoice.py             # CosyVoice TTS (143 lines)
├── fal_flux.py              # FLUX.2 image gen (158 lines)
└── storm_research.py        # STORM reports (110 lines)
```

## Worker Integration Pattern

Each Worker adds a new `action` case in its `execute()` method:

```python
async def execute(self, task, context=None):
    action = task.payload.get("action", "default")

    # v2.1 新增 action
    if action == "deep_research":
        output = await self._deep_research(task.payload)

    elif action == "firecrawl_search":
        output = await self._firecrawl_search(task.payload)

    # ... existing actions preserved
    elif action == "predict":
        output = await self._llm_predict(...)

    return WorkerResult(...)
```

**Key principle:** New actions are ADDED alongside existing ones — never remove old functionality. Old LLM-based fallbacks remain as `source: "mock"` when external tools are unavailable.

## Fallback Chain Pattern

Always try the best option first, degrade gracefully:

```python
async def _synthesize(self, payload):
    text = payload.get("text", "")

    # Tier 1: Cloud API (best quality)
    try:
        from molib.infra.external.cosyvoice import synthesize
        result = synthesize(text=text, voice=voice, emotion=emotion)
        if result.get("status") == "success":
            return result
    except Exception:
        pass

    # Tier 2: macOS built-in (local, free)
    try:
        subprocess.run(["say", "-v", "Tingting", "-o", output_path, text])
        return {"fallback": "macos_say", ...}
    except Exception:
        pass

    # Tier 3: LLM description (always works)
    return {"status": "unavailable", "error": "TTS不可用"}
```

## Feasibility Filtering for Mac M2 8GB

When evaluating external projects from upgrade documents:

| Project | Stars | Local Feasible? | Decision | Alternative |
|---------|-------|----------------|----------|-------------|
| gpt-researcher | 18k | ✅ pip, ~5MB, 0 GPU | pip install + SDK | — |
| firecrawl | 70k | ⚠️ cloud API | pip install SDK | — |
| browser-use | 50k | ✅ pip + playwright | pip install | — |
| CosyVoice | 21k | ❌ local needs GPU | DashScope API | macOS `say` fallback |
| ComfyUI | 97k | ❌ needs >6GB GPU | fal.ai API | — |
| FLUX.2 | 20k | ❌ needs GPU | fal.ai API ($0.04/img) | — |
| RAGFlow | 70k | ❌ Docker 4GB+ RAM | Enhance existing RAGEngine | HyDE+BM25 wrapper |
| n8n | 65k | ❌ no Docker | CRM已有完整功能 | Pure Python campaign sequences |
| STORM | 22k | ✅ pip, pure Python | pip install + SDK | — |

**Rule:** Cloud API is acceptable for GPU-heavy tasks (image gen, TTS models) when local hardware can't support them. Docker-dependent projects are acceptable only when Docker is installed; otherwise fall back to pure Python alternatives.

## Verification Protocol

After adding new integrations:
1. `python -c "import molib.infra.external; print('OK')"` — all modules
2. `python -c "from molib.agencies.workers.<name> import <Class>"` — each Worker
3. `git diff --stat` — confirm only intended files changed
4. `git commit` + `git push` — sync to GitHub
