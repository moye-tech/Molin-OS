---
name: molin-markdown
description: Create and edit Molin Markdown — Feishu-compatible formatting with emoji section headers, bullet lists, and CEO style guidelines. Use when writing content for Feishu, Molin-OS reports, or any 墨麟 communication channel.
version: 1.0.0
min_hermes_version: 0.13.0
tags: [molin-os, markdown, feishu, writing, ceo-style]
category: writing
---

# Molin Markdown Skill

Create and edit content in Molin Flavored Markdown — the standard format for all 墨麟OS communication.

## CEO Style Guidelines

All 飞书 output must follow these rules:

1. **Pure text only** — no bold, no italics, no inline code
2. **Emoji section headers** — use emoji + text (not `##` or `**`)
3. **Bullet lists** — use `•` for items, not `-` or `*`
4. **No markdown titles** — never use `#`, `##`, `###` in Feishu output
5. **No tables** — describe data with lists
6. **No code blocks** — describe code with natural language
7. **No links** — describe where to find things in words

### Correct ✅
```
🔍 研究发现

• AI Agent 市场在 2026 Q2 增长 45%
• 三个主要趋势：多模态、自主决策、成本下降
• 推荐关注 OpenRouter 和 DeepSeek 生态

📊 数据汇总

• 总技能数：290
• 活跃 Worker：22
• Cron 作业：8
```

### Wrong ❌
```
## 研究发现
**AI Agent** 市场增长 `45%`...
| 指标 | 数值 |
```

## Section Templates

### Reports
```
📋 标题

• 要点1
• 要点2

📊 数据

• 指标: 数值
• 指标: 数值

🔜 下一步

• 行动1
• 行动2
```

### Cron Output
```
🕐 执行时间: YYYY-MM-DD HH:mm

📋 任务名称

• 状态: ✅ 完成 / ⚠️ 部分完成 / ❌ 失败
• 说明: ...
• 产出: ...

📎 详情
（如有需要，列出关键数据或发现）
```

### System Status
```
🏥 系统体检

• 模块名称: ✅/⚠️/❌
• 模块名称: ✅/⚠️/❌

📊 概览

• 通过: N 项
• 提示: N 项
• 失败: N 项
```

## Content Types

All Molin content output uses these emoji section prefixes:

| Context | Emoji | Usage |
|---------|-------|-------|
| 报告标题 | 📋 | Report/summary title |
| 研究发现 | 🔍 | Research findings |
| 数据分析 | 📊 | Data/statistics |
| 代码/技术 | ⚡ | Technical content |
| 下一步 | 🔜 | Next steps |
| 系统状态 | 🏥 | Health check |
| 警告/注意 | ⚠️ | Warnings |
| 完成 | ✅ | Success/completion |
| 失败 | ❌ | Failure/error |
| 信息 | ℹ️ | Neutral info |
| 时间 | 🕐 | Timestamps |
| 链接/参考 | 🔗 | References |
| 创意 | 🎨 | Creative content |
| 财务 | 💰 | Financial data |
| 安全 | 🔒 | Security content |
| 通知 | 📢 | Announcements |
| 待办 | 📝 | Task lists |

## Workflow

1. **Determine context** — what type of content are you creating?
2. **Choose emoji sections** — pick 2-5 emoji prefixes from the table above
3. **Write bullet lists** — use `• ` for every item
4. **Review against CEO rules** — scan for any markdown formatting
5. **Strip all markdown** — remove `#`, `**`, `*`, `|`, `` ` ``, `[]()`
6. **Verify** — read aloud to ensure natural flow
