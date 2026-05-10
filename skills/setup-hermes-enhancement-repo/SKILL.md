---
name: setup-hermes-enhancement-repo
description: Handle GitHub repos that are enhancements/layers on top of Hermes Agent
  itself — not standalone services. Distinguish between deployable projects and Hermes-integration
  repos, then set them up properly without redundant standalone deployment.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - Hermes-Agent
    - GitHub
    - Setup
    - Integration
    - Environment
    related_skills:
    - github-auth
    - github-repo-management
    molin_owner: CEO
min_hermes_version: 0.13.0
---

# Setup Hermes Enhancement Repo

When a user says "deploy this repo" or "set this up", first determine whether it's a **standalone service** or a **Hermes Agent enhancement layer**.

## Detection

Before running any setup scripts, inspect the repo structure and README.

**Standalone Project** signs:
- Has a `Dockerfile` / `docker-compose.yml`
- Has a web framework entrypoint (`app.py`, `main.go`, `package.json` start script)
- Describes itself as a "service", "API", "web app"
- Has its own database or external service dependencies

**Hermes Enhancement Repo** signs:
- Contains a Python package (e.g. `molin/`) that references Hermes Agent
- Has a `skills/` directory with `SKILL.md` files
- Has `config/` YAML files defining company/agent structure
- README says "built on Hermes Agent" or "Hermes OS"
- Describes itself as an "OS" or "layer" on top of Hermes
- **User explicitly says**: "这个仓库就是你最终状态", "不要分开部署", "这就是我备份的你的完整形态"

## Setup Flow for Enhancement Repos

**Do NOT** run the repo's `setup.sh` as if it's a standalone project.

### Step 1: Clone the repo
```bash
git clone <repo-url> ~/<repo-name>
```

### Step 2: Install Python package into Hermes Agent's existing venv
Do NOT create a separate venv. Use Hermes's environment:
```bash
cd ~/<repo-name>
uv pip install -e . --python ~/.hermes/hermes-agent/venv/bin/python
```

### Step 3: Verify
```bash
~/.hermes/hermes-agent/venv/bin/python -c "import <pkg>; print('<pkg>', <pkg>.__version__)"
```

### Step 4: Sync skills from repo to Hermes

Compare the repo's `skills/` with `~/.hermes/skills/`. Only copy missing skills:

```bash
# Find repo skills that Hermes doesn't have (practical approach)
for d in ~/hermes-os/skills/*/; do
  domain=$(basename "$d")
  mkdir -p ~/.hermes/skills/"$domain"
  for skill_dir in "$d"*/; do
    skill_name=$(basename "$skill_dir")
    if [ ! -d ~/.hermes/skills/"$domain"/"$skill_name" ]; then
      cp -r "$skill_dir" ~/.hermes/skills/"$domain"/
    fi
  done
done
```

Critical skills to prioritize:
- Meta skills (`meta/`) — CEO persona, company structure, goals, governance
- Domain skills (`business/`, `content/`, `engineering/`, `growth/`)

### Step 5: Load config definitions

Read `config/*.yaml` files — they are AI-readable company/organization definitions, not deployment configs. Load them into context so the AI understands the company structure, publishing channels, and governance rules.

### Step 6: Save integrated state to memory

Save to `memory(action='add', target='user')` with:
- Integration status (what was synced)
- Repo path
- Key skills loaded
- Company/system definition summary

## What NOT to do
- ❌ Do NOT create a separate Python venv for the repo
- ❌ Do NOT add separate cron/systemd entries (use Hermes cronjob tool)
- ❌ Do NOT run `pip install -r requirements.txt` separately
- ❌ Do NOT run setup scripts that modify shell config (bashrc, PATH)
- ❌ Do NOT think "deploy" — think "integrate"

## Architecture Summary

Explain to the user:

> This repo is an enhancement layer on Hermes Agent. Unlike a standalone service:
> - It uses Hermes's existing AI model (no separate API keys)
> - Its Python package goes into Hermes's venv (no separate env)
> - Its skills/config/docs are referenced by Hermes
> - Orchestration happens through Hermes itself, not through its own CLI

## Common Pitfalls
1. Running setup.sh without inspecting — enhancement repos include setup scripts for non-Hermes environments
2. The repo's CLI (molin, etc.) is often a thin placeholder; actual execution happens through Hermes Agent
3. Standalone venvs created by setup.sh are harmless but wasteful; ask user before deleting
4. **Treating config/ as deploy config** — `config/` YAML files are AI-readable *definitions* (company structure, channels, governance), not runtime configs. Don't try to "deploy" them, read them into context.
5. **Forgetting to update memory** — After integration, the full system state (what was synced, key skills, company structure) must be saved to memory so future sessions don't start from scratch.