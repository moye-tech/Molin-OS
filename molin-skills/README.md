# Molin Skills

Agent Skills for Molin-OS — 对标 [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) (30K⭐)。

Teach your AI agent to use Molin Markdown, Bases, JSON Canvas, MQL queries, and the molib CLI.

## Installation

### Via Claude Code Marketplace

```
/plugin marketplace add moye-tech/molin-skills
/plugin install molin-os@molin-skills
```

### Via npx skills

```bash
npx skills add git@github.com:moye-tech/molin-skills.git
```

Or via HTTPS:

```bash
npx skills add https://github.com/moye-tech/molin-skills
```

### Manually

Add to your Hermes skills directory:

```bash
git clone https://github.com/moye-tech/molin-skills.git ~/.hermes/skills/molin-skills
```

## Skills

| Skill | Description |
|-------|-------------|
| `molin-markdown` | Feishu-compatible Markdown with CEO style guidelines |
| `molin-cli` | Operate Molin-OS via the molib CLI |
| `molin-bases` | Create/query structured data tables (.mbase) |
| `molin-canvas` | Visual knowledge maps (.mcanvas) |
| `molin-query` | MQL structured knowledge queries |

## Usage

Once installed, your AI agent can:

- **Write in CEO style**: "写一份今日系统体检报告" → formatted with emoji sections, bullet lists, no markdown
- **Query knowledge**: "查询所有engineering类别的技能" → MQL query across 290+ skills
- **Create data views**: "创建一个活跃项目看板" → .mbase file with kanban view
- **Draw architecture**: "画一个墨麟OS架构图" → .mcanvas visual map
- **Operate system**: "检查系统健康状态" → `python -m molib health`

## Specification

These skills follow the [Agent Skills specification](https://github.com/agent-skills/specification), compatible with:
- Claude Code
- Codex CLI
- Hermes Agent
- OpenCode
- Any skills-compatible agent

## License

MIT
