---
name: seo-machine
description: 'SEO-optimized content machine: keyword research, intent detection, quality
  scoring, readability, internal linking, and competitive gap analysis.'
version: 1.0.0
author: Hermes Agent (based on TheCraigHewitt/seomachine)
license: MIT
metadata:
  hermes:
    tags:
    - seo
    - content
    - keywords
    - optimization
    - search
    - marketing
    - writing
    related_skills: []
    category: productivity
    molin_owner: 墨增（增长引擎）
min_hermes_version: 0.13.0
---

# SEO Machine

## Overview

SEO Machine is a comprehensive SEO-optimized content engine that automates the entire content creation lifecycle: from keyword research and clustering through writing, quality scoring, readability analysis, and internal linking strategy. It also performs competitive content gap analysis to identify opportunities your competitors are ranking for that you're missing.

**Core principle:** Data-driven content that ranks. Every piece of content is optimized against search intent, competitive landscape, and technical SEO best practices before publication.

## When to Use

Use this skill when:
- Planning a content strategy for a website or blog
- Writing SEO-optimized articles, landing pages, or product descriptions
- Auditing existing content for SEO improvement opportunities
- Performing keyword research to find high-value, low-competition topics
- Analyzing competitors' content to find gaps in your own strategy
- Building topic clusters and internal linking structures
- Scoring content quality on a 0-100 scale before publishing

**vs. generic AI writing:**
- Keyword-driven, not just topic-driven
- Search intent classification ensures content matches what users actually want
- Competitive analysis built into the workflow
- Structured for search engine crawlability (headings, schema, internal links)
- Quality scoring quantifies how likely content is to rank

## The Workflow

```
Topic/Business Goal
        │
        ▼
┌───────────────────┐
│ 1. KEYWORD        │  Research, cluster, and prioritize keywords
│    RESEARCH       │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 2. INTENT         │  Classify search intent per keyword cluster
│    DETECTION      │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 3. COMPETITIVE    │  Analyze ranking pages for content gaps
│    GAP ANALYSIS   │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 4. CONTENT        │  Write with SEO structure, readability, E-E-A-T
│    CREATION       │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 5. QUALITY        │  Score content 0-100 against ranking factors
│    SCORING        │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ 6. INTERNAL       │  Build linking strategy across content clusters
│    LINKING        │
└────────┬──────────┘
         │
         ▼
   Publish-Ready Content
```

### Stage 1: Keyword Research & Clustering

**Input:** Seed topic(s), target audience, business goals, domain

**Process:**
1. Generate seed keyword list from topic and competitor analysis
2. Expand keywords using related terms, questions (People Also Ask), autocomplete
3. Gather metrics per keyword: search volume, keyword difficulty (KD%), CPC, trend
4. Cluster keywords by semantic similarity into topic groups
5. Prioritize clusters by opportunity score

**Keyword clustering method:**
```yaml
clustering:
  method: "semantic_similarity"  # or "serp_overlap"
  similarity_threshold: 0.75
  min_cluster_size: 3
  max_cluster_size: 15
  
  # Opportunity scoring formula
  opportunity_score: "volume * (1 - kd/100) * trend_factor"
```

**Cluster output format:**
```yaml
clusters:
  - cluster_id: "ai-writing-tools"
    primary_keyword: "best AI writing tools"
    keywords:
      - keyword: "best AI writing tools"
        volume: 5400
        kd: 42
        cpc: 8.50
      - keyword: "AI content generator"
        volume: 3200
        kd: 38
        cpc: 6.20
      - keyword: "AI writing assistant free"
        volume: 1800
        kd: 28
        cpc: 4.10
    total_volume: 10400
    avg_kd: 36
    opportunity_score: 78
    content_type: "listicle_comparison"
```

**Prioritization matrix:**
|   | Low KD (<30) | Medium KD (30-50) | High KD (>50) |
|---|---|---|---|
| **High Volume (>5K)** | 🟢 Priority 1 | 🟡 Priority 2 | 🔴 Priority 4 |
| **Medium Volume (1-5K)** | 🟢 Priority 2 | 🟡 Priority 3 | 🔴 Priority 5 |
| **Low Volume (<1K)** | 🟡 Priority 3 | 🔴 Priority 5 | ⚫ Ignore |

### Stage 2: Search Intent Detection

Classify the intent behind each keyword cluster to ensure content matches user expectations:

**Intent categories:**
| Intent | Description | Content Type | SERP Features |
|--------|-------------|--------------|---------------|
| **Informational** | User wants to learn | How-to guides, explainers, listicles | Featured snippets, PAA |
| **Commercial** | User researching before buying | Comparisons, reviews, best-of lists | Product carousels, reviews |
| **Transactional** | User wants to buy | Product pages, landing pages | Shopping ads, rich snippets |
| **Navigational** | User wants a specific site | Brand pages | Sitelinks, knowledge panels |
| **Local** | User wants nearby results | Local landing pages | Map pack, local pack |

**Intent detection signals:**
```yaml
intent_signals:
  informational:
    - keyword_contains: ["how", "what", "why", "guide", "tutorial", "learn"]
    - serp_has: ["featured_snippet", "people_also_ask", "knowledge_panel"]
    - content_length_bias: "long_form"  # Average ranking page >1500 words
  commercial:
    - keyword_contains: ["best", "vs", "comparison", "review", "top", "cheap"]
    - serp_has: ["product_carousel", "review_stars", "shopping_ads"]
    - content_length_bias: "medium_form"
  transactional:
    - keyword_contains: ["buy", "price", "discount", "coupon", "for sale"]
    - serp_has: ["shopping_ads_top", "product_snippets"]
    - content_length_bias: "short_form"
```

**Mixed intent handling:** Many keywords have mixed intent (e.g., "best laptops" is commercial + informational). Address both by:
1. Opening with commercial comparison (satisfy quick-decision intent)
2. Following with detailed informational sections (satisfy research intent)
3. Clear CTAs for transactional conversion

### Stage 3: Competitive Content Gap Analysis

Analyze what competitors rank for that you don't, and what their content does well/poorly:

**Process:**
1. Identify top 5-10 competitors for your target keywords
2. Extract their ranking keywords (via SERP analysis or SEO tools)
3. Find keywords they rank for (top 20) that you don't target at all
4. For shared keywords, analyze content differences:
   - Word count comparison
   - Heading structure depth
   - Media usage (images, videos, infographics)
   - Schema markup presence
   - Backlink profile strength
   - Content freshness (last updated)
5. Build a gap-filling content plan

**Gap analysis report:**
```yaml
competitive_gaps:
  missed_keywords:
    - keyword: "AI writing for ecommerce"
      competitor: "competitor-a.com"
      competitor_position: 3
      competitor_word_count: 2400
      opportunity: "high"
      suggested_action: "Create dedicated ecommerce AI writing landing page"
      
    - keyword: "free AI content detector"
      competitor: "competitor-b.com"
      competitor_position: 5
      competitor_word_count: 1800
      opportunity: "medium"
      suggested_action: "Build free tool page + comparison content"

  content_improvement_opportunities:
    shared_keyword: "best AI writing tools"
    your_position: 12
    competitor_best_position: 2
    gaps:
      - factor: "word_count"
        you: 1200
        competitor: 3500
        impact: "high"
      - factor: "headings_h2_count"
        you: 4
        competitor: 12
        impact: "high"
      - factor: "images_count"
        you: 2
        competitor: 15
        impact: "medium"
      - factor: "schema_type"
        you: "none"
        competitor: "Article + FAQ + HowTo"
        impact: "high"
      - factor: "last_updated"
        you: "2025-01"
        competitor: "2026-04"
        impact: "medium"
```

### Stage 4: Content Creation

Write content optimized for both users and search engines:

**Content structure template:**
```markdown
# [H1: Primary Keyword - Exact or close match]

> [Compelling meta description: 150-160 chars with primary keyword and CTA]

## [H2: Address the main search intent directly]

[Opening paragraph: Hook + answer the query within first 100 words]

## [H2: Secondary intent / subtopic]

[Detailed content with supporting keywords naturally woven in]

### [H3: Specific aspect]

[Examples, data, or step-by-step instructions]

## [H2: Common questions (PAA optimization)]

### [H3: Question 1 from PAA]
### [H3: Question 2 from PAA]

## [H2: Expert insights / unique perspective (E-E-A-T)]

[Original research, personal experience, or expert quotes — don't just rehash top 10 results]

## [H2: Conclusion + CTA]

[Summary + clear next step for the reader]
```

**SEO writing rules:**
- Primary keyword in H1, first 100 words, and one H2
- Secondary keywords in H2s and H3s
- Keyword density: 1-2% (natural, never forced)
- LSI and related terms throughout (semantic richness)
- Internal links: 3-5 to related content
- External links: 2-3 to authoritative sources
- Image alt text with descriptive keywords
- Short paragraphs (2-4 sentences max)
- Bullet points and numbered lists for scannability

**E-E-A-T signals (Experience, Expertise, Authoritativeness, Trustworthiness):**
- Author bio with credentials
- Cite original sources and studies
- Include first-hand examples or case studies
- Date published + "last updated" with actual update history
- Contact information and about page links
- Privacy policy and terms links where appropriate

### Stage 5: Quality Scoring (0-100)

Score content on a 0-100 scale against proven ranking factors:

```yaml
quality_scoring:
  on_page_seo (30 points):
    title_tag_optimization: 5      # Keyword at beginning, 50-60 chars
    meta_description: 5            # 150-160 chars, includes keyword + CTA
    h1_optimization: 5             # One H1, contains primary keyword
    heading_structure: 5           # Logical H2→H3 hierarchy, keyword in H2s
    url_structure: 5               # Short, contains keyword, hyphens
    image_alt_text: 5              # All images have descriptive alt text
  
  content_quality (40 points):
    search_intent_match: 10        # Content type matches user intent
    comprehensiveness: 10          # Covers topic more thoroughly than top 10
    originality: 8                 # Unique perspective, data, or examples
    readability: 6                 # Grade 7-9 reading level, scannable
    freshness: 6                   # Recently published or updated
  
  technical_seo (15 points):
    schema_markup: 5               # Relevant schema types implemented
    mobile_friendly: 5             # Responsive, readable on mobile
    page_speed: 5                  # Load time <3s (desktop), <5s (mobile)
  
  authority_signals (15 points):
    internal_linking: 5            # 3-5 contextual internal links
    external_linking: 5            # 2-3 links to authoritative sources
    e_e_a_t_demonstrated: 5        # Author bio, sources, trust signals
```

**Scoring thresholds:**
- **90-100:** Excellent — ready to publish, high confidence of ranking
- **75-89:** Good — minor improvements recommended before publishing
- **60-74:** Adequate — needs significant work in multiple areas
- **Below 60:** Needs rewrite — do not publish

### Stage 6: Readability Analysis

Ensure content is accessible to the target audience:

**Metrics:**
```yaml
readability:
  flesch_reading_ease:
    target: 60-70  # Standard / fairly easy
    formula: "206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)"
    
  flesch_kincaid_grade:
    target: 7-9  # 7th-9th grade level for general audience
    formula: "0.39*(words/sentences) + 11.8*(syllables/words) - 15.59"
    
  avg_sentence_length:
    target: 15-20 words
    max: 25 words  # Flag sentences exceeding this
    
  paragraph_length:
    target: 2-4 sentences
    max: 6 sentences
    
  passive_voice_percentage:
    max: 10%
    
  transition_words_percentage:
    min: 30%  # At least 30% of sentences use transition words
```

**Readability improvements:**
- Split sentences over 25 words
- Break paragraphs over 6 sentences
- Convert passive to active voice
- Add transition words (however, therefore, additionally, in contrast)
- Replace complex words with simpler alternatives
- Add bullet points for lists of 3+ items

### Stage 7: Internal Linking Strategy

Build a strategic internal linking structure:

**Principles:**
1. **Topic clusters:** Pillar page → cluster content → supporting pages
2. **Contextual relevance:** Link from naturally relevant anchor text, not "click here"
3. **Link depth:** No page more than 3 clicks from homepage
4. **Link distribution:** Distribute authority evenly; avoid orphan pages
5. **Anchor text variety:** Mix exact-match, partial-match, branded, and generic anchors

**Strategy template:**

```yaml
internal_linking:
  pillar_page: "/ai-writing-tools/"
  cluster_pages:
    - url: "/ai-writing-tools/best/"
      anchor_texts: ["best AI writing tools", "top AI writers", "AI writing tool comparison"]
      links_from: ["/ai-writing-tools/", "/content-marketing-tools/", "/blog/ai-content-guide/"]
    - url: "/ai-writing-tools/free/"
      anchor_texts: ["free AI writing tools", "free AI content generators"]
      links_from: ["/ai-writing-tools/", "/ai-writing-tools/best/", "/blog/budget-content-tools/"]
    - url: "/ai-writing-tools/for-bloggers/"
      anchor_texts: ["AI writing for bloggers", "blogging AI tools"]
      links_from: ["/ai-writing-tools/", "/blogging-tips/", "/content-creation-workflow/"]
  
  orphan_check:
    pages_with_zero_internal_inlinks: []
    pages_with_zero_internal_outlinks:
      - "/ai-writing-tools/enterprise/"  # Needs links to other pages
```

**Link audit commands:**
- Find orphan pages (no incoming internal links)
- Find pages with excessive links (>100 per page)
- Check for broken internal links
- Identify pages 4+ clicks from homepage

## Content Brief Generator

Generate a complete content brief from a keyword cluster:

```yaml
content_brief:
  primary_keyword: "best AI writing tools"
  target_audience: "Content marketers and bloggers looking to automate writing"
  search_intent: "Commercial investigation"
  recommended_content_type: "Listicle with comparison table"
  target_word_count: 2800
  outline:
    - h2: "What Are AI Writing Tools?"
    - h2: "Top 10 AI Writing Tools Compared"
    - h2: "How We Tested Each Tool"
    - h2: "Best AI Writing Tool for [Use Case]"
    - h2: "Pricing Comparison"
    - h2: "Frequently Asked Questions"
  competitors_to_beat:
    - url: "competitor-a.com/best-ai-writing-tools"
      word_count: 3200
      strength: "Detailed comparison table, video reviews"
      weakness: "Outdated pricing, no free options covered"
    - url: "competitor-b.com/ai-writing-tools"
      word_count: 2500
      strength: "Original testing data, author expertise"
      weakness: "Poor mobile layout, slow load time"
  content_differentiators:
    - "Include actual output samples from each tool"
    - "Video walkthrough of top 3 tools"
    - "2026 pricing update (most competitors show 2025 pricing)"
    - "Free alternatives section (most competitors ignore free tier)"
  internal_links_to_include:
    - "/blog/ai-content-strategy/"
    - "/tools/content-marketing-toolkit/"
    - "/blog/how-to-use-ai-for-blogging/"
```

## Quick Start

```python
from seo_machine import SEOMachine

# Full workflow
seo = SEOMachine(domain="yoursite.com")

# 1. Keyword research
clusters = seo.research_keywords("AI writing tools", max_clusters=5)

# 2. Get content brief
brief = seo.generate_brief(clusters[0])

# 3. Write optimized content
content = seo.write_content(brief)

# 4. Score the content
score = seo.score_content(content)
print(f"Quality score: {score}/100")

# 5. Get readability report
seo.analyze_readability(content)

# 6. Link strategy
seo.generate_linking_strategy(content, clusters)

# 7. Competitive gap check
gaps = seo.competitive_gap_analysis("best AI writing tools")
```

## Tips

- **Intent first, keywords second:** A perfectly keyword-optimized page with wrong intent will never rank
- **Content score ≥80 before publishing:** Aim for 80+ on the quality scale
- **Update, don't just create:** Refreshing old content often beats creating new content
- **Cluster, don't scatter:** Build topic clusters with pillar pages, not isolated articles
- **Competitor gaps are gold:** The easiest wins are keywords competitors rank for that you don't target
- **Readability is underrated:** Complex content loses readers. Write at an 8th-grade level for mass appeal
- **Internal links are free SEO:** Proper internal linking can boost rankings more than new backlinks