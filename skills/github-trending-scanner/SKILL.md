---
name: github-trending-scanner
description: "Daily GitHub trending scanner — discovers high-star projects, analyzes against Molin-OS architecture, and recommends integration paths."
version: 1.0.0
author: 墨麟OS CEO
license: MIT
tags:
- research
- github
- trending
- molin-os
- architecture
- daily-scan
- competitive-intelligence
platforms: [macos, linux]
metadata:
  hermes:
    molin_owner: 墨研竞情
    category: research
    tags:
      - github-trending
      - daily-scan
      - architecture-match
      - technology-radar
      - integration-intelligence
    related_skills: [arxiv, blogwatcher, llm-wiki]
---

# GitHub Trending Scanner

Daily automated scan of GitHub trending repositories with Molin-OS architecture
matching, integration assessment, and technology radar updates.

## What This Skill Does

1. **Discover**: Scan GitHub Trending (all languages + weekly), awesome-ai-agents,
   paperswithcode trending, and HN/Reddit AI discussions
2. **Analyze**: For each discovered project, assess against Molin-OS v2.5
   architecture layers (CEO/SmartDispatcher/Worker/Shared/Content/Feishu)
3. **Score**: Match score (0-10) based on architecture fit, integration cost,
   and capability gap
4. **Recommend**: Specific integration path, which Worker benefits, pip/npm
   install commands, and expected impact
5. **Deliver**: Formatted Feishu message with top 5-10 discoveries

## Architecture Match Framework

Each discovered project is scored against Molin-OS layers:

| Layer | What to Match | Weight |
|-------|--------------|--------|
| CEO层 (记忆+记忆召回) | mem0替代/增强, 知识图谱, 用户画像 | 0.15 |
| SmartDispatcher (路由) | 任务路由优化, 意图识别, 多Agent编排 | 0.10 |
| Worker执行层 (20子公司) | 对应Worker能力增强, 新工具集成 | 0.30 |
| 共享基础层 (LLM/存储/事件) | LLM路由, 向量存储, 事件总线, 记忆 | 0.15 |
| 内容生产层 (视频/图像/TTS) | 视频生成, 图像生成, TTS, 数字人 | 0.15 |
| 飞书输出层 | 消息增强, 卡片组件, 自动化通知 | 0.05 |
| 运维/可观测性 | 追踪, 监控, 自愈, 安全 | 0.10 |

## Scan Methodology

### Primary Sources
1. `https://github.com/trending?since=weekly` — raw HTML
2. `https://github.com/trending/python?since=weekly` — Python-specific
3. Awesome lists: `awesome-ai-agents`, `awesome-llm-apps`, `awesome-mcp-servers`
4. PapersWithCode trending

### Analysis Pipeline
1. Fetch trending repos (30-50 candidates)
2. Filter: stars > 100 (weekly growth), AI/ML/DevTools/Automation relevant
3. For each candidate → web_extract README + description
4. Score against architecture layers
5. Rank and select top 5-10 for report

## Output Format

Use Feishu CEO specification (no Markdown):

```
🧬 GitHub 技术雷达 · 2026-05-12

━━━━━━━━━━━━━━━━━━━━

📊 概览
• 扫描: 47个项目
• 精选: 8个高匹配
• 平均匹配度: 7.2/10

📌 精选项目

🔴 架构级匹配 (≥8分)

• 项目名 (⭐ stars)
  描述: 一句话
  场景: 应用场景
  匹配: 匹配层/Molin-OS模块
  借鉴: 具体借鉴点
  成本: pip install xxx
  链接: github.com/xxx/xxx

🟠 内容层增强 (7-8分)
...

🟡 工具链补充 (5-7分)
...
```

## Dependencies

- web_search + web_extract (built-in)
- Firecrawl API (for deep scraping README)
- OPENROUTER_API_KEY (for LLM analysis)

## Schedule

- Cron: `0 8 * * *` (每日 08:00)
- 交付: 飞书自动化控制台群 (oc_94c87f141e118b68c2da9852bf2f3bda) + 当前对话
- 归档: `~/.hermes/daily_reports/github_radar_{date}.md`
- 云端: SuperMemory (app.supermemory.ai) — 通过 supermemory_sync.py 自动推送

## Archive & Sync Pipeline

每次扫描完成后自动执行：
1. `write_file` → `~/.hermes/daily_reports/github_radar_{YYYY-MM-DD}.md`
2. `terminal` → `python3 ~/.hermes/scripts/supermemory_sync.py ~/.hermes/daily_reports/github_radar_{date}.md`
3. 报告尾部显示存档状态（本地路径 + 云端同步状态）

存档查看：
- 本地: `ls ~/.hermes/daily_reports/github_radar_*.md`
- 云端: https://app.supermemory.ai/?view=list
