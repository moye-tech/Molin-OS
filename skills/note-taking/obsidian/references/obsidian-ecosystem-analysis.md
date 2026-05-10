# Obsidian 生态分析（2026-05 研究）

## obsidianmd/obsidian-releases — 插件注册中心

GitHub: https://github.com/obsidianmd/obsidian-releases (17.6k⭐)

核心机制:
- community-plugins.json: 2750 个插件、2165 位作者，单文件即整个市场
- PR 提交制: fork → 添加条目 → PR → 审核 → 合并即上线
- 自动统计: GitHub Actions 每 8h 更新 stats
- 版本管理: 每个插件独立 repo 的 manifest.json (version + minAppVersion)
- 五步拉取: 读索引 → 搜索匹配 → 拉 manifest+README → 版本兼容检查 → GitHub Release 下载 main.js
- 不托管代码，只维护索引，作者保留 100% 控制权

## 插件生态规模

| 类别 | 数量 |
|------|------|
| 总插件 | 2750 |
| AI/LLM 插件 | 131 |
| 版本/同步 | 224 |
| 自动化/工作流 | 56 |
| 数据查询 | 101 |
| 发布/建站 | 111 |

## 关键 AI 插件

- Smart Connections (5k⭐): 嵌入语义链接 + AI 对话 (brianpetro/obsidian-smart-connections)
- Copilot (4k⭐): AI 写作副驾驶 (logancyang/obsidian-copilot)
- SystemSculpt AI: AI 笔记+任务管理
- Ayanite: AI 知识副驾驶 (Claude 集成)
- Smart Second Brain: 隐私优先，Ollama/OpenAI
- MCP Tools: Claude Desktop ↔ vault 安全连接
- Dataview (8.9k⭐): 结构化查询引擎

## kepano/obsidian-skills (30k⭐)

GitHub: https://github.com/kepano/obsidian-skills

Agent Skills 规范的最佳实践:
- obsidian-markdown: wikilinks、embeds、callouts、properties
- obsidian-bases: .base 文件、filter、formula、views
- json-canvas: .canvas 文件、nodes、edges
- obsidian-cli: 命令行工具

## 对标墨麟OS的六项吸收

| # | 模块 | 对标 | 状态 |
|---|------|------|------|
| A | 技能注册中心 | obsidian-releases | P1 待做 |
| B | molin-skills 技能包 | kepano/obsidian-skills | P1 待做 |
| C | MQL 查询引擎 | Dataview DQL | ✅ 已完成 |
| D | 墨麟画布 | JSON Canvas | P2 待做 |
| E | 本地 REST API | Local REST API 插件 | P2 待做 |
| F | Manifest 标准化 | manifest.json | ✅ 已完成 |

## 墨麟OS已实现的对标模块

### MQL (Molin Query Language)
- 位置: molib/shared/query/
- CLI: python -m molib query "FROM skills WHERE ..."
- 支持: FROM/WHERE/SORT/GROUP BY/FLATTEN/LIMIT
- 12种操作符, 5大数据源

### Manifest 标准化
- 位置: molib/core/tools/manifest_validator.py
- CLI: python -m molib manifest validate/fix/upgrade
- 288/329 技能已标准化
