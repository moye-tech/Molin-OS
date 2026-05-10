# 对标 Obsidian Dataview

## 设计参考

MQL 的设计直接对标 [Obsidian Dataview](https://github.com/blacksmithgu/obsidian-dataview) (8.9k⭐)，
吸收其核心查询范式：

| 特性 | Dataview DQL | MQL |
|------|-------------|-----|
| 数据源 | vault notes | skills/notes/memory/experiences/sessions |
| FROM | FROM "folder" | FROM skills, notes |
| WHERE | WHERE field = value | WHERE field = 'value' |
| SORT | SORT field ASC | SORT BY field ASC |
| GROUP BY | GROUP BY field | GROUP BY field |
| FLATTEN | FLATTEN field | FLATTEN field |
| LIMIT | LIMIT n | LIMIT n |
| 标签 | FROM #tag | WHERE tags HAS_TAG 'tag' |
| 正则 | WHERE regexmatch(...) | WHERE field MATCHES 'pattern' |
| 包含 | WHERE contains(...) | WHERE field CONTAINS 'text' |

## 关键差异

1. **多数据源**: Dataview 只能查询 Obsidian vault，MQL 可跨 5 种数据源联合查询
2. **索引机制**: Dataview 自动索引 vault metadata，MQL 延迟索引（首次查询时构建）
3. **操作符**: MQL 增加了 HAS_TAG、STARTS_WITH、ENDS_WITH 等专用操作符
4. **Python API**: Dataview 提供 JS API，MQL 提供 Python API + CLI

## Ecosystem Context

Obsidian 插件生态规模：2,750+ 插件，2,165 位作者，131 个 AI 专用插件。
注册中心 `obsidianmd/obsidian-releases` (17.6k⭐) 使用 PR-based JSON 目录模式。
Agent Skills 参考 `kepano/obsidian-skills` (30k⭐) 的原子化技能设计。
