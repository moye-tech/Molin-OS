---

name: world-monitor
description: Real-time global intelligence monitoring — track news, geopolitical events, tech trends, and industry shifts across multiple sources. Use when you need to stay informed about what's happening in the world that affects your business.
version: 1.0.0
tags: [intelligence, monitoring, news, geopolitics, trends, awareness]
category: research
related_skills: [last30days, blogwatcher, polymarket, mirofish-trends]
metadata:
  hermes:
    source: https://github.com/koala73/worldmonitor
    stars: 53000
    molin_owner: 墨思（情报研究）
---

# World Monitor — 全球情报监控

## Overview

A situational awareness framework for tracking global events that impact your business. Patterned after World Monitor's real-time intelligence dashboard — but executed through Hermes's research capabilities.

## Monitoring Dimensions

### 1. Technology & AI
- Major model releases (GPT, Claude, Gemini, DeepSeek)
- AI regulation changes (EU AI Act, China AI laws, US executive orders)
- Platform policy changes (Xiaohongshu algorithm, Douyin rules)
- Open-source breakthroughs

### 2. Market & Economy
- Interest rate decisions, inflation data
- Tech sector layoffs/hiring trends
- VC funding trends (which sectors are hot/cold)
- Consumer spending patterns

### 3. Geopolitical
- Trade restrictions, sanctions
- Cross-border business impacts
- Data localization requirements
- Platform bans/restrictions in key markets

### 4. Industry-Specific
- Freelance platform changes (猪八戒, 闲鱼, Upwork)
- Content platform algorithm updates
- Competitor movements
- New monetization channels

## Usage Protocol

When user asks "what's happening in X" or "monitor Y":

1. **Scan**: Cross-reference last30days + blogwatcher + web search
2. **Filter**: Only items with direct business impact
3. **Synthesize**: Not a news dump — explain WHY it matters
4. **Recommend**: What action, if any, should be taken

## Alert Triggers

Proactively alert when:
- A major AI model is released (market shift opportunity)
- Platform rules change (risk to current strategy)
- New monetization channel opens (opportunity)
- Competitor makes a significant move

## Integration with 一人公司

```
World Monitor detects → AI regulation change
    ↓
TradingAgents analyzes → impact on AI service market
    ↓
MiroFish predicts → how this shifts demand
    ↓
CEO persona decides → adjust service pricing or pivot
```

## Limitations

- Not real-time ticker (relies on search freshness)
- Geopolitical analysis is framework-based, not intelligence-grade
- Always cross-reference multiple sources
