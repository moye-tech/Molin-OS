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

**Location:** Set via `OBSIDIAN_VAULT_PATH` in `~/.hermes/.env`.

Default: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` (iCloud multi-device sync, no subscription needed).

**Sync script:** `~/Molin-OS/scripts/obsidian_sync.py` — copies Molin-OS reports into the vault with Obsidian frontmatter.

Vault structure: `00-Inbox/`, `10-Daily/`, `20-Reports/`, `30-Knowledge/`, `40-Projects/`, `50-Archive/`, `99-Templates/`.

Note: paths contain spaces — always quote them in shell commands.

**Multi-device sync:** This vault lives in iCloud — files written here appear on all devices with Obsidian + same iCloud account. No Obsidian Sync subscription needed.

**Vault structure:**
```
00-Inbox/      — 临时收集、待整理
10-Daily/      — 日报/早报/晚报 (墨研竞情自动)
20-Reports/    — 周报/月报/专项报告
30-Knowledge/  — 知识卡片、技术笔记
40-Projects/   — 项目追踪、计划
50-Archive/    — 历史归档
99-Templates/  — 笔记模板
```

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

## Sync Reports

Sync Molin-OS reports to Obsidian vault:

```bash
# 全部同步
python3 ~/Molin-OS/scripts/obsidian_sync.py

# 仅 GitHub 雷达
python3 ~/Molin-OS/scripts/obsidian_sync.py --type=github-radar

# 预览模式
python3 ~/Molin-OS/scripts/obsidian_sync.py --dry-run
```

Source directories:
- `~/.hermes/daily_reports/` → Vault `10-Daily/`
- `~/Molin-OS/output/reports/` → Vault `20-Reports/`

## iCloud Multi-Device Sync

The vault lives in `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` — Apple's standard Obsidian iCloud sync path. All Macs signed into the same Apple ID automatically sync. No Obsidian Sync subscription needed.

**On another Mac:**
```
1. Install Obsidian → Open
2. Click "Open folder as vault"
3. Select: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/
4. All notes appear — iCloud syncs automatically in background
```

**Note:** The Obsidian app must be installed in `/Applications/Obsidian.app`. If not installed, download from https://obsidian.md/download and drag to /Applications (or `brew install --cask obsidian`).

## Feishu Doc Cross-Tenant Limitation

Feishu docs on a different tenant (e.g., `sparkedu.feishu.cn`) CANNOT be accessed via `feishu-cli doc export` even with correct App credentials — the API returns `code=1770032, msg=forBidden`. Workarounds:
1. User copy-pastes content directly into chat
2. User exports doc as Markdown from Feishu UI and shares
3. User grants the app cross-tenant access (requires tenant admin)

## MQL 查询 Obsidian 笔记

墨麟OS 的 MQL 引擎可直接查询 Obsidian Vault:

```bash
python -m molib query "FROM notes WHERE tags HAS_TAG 'project' SORT BY modified_at DESC LIMIT 10"
python -m molib query --search "关键词" --source notes
```
