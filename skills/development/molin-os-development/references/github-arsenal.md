# GitHub Open Source Arsenal for Molin-OS

> Source: `molin-os-github-arsenal.html` (2026-05, 47+ projects, 300万+ stars)
> Full HTML: `/Users/moye/.hermes/cache/documents/doc_546fac05580e_molin-os-github-arsenal.html`

## Integration Philosophy

- Not stacking tools — targeting capability ceilings per subsidiary
- Preference: ① Python SDK ② self-hosted ③ active 2025-2026 ④ DashScope/DeepSeek compatible
- Integration: `request_collaboration()` or Worker `execute()` wrapping Python SDK
- Shared infra layer (RAGFlow, Graphiti, n8n) as global services

## P1 立刻 (4 projects, 72h deliverable)

| Project | Stars | Worker | Benefit | Difficulty |
|---------|-------|--------|---------|------------|
| assafelovic/gpt-researcher | 18K | Research → all | Real-time web research replaces LLM hallucination | Low (pip) |
| mendableai/firecrawl | 70K | Research/ContentWriter | Competitor article scraping, trend extraction | Low (API) |
| FunAudioLLM/CosyVoice v3 | 21K | VoiceActor/ShortVideo | Real TTS (Chinese, 18+ dialects, zero-shot cloning) | Medium (Docker) |
| browser-use/browser-use | 50K | Ecommerce/BD | Xianyu auto-listing, price monitoring, BD outreach | Low (pip) |

## P2 本月 (4 projects)

| Project | Stars | Worker | Benefit | Difficulty |
|---------|-------|--------|---------|------------|
| comfyanonymous/ComfyUI | 97K | Designer/ShortVideo | Real AI image gen, FLUX.2/ControlNet | Medium (Docker) |
| infiniflow/ragflow | 70K | Knowledge → all | Enterprise RAG replacing simple RAGEngine | Medium (Docker) |
| n8n-io/n8n | 65K | CRM/CS/BD | Private domain automation hub, 400+ integrations | Medium (npx) |
| stanford-oval/storm | 22K | Research/Education | Wikipedia-quality deep reports | Low (pip) |

## P3 下月 (4 projects)

| Project | Stars | Worker | Benefit |
|---------|-------|--------|---------|
| getzep/graphiti | 5K | Knowledge → all | Real-time knowledge graph, temporal queries |
| OpenDevin/OpenHands | 45K | Developer | Autonomous coding + PR submission |
| fishaudio/fish-speech S2 | 18K | VoiceActor | SOTA TTS, Taiwanese accent support |
| EvoAgentX/EvoAgentX | new | AutoDream | Auto workflow evolution |

## Shared Infrastructure Layer

| Project | Stars | Replaces | Benefit |
|---------|-------|----------|---------|
| RAGFlow | 70K | Simple RAGEngine | Deep doc understanding, traceable citations |
| Graphiti | 5K | — | Real-time knowledge graph, entity tracking |
| n8n | 65K | — | Global automation engine, 400+ integrations |
| LangGraph | 15K | — | Graph-based Agent workflow orchestration |
| RAG-Anything | 1K | — | Multi-modal RAG (PDF + images + tables) |
| LightRAG | 12K | — | Graph RAG, multi-hop reasoning retrieval |

## Per-Subsidiary Mapping

### VP Marketing
- **ContentWriter**: firecrawl (70K) + crawl4ai (30K)
- **Designer**: ComfyUI (97K) + AUTOMATIC1111 (159K) + FLUX.2 (20K)
- **ShortVideo**: WanX 2.1 + moviepy (13K)
- **VoiceActor**: CosyVoice v3 (21K) + fish-speech S2 (18K)

### VP Operations
- **CRM**: n8n (65K) — automation hub
- **CustomerService**: LibreChat (25K) + openai-agents-python (19K)
- **Education**: STORM (22K) — deep research → course outline
- **Ecommerce**: browser-use (50K) — auto-listing, price monitoring

### VP Technology
- **Developer**: OpenHands (45K) + Miyabi (new)
- **Ops**: Ollama (120K) — local LLM, cost reduction
- **Security**: NeMo-Guardrails (5K)
- **AutoDream**: EvoAgentX (new) — auto workflow evolution

### VP Strategy
- **Research**: gpt-researcher (18K) + STORM (22K) + firecrawl (70K)
- **GlobalMarketing**: ByteDance Seed-X translation
- **BD**: browser-use (50K) — LinkedIn/Xiaohongshu outreach

## 72-Hour Action Plan

1. `pip install gpt-researcher firecrawl-py browser-use` → 3 P1 projects, half-day
2. CosyVoice Docker deploy (M1 Mac compatible) → VoiceActor activation
3. Integrate GPT-Researcher into Research Worker → qualitative leap for all downstream workers
