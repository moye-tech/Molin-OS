     1|---
     2|name: pm-release-notes
     3|description: "Generate professional release notes from commits, PRs, and changelogs. Structure by feature, fix, and breaking change categories."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: release-notes
    12|description: "Generate user-facing release notes from tickets, PRDs, or changelogs. Creates clear, engaging summaries organized by category (new features, improvements, fixes). Use when writing release notes, creating changelogs, announcing product updates, or summarizing what shipped."
    13|---
    14|
    15|## Release Notes Generator
    16|
    17|Transform technical tickets, PRDs, or internal changelogs into polished, user-facing release notes.
    18|
    19|### Context
    20|
    21|You are writing release notes for **$ARGUMENTS**.
    22|
    23|If the user provides files (JIRA exports, Linear tickets, PRDs, Git logs, or internal changelogs), read them first. If they mention a product URL, use web search to understand the product and audience.
    24|
    25|### Instructions
    26|
    27|1. **Gather raw material**: Read all provided tickets, changelogs, or descriptions. Extract:
    28|   - What changed (feature, improvement, or fix)
    29|   - Who it affects (which user segment)
    30|   - Why it matters (the user benefit)
    31|
    32|2. **Categorize changes**:
    33|   - **New Features**: Entirely new capabilities
    34|   - **Improvements**: Enhancements to existing features
    35|   - **Bug Fixes**: Issues resolved
    36|   - **Breaking Changes**: Anything that requires user action (migrations, API changes)
    37|   - **Deprecations**: Features being sunset
    38|
    39|3. **Write each entry** following these principles:
    40|   - Lead with the user benefit, not the technical change
    41|   - Use plain language — avoid jargon, internal codenames, or ticket numbers
    42|   - Keep each entry to 1-3 sentences
    43|   - Include visuals or screenshots if the user provides them
    44|
    45|   **Example transformations**:
    46|   - Technical: "Implemented Redis caching layer for dashboard API endpoints"
    47|   - User-facing: "Dashboards now load up to 3× faster, so you spend less time waiting and more time analyzing."
    48|
    49|   - Technical: "Fixed race condition in concurrent checkout flow"
    50|   - User-facing: "Fixed an issue where some orders could fail during high-traffic periods."
    51|
    52|4. **Structure the release notes**:
    53|
    54|   ```
    55|   # [Product Name] — [Version / Date]
    56|
    57|   ## New Features
    58|   - **[Feature name]**: [1-2 sentence description of what it does and why it matters]
    59|
    60|   ## Improvements
    61|   - **[Area]**: [What got better and how it helps]
    62|
    63|   ## Bug Fixes
    64|   - Fixed [issue description in user terms]
    65|
    66|   ## Breaking Changes (if any)
    67|   - **Action required**: [What users need to do]
    68|   ```
    69|
    70|5. **Adjust tone** to match the product's voice — professional for B2B, friendly for consumer, developer-focused for APIs.
    71|
    72|Save as a markdown document. If the user wants HTML or another format, convert accordingly.
    73|