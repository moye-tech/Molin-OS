---
name: molin-mql
description: MQL (Molin Query Language) 查询引擎 — 对标 Obsidian Dataview，为墨麟OS提供结构化知识查询。支持 FROM/WHERE/SORT/GROUP BY/FLATTEN/LIMIT 语法，可从 skills/notes/memory/experiences 多种数据源查询。
version: 1.0.0
min_hermes_version: 0.13.0
tags: [molin-os, query, knowledge, dataview, search]
category: infrastructure
---

# MQL — Molin Query Language

墨麟OS 结构化知识查询引擎。对标 Obsidian Dataview DQL。

## 语法

```mql
FROM skills|notes|memory|experiences|hermes_sessions|all
WHERE field operator value [AND|OR condition ...]
SORT BY field [ASC|DESC]
GROUP BY field
FLATTEN field
LIMIT n
```

## 操作符

| 类型 | 操作符 | 说明 |
|------|--------|------|
| 比较 | = != > < >= <= | 值比较 |
| 包含 | CONTAINS | 字符串包含 |
| 列表 | IN (a, b, c) | 值在列表中 |
| 标签 | HAS_TAG | 标签匹配 |
| 模式 | MATCHES | 正则匹配 |
| 前缀 | STARTS_WITH | 以...开头 |
| 后缀 | ENDS_WITH | 以...结尾 |

## 示例

```bash
# 查询所有 ML 相关技能
python -m molib query "FROM skills WHERE category = 'mlops' SORT BY name ASC LIMIT 10"

# 全文搜索
python -m molib query --search "AI agent"

# 精确查找
python -m molib query --lookup name obsidian --source skills

# 多数据源查询
python -m molib query "FROM skills, notes WHERE tags HAS_TAG 'project'"

# 列出数据源
python -m molib query --sources

# 重建索引
python -m molib query --index --rebuild
```

## Python API

```python
from molib.shared.query import query, search, lookup

# 结构化查询
result = query("FROM skills WHERE category = 'engineering' LIMIT 5")

# 全文搜索
result = search("obsidian", source="skills")

# 精确查找
result = lookup("name", "obsidian", source="skills")

# 遍历结果
for entry in result:
    print(f"[{entry.source}] {entry.name} v{entry.version}")
    print(f"  {entry.description}")
```

## 索引数据源

- **skills**: ~/.hermes/skills/*/SKILL.md (290+ 技能)
- **notes**: Obsidian Vault 中的 Markdown 笔记
- **memory**: Hermes 持久记忆 (memory.md, user.md)
- **experiences**: ExperienceVault 经验金库
- **hermes_sessions**: 历史会话记录

## 对标参考

- Obsidian Dataview: https://github.com/blacksmithgu/obsidian-dataview
- Dataview DQL: FROM/WHERE/SORT/GROUP BY/FLATTEN/LIMIT
