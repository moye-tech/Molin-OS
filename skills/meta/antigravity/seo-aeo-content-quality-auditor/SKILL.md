     1|---
     2|name: ag-seo-aeo-content-quality-auditor
     3|description: "Audits content for SEO and AEO performance with scored reports, severity-ranked fix lists, and projected scores after fixes. Activate when the user wa"
     4|version: 1.0.0
     5|tags: [antigravity, planning]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: seo-aeo-content-quality-auditor
    12|description: "Audits content for SEO and AEO performance with scored reports, severity-ranked fix lists, and projected scores after fixes. Activate when the user wants to audit, review, or score content for SEO or AEO compliance."
    13|risk: safe
    14|source: community
    15|date_added: "2026-04-01"
    16|---
    17|
    18|# SEO-AEO Content Quality Auditor
    19|
    20|## Overview
    21|
    22|Runs a dual SEO + AEO audit on any landing page or blog post. Produces an overall score, SEO score, AEO score, and readability score — each out of 100 — with severity-ranked issue lists (Critical / Warning / Polish), exact fix instructions for every issue, and projected scores after all fixes are applied.
    23|
    24|Part of the [SEO-AEO Engine](https://github.com/mrprewsh/seo-aeo-engine).
    25|
    26|## When to Use This Skill
    27|
    28|- Use when auditing a landing page or blog post before publishing
    29|- Use after the blog-writer or landing-page-writer skill outputs content
    30|- Use when diagnosing why existing content is underperforming in search
    31|- Use when you need a scored, actionable SEO and AEO report
    32|
    33|## How It Works
    34|
    35|### Step 1: Run SEO Checks
    36|Verify keyword density, H1/H2/H3 structure, meta elements, word count, sentence length, and paragraph density. Flag every issue with its severity.
    37|
    38|### Step 2: Run AEO Checks
    39|Check for TL;DR block, definition sentence, FAQ section (minimum 4 entries), bullet and numbered lists, comparison table, and extractable direct answers. Score each signal as found or missing.
    40|
    41|### Step 3: Run Readability Checks
    42|Check passive voice ratio, transition word presence, wall-of-text paragraphs, subheading frequency, and reading level.
    43|
    44|### Step 4: Score and Prioritise
    45|Calculate three scores out of 100. Sort all issues into Critical (fix before publishing), Important (fix soon), and Polish (optional improvements). Generate projected scores after all fixes are applied.
    46|
    47|## Scoring System
    48|
    49|| Score | Status | Label |
    50||-------|--------|-------|
    51|| 85–100 | ✅ Pass | Strong |
    52|| 70–84 | ⚠️ Warn | Acceptable |
    53|| 50–69 | 🔶 Weak | Needs work |
    54|| 0–49 | ❌ Fail | Do not publish |
    55|
    56|## Examples
    57|
    58|### Example: Audit Summary
    59|Overall Score:    84/100  ⚠️ Acceptable
    60|SEO Score:        88/100  ✅ Pass
    61|AEO Score:        74/100  ⚠️ Acceptable
    62|Readability:      91/100  ✅ Pass
    63|Verdict: Strong SEO foundation. AEO needs a TL;DR block
    64|and one more FAQ entry before publishing.
    65|🔴 Critical (fix before publishing):
    66|
    67|AEO: No TL;DR block found
    68|Fix: Add a 2–3 sentence direct-answer block in a
    69|blockquote immediately after the H1.
    70|
    71|🟡 Important (fix soon):
    72|2. AEO: FAQ has 3 entries — minimum is 4
    73|Fix: Add one more FAQ entry using a secondary keyword
    74|as the question.
    75|Projected score after fixes: 93/100 ✅
    76|
    77|## Best Practices
    78|
    79|- ✅ **Do:** Fix all Critical issues before publishing — they block AEO extraction
    80|- ✅ **Do:** Use the projected score to prioritise which fixes to make first
    81|- ✅ **Do:** Run the audit on both the landing page and blog post in the same session
    82|- ❌ **Don't:** Publish content scoring below 50/100 overall
    83|- ❌ **Don't:** Ignore AEO warnings — they directly affect AI engine citation probability
    84|
    85|## Common Pitfalls
    86|
    87|- **Problem:** SEO score is high but AEO score is low
    88|  **Solution:** Traditional SEO tools miss AEO signals entirely. Run the AEO checklist separately and treat it as equally important.
    89|
    90|- **Problem:** Fix list is long and overwhelming
    91|  **Solution:** Work through Critical issues only first, re-run the audit, then tackle Important issues.
    92|
    93|## Related Skills
    94|
    95|- `@seo-aeo-blog-writer` — produces the content this skill audits
    96|- `@seo-aeo-landing-page-writer` — produces landing pages this skill audits
    97|- `@seo-aeo-schema-generator` — uses audit output to determine schema priorities
    98|
    99|## Additional Resources
   100|
   101|- [SEO-AEO Engine Repository](https://github.com/mrprewsh/seo-aeo-engine)
   102|- [Full Content Quality Auditor SKILL.md](https://github.com/mrprewsh/seo-aeo-engine/blob/main/.agent/skills/content-quality-auditor/SKILL.md)
   103|
   104|## Limitations
   105|- Use this skill only when the task clearly matches the scope described above.
   106|- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
   107|- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
   108|