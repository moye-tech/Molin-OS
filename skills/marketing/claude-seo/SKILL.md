---

name: claude-seo
version: "1.9.6"
description: "Universal SEO skill with 19 core sub-skills and 3 extensions. Full site audits, single-page analysis, technical SEO (crawlability, indexability, Core Web Vitals with INP), schema markup, content quality (E-E-A-T), image optimization, sitemap analysis, GEO for AI Overviews/ChatGPT/Perplexity, semantic clustering, SXO, drift monitoring, e-commerce SEO, programmatic SEO, competitor pages, local SEO, maps intelligence, hreflang/i18n, Google APIs, backlink profile analysis, and strategic planning. Industry detection for SaaS, e-commerce, local, publishers, agencies. Trigger phrases: SEO, audit, schema, Core Web Vitals, sitemap, E-E-A-T, AI Overviews, GEO, technical SEO, content quality, page speed, structured data, backlinks, keyword research, topic cluster, search experience, SEO drift, ecommerce SEO, local SEO, Google Maps, hreflang, programmatic SEO, competitor comparison."
author: AgriciDaniel (converted for Hermes Agent)
tags: [seo, marketing, content-optimization, search-engine, keyword-research, technical-seo, local-seo, ecommerce-seo, schema, backlinks]
allowed-tools: [web_search, web_extract, read_file, write_file, terminal]
source: "https://github.com/AgriciDaniel/claude-seo"
metadata:
  hermes:
    molin_owner: 墨增（增长引擎）
---

# claude-seo: Universal SEO Mastery for AI Agents

Orchestrates 19 core sub-skills (+ 3 optional extensions) for comprehensive SEO analysis across all industries (SaaS, local services, e-commerce, publishers, agencies). Adapted from the [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) repository (5,951⭐).

## Quick Reference

| Command | What it does |
|---------|-------------|
| **Audit & Analysis** | |
| `seo audit <url>` | Full website audit with parallel subagent delegation |
| `seo page <url>` | Deep single-page analysis |
| `seo technical <url>` | Technical SEO audit (9 categories) |
| **Content & Schema** | |
| `seo content <url>` | E-E-A-T and content quality analysis |
| `seo schema <url>` | Detect, validate, and generate Schema.org markup |
| `seo sitemap <url or generate>` | Analyze or generate XML sitemaps |
| `seo images <url>` | Image SEO: on-page audit, SERP analysis, file optimization |
| **AI & Modern Search** | |
| `seo geo <url>` | AI Overviews / Generative Engine Optimization |
| `seo sxo <url>` | Search Experience Optimization: page-type analysis, personas |
| `seo cluster <seed-keyword>` | SERP-based semantic clustering and content architecture |
| **Industry-Specific** | |
| `seo local <url>` | Local SEO analysis (GBP, citations, reviews, map pack) |
| `seo maps [command] [args]` | Maps intelligence (geo-grid, GBP audit, reviews, competitors) |
| `seo ecommerce <url>` | E-commerce SEO: product schema, marketplace intelligence |
| `seo programmatic [url|plan]` | Programmatic SEO at scale |
| `seo competitor-pages [url|generate]` | Competitor comparison page generation |
| **International** | |
| `seo hreflang [url]` | Hreflang/i18n SEO audit and generation |
| **Google & Data** | |
| `seo google [command] [url]` | Google SEO APIs (GSC, PageSpeed, CrUX, Indexing, GA4) |
| `seo backlinks <url>` | Backlink profile analysis |
| **Strategic & Monitoring** | |
| `seo plan <business-type>` | Strategic SEO planning |
| `seo drift baseline <url>` | Capture SEO baseline for change monitoring |
| `seo drift compare <url>` | Compare current state to stored baseline |
| `seo drift history <url>` | Show drift history over time |
| **Extensions** | |
| `seo dataforseo [command]` | Live SEO data via DataForSEO |
| `seo image-gen [use-case]` | AI image generation for SEO assets |
| `seo firecrawl [command] <url>` | Full-site crawling and site mapping |

---

## 19 Core Sub-Skills

### 1. SEO Audit (`seo audit <url>`)
Full website audit orchestrating parallel analysis across all relevant sub-skills.
1. **Detect business type** from homepage signals (SaaS, local, e-commerce, publisher, agency, other)
2. **Spawn parallel analysis** across: technical, content, schema, sitemap, performance, visual, GEO, and SXO
3. **Conditionally include**: Google APIs (if credentials detected), local (if local business), backlinks (if APIs detected), cluster (if content strategy signals), e-commerce (if e-commerce detected), drift (if baseline exists)
4. **Collect results** and generate unified report with **SEO Health Score (0-100)**
5. **Prioritized action plan** (Critical → High → Medium → Low)

**Scoring Methodology:**
| Category | Weight |
|----------|--------|
| Technical SEO | 22% |
| Content Quality | 23% |
| On-Page SEO | 20% |
| Schema / Structured Data | 10% |
| Performance (CWV) | 10% |
| AI Search Readiness | 10% |
| Images | 5% |

### 2. Single Page Analysis (`seo page <url>`)
Deep analysis of a single URL covering:
- **On-Page SEO**: Title tag (50-60 chars), meta description (150-160 chars), H1-H6 hierarchy, URL structure, internal/external links
- **Content Quality**: Word count vs page type minimums, readability (Flesch Reading Ease), keyword density (1-3%), E-E-A-T signals
- **Technical Elements**: Canonical tag, meta robots, Open Graph, Twitter Card, hreflang
- **Schema Markup**: Detect all types (JSON-LD preferred), validate required properties, identify opportunities
- **Images**: Alt text, file size thresholds, format recommendations (WebP/AVIF), dimensions, lazy loading
- **Core Web Vitals**: Flag potential LCP/INP/CLS issues (reference only, not measurable from HTML alone)

**Output:**
```
Overall Score: XX/100

On-Page SEO:     XX/100  ████████░░
Content Quality: XX/100  ██████████
Technical:       XX/100  ███████░░░
Schema:          XX/100  █████░░░░░
Images:          XX/100  ████████░░
```

### 3. Technical SEO Audit (`seo technical <url>`)
Audit across 9 categories:

**1. Crawlability**: robots.txt, XML sitemap references, noindex tags, crawl depth, JS rendering, crawl budget
- **AI Crawler Management**: GPTBot, ChatGPT-User, ClaudeBot, PerplexityBot, Bytespider, Google-Extended, CCBot — recommend selective blocking strategies

**2. Indexability**: Canonical tags, duplicate content, thin content, pagination (rel=next/prev), hreflang, index bloat

**3. Security**: HTTPS enforcement, valid SSL, no mixed content, security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Permissions-Policy, Referrer-Policy)

**4. URL Structure**: Short descriptive slugs, lowercase, hyphens, consistent trailing slash, logical hierarchy

**5. Mobile**: Responsive design, viewport meta tag, tap target sizes (48x48px min), font sizes (16px min), no horizontal scroll, no intrusive interstitials

**6. Core Web Vitals**: LCP (<2.5s), INP (<200ms) — **always INP, never FID**, CLS (<0.1), FCP (<1.8s), TTFB (<800ms)

**7. Structured Data**: JSON-LD preferred, valid @context and @type, required properties, no deprecated types

**8. JavaScript Rendering**: SSR vs CSR, critical content server-rendered, lazy loading for non-critical JS, dynamic imports

**9. IndexNow Protocol**: Support recommended for large sites (>10k pages) or frequently changing content

### 4. Content Quality & E-E-A-T (`seo content <url>`)
**E-E-A-T Framework** (updated Sept 2025 QRG):
- **Experience**: Original research, case studies, personal anecdotes, unique data, first-hand photos/videos
- **Expertise**: Author credentials, professional background, technical depth, accurate well-sourced claims
- **Authoritativeness**: External citations, backlinks from authoritative sources, brand mentions, industry recognition
- **Trustworthiness**: Contact info, privacy policy, testimonials, date stamps, transparent corrections, HTTPS

**Content Metrics:**
| Page Type | Min Words |
|-----------|-----------|
| Homepage | 500 |
| Service page | 800 |
| Blog post | 1,500 |
| Product page | 300+ |
| Location page | 500-600 |

**Key notes**: Word count is a topical coverage floor, not a ranking factor. Flesch Reading Ease is a content quality indicator, not a direct ranking factor.

### 5. Schema Markup (`seo schema <url>`)
**Detection**: Scan for JSON-LD (`<script type="application/ld+json">`), Microdata, RDFa. Always recommend JSON-LD.

**Validation**: Check required properties, validate against Google's rich result types, test for common errors (missing @context, invalid @type, wrong data types, placeholder text, relative URLs, invalid date formats).

**Active types** (recommend freely): Organization, LocalBusiness, SoftwareApplication, Product (with Certification markup as of April 2025), ProductGroup, Offer, Service, Article, BlogPosting, NewsArticle, Review, AggregateRating, BreadcrumbList, WebSite, WebPage, Person, ProfilePage, ContactPage, VideoObject, ImageObject, Event, JobPosting, Course, DiscussionForumPosting

**RESTRICTED**: FAQ — ONLY for government and healthcare authority sites (restricted Aug 2023)

**DEPRECATED** (never recommend): HowTo, SpecialAnnouncement, CourseInfo, EstimatedSalary, LearningVideo, ClaimReview, VehicleListing, Practice Problem, Dataset

**Generation**: Identify page type, select appropriate schema type(s), generate valid JSON-LD with required + recommended properties, include only truthful verifiable data.

### 6. Image Optimization (`seo images <url>`)
**Alt Text**: Present on all `<img>` elements, descriptive (10-125 chars), includes relevant keywords naturally

**File Size Thresholds:**
| Category | Target | Warning | Critical |
|----------|--------|---------|----------|
| Thumbnails | <50KB | >100KB | >200KB |
| Content images | <100KB | >200KB | >500KB |
| Hero/banner images | <200KB | >300KB | >700KB |

**Format**: Recommend WebP/AVIF over JPEG/PNG. Use `<picture>` element with format fallbacks.

**Responsive Images**: Use `srcset` with multiple widths, `sizes` attribute, `width` and `height` attributes for aspect ratio (CLS prevention).

**Lazy Loading**: `loading="lazy"` and `decoding="async"` on below-fold images. Use `fetchpriority="high"` on LCP image.

**Sitemap**: Include images in image sitemap extension.

### 7. Sitemap Analysis & Generation (`seo sitemap <url or generate>`)
**Analysis mode**: Valid XML format, URL count <50K per file, all URLs return HTTP 200, `<lastmod>` dates accurate, no deprecated tags (`<priority>` and `<changefreq>` ignored by Google), sitemap referenced in robots.txt.

**Generation mode**: Business type detection, industry template loading, interactive structure planning, quality gates:
- ⚠️ WARNING at 30+ location pages (require 60%+ unique content)
- 🛑 HARD STOP at 50+ location pages (require justification)

**Quality signals**: Sitemap index if >50K URLs, split by content type, no non-canonical/noindexed/redirected URLs, HTTPS only.

### 8. GEO / AI Search Optimization (`seo geo <url>`)
Optimize content for AI Overviews (1.5B users/month), ChatGPT (900M weekly active), Perplexity (500M+ monthly queries).

**Key insight**: Brand mentions correlate **3x more strongly** with AI visibility than backlinks (Ahrefs study of 75,000 brands). Only 11% of domains cited by both ChatGPT and Google AI Overviews for same query.

**Analysis criteria:**
- **Citability (25%)**: Optimal passage length 134-167 words. Clear quotable sentences with specific facts/statistics, self-contained answer blocks, direct answer in first 40-60 words
- **Structural Readability (20%)**: 92% of AI Overview citations from top-10 ranking pages, clean heading hierarchy, question-based headings, short paragraphs (2-4 sentences), tables, lists
- **Authority Signals (20%)**: Wikipedia presence, YouTube mentions, Reddit mentions, LinkedIn presence
- **Technical Access (15%)**: llms.txt, AI crawler access in robots.txt, no JS-gated content
- **Platform-Specific (20%)**: ChatGPT platform-specific optimization, Perplexity platform-specific optimization

**Content formats by AI citation probability**: Definitions (highest), Statistics/Data, Comparisons, How-to Steps, Lists, Quotes.

### 9. Strategic SEO Planning (`seo plan <business-type>`)
**6-step process:**
1. **Discovery**: Business type, target audience, competitors, goals, KPIs
2. **Competitive Analysis**: Top 5 competitors, content strategy, schema usage, keyword gaps, E-E-A-T signals
3. **Architecture Design**: URL hierarchy, content pillars, internal linking strategy
4. **Content Strategy**: Content gaps, page types, publishing cadence, E-E-A-T building plan
5. **Technical Foundation**: Hosting/performance, schema markup plan, CWV targets, AI search readiness
6. **Implementation Roadmap** (4 phases over 12 months):
   - Phase 1: Foundation (weeks 1-4)
   - Phase 2: Expansion (weeks 5-12)
   - Phase 3: Scale (weeks 13-24)
   - Phase 4: Authority (months 7-12)

### 10. Programmatic SEO (`seo programmatic [url|plan]`)
Build and audit SEO pages generated at scale from structured data sources.

**Data Source Assessment**: CSV/JSON files, API endpoints, database queries. Each record must have enough unique attributes for distinct content.

**Template Engine Planning**: Variable injection points (title, H1, body, meta desc, schema), conditional logic, supplementary content. No "mad-libs" patterns.

**URL Pattern Strategy**: `/tools/[name]`, `/[city]/[service]`, `/integrations/[platform]`, `/glossary/[term]`

**Thin Content Safeguards**: Enforce quality gates, penalize location pages with only city name swapped, "Best X for Y" without industry-specific value, AI-generated pages without human review.

### 11. Competitor Comparison Pages (`seo competitor-pages [url|generate]`)
Generate SEO-optimized competitor comparison pages targeting competitive intent keywords.

**Page Types:**
1. **"X vs Y" Comparison**: Direct head-to-head, balanced feature-by-feature analysis, clear verdict
2. **"Alternatives to X"**: List of alternatives with pros/cons, best-for use case
3. **"Best [Category] Tools" Roundups**: Curated list with ranking criteria
4. **Comparison Table Pages**: Feature matrix with multiple products

**Data Accuracy**: All feature claims must be verifiable from public sources. Include pricing accuracy and last-verified date.

### 12. Local SEO (`seo local <url>`)
**Key Stats** (March 2026): GBP signals = 32% of local pack weight, proximity = 55.2% of ranking variance, review signals ~20%, ChatGPT/AI usage for local recommendations = 45%.

**Business Type Detection**: Brick-and-Mortar (physical address, Maps embed), Service Area Business (SAB — areaServed, no street address), Hybrid (both)

**Analysis Checklist:**
- **GBP Optimization**: Business name, categories (primary + secondary, max 10), attributes, description, service list, photos/videos, posts, Q&A, booking links
- **NAP Consistency**: Name, Address, Phone across Google, Bing, Apple Maps, OpenStreetMap, Facebook, Yelp, major citation sites
- **Citation Health**: Tiers (Tier 1: Foursquare, Yelp; Tier 2: Yellowpages, BBB; Tier 3: niche/industry)
- **Review Signals**: Quantity, rating, velocity, sentiment, response rate, keyword themes
- **Local Schema**: LocalBusiness subtype selection, industry-specific properties
- **Multi-Location**: Duplicate GBP management, bulk schema with `parentOrganization`, location-specific pages

### 13. Maps Intelligence (`seo maps [command] [args]`)
Maps platform analysis for local businesses. Three-tier capability detection:
- **Tier 0 (Free)**: Overpass API, Geoapify POI search, Nominatim geocoding, static GBP checklist
- **Tier 1 (DataForSEO)**: Geo-grid rank tracking (7x7), live GBP profile audit, review intelligence
- **Tier 2 (DataForSEO + Google)**: Full coverage including Google Business Profile Performance API

**Commands:**
- `seo maps <url>` — Full maps presence audit
- `seo maps grid <keyword> <location>` — Geo-grid rank scan
- `seo maps reviews <business> <location>` — Cross-platform review intelligence
- `seo maps competitors <keyword> <location>` — Competitor radius mapping
- `seo maps nap <business-name>` — Cross-platform NAP verification
- `seo maps gbp <business> <location>` — GBP completeness audit
- `seo maps schema <business-name>` — Generate LocalBusiness JSON-LD

### 14. E-commerce SEO (`seo ecommerce <url>`)
**Product Page Analysis (no API needed)**:
- Title tag: primary keyword + brand, under 60 chars
- Meta description: keyword + benefit + price trigger
- Product images: high-res, multiple angles, zoom, lifestyle shots
- Product schema: Product type, name, description, SKU, offers, brand, aggregateRating, review

**Product Schema Checklist:**
- [ ] `@type: Product` with all required properties
- [ ] `offers` with price, priceCurrency, availability (use `https://schema.org/InStock` etc.)
- [ ] `brand` with `@type: Brand`
- [ ] `review` or `aggregateRating` if reviews exist
- [ ] `sku` or `mpn` for product identification
- [ ] `image` with absolute URL

**Additional commands** (with DataForSEO): `seo ecommerce products <keyword>` for Google Shopping analysis, `seo ecommerce gaps <domain>` for keyword gap analysis.

### 15. Hreflang & International SEO (`seo hreflang [url]`)
**Validation Checks:**
1. **Self-Referencing Tags**: Every page must include hreflang pointing to itself
2. **Return Tags**: Bidirectional relationships (A→B and B→A)
3. **x-default Tag**: Required fallback for unmatched languages/regions
4. **Language Code Validation**: ISO 639-1 (e.g., `en`, `fr`, `de`, `ja`)
5. **Region Code Validation**: ISO 3166-1 Alpha-2 (e.g., `en-US`, `en-GB`)
6. **Canonical URL Alignment**: Hreflang tags only on canonical URLs
7. **Implementation Format**: Supports HTML `<link>` tags, HTTP headers, and XML sitemap

**Cultural Profiles**: Read `references/cultural-profiles.md` for region-specific SEO considerations, color/imagery preferences, and trust signals.

### 16. Google SEO APIs (`seo google [command] [url]`)
Direct access to Google's SEO data. All APIs free via Google Cloud project.

**Credential Tiers:**
- **Tier 0 (API Key)**: PageSpeed Insights, CrUX, YouTube, NLP
- **Tier 1 (OAuth/SA)**: + Search Console, URL Inspection, Sitemaps, Indexing API
- **Tier 2 (Full)**: + GA4 organic traffic data
- **Tier 3 (Ads)**: + Keyword Planner

**Available Commands:**
- `setup` — Step-by-step Google Cloud project setup
- `pagespeed <url>` — PageSpeed Insights v5 (lab + field data)
- `crux <url>` — CrUX real-user metrics
- `crux-history <url>` — 25-week CrUX trend
- `gsc <url>` — Search Console performance (impressions, clicks, CTR, position)
- `inspect <url>` — URL Inspection (index status, coverage, sitemap)
- `sitemaps <url>` — Sitemap submission status
- `index <url>` — Indexing API v3 (URL submitted notification)
- `ga4 <url>` — GA4 organic traffic trends
- `ga4-pages <url>` — GA4 page-level organic performance
- `keywords <url>` — Keyword Planner (Tier 3)
- `youtube <query>` — YouTube Search API
- `nlp <query>` — Natural Language API (entity extraction, sentiment)
- `report <url>` — Generate professional PDF/HTML SEO report

### 17. Backlink Profile Analysis (`seo backlinks <url>`)
**Data Sources** (in preference order): DataForSEO MCP (premium), Moz API (free), Bing Webmaster (free), Common Crawl (always available), Verification Crawler

**7-Section Analysis Framework:**
1. **Profile Overview**: Total backlinks, referring domains, domain rank, follow ratio
2. **Referring Domains**: Quality distribution (news sites, .edu/.gov, niche authorities, PBNs/spam)
3. **Anchor Text Distribution**: Branded, exact match, partial match, generic, naked URLs, LSI/semantic
4. **Top Linking Pages**: Most linked-to pages on the domain
5. **Competitor Gap**: Compare backlink profiles of up to 3 competitors
6. **Toxic Link Detection**: Flag spammy/tiered/DDoS/parasite links, disavow recommendations
7. **New & Lost Links**: Trend analysis over time

**Scoring:**
| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Referring domains | >100 | 20-100 | <20 |
| Follow ratio | >60% | 40-60% | <40% |

### 18. Semantic Topic Clustering (`seo cluster <seed-keyword>`)
SERP-overlap-driven keyword clustering for content architecture. Contributed by Lutfiya Miller.

**4-Step Workflow:**
1. **Seed Keyword Expansion**: Expand to 30-50 variants via related searches, PAA questions, long-tail modifiers, question mining
2. **SERP Overlap Clustering**: Group keywords by shared top-10 results
3. **Hub-and-Spoke Architecture**: Design pillar pages (2,000+ words, comprehensive intent coverage) + cluster content (1,500+ words, specific sub-topics) with internal link matrix
4. **Interactive Visualization**: Mermaid.js cluster map showing hub/spoke relationships with color-coded phases

### 19. Search Experience Optimization (`seo sxo <url>`)
Bridge between SEO (what Google rewards) and UX (what users need). Contributed by Florian Schmitz.

**Core Insight**: A page can score 95/100 on technical SEO and still fail to rank because it's the **wrong page type** for the keyword.

**Execution Pipeline:**
1. **Target Acquisition**: Fetch and parse the target URL, extract SEO elements
2. **SERP Backwards Analysis**: Classify top 10 organic results by page type (using `references/page-type-taxonomy.md`)
3. **Page-Type Mismatch Detection**: Is the target page the same type as what Google ranks?
4. **User Story Derivation**: Map search intent to user stories
5. **Persona Scoring**: Score page from multiple persona perspectives
6. **IST/SOLL Wireframe**: Generate current state vs ideal state wireframes

### 20. SEO Drift Monitoring (`seo drift <baseline|compare|history> <url>`)
Git for your SEO. Contributed by Dan Colta.

**What it captures**: Title tag, meta description, canonical URL, robots directives, H1-H3 headings, JSON-LD schema, Open Graph tags, Core Web Vitals, HTTP status, HTML content hash (SHA-256), schema content hash

**17 comparison rules across 3 severity levels**: Title changes, description, canonical, noindex toggle, heading changes, schema removal, schema addition, CWV regression, status code changes, content hash changes

### 21. SEO Flow Framework (`seo flow [stage] [url|topic]`)
Evidence-led AI prompts framework: Find → Leverage → Optimize → Win → Local stages. 41 AI prompts organized by stage. CC BY 4.0 licensed.

---

## Industry Detection

Detect business type from homepage signals:
- **SaaS**: pricing page, /features, /integrations, /docs, "free trial", "sign up"
- **Local Service**: phone number, address, service area, "serving [city]", Google Maps embed
- **E-commerce**: /products, /collections, /cart, "add to cart", product schema
- **Publisher**: /blog, /articles, /topics, article schema, author pages, publication dates
- **Agency**: /case-studies, /portfolio, /industries, "our work", client logos

---

## Quality Gates

Read `references/quality-gates.md` for thin content thresholds per page type.

**Hard rules:**
- WARNING at 30+ location pages (enforce 60%+ unique content)
- HARD STOP at 50+ location pages (require user justification)
- Never recommend HowTo schema (deprecated Sept 2023)
- FAQ schema: only government and healthcare sites (Aug 2023 restriction)
- All Core Web Vitals references use INP, never FID

---

## Priority Levels

- **Critical**: Blocks indexing or causes penalties (immediate fix required)
- **High**: Significantly impacts rankings (fix within 1 week)
- **Medium**: Optimization opportunity (fix within 1 month)
- **Low**: Nice to have (backlog)

---

## Extensions

Three optional extension sub-skills are available (not loaded by default):
1. **seo-dataforseo** — Live SEO data via DataForSEO MCP (SERP, keywords, backlinks, local, merchant)
2. **seo-image-gen** — AI image generation for SEO assets via Gemini
3. **seo-firecrawl** — Full-site crawling and site mapping via Firecrawl

---

## Usage with Hermes Agent

### Running an SEO Audit

```
> seo audit https://example.com
```

The agent will:
1. Fetch the homepage to detect business type
2. Run parallel analysis across relevant sub-skills
3. Generate a comprehensive SEO health score report with prioritized actions

### Individual Analysis

```
> seo technical https://example.com
> seo content https://example.com/page
> seo schema https://example.com
> seo backlinks https://example.com
> seo cluster "best seo tools"
```

### Using the Helper Scripts

Python helper scripts are available in the `scripts/` directory of the original repo. Key scripts include:

| Script | Purpose |
|--------|---------|
| `fetch_page.py` | SSRF-safe page fetching |
| `parse_html.py` | HTML SEO element extraction |
| `pagespeed_check.py` | PageSpeed Insights with CrUX data |
| `google_auth.py` | Google API credential detection |
| `backlinks_auth.py` | Backlink API credential detection |
| `moz_api.py` | Moz API metrics |
| `bing_webmaster.py` | Bing Webmaster backlinks |
| `commoncrawl_graph.py` | Common Crawl domain graph |
| `drift_baseline.py` | SEO baseline capture |
| `drift_compare.py` | SEO baseline comparison |
| `drift_history.py` | Drift history |
| `google_report.py` | Professional PDF report generation |
| `gsc_query.py` | Search Console query |
| `ga4_report.py` | GA4 traffic report |
| `keyword_planner.py` | Google Keyword Planner |
| `indexing_notify.py` | Indexing API notification |
| `nlp_analyze.py` | NLP entity/sentiment analysis |
| `youtube_search.py` | YouTube search |
| `dataforseo_merchant.py` | DataForSEO Merchant API |

---

## Reference Files

Load these on-demand as needed:
- `references/cwv-thresholds.md`: Current Core Web Vitals thresholds
- `references/schema-types.md`: All supported schema types with deprecation status
- `references/eeat-framework.md`: E-E-A-T evaluation criteria (Sept 2025 QRG update)
- `references/quality-gates.md`: Content length minimums, uniqueness thresholds
- `references/local-seo-signals.md`: Local ranking factors, review benchmarks, citation tiers
- `references/local-schema-types.md`: LocalBusiness subtypes, industry-specific schema
- `references/backlink-quality.md`: Backlink quality assessment criteria
- `references/free-backlink-sources.md`: Free backlink API setup guides

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Unrecognized command | List available commands from Quick Reference. Suggest closest match. |
| URL unreachable | Report error, suggest verifying URL. Do not guess site content. |
| Sub-skill fails during audit | Report partial results from successful sub-skills. Note which failed. Suggest re-running the failed sub-skill individually. |
| Ambiguous business type | Present top two detected types with supporting signals. Ask user to confirm. |

---

## Credits

Original work by [@AgriciDaniel](https://github.com/AgriciDaniel) (v1.9.6). Community contributions by Lutfiya Miller (clustering), Chris Muller, Florian Schmitz (SXO), Dan Colta (drift), and Matej Marjanovic (e-commerce). Converted for Hermes Agent compatibility.
