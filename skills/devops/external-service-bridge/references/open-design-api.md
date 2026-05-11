# Open Design Daemon API Reference

Discovered 2026-05-11 from source code grepping `apps/daemon/src/server.ts`.

Base URL: `http://127.0.0.1:55888`

## Health & Version

| Endpoint | Method | Response |
|:--|:--|:--|
| `/api/health` | GET | `{"ok":true,"version":"0.6.0"}` |
| `/api/version` | GET | Version string |

## Skills

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/skills` | GET | List all 134 built-in skills |
| `/api/skills/:id` | GET | Single skill detail |
| `/api/skills/:id/example` | GET | Example prompt/output |
| `/api/skills/:id/assets/*` | GET | Skill assets |
| `/api/skills/install` | POST | Install community skill |
| `/api/skills/:id` | DELETE | Remove installed skill |

## Design Systems

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/design-systems` | GET | List 149 design systems |
| `/api/design-systems/:id` | GET | Single design system |
| `/api/design-systems/:id/preview` | GET | Preview image |
| `/api/design-systems/:id/showcase` | GET | Showcase page |
| `/api/design-systems/install` | POST | Install community DS |
| `/api/design-systems/:id` | DELETE | Remove installed DS |

## Projects (Core workflow: projects→conversations→messages)

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/projects` | GET | List projects |
| `/api/projects` | POST | Create project |
| `/api/projects/:id` | GET | Project detail |
| `/api/projects/:id` | DELETE | Delete project |
| `/api/projects/:id/events` | GET | SSE event stream |
| `/api/projects/:id/conversations` | GET/POST | List/Create conversations |
| `/api/projects/:id/conversations/:cid` | DELETE | Delete conversation |
| `/api/projects/:id/conversations/:cid/messages` | GET | List messages |
| `/api/projects/:id/conversations/:cid/messages/:mid` | PUT | Edit message |
| `/api/projects/:id/conversations/:cid/comments` | GET/POST | List/Add comments |
| `/api/projects/:id/tabs` | GET/PUT | Get/Set tabs |
| `/api/projects/:id/files` | GET | List project files |
| `/api/projects/:id/search` | GET | Search project |
| `/api/projects/:id/archive` | GET | Archive |
| `/api/projects/:id/raw/*` | GET/DELETE | Raw file access |

## Artifacts & Live Artifacts

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/artifacts/save` | POST | Save artifact |
| `/api/artifacts/lint` | POST | Lint artifact |
| `/api/live-artifacts` | GET | List live artifacts |
| `/api/live-artifacts/:id` | GET | Get live artifact |
| `/api/live-artifacts/:id/preview` | GET | Preview (localhost only) |
| `/api/live-artifacts/:id/refreshes` | GET | Refresh history |
| `/api/live-artifacts/:id/refresh` | POST | Trigger refresh |
| `/api/live-artifacts/:id` | DELETE | Delete |
| `/api/tools/live-artifacts/create` | POST | Create via tools API |
| `/api/tools/live-artifacts/list` | GET | List via tools API |
| `/api/tools/live-artifacts/update` | POST | Update via tools API |
| `/api/tools/live-artifacts/refresh` | POST | Refresh via tools API |

## Agent Detection

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/agents` | GET | List 16 detectable agents (Claude/Codex/OpenCode/Hermes...) |
| `/api/active` | POST | Set active agent session |
| `/api/active` | GET | Get active agent status |

## Templates & Prompt Templates

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/templates` | GET/POST | List/Create templates |
| `/api/templates/:id` | GET/DELETE | Get/Delete template |
| `/api/prompt-templates` | GET | List prompt templates |
| `/api/prompt-templates/:surface/:id` | GET | Get prompt template |

## Deploy

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/deploy/config` | GET/PUT | Deploy configuration |
| `/api/projects/:id/deployments` | GET | List deployments |
| `/api/projects/:id/deploy` | POST | Deploy project |
| `/api/projects/:id/deploy/preflight` | POST | Pre-deploy checks |

## MCP

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/mcp/install-info` | GET | MCP install guide |
| `/api/mcp/servers` | GET/PUT | List/Update MCP servers |
| `/api/mcp/oauth/start` | POST | Start OAuth flow |
| `/api/mcp/oauth/callback` | GET | OAuth callback |
| `/api/mcp/oauth/status` | GET | OAuth status |
| `/api/mcp/oauth/disconnect` | POST | Disconnect OAuth |

## Upload & Import

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/upload` | POST | Upload images (multipart, max 8) |
| `/api/import/folder` | POST | Import folder as project |

## Composio

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/connectors/composio/config` | GET/PUT | Composio connector config |

## Codex Pets

| Endpoint | Method | Description |
|:--|:--|:--|
| `/api/codex-pets` | GET | List codex pets |
| `/api/codex-pets/sync` | POST | Sync codex pets |
| `/api/codex-pets/:id/spritesheet` | GET | Get pet spritesheet |

## Integration Notes

- **No `/api/skills/run` endpoint exists.** Skills are used within the context of projects/conversations, not directly invoked via REST.
- **Bridge approach for Molin-OS:**
  1. Create a project via `POST /api/projects`
  2. Create a conversation via `POST /api/projects/:id/conversations`
  3. Messages in the conversation drive skill execution
  4. Artifacts are saved via `/api/artifacts/save` or `/api/tools/live-artifacts/create`
- **Live artifacts** are the primary output mechanism — they stream HTML previews
- **Agent auto-detection**: Hermes was detected as `available=True` (the only one)
