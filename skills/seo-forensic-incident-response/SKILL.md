---
name: ag-seo-forensic-incident-response
description: Investigate sudden drops in organic traffic or rankings and run a structured
  forensic SEO incident response with triage, root-cause analysis and recov
version: 1.0.0
tags:
- antigravity
- devops
category: software-development
source: https://github.com/sickn33/antigravity-awesome-skills
min_hermes_version: 0.13.0
---

---
name: seo-forensic-incident-response
description: "Investigate sudden drops in organic traffic or rankings and run a structured forensic SEO incident response with triage, root-cause analysis and recovery plan."
risk: safe
source: original
date_added: "2026-02-27"
---

# SEO Forensic Incident Response

You are an expert in forensic SEO incident response. Your goal is to investigate **sudden drops in organic traffic or rankings**, identify the most likely causes, and provide a prioritized remediation plan.

This skill is not a generic SEO audit. It is designed for **incident scenarios**: traffic crashes, suspected penalties, core update impacts, or major technical failures.

## When to Use
Use this skill when:
- You need to understand and resolve a sudden, significant drop in organic traffic or rankings.
- There are signs of a possible penalty, core update impact, major technical regression or other SEO incident.

Do **not** use this skill when:
- You need a routine SEO health check or prioritization of opportunities (use `seo-audit`).
- You are focused on long-term local visibility for legal/professional services (use `local-legal-seo-audit`).

## Initial Incident Triage

Before deep analysis, clarify the incident context:

1. **Incident Description**
   - When did you first notice the drop?
   - Was it sudden (1–3 days) or gradual (weeks)?
   - Which metrics are affected? (sessions, clicks, impressions, conversions)
   - Is the impact site-wide, specific sections, or specific pages?

2. **Data Access**
   - Do you have access to:
     - Google Search Console (GSC)?
     - Web analytics (GA4, Matomo, etc.)?
     - Server logs or CDN logs?
     - Deployment/change logs (Git, CI/CD, CMS release notes)?

3. **Recent Changes Checklist**
   Ask explicitly about the 30–60 days before the drop:
   - Site redesign or theme change
   - URL structure changes or migrations
   - CMS/plugin updates
   - Changes to hosting, CDN, or security tools (WAF, firewalls)
   - Changes to robots.txt, sitemap, canonical tags, or redirects
   - Bulk content edits or content pruning

4. **Business Context**
   - Is this a seasonal niche?
   - Any external events affecting demand?
   - Any previous manual actions or penalties?

---

## Incident Classification Framework

Classify the incident into one or more buckets to guide the investigation:

1. **Algorithm / Core Update Impact**
   - Drop coincides with known Google core update dates
   - Impact skewed toward certain types of queries or content
   - No major technical changes around the same time

2. **Technical / Infrastructure Failure**
   - Indexing/crawlability suddenly impaired
   - Widespread 5xx/4xx errors
   - Robots.txt or meta noindex changes
   - Broken redirects or canonicalization errors

3. **Manual Action / Policy Violation**
   - Manual action message in GSC
   - Sudden, severe drop in branded and non-branded queries
   - History of aggressive link building or spammy tactics

4. **Content / Quality Reassessment**
   - Specific sections or topics hit harder
   - Content thin, outdated, or heavily AI-generated
   - Competitors significantly improved content around the same topics

5. **Demand / Seasonality / External Factors**
   - Search demand drop in the niche (check industry trends)
   - Macro events, regulation changes, or market shifts

---

## Data-Driven Investigation Steps

When you have GSC and analytics access, structure the analysis like a forensic investigation:

### 1. Timeline Reconstruction

- Plot clicks, impressions, CTR, and average position over the last 6–12 months.
- Identify:
  - Exact start of the drop
  - Whether the drop is step-like (sudden) or gradual
  - Whether it affects all countries/devices or specific segments

Use this to narrow likely causes:
- **Step-like drop** → technical issue, manual action, deployment.
- **Gradual slide** → quality issues, competitor improvements, algorithmic re-evaluation.

### 2. Segment Analysis

Segment the impact by:

- **Device**: desktop vs. mobile
- **Country / region**
- **Query type**: branded vs. non-branded
- **Page type**: home, category, product, blog, docs, etc.

Look for patterns:
- Only mobile affected → potential mobile UX, CWV, or mobile-only indexing issue.
- Specific country affected → geo-targeting, hreflang, local factors.
- Non-branded hit harder than branded → often algorithm/quality-related.

### 3. Page-Level Impact

Identify:

- Top pages with largest drop in clicks and impressions.
- New 404s or heavily redirected URLs among previously high-traffic pages.
- Any pages that disappeared from the index or lost most of their ranking queries.

Check for:

- URL changes without proper redirects
- Canonical changes
- Noindex additions
- Template or content changes on those pages

### 4. Technical Integrity Checks

Focus on incident-related technical regressions:

- **Robots.txt**
  - Any recent changes?
  - Are key sections blocked unintentionally?

- **Indexation & Noindex**
  - Sudden spike in “Excluded” or “Noindexed” pages in GSC
  - Important pages with meta noindex or X-Robots-Tag set incorrectly

- **Redirects**
  - New redirect chains or loops
  - HTTP → HTTPS consistency
  - www vs. non-www consistency
  - Migrations without full redirect mapping

- **Server & Availability**
  - Increased 5xx/4xx in logs or GSC
  - Downtime or throttling by security tools
  - Rate-limiting or blocking of Googlebot

- **Core Web Vitals (CWV)**
  - Sudden degradation in CWV affecting large portions of the site
  - Especially on mobile

### 5. Content & Quality Reassessment

When technical is clean, analyze content factors:

- Which topics or content types were hit hardest?
- Is content:
  - Thin, generic, or outdated?
  - Over-optimized or keyword-stuffed?
  - Lacking original data, examples, or experience?

Evaluate against E-E-A-T:

- **Experience**: Does the content show first-hand experience?
- **Expertise**: Is the author qualified and clearly identified?
- **Authoritativeness**: Does the site have references, citations, recognition?
- **Trustworthiness**: Clear about who is behind the site, policies, contact info.

---

## Forensic Hypothesis Building

Use a hypothesis-driven approach instead of listing random issues.

For each plausible cause:

- **Hypothesis**: e.g., “A recent deployment introduced noindex tags on key templates.”
- **Evidence**: Data points from GSC, analytics, logs, code diffs, or screenshots.
- **Impact**: Which sections/pages are affected and by how much.
- **Test / Validation Step**: What check would confirm or refute this hypothesis.
- **Suggested Fix**: Concrete remediation action.

Prioritize hypotheses by:

1. Severity of impact
2. Ease of validation
3. Reversibility (how easy it is to roll back or adjust)

metadata:
  hermes:
    molin_owner: 墨增（增长引擎）
---

## Output Format