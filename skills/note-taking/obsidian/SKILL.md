---
name: obsidian
description: Obsidian 知识管理与生态研究 — vault 读写、插件市场分析、设计模式吸收。当用户提到 Obsidian 的任何功能/插件/生态、或要做对标研究/模式吸收时加载。
version: 2.0.0
min_hermes_version: 0.13.0
tags: [knowledge-management, obsidian, notes, ecosystem]
category: knowledge
platforms: [linux, macos, windows]
metadata:
  hermes:
    molin_owner: 墨脑（知识管理）
---

# Obsidian — 知识管理与生态研究

触发条件: 用户提到 Obsidian 的任何功能、插件、生态、或要做对标研究/模式吸收。

重要原则:
- 完整功能，不做减法。生态研究要逐文件对照，不遗漏。
- 先摸清对方核心机制（注册中心/插件提交/版本管理），再提取可复用模式。
- 生态分析参考: [references/obsidian-ecosystem-analysis.md](references/obsidian-ecosystem-analysis.md) — 含 2750 插件生态全景、AI 插件分类、墨麟OS 六项吸收清单。

## Vault 操作

**Location:** Set via `OBSIDIAN_VAULT_PATH` environment variable (e.g. in `~/.hermes/.env`).

If unset, defaults to `~/Documents/Obsidian Vault`.

Note: Vault paths may contain spaces - always quote them.

### Read a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat "$VAULT/Note Name.md"
```

### List notes

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# All notes
find "$VAULT" -name "*.md" -type f

# In a specific folder
ls "$VAULT/Subfolder/"
```

### Search

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# By filename
find "$VAULT" -name "*.md" -iname "*keyword*"

# By content
grep -rli "keyword" "$VAULT" --include="*.md"
```

### Create a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat > "$VAULT/New Note.md" << 'ENDNOTE'
# Title

Content here.
ENDNOTE
```

### Append to a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
echo "
New content here." >> "$VAULT/Existing Note.md"
```

### Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## MQL 查询 Obsidian 笔记

墨麟OS 的 MQL 引擎可直接查询 Obsidian Vault:

```bash
python -m molib query "FROM notes WHERE tags HAS_TAG 'project' SORT BY modified_at DESC LIMIT 10"
python -m molib query --search "关键词" --source notes
```
