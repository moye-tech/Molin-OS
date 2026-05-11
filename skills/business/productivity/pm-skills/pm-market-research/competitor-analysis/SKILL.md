---
name: pm-competitor-analysis
description: "Comprehensive competitive analysis framework — identify competitors, compare features, pricing, market position, and derive strategic insights."
version: 1.0.0
tags: [pm, product-management, market-research]
category: productivity
source: https://github.com/phuryn/pm-skills
---

---
name: competitor-analysis
description: "Analyze competitors with strengths, weaknesses, and differentiation opportunities. Identifies direct competitors and maps the competitive landscape. Use when doing competitive research, preparing a competitive brief, or finding differentiation opportunities."
---

# Competitor Analysis

## Purpose
Conduct a comprehensive competitive analysis to understand the landscape, identify 5 direct competitors, and uncover differentiation opportunities. This skill maps competitive positioning, synthesizes competitor strengths and weaknesses, and highlights opportunities for strategic differentiation.

## Instructions

You are a strategic product analyst and competitive intelligence expert specializing in competitive positioning and market landscape mapping.

### Input
Your task is to analyze the competitive landscape for **$ARGUMENTS** in the **[market/industry segment]** (if specified).

Conduct web research to identify direct competitors. If the user provides market research, competitor data, pricing sheets, feature comparisons, or customer feedback about competitors, read and analyze them directly. Synthesize data into a comprehensive competitive view.

### Analysis Steps (Think Step by Step)

1. **Market Scoping**: Define the market, industry, and addressable customer base for $ARGUMENTS
2. **Competitor Identification**: Use web search to identify 5 primary direct competitors
3. **Competitive Intelligence**: Research each competitor's positioning, features, pricing, go-to-market strategy
4. **Strengths & Weaknesses**: Assess competitor capabilities, limitations, and market positioning
5. **Differentiation Mapping**: Identify gaps, overlaps, and opportunities for $ARGUMENTS to differentiate
6. **Strategic Synthesis**: Develop insights about competitive dynamics and future threats

### Output Structure

**Market Overview & Definition**
- Market size and growth trends
- Primary customer segments and use cases
- Key success factors in this market
- Market dynamics and competitive intensity

**Competitive Set Summary**
- 5 primary direct competitors identified
- Market positions: leaders, challengers, niche players
- Estimated market share or positioning
- Notable adjacent or indirect competitors

For each of the 5 competitors:

**Competitor Profile**
- Company name, founding date, funding/status
- Primary market focus and customer segments served
- Estimated market share or customer base size
- Market positioning and go-to-market strategy

**Core Product Strengths**
- Key features and capabilities
- Unique competitive advantages
- Customer value proposition
- Technology differentiation or moats
- Customer satisfaction and retention signals

**Product Weaknesses & Gaps**
- Missing features or use cases
- Known limitations or pain points for customers
- Technical or operational weaknesses
- Market positioning gaps
- Customer dissatisfaction areas

**Business Model & Pricing**
- Pricing structure (per-seat, per-usage, flat-fee, freemium, etc.)
- Price point(s) in market
- Go-to-market channels and sales motion
- Revenue model and growth stage

**Competitive Threats & Advantages**
- How this competitor threatens $ARGUMENTS
- Existing customer base and switching costs
- Strategic partnerships or ecosystems
- Recent product updates or strategic moves

**Differentiation Opportunities for $ARGUMENTS**

- Unmet customer needs across competitive set
- Feature/pricing/UX opportunities to stand out
- Target segments underserved by competitors
- Jobs-to-be-done not effectively solved by competitors
- Channel or go-to-market approaches not yet deployed
- Potential partnerships or integrations competitors lack

**Competitive Positioning Recommendation**
- Recommended competitive positioning for $ARGUMENTS
- Key differentiators to emphasize
- Segments or use cases to target or avoid
- Competitive threats to monitor
- 12-18 month competitive risks and opportunities

## Pitfalls

- **Xianyu/Taobao direct scraping is blocked.** PC browser access to goofish.com and s.2.taobao.com returns empty pages or login walls. Use `web_search` with targeted queries (e.g., "闲鱼 PPT代做 价格 2026") as the primary data source. Web search snippets provide enough detail for pricing bands, though exact listing counts are unavailable.
- **web_extract often fails on Chinese ecommerce sites.** Taobao, Zhihu, SegmentFault, and similar .cn domains frequently return "Blocked: private/internal network" errors. Rely on web_search result snippets and cross-reference across multiple sources (什么值得买, 掘金, CSDN, 简书).
- **Pricing data is directional, not exact.** Web search gives ranges (low/median/high), not precise real-time prices. Treat as competitive intelligence bands, not order-book quotes.
- **Always save a pricing_cache.json** after analysis runs so future sessions can detect price movements. Format: `{last_check, suggestions[{sku, our_price, market_low, market_median, market_high, recommendation}]}`. Store at `~/.hermes/xianyu_bot/pricing_cache.json`.

## Cron Automation

When run as a scheduled cron job (no user present):
- Scrape via web_search (not browser — login walls block it)
- Compare against last pricing_cache.json if it exists; flag deltas >15%
- Import full report as Feishu doc via `feishu-cli doc import` (content >500 chars or has tables)
- Send summary card to automation control group per feishu-message-formatter cron template
- Update pricing_cache.json with new data

## Best Practices

- Research current competitor websites, pricing pages, and customer reviews
- Use web search to identify product launches, funding, executive moves
- Distinguish between direct competitors and adjacent alternatives
- Validate competitive insights across multiple sources
- Identify both obvious and subtle differentiation opportunities
- Consider customer pain points not yet addressed in market
- Look for emerging competitors or new market entrants
- Flag competitors gaining traction or gaining market share
- Consider long-term competitive dynamics and market shifts

## Molin-OS Cron 集成

当用于 cron 定时竞品定价巡检时，详见 `references/xianyu-pricing-monitor.md`：
- 数据存储：`~/.hermes/xianyu_bot/pricing_cache.json`
- 异常检测阈值：价格变动 >15%（MEDIUM）/ >30%（HIGH）
- 输出格式：遵循 cron-output-formatter 卡片模板
- 支持 SKU：BP代写、PPT美化、LOGO设计、AI数字人

## References

- `references/benchmark-pricing-20260511.md` — Real benchmark pricing data from 2026-05-11 cron run across Xianyu + Taobao + content platforms

metadata:
  hermes:
    molin_owner: 墨品（产品设计）
---

### Further Reading

- [Market Research: Advanced Techniques](https://www.productcompass.pm/p/market-research-advanced-techniques)
- [User Interviews: The Ultimate Guide to Research Interviews](https://www.productcompass.pm/p/interviewing-customers-the-ultimate)
