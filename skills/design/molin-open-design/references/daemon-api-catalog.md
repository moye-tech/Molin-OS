# Open Design Daemon API Catalog

> v0.6.0 · `http://127.0.0.1:55888` · Discovered 2026-05-11

## Health & Meta

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/health` | `{"ok":true,"version":"0.6.0"}` |
| GET | `/api/version` | Version info |

## Skills (134 total)

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/skills` | List all skills (id, name, description, triggers, mode, surface, craftRequires, previewType, examplePrompt, body) |
| GET | `/api/skills/:id` | Single skill with full body + system prompt |
| GET | `/api/skills/:id/example` | Skill example |
| GET | `/api/skills/:id/assets/*` | Skill asset files |
| POST | `/api/skills/install` | Install community skill |
| DELETE | `/api/skills/:id` | Remove skill |

## Design Systems (149 total)

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/design-systems` | List all (id + metadata, no body) |
| GET | `/api/design-systems/:id` | Full DESIGN.md body (e.g., apple: 17,764 chars; stripe: 20,552 chars) |
| GET | `/api/design-systems/:id/preview` | Preview |
| GET | `/api/design-systems/:id/showcase` | Showcase |
| POST | `/api/design-systems/install` | Install community DS |
| DELETE | `/api/design-systems/:id` | Remove |

## Projects

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/projects` | List projects |
| POST | `/api/projects` | Create project: `{id, name, skillId?, designSystemId?, pendingPrompt?, metadata?}` |
| GET | `/api/projects/:id` | Get project |
| DELETE | `/api/projects/:id` | Delete |
| GET | `/api/projects/:id/files` | List files |
| GET | `/api/projects/:id/search` | Search files |
| GET | `/api/projects/:id/raw/*` | Read raw file |
| POST | `/api/projects/:id/export/pdf` | Export PDF |

## Conversations

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/projects/:id/conversations` | List conversations |
| POST | `/api/projects/:id/conversations` | Create conversation |
| DELETE | `/api/projects/:id/conversations/:cid` | Delete |
| GET | `/api/projects/:id/conversations/:cid/messages` | Messages |
| PUT | `/api/projects/:id/conversations/:cid/messages/:mid` | Update message |

## Artifacts (primary integration surface)

| Method | Path | Description |
|:--|:--|:--|
| POST | `/api/artifacts/save` | Save artifact: `{identifier?, title?, html}` → `{path, url, lint}` |
| POST | `/api/artifacts/lint` | Lint HTML without saving: `{html}` → `{findings, agentMessage}` |
| GET | `/api/live-artifacts` | List (requires `?projectId=`) |
| GET | `/api/live-artifacts/:id` | Get artifact |
| GET | `/api/live-artifacts/:id/preview` | Preview URL (local daemon only) |
| POST | `/api/live-artifacts/:id/refresh` | Refresh |

## Agents

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/agents` | List 16 detected agents (claude, codex, devin, gemini, opencode, hermes, etc.) |
| GET | `/api/active` | Current active agent session |
| POST | `/api/active` | Set active agent |

## Templates & Prompt Templates

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/templates` | List templates |
| GET | `/api/templates/:id` | Get template |
| POST | `/api/templates` | Create template |
| DELETE | `/api/templates/:id` | Delete |
| GET | `/api/prompt-templates` | List prompt templates |
| GET | `/api/prompt-templates/:surface/:id` | Get prompt template |

## Deploy

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/deploy/config` | Deploy config |
| PUT | `/api/deploy/config` | Update |
| POST | `/api/projects/:id/deploy` | Deploy project |
| POST | `/api/projects/:id/deploy/preflight` | Pre-flight check |

## MCP & Connectors

| Method | Path | Description |
|:--|:--|:--|
| GET | `/api/mcp/install-info` | MCP install info |
| GET | `/api/mcp/servers` | List servers |
| PUT | `/api/mcp/servers` | Update |
| POST | `/api/mcp/oauth/start` | OAuth start |
| GET | `/api/mcp/oauth/callback` | OAuth callback |
| GET | `/api/mcp/oauth/status` | OAuth status |
| GET | `/api/connectors/composio/config` | Composio config |

## Key Integration Pattern

The daemon is **passive** — it stores skills/design-systems/artifacts. The agent generates content. Integration flow:

```
1. GET /api/skills/:id          → skill definition (body + system prompt)
2. GET /api/design-systems/:id  → DESIGN.md tokens (color, font, spacing)
3. Agent generates HTML         ← (LLM, following skill + DS specs)
4. POST /api/artifacts/save     → {html} → preview URL + lint results
```
