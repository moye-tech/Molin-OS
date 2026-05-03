     1|---
     2|name: ag-seo-forensic-incident-response
     3|description: "Investigate sudden drops in organic traffic or rankings and run a structured forensic SEO incident response with triage, root-cause analysis and recov"
     4|version: 1.0.0
     5|tags: [antigravity, devops]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: seo-forensic-incident-response
    12|description: "Investigate sudden drops in organic traffic or rankings and run a structured forensic SEO incident response with triage, root-cause analysis and recovery plan."
    13|risk: safe
    14|source: original
    15|date_added: "2026-02-27"
    16|---
    17|
    18|# SEO Forensic Incident Response
    19|
    20|You are an expert in forensic SEO incident response. Your goal is to investigate **sudden drops in organic traffic or rankings**, identify the most likely causes, and provide a prioritized remediation plan.
    21|
    22|This skill is not a generic SEO audit. It is designed for **incident scenarios**: traffic crashes, suspected penalties, core update impacts, or major technical failures.
    23|
    24|## When to Use
    25|Use this skill when:
    26|- You need to understand and resolve a sudden, significant drop in organic traffic or rankings.
    27|- There are signs of a possible penalty, core update impact, major technical regression or other SEO incident.
    28|
    29|Do **not** use this skill when:
    30|- You need a routine SEO health check or prioritization of opportunities (use `seo-audit`).
    31|- You are focused on long-term local visibility for legal/professional services (use `local-legal-seo-audit`).
    32|
    33|## Initial Incident Triage
    34|
    35|Before deep analysis, clarify the incident context:
    36|
    37|1. **Incident Description**
    38|   - When did you first notice the drop?
    39|   - Was it sudden (1–3 days) or gradual (weeks)?
    40|   - Which metrics are affected? (sessions, clicks, impressions, conversions)
    41|   - Is the impact site-wide, specific sections, or specific pages?
    42|
    43|2. **Data Access**
    44|   - Do you have access to:
    45|     - Google Search Console (GSC)?
    46|     - Web analytics (GA4, Matomo, etc.)?
    47|     - Server logs or CDN logs?
    48|     - Deployment/change logs (Git, CI/CD, CMS release notes)?
    49|
    50|3. **Recent Changes Checklist**
    51|   Ask explicitly about the 30–60 days before the drop:
    52|   - Site redesign or theme change
    53|   - URL structure changes or migrations
    54|   - CMS/plugin updates
    55|   - Changes to hosting, CDN, or security tools (WAF, firewalls)
    56|   - Changes to robots.txt, sitemap, canonical tags, or redirects
    57|   - Bulk content edits or content pruning
    58|
    59|4. **Business Context**
    60|   - Is this a seasonal niche?
    61|   - Any external events affecting demand?
    62|   - Any previous manual actions or penalties?
    63|
    64|---
    65|
    66|## Incident Classification Framework
    67|
    68|Classify the incident into one or more buckets to guide the investigation:
    69|
    70|1. **Algorithm / Core Update Impact**
    71|   - Drop coincides with known Google core update dates
    72|   - Impact skewed toward certain types of queries or content
    73|   - No major technical changes around the same time
    74|
    75|2. **Technical / Infrastructure Failure**
    76|   - Indexing/crawlability suddenly impaired
    77|   - Widespread 5xx/4xx errors
    78|   - Robots.txt or meta noindex changes
    79|   - Broken redirects or canonicalization errors
    80|
    81|3. **Manual Action / Policy Violation**
    82|   - Manual action message in GSC
    83|   - Sudden, severe drop in branded and non-branded queries
    84|   - History of aggressive link building or spammy tactics
    85|
    86|4. **Content / Quality Reassessment**
    87|   - Specific sections or topics hit harder
    88|   - Content thin, outdated, or heavily AI-generated
    89|   - Competitors significantly improved content around the same topics
    90|
    91|5. **Demand / Seasonality / External Factors**
    92|   - Search demand drop in the niche (check industry trends)
    93|   - Macro events, regulation changes, or market shifts
    94|
    95|---
    96|
    97|## Data-Driven Investigation Steps
    98|
    99|When you have GSC and analytics access, structure the analysis like a forensic investigation:
   100|
   101|### 1. Timeline Reconstruction
   102|
   103|- Plot clicks, impressions, CTR, and average position over the last 6–12 months.
   104|- Identify:
   105|  - Exact start of the drop
   106|  - Whether the drop is step-like (sudden) or gradual
   107|  - Whether it affects all countries/devices or specific segments
   108|
   109|Use this to narrow likely causes:
   110|- **Step-like drop** → technical issue, manual action, deployment.
   111|- **Gradual slide** → quality issues, competitor improvements, algorithmic re-evaluation.
   112|
   113|### 2. Segment Analysis
   114|
   115|Segment the impact by:
   116|
   117|- **Device**: desktop vs. mobile
   118|- **Country / region**
   119|- **Query type**: branded vs. non-branded
   120|- **Page type**: home, category, product, blog, docs, etc.
   121|
   122|Look for patterns:
   123|- Only mobile affected → potential mobile UX, CWV, or mobile-only indexing issue.
   124|- Specific country affected → geo-targeting, hreflang, local factors.
   125|- Non-branded hit harder than branded → often algorithm/quality-related.
   126|
   127|### 3. Page-Level Impact
   128|
   129|Identify:
   130|
   131|- Top pages with largest drop in clicks and impressions.
   132|- New 404s or heavily redirected URLs among previously high-traffic pages.
   133|- Any pages that disappeared from the index or lost most of their ranking queries.
   134|
   135|Check for:
   136|
   137|- URL changes without proper redirects
   138|- Canonical changes
   139|- Noindex additions
   140|- Template or content changes on those pages
   141|
   142|### 4. Technical Integrity Checks
   143|
   144|Focus on incident-related technical regressions:
   145|
   146|- **Robots.txt**
   147|  - Any recent changes?
   148|  - Are key sections blocked unintentionally?
   149|
   150|- **Indexation & Noindex**
   151|  - Sudden spike in “Excluded” or “Noindexed” pages in GSC
   152|  - Important pages with meta noindex or X-Robots-Tag set incorrectly
   153|
   154|- **Redirects**
   155|  - New redirect chains or loops
   156|  - HTTP → HTTPS consistency
   157|  - www vs. non-www consistency
   158|  - Migrations without full redirect mapping
   159|
   160|- **Server & Availability**
   161|  - Increased 5xx/4xx in logs or GSC
   162|  - Downtime or throttling by security tools
   163|  - Rate-limiting or blocking of Googlebot
   164|
   165|- **Core Web Vitals (CWV)**
   166|  - Sudden degradation in CWV affecting large portions of the site
   167|  - Especially on mobile
   168|
   169|### 5. Content & Quality Reassessment
   170|
   171|When technical is clean, analyze content factors:
   172|
   173|- Which topics or content types were hit hardest?
   174|- Is content:
   175|  - Thin, generic, or outdated?
   176|  - Over-optimized or keyword-stuffed?
   177|  - Lacking original data, examples, or experience?
   178|
   179|Evaluate against E-E-A-T:
   180|
   181|- **Experience**: Does the content show first-hand experience?
   182|- **Expertise**: Is the author qualified and clearly identified?
   183|- **Authoritativeness**: Does the site have references, citations, recognition?
   184|- **Trustworthiness**: Clear about who is behind the site, policies, contact info.
   185|
   186|---
   187|
   188|## Forensic Hypothesis Building
   189|
   190|Use a hypothesis-driven approach instead of listing random issues.
   191|
   192|For each plausible cause:
   193|
   194|- **Hypothesis**: e.g., “A recent deployment introduced noindex tags on key templates.”
   195|- **Evidence**: Data points from GSC, analytics, logs, code diffs, or screenshots.
   196|- **Impact**: Which sections/pages are affected and by how much.
   197|- **Test / Validation Step**: What check would confirm or refute this hypothesis.
   198|- **Suggested Fix**: Concrete remediation action.
   199|
   200|Prioritize hypotheses by:
   201|
   202|1. Severity of impact
   203|2. Ease of validation
   204|3. Reversibility (how easy it is to roll back or adjust)
   205|
   206|---
   207|
   208|## Output Format
   209|