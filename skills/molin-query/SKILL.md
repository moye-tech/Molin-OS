---
name: molin-query
description: Query Molin-OS knowledge using MQL (Molin Query Language). Use when searching skills, notes, experiences, memory, or sessions with structured queries.
version: 1.0.0
min_hermes_version: 0.13.0
dependencies: [molin-cli]
tags: [molin-os, query, search, mql, knowledge]
category: infrastructure
---

# Molin Query Skill (MQL)

Query Molin-OS knowledge with MQL — 对标 Obsidian Dataview DQL。

## Quick Reference

```mql
FROM source [, source...]
WHERE field operator value [AND|OR condition...]
SORT BY field [ASC|DESC]
GROUP BY field
FLATTEN field
LIMIT number
```

## Data Sources

| Source | Content | Location |
|--------|---------|----------|
| skills | 290+技能 | ~/.hermes/skills/*/SKILL.md |
| notes | Obsidian笔记 | ~/Documents/Obsidian Vault/ |
| memory | 持久记忆 | ~/.hermes/memory.md, user.md |
| experiences | 经验金库 | ExperienceVault |
| hermes_sessions | 会话记录 | ~/.hermes/sessions/*.jsonl |
| all | 全部数据源 | (combined) |

## Operators

| Type | Operators | Example |
|------|-----------|---------|
| 比较 | = != > < >= <= | `quality_score > 80` |
| 包含 | CONTAINS | `description CONTAINS 'AI'` |
| 列表 | IN (a, b, c) | `tags IN ('ml', 'ai')` |
| 标签 | HAS_TAG | `tags HAS_TAG 'urgent'` |
| 正则 | MATCHES | `name MATCHES '^molin-'` |
| 前缀 | STARTS_WITH | `name STARTS_WITH 'agent-'` |
| 后缀 | ENDS_WITH | `name ENDS_WITH '-skill'` |

## Common Queries

### Skills
```bash
# All skills in a category
python -m molib query "FROM skills WHERE category = 'engineering' SORT BY name ASC"

# Skills with specific tag
python -m molib query "FROM skills WHERE tags HAS_TAG 'mlops'"

# Search skill descriptions
python -m molib query "FROM skills WHERE description CONTAINS 'AI agent'"

# Newest skills
python -m molib query "FROM skills SORT BY modified_at DESC LIMIT 10"

# Skills needing updates
python -m molib query "FROM skills WHERE version < '1.0.0'"
```

### Notes
```bash
# Notes with specific tag
python -m molib query "FROM notes WHERE tags HAS_TAG 'project' SORT BY modified_at DESC"

# Notes mentioning AI
python -m molib query "FROM notes WHERE description CONTAINS 'artificial intelligence'"

# Recently modified
python -m molib query "FROM notes SORT BY modified_at DESC LIMIT 20"

# Notes with wikilinks to specific page
python -m molib query "FROM notes WHERE description CONTAINS 'Molin-OS'"
```

### Memory
```bash
# Search persistent memory
python -m molib query "FROM memory WHERE description CONTAINS 'preference'"
```

### Cross-source
```bash
# Everything about AI
python -m molib query "FROM all WHERE description CONTAINS 'AI' OR tags CONTAINS 'ai' LIMIT 50"

# Combined engineering + tools
python -m molib query "FROM skills, notes WHERE category = 'engineering' SORT BY name ASC"
```

## Shortcuts

```bash
# Full-text search (simplest)
python -m molib query --search "AI agent"

# Exact lookup
python -m molib query --lookup name obsidian --source skills

# List available sources
python -m molib query --sources

# Rebuild index
python -m molib query --index --rebuild
```

## Python API

```python
from molib.shared.query import query, search, lookup

# Structured query
result = query("FROM skills WHERE category = 'engineering' SORT BY name ASC LIMIT 5")
for entry in result:
    print(f"{entry.name} v{entry.version}")

# Full-text search
result = search("AI agent", source="skills", limit=10)

# Exact lookup
result = lookup("name", "obsidian", source="skills")

# Get stats
print(f"Found {result.stats.entries_matched} of {result.stats.entries_scanned}")
print(f"Took {result.stats.time_ms:.0f}ms")

# Convert to dicts
data = result.to_dicts()

# Table view
print(result.table_view())
```

## Indexing

The indexer automatically indexes data sources on first query. To force rebuild:

```bash
python -m molib query --index --rebuild
```

Indexed fields per source:
- **skills**: name, description, tags, category, version, modified_at
- **notes**: title, tags, wikilinks, word_count, modified_at
- **memory**: content, tags
- **experiences**: worker_id, task_summary, approach, quality_score

## Query Patterns

### Find What's Broken
```mql
FROM skills WHERE version < '1.0.0' OR min_hermes_version > '0.13.0'
```

### Find What's Popular
```mql
FROM skills WHERE tags CONTAINS 'engineering' SORT BY modified_at DESC LIMIT 10
```

### Group Analysis
```mql
FROM skills GROUP BY category
```

### Dependency Check
```mql
FROM skills WHERE name = 'molin-cli' FLATTEN dependencies
```

## Pitfalls

- String values in WHERE must be quoted: `WHERE name = 'skill-name'`
- CONTAINS on tags checks within the tag array
- HAS_TAG checks exact tag match
- GROUP BY returns one representative per group (with _group_count metadata)
- FLATTEN duplicates entries for each array item
- Index rebuild required after adding/removing data sources
