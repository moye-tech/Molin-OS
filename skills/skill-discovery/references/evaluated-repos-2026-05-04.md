# 25-Project Evaluation Session — 2026-05-03/04

User: 尹建业 | Channel: Feishu DM | Skills final: 219

## Evaluated Projects (Tier 1 — Direct Integration)

| Project | Converted To | Skills |
|---------|-------------|--------|
| mvanhorn/last30days-skill | `last30days` | 1 |
| forrestchang/andrej-karpathy-skills | `karpathy-coding-principles` | 1 |
| shanraisshan/claude-code-best-practice | `agentic-engineering` | 1 |
| phuryn/pm-skills | 49 `pm-*` skills | 49 |
| msitarzewski/agency-agents | 23 `agent-*` personas | 23 |
| sickn33/antigravity-awesome-skills (36K stars) | 39 `ag-*` skills | 39 |
| VoltAgent/awesome-openclaw-skills (47K stars) | Reference catalog | 1 |

## Evaluated Projects (Tier 2 — Reference/Learning)

| Project | Derived Skills |
|---------|---------------|
| ruvnet/ruflo (37K stars) | `swarm-orchestration`, `self-learning-loop` |
| Yeachan-Heo/oh-my-claudecode | Orchestration patterns (studied only) |
| Yeachan-Heo/oh-my-codex | Workflow patterns (studied only) |
| moye-tech/GenericAgent | Self-evolving architecture (studied only) |
| KimYx0207/CN Guide | Chinese reference (130K words) |

## Special — Molin AI System v6.7 (ZIP upload)

| Asset Extracted | Created Skills |
|----------------|---------------|
| CEO system prompt (148 lines) | `molin-ceo-persona` |
| IP/Xiaohongshu prompt (47 lines) | `xiaohongshu-content-engine` (268 lines) |
| Shop sales framework (65 lines) | (merged into xianyu-automation) |
| Xianyu listener (220 lines) | `xianyu-automation` (348 lines) |
| 12 hermes-agent-skills/ | 12 `molin/*` subsidiary skills |
| 20 subsidiaries.toml | (reference only, trigger-based routing) |

## Skipped/Evaluated-Only (13 projects)
openclaw/openclaw, claw-code, ClawTeam, paperclip (404), supermemory, claude-mem ×2, lightpanda, xiaohongshu-cli, OpenCLI, Deep-Live-Cam, claude-code-best, Agent-Reach

## Key Techniques Learned
1. Large repo clone: git clone --depth 1 --filter=blob:none --sparse → sparse-checkout → GitHub API tree → raw fetch
2. Batch import: execute_code + curl loop, 8-10/round, retry failures
3. Triple-timeout rule: 3x delegate_task timeout → direct tools
4. Molin extraction pattern: read agency/prompts/*.txt → convert to Hermes SKILL.md
5. execute_code f-string escaping: avoid backslashes in f-string shell commands

## Deliverables Produced
- Full capability whitepaper (18.8KB, 12 chapters)
- 3 Xianyu portfolio samples (business plan, resume, AI art)
- 6 Xianyu listing templates
- 4-path monetization strategy with 30-day execution calendar
