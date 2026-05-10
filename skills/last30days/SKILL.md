---
name: last30days
description: AI agent-led search engine scored by real user engagement. Searches Reddit,
  Hacker News, Polymarket, GitHub, YouTube, TikTok, X across the last 30 days — ranked
  by upvotes/likes/real money, not editors.
version: 1.0.0
tags:
- search
- social-media
- research
- trends
- monitoring
- content-discovery
category: research
related_skills:
- arxiv
- youtube-content
- blogwatcher
- polymarket
metadata:
  hermes:
    homepage: https://github.com/mvanhorn/last30days-skill
    install_note: Zero-config for Reddit/HN/Polymarket/GitHub. Run setup wizard for
      X/YouTube/TikTok.
    molin_owner: 墨思（情报研究）
min_hermes_version: 0.13.0
---

# Last30Days — Social Engagement Search Engine

AI agent-led search engine that searches what real people actually engage with — upvotes, likes, real money. Not editors.

Reddit upvotes. X likes. YouTube transcripts. TikTok engagement. Polymarket odds. That's millions of people voting with their attention every day. This skill searches all of it in parallel, scores it by what people engage with, and synthesizes it.

## Platforms (Zero Config)
- **Reddit** — posts, comments, upvote counts
- **Hacker News** — stories, comments, points
- **Polymarket** — real-money prediction markets
- **GitHub** — trending repositories, discussions
- **X / Twitter** — posts, likes, retweets (requires setup)
- **YouTube** — transcripts, view counts (requires setup)
- **TikTok** — engagement data (requires setup)

## When to Use
- Research what people are saying about a topic
- Discover trending content for social media
- Validate ideas against real audience interest
- Monitor brand/product mentions
- Find content inspiration backed by engagement data
- Pre-post research: what formats/topics are getting traction

## When NOT to Use
- Academic literature search → use `arxiv` skill
- Real-time news → use web search
- Niche topics with low social volume
- Tasks requiring authoritative sources (use web search instead)

## Usage

```
/last30days <query> [--sources reddit,hn,polymarket] [--days 30]
```

The skill searches all configured platforms in parallel, ranks results by engagement, and returns a synthesized brief with links.

## Setup

For Reddit, HN, Polymarket, and GitHub — zero config. Just use it.

For X, YouTube, TikTok — run `sync.sh` once and follow the setup wizard (requires API keys).

## Output Format
- **Top results** ranked by engagement score
- **Links** to original posts
- **Synthesis** — AI summary of the conversation across platforms
- **Trend signals** — what's rising, what's peaking

## Integration Tips
- Use before writing social media posts to align with trending topics
- Use to find high-engagement content formats to emulate
- Use to monitor competitors and your own brand mentions
- Combine with `youtube-content` skill for deeper video analysis