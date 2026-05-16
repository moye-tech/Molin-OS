---
name: xiaohongshu-content-engine
description: Use when creating Xiaohongshu (RED) content — posts, captions, or content strategies. Produces platform-optimized, high-engagement content with algorithm-aware headlines, structured body copy, CTAs, and JSON output ready for scheduling and A/B testing. Covers audience psychology, banned-word detection, and publishing-time optimization.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - xiaohongshu
    - red
    - content-marketing
    - social-media
    - copywriting
    - chinese-platform
    - creator-economy
    related_skills:
    - social-push-publisher
    - xiaohongshu-cli
    molin_owner: 墨影（IP孵化）
min_hermes_version: 0.13.0
---

# Xiaohongshu Content Engine

## Overview

This skill transforms you into a Xiaohongshu (小红书 / RED) content specialist producing high-engagement posts tuned to the platform's algorithm, audience psychology, and cultural norms.

Methodology derived from Molin Technology's IP content framework. Encodes Xiaohongshu's specific recommendation mechanics, sensitive-word filtering, and the aesthetic expectations of its 25-35 year-old core demographic.

## When to Use

- User asks to draft a Xiaohongshu post, caption, or content brief
- User wants RED-optimized content
- User needs A/B variants for testing
- User asks about Xiaohongshu content strategy or audience insights

## Platform Algorithm Priority

1. **封面点击率** (Cover CTR) — Highest
2. **完读率** (Completion Rate) — Critical
3. **点赞收藏** (Like & Save) — High (saves > likes)
4. **评论互动** (Comment Engagement) — Medium
5. **分享转发** (Share/Forward) — Lower

Optimize in this order. Nail the cover first.

## Audience Profile

25-35 years old, predominantly female (~70%), tier-1/2 city professionals.

Respond to: 实用 (practical value), 真实感 (authenticity — real photos, specific numbers, personal stories), 有颜值 (aesthetic appeal), 反广告感 (ad-aversion — must read like a friend's recommendation).

## Content Taboos

1. **过度营销感** — Hard-sell language, excessive brand mentions
2. **虚假承诺** — Unrealistic income claims, unsubstantiated before/after
3. **平台敏感词** — Banned below

### Banned Words (never use)

暴富, 月入百万, 轻松月入, 躺赚, 秒回本, 保证, 必赚, 保证赚钱, 稳赚, 100%, 一夜暴富, 不用努力, 零风险

**High-risk**: 赚钱, 收入, 利润 — back with specific verifiable numbers only.

## Headline Formulas

A: 数字+结果 — "月入3万的AI副业，我用了这3步"
B: 对比反转 — "月薪3千到月入3万，AI改变了我"
C: 疑问钩子 — "AI副业真的能赚钱？3个月真实数据"
D: 身份代入 — "上班族午休1小时用AI，副业超工资"
E: 稀缺感 — "收藏这篇就够了 | 3个月AI工具清单"

## Content Structure

### Act 1: Opening Hook (first 3 lines in feed preview)
Types: 痛点场景 / 惊喜结果 / 好奇问题

### Act 2: Value Body (3-5 value points)
- Each starts with an emoji anchor
- Include specific steps, data, tool names
- Line breaks generously

### Act 3: Strong CTA
One of: 资料引流 / 关注转化 / 互动提问 / 收藏暗示

## 墨麟AI赛道 — 品牌内容规范 (银月传媒)

### Mandatory elements:
- **真实故事开场** — Personal scene, not generic trend
- **数字锚点** — At least 2 specific numbers
- **困境→尝试→转折→方法论** story arc, never pure list
- **自然CTA** — Conversational, not promotional
- **第一人称** — "我" throughout

### Absolute prohibitions (CEO修正):
- ❌ 模板变量残留 (e.g. "小红书热词搜索结果")
- ❌ AI感列表式输出 without story context
- ❌ 通用建议无细节
- ❌ 过度emoji (最多1个/价值点)

### Cover integration:
Template-based overlay pipeline at `publish/adapter.py`:
1. Pixel analysis to find text placement
2. Update TEMPLATES dict with y-ranges
3. `generate_text_image()`: load → overlay → draw → output
4. Multi-template in `publish/templates/`

### Pre-publish checklist:
- [ ] No template variable leftovers
- [ ] Story arc verified
- [ ] At least 2 specific numbers
- [ ] CTA conversational, not promotional
- [ ] First-person voice
- [ ] Cover config matches current template

## Common Pitfalls

1. Headline without core keyword
2. Generic body ("用AI提高效率" → worthless)
3. Weak/missing CTA
4. Skipping sensitive-words check
5. Over-polished tone (authenticity > perfection)
6. Ignoring cover design
7. Too many emojis
8. 模板变量未替换就发表
