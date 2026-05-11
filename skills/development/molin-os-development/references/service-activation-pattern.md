# Service Activation Pattern (v2.5 — 2026-05-11)

> Pattern extracted from 2026-05-11 sessions: how to handle GitHub projects that need local service startups on Mac M2.

## The "Code-Ready, Service-Pending" Pattern

When integrating a GitHub project that requires local GPU/Docker/service startup:

1. **Write the integration module NOW** — API endpoints, fallback chains, health checks
2. **Document the activation command** in the module's status property
3. **Tag as "code-ready, service-pending"** in commits
4. **Provide graceful degradation** — the system should work (in reduced mode) even without the service

## MPT (MoneyPrinterTurbo) Activation Checklist

```
# MPT is already cloned to fork_repos/MoneyPrinterTurbo
cd /Users/moye/Molin-OS/fork_repos/MoneyPrinterTurbo

# Check Python deps
pip install -r requirements.txt --proxy http://127.0.0.1:7890

# Start service (runs on localhost:8899 by default)
python main.py

# Verify
curl http://localhost:8899/health
```

**Status codes:**
- `200` — MPT running, video_generator.py can use it
- `000` — MPT not running, falls back to DashScope HappyHorse API
- `BACKENDS = ["happyhorse", "mpt"]` — MPT is tier 2 in video_generator.py. When MPT is up, it handles most requests.

## ComfyUI Hardware Determination

```
python3 ~/.hermes/skills/creative/comfyui/scripts/hardware_check.py
```

**Result for M2 8GB:** "M2 with 8.0 GB unified memory — below the 16 GB practical minimum.
SD1.5 may work; SDXL/Flux will swap or OOM. Recommend Comfy Cloud."

**Decision tree:**
- M2 16GB+ → Local ComfyUI (MPS backend)
- M2 8GB → Comfy Cloud API ($0 free tier)
- No GPU → Comfy Cloud or DashScope qwen-image-2.0-pro

**ComfyUI skill scripts** (at `~/.hermes/skills/creative/comfyui/scripts/`) support both local and cloud modes via `comfy-cli`.

## MuseTalk / LivePortrait / Linly-Talker

These require GPU (Docker or native CUDA/MPS). On Mac M2 8GB:

| Service | Port | Purpose | Feasibility |
|---------|------|---------|-------------|
| MuseTalk | 8898 | Lip-sync | ❌ Needs GPU, Docker recommended |
| LivePortrait | 8899 | Head motion | ❌ Needs GPU |
| Linly-Talker | 8900 | Live AI avatar | ❌ Needs full GPU pipeline |

All have API endpoints pre-configured in `molib/content/digital_human.py`.
When a GPU server becomes available, update the endpoints and the health checks will auto-detect.

## larksuite/cli Integration

```
# Install (Node.js v24.14.0 required)
npm install -g @larksuite/cli

# Verify
lark-cli --help  # 25+ commands: im/calendar/docs/base/sheets/task/approval/mail/drive

# Authentication (needs Feishu app credentials)
lark-cli config init --app-id <ID> --app-secret-stdin
lark-cli auth login
```

**Why use it:**
- Official Feishu/Lark CLI, MIT open source
- Agent-Native design: structured output for AI consumption
- 200+ commands covering 17 business domains
- Auto-syncs with Feishu API changes
- Alternative to custom `molib/infra/gateway/feishu_*.py` modules

## API Key Auto-Detection Pattern

When an API key exists in `~/.hermes/config.yaml` but NOT in `~/.hermes/.env`:

```bash
# Extract from config.yaml
DASHSCOPE_KEY=$(grep "api_key:" ~/.hermes/config.yaml | head -1 | sed 's/.*api_key: //' | tr -d ' ')

# Add to .env if missing
if ! grep -q "^DASHSCOPE_API_KEY=" ~/.hermes/.env; then
    echo "DASHSCOPE_API_KEY=$DASHSCOPE_KEY" >> ~/.hermes/.env
fi
```

This bridges the gap between Hermes Agent's config.yaml (where provider API keys live) and Python modules that expect `os.environ.get("KEY")`.

## Health Check Template

After any service activation, run this check pattern:

```python
import subprocess
services = {
    'MPT(8899)': ('视频批量生产', '/health'),
    'ComfyUI(8188)': ('本地生图', '/system_stats'),
    'MuseTalk(8898)': ('唇形同步', '/health'),
}
for svc, (purpose, endpoint) in services.items():
    port = svc.split('(')[1].rstrip(')')
    r = subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}',
                      f'http://localhost:{port}{endpoint}'],
                     capture_output=True, text=True, timeout=2)
    ok = r.stdout.strip() == '200'
    print(f'  {"✅" if ok else "⚠️"} {svc}: {"运行中" if ok else "未启动"} ({purpose})')
```
