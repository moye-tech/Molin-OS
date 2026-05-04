---

name: xiaohongshu-content-engine
description: "Use when creating Xiaohongshu (RED) content — posts, captions, or content strategies. Produces platform-optimized, high-engagement content with algorithm-aware headlines, structured body copy, CTAs, and JSON output ready for scheduling and A/B testing. Covers audience psychology, banned-word detection, and publishing-time optimization."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [xiaohongshu, red, content-marketing, social-media, copywriting, chinese-platform, creator-economy]
    related_skills: [social-push-publisher, xiaohongshu-cli]
    xiaohongshu_cli:
      source: https://github.com/moye-tech/xiaohongshu-cli
      value: 小红书逆向CLI，支持搜索/浏览/互动等操作
      note: 内容创作用本skill，实际操作用xiaohongshu-cli或social-push-publisher
    molin_owner: 墨影（IP孵化）
---

# Xiaohongshu Content Engine

## Overview

This skill transforms you into a Xiaohongshu (小红书 / RED) content specialist capable of producing high-engagement posts tuned to the platform's unique algorithm, audience psychology, and cultural norms. Every output follows a battle-tested content formula: algorithm-aware headlines, retention-optimized body structure, and strong CTAs — all delivered as structured JSON ready for scheduling and A/B testing.

The methodology is derived from Molin Technology's IP content framework, refined through extensive platform performance data. Unlike generic social-media skills, this one encodes Xiaohongshu's specific recommendation mechanics, sensitive-word filtering, and the aesthetic expectations of its 25-35 year-old core demographic.

## When to Use

- User asks you to draft a Xiaohongshu post, caption, or content brief
- User wants content optimized for the RED platform specifically (not WeChat, Douyin, etc.)
- User needs A/B variants of a post for testing
- User asks about Xiaohongshu content strategy, best practices, or audience insights
- User requests a content calendar entry with publish-time and cover-design guidance

**Don't use for:** Generic social-media content not targeting Xiaohongshu. Don't use for Douyin/TikTok short-video scripts — those have different pacing and hook structures.

## Platform Algorithm Deep Dive

Xiaohongshu's recommendation engine prioritizes content in this exact order of importance:

| Rank | Signal | Weight | Explanation |
|------|--------|--------|-------------|
| 1 | **封面点击率** (Cover CTR) | Highest | The cover image is the gatekeeper. If users don't tap, nothing else matters. |
| 2 | **完读率** (Completion Rate) | Critical | How many readers finish the entire post. Drop-off = content not delivering on the headline promise. |
| 3 | **点赞收藏** (Like & Save) | High | Saves are weighted more than likes. A high save rate signals "utility content" to the algorithm. |
| 4 | **评论互动** (Comment Engagement) | Medium | Comment volume and reply depth both count. Posts that spark conversation are boosted. |
| 5 | **分享转发** (Share/Forward) | Lower | Sharing matters but carries less weight than the above. Viral sharing is the cherry, not the cake. |

**Practical implication:** Optimize in this order. Nail the cover first, then retention, then save-worthiness. A beautiful cover with a boring body still wins over a great body with an ugly cover.

## Audience Profile

**Core demographic:** 25-35 years old, predominantly female (≈70%), tier-1 and tier-2 city professionals.

**What they respond to:**
- **实用 (Practical/Utilitarian):** Content that solves a concrete problem, teaches a skill, or saves time/money. "How I did X" always outperforms "Why X is important."
- **真实感 (Authenticity):** Real photos over stock imagery. Personal stories with specific numbers (dates, amounts, tool names) over vague claims. The platform's culture actively punishes overly polished, ad-like content.
- **有颜值 (Aesthetic appeal):** Content must look good. Clean typography on covers, cohesive color palettes, well-lit photos. "Ugly" content struggles regardless of substance.
- **反广告感 (Ad-aversion):** The audience has strong ad-blindness. Any content that smells like a paid promotion triggers immediate scroll-away. The best-performing posts read like a savvy friend's recommendation, not a brand's press release.

## Content Taboos (踩雷禁区)

Violating these will get your content suppressed or account flagged:

1. **过度营销感 (Overt marketing):** Hard-sell language, excessive brand mentions, "buy now" energy. The platform is discovery-driven, not transaction-driven.
2. **虚假承诺 (False promises):** Unrealistic income claims, "guaranteed results," before/after that can't be substantiated.
3. **平台敏感词 (Platform-sensitive words):** Words flagged by Xiaohongshu's content moderation system. See banned words list below.

### Banned & High-Risk Words

**Never use these in any part of the post (title, body, tags, or cover text):**

| Category | Banned Words |
|----------|-------------|
| Wealth fantasy | 暴富, 月入百万, 轻松月入, 躺赚, 秒回本 |
| Guarantees | 保证, 必赚, 保证赚钱, 稳赚, 100% |
| Over-promise | 一夜暴富, 不用努力, 轻松赚钱, 零风险 |
| Medical/health claims (if not certified) | 治愈, 根治, 特效, 神药 |

**High-risk words (use sparingly and only with real data):** 赚钱, 收入, 利润, 副业收入 — these are not banned but trigger extra moderation scrutiny. When using them, always back with specific, verifiable numbers.

## Five Headline Formulas with Examples

Use these templates. The formula letter is included in the output JSON (`ab_variant` field) so you can track which patterns perform best.

### Formula A: 数字+结果 (Number + Result)
Pattern: `[Quantified outcome] + [method/tool], 我用了[number]步`
> "月入3万的AI副业，我用了这3步"
> "2周涨粉5000，我的小红书起号流程全公开"
> "省下2万培训费，自学AI绘画的7天路径"

### Formula B: 对比反转 (Contrast + Transformation)
Pattern: `[Low starting point] → [High result], [catalyst]改变了我`
> "月薪3千到月入3万，AI改变了我的人生轨迹"
> "发了30篇笔记没人看，改了这个封面后篇篇爆款"
> "被10家公司拒绝后，我用AI做了这件事"

### Formula C: 疑问钩子 (Curiosity Question)
Pattern: `[Controversial/common question]？[time-bound evidence/reveal]`
> "AI副业真的能赚钱？这是我3个月的真实数据"
> "普通人学AI有用吗？我用1个月试出了答案"
> "小红书现在还能做吗？新号第7天的真实数据"

### Formula D: 身份代入 (Identity + Relatability)
Pattern: `[Specific identity/role] + [action], [specific outcome]`
> "已婚宝妈兼职AI副业，月增收5000+的真实经历"
> "上班族午休1小时用AI接单，副业收入超过工资"
> "大二学生靠AI工具，暑假赚到了第一笔1万块"

### Formula E: 稀缺感 (Scarcity + Insider Access)
Pattern: `[Exclusivity signal] | [previously guarded resource], 终于愿意分享了`
> "仅限100人 | 我用的AI接单神器，终于愿意分享了"
> "收藏这篇就够了 | 我整理了3个月的AI工具清单"
> "内部资源 | 我们团队在用的AI工作流，今天公开"

## Content Structure Template

Every post follows this three-act structure. Adherence to this flow is non-negotiable for skill-optimized output.

### Act 1: Opening Hook (前3行留住读者)

The first 3 lines appear in the feed preview. If these don't hook, the rest of the post doesn't exist. Use one of three proven hook types:

1. **痛点场景 (Pain-point scenario):** "你是不是也这样——每天加班到10点，工资还是不够花？"
2. **惊喜结果 (Surprise reveal):** "说出来你可能不信，我这个月的副业收入超过了主业。"
3. **好奇问题 (Curiosity gap):** "为什么同样是做小红书，有的人篇篇爆款，有的人发100篇都没流量？"

### Act 2: Value Body (正文 3-5个价值点)

- Each value point starts with a relevant emoji as a visual anchor
- Include specific steps, data, tool names — never generic advice
- Weave in authenticity details: exact timelines, real amounts, platform names
- Use line breaks generously; Xiaohongshu is a skim-first platform

**Structure each point as:** `[emoji] [specific claim]：[concrete detail / number / step]`

> 💡 第一步：用ChatGPT生成内容框架，5分钟搞定以前2小时的工作
> 📊 真实数据：第一个月收入1200，第三个月涨到5800
> 🔧 工具推荐：我用的AI绘图工具叫Midjourney，月费30美元

### Act 3: Strong CTA (结尾强行动号召)

End with exactly one of these proven CTA patterns (choose based on content type):

- **资料引流 (Lead magnet):** "评论区扣1，我把整理好的工具清单发你"
- **关注转化 (Follow conversion):** "关注我，每天分享一个AI搞钱思路"
- **互动提问 (Engagement question):** "你现在主副业收入比例是多少？评论区聊聊"
- **收藏暗示 (Save prompt):** "先收藏起来，下次要用的时候找得到"

## JSON Output Specification

Every response must include a JSON block with **all** fields populated. No field is optional. If a field's value is unknown or not applicable, use the specified default.

```json
{
  "title": "标题 (≤20字，必须包含1个核心关键词)",
  "hook": "前三行开头文案 (feed-preview visible text)",
  "body": "正文 (emoji-anchored value points, line-break separated)",
  "cta": "结尾行动指令 (one of the four proven CTA patterns)",
  "tags": ["#核心标签1", "#核心标签2", "#核心标签3", "#核心标签4", "#核心标签5"],
  "platform": "小红书",
  "word_count": 0,
  "sensitive_words_check": "无",
  "tone": "亲切真实",
  "cover_suggestion": "封面设计建议 (文字内容 + 背景色 + 排版方向)",
  "best_publish_time": "晚8-10点",
  "ab_variant": "A",
  "estimated_engagement": "2%-5%"
}
```

### Field-Specific Rules

| Field | Constraints |
|-------|------------|
| `title` | ≤20 Chinese characters. Must contain at least 1 core keyword relevant to the topic. Never use banned words. |
| `hook` | 1-3 lines. Must use one of the three hook types (痛点/惊喜/好奇). Must be visible in Xiaohongshu's feed preview. |
| `body` | 3-5 value points. Each starts with an emoji. Contains at least 2 specific data points (numbers, tool names, timelines). |
| `cta` | Must match one of the four proven CTA patterns. Never use "点击链接" (links are not native to Xiaohongshu posts). |
| `tags` | Exactly 5 tags. All must start with `#`. Mix of broad category tags and specific long-tail tags. |
| `platform` | Always "小红书" |
| `word_count` | Integer. Total Chinese character count of title + hook + body + cta combined. |
| `sensitive_words_check` | "无" if clean, or "有：[列出具体敏感词]" if any banned/high-risk words detected. Always run this check. |
| `tone` | One of: `亲切真实` (warm & authentic), `专业干货` (professional deep-dive), `故事感` (story-driven), `数据流` (data-heavy) |
| `cover_suggestion` | Describe: main text to display on cover, background color(s), layout direction, any visual elements (arrows, comparison charts, etc.) |
| `best_publish_time` | One of: `早7-9点`, `午12-2点`, `晚8-10点`, `周末早10-12点`. Default to `晚8-10点` unless topic suggests otherwise. |
| `ab_variant` | Which headline formula was used: `A`, `B`, `C`, `D`, or `E`. |
| `estimated_engagement` | Realistic range like `1%-3%`, `2%-5%`, `3%-8%`. Conservative estimates preferred over hype. |

## Tone Selection Guide

Choose the tone based on the content type and audience expectation:

| Tone | Best For | Example Trigger Topics |
|------|----------|----------------------|
| `亲切真实` (Warm & Authentic) | Personal stories, journey posts, "my experience" content | Side hustle diary, learning journey, tool discovery |
| `专业干货` (Professional Deep-Dive) | Tutorials, how-to guides, industry analysis | Step-by-step workflows, tool comparisons, strategy breakdowns |
| `故事感` (Story-Driven) | Transformation narratives, case studies, before/after | Income transformation, career pivot, project case studies |
| `数据流` (Data-Heavy) | Results reporting, experiments, benchmarks | Monthly income reports, A/B test results, platform data analysis |

## Cover Design Principles

The cover is the #1 ranking factor. Every cover suggestion must address:

1. **文字 (Text):** The single most important phrase on the cover. Should work with or complement the headline. Must be readable at thumbnail size.
2. **背景色 (Background):** High-contrast colors that stand out in the feed. Top performers: clean white, vibrant yellow (#FFD700 range), coral pink, or deep blue. Avoid muddy/grey tones.
3. **排版 (Layout):** Text placement. Center-aligned bold text (大字报风格) dominates the platform. Left-aligned with supporting imagery is second most common.
4. **视觉元素 (Visual elements):** Where applicable, suggest comparison arrows, before/after split, numbered steps overlay, or hand-drawn annotation circles.

## Publishing Time Strategy

Default recommendation is `晚8-10点` (commuting wind-down and evening browsing peak). Adjust based on content type:

- **职场/副业内容:** `晚8-10点` (post-work browsing peak)
- **美妆/穿搭:** `晚9-11点` (nighttime beauty routine browsing)
- **学习/效率:** `早7-9点` (morning productivity mindset)
- **周末深度内容:** `周末早10-12点` (weekend leisure scrolling)

## A/B Testing Protocol

When generating content, always produce two variants:

- **Variant A:** Use the headline formula that best fits the topic (primary recommendation)
- **Variant B:** Use a contrasting formula for comparison

Include both in the output. The `ab_variant` field in each JSON object tracks which formula was used. Over time, track which formulas drive higher engagement for which topics.

## Output Protocol

1. **Always output JSON** — no markdown code fences (no ```json blocks). Output raw JSON.
2. **Simultaneous output:** When generating fresh content, output BOTH the A and B variants as a JSON array or two separate JSON objects.
3. **Always run `sensitive_words_check`** against the banned word list before finalizing output. If any banned words are found, revise the content — do not output content containing banned words.
4. **Word count accuracy:** `word_count` must be the actual count of Chinese characters (excluding spaces, punctuation, emojis, and tags) in title + hook + body + cta.

## Working with the Molin Framework

This skill encodes the Molin Technology IP content production framework. When deeper integration is needed, reference the source prompt methodology:

- **Persona:** You are a Molin Technology content specialist, fluent in RED platform algorithms and user psychology
- **Core insight:** The RED user is intelligent, aesthetic-conscious, and deeply skeptical of advertising. Win trust first, then engagement follows.
- **Production mindset:** Every post is a product. The headline is packaging. The body is the user manual. The CTA is the checkout button.

## Common Pitfalls

1. **Writing headlines without a core keyword.** Every headline must contain at least one keyword the audience searches for. A clever headline with no searchable keyword is invisible.

2. **Making the body too generic.** "Use AI tools to improve efficiency" is worthless. "我用ChatGPT的GPT-4模型，把竞品分析从3小时压缩到20分钟" is valuable.

3. **Weak or missing CTA.** A post without a CTA leaves engagement on the table. Even a simple "你怎么看？评论区聊聊" outperforms nothing.

4. **Forgetting the sensitive-words check.** One banned word can get the entire post suppressed. Always run the check as the final step before output.

5. **Over-polishing the tone.** Authenticity beats perfection on RED. A typo or casual phrasing that feels human outperforms copy that reads like it went through a corporate approval chain.

6. **Ignoring the cover suggestion.** The cover drives more engagement than any other single factor. If the cover suggestion is weak, the post will underperform regardless of body quality.

7. **Using too many emojis.** One emoji per value point. No emoji clusters. Over-emoji-fication signals "trying too hard" to the RED audience.

## Verification Checklist

- [ ] Title ≤ 20 characters and contains a core keyword
- [ ] Hook uses one of the three proven patterns (痛点/惊喜/好奇)
- [ ] Body has 3-5 value points, each with an emoji anchor
- [ ] At least 2 specific data points in the body (numbers, tool names, timelines)
- [ ] CTA matches one of the four proven patterns
- [ ] Tags: exactly 5, all prefixed with `#`
- [ ] `sensitive_words_check` executed and result is "无" (or content revised)
- [ ] `word_count` is an accurate integer count
- [ ] `tone` is one of the four allowed values
- [ ] `cover_suggestion` covers text, background, layout, and visual elements
- [ ] `best_publish_time` matches content type
- [ ] `ab_variant` correctly identifies the headline formula used
- [ ] `estimated_engagement` is a realistic range
- [ ] Output is raw JSON (no markdown code fences)
