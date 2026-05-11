# v2.5 Upgrade Pipeline Reference

> GAP分析 → 并行实现 → 验证 → 提交 的系统升级流水线

## Pattern: Three Commit Upgrade Cycle

Session learnings from molin-os-v2-upgrade-map.html and molin-os-content-feishu-upgrade.html implementation.

### Commit 1: Architecture Foundation (6 GAPs)
```
2d467aa — GAP-01~06 补强
├── molib/shared/memory_layer.py       (mem0 双层记忆)
├── molib/shared/observability.py      (Langfuse 追踪)
├── molib/shared/fault_tolerance.py    (Prefect 断点续跑)
├── molib/shared/llm/llm_router.py     (OpenRouter 免费模型路由)
└── molib/agencies/research/agency.py  (GPT-Researcher 注入)
```

### Commit 2: Content Layer + Feishu (6 capabilities)
```
cb8cde4 — 内容生产增强 + 飞书优化
├── molib/shared/publish/feishu_card_router.py  (5种卡片决策树)
├── molib/shared/content/reference_engine.py     (crawl4ai 对标写作)
├── molib/shared/tts/cosyvoice_tts.py            (声音克隆+方言)
├── molib/content/digital_human.py               (数字人口播)
└── molib/content/video_processor.py             (MoviePy胶水层)
```

### Commit 3: Service Activation + Tooling
```
4ca35cd — EnvLoader + video_generator v2.5 + lark-cli
├── molib/shared/env_loader.py                   (统一 .env 加载)
├── bots/video_generator.py                      (+moviepy_slideshow 后端)
└── lark-cli (npm global @larksuite/cli)         (25+命令)
```

## Key Decisions Made

### OpenRouter free models → NOT Ollama
User explicitly chose OpenRouter's `:free` suffix models instead of local Ollama. Four models rotate: mistral-small-3.1-24b, qwen3-8b, gemma-3-4b, llama-4-scout. All $0/1M tokens. Rate limits spread via rotation.

### MPT → too heavy for 8GB M2
MoneyPrinterTurbo (streamlit + redis + faster-whisper + litellm) was cloned but NOT started. Instead: moviepy_slideshow backend (zero dep, ffmpeg-only) fills the local video generation gap.

### ComfyUI → Comfy Cloud
Hardware check (scripts/hardware_check.py) confirmed: M2 8GB below 16GB minimum for SDXL/Flux. Decision: use Comfy Cloud API ($0 free tier) or DashScope qwen-image-2.0-pro.

### lark-cli → installed, not authenticated
`npm install -g @larksuite/cli` succeeded. Command is `lark-cli` (not `lark` or `larksuite`). 25+ commands covering im/calendar/docs/base/sheets/task/approval/mail/drive. Needs `lark-cli auth init` with Feishu App ID/Secret to activate.

## API Key Status (2026-05-11)
| Key | Source | Status |
|-----|--------|--------|
| DASHSCOPE_API_KEY | config.yaml → .env | ✅ CosyVoice/HappyHorse/图像 |
| OPENROUTER_API_KEY | .env | ✅ 免费模型路由 |
| FIRECRAWL_API_KEY | .env | ✅ 竞品数据采集 |
| DEEPSEEK_API_KEY | .env | ✅ mem0 embedding |
| LANGFUSE_PUBLIC_KEY | .env | ✅ 全链路追踪 |
| FISH_AUDIO_API_KEY | — | ❌ 出海TTS (非必须) |
