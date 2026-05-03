     1|---
     2|name: pm-prioritization-frameworks
     3|description: "Apply RICE, MoSCoW, Kano, and Value vs Effort prioritization frameworks to feature backlogs."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: prioritization-frameworks
    12|description: "Reference guide to 9 prioritization frameworks with formulas, when-to-use guidance, and templates — RICE, ICE, Kano, MoSCoW, Opportunity Score, and more. Use when selecting a prioritization method, comparing frameworks like RICE vs ICE, or learning how different prioritization approaches work."
    13|---
    14|
    15|## Prioritization Frameworks Reference
    16|
    17|A reference guide to help you select and apply the right prioritization framework for your context.
    18|
    19|### Core Principle
    20|
    21|Never allow customers to design solutions. Prioritize **problems (opportunities)**, not features.
    22|
    23|### Opportunity Score (Dan Olsen, *The Lean Product Playbook*)
    24|
    25|The recommended framework for prioritizing customer problems.
    26|
    27|Survey customers on **Importance** and **Satisfaction** for each need (normalize to 0–1 scale).
    28|
    29|Three related formulas:
    30|- **Current value** = Importance × Satisfaction
    31|- **Opportunity Score** = Importance × (1 − Satisfaction)
    32|- **Customer value created** = Importance × (S2 − S1), where S1 = satisfaction before, S2 = satisfaction after
    33|
    34|High Importance + low Satisfaction = highest Opportunity Score = best opportunities. Plot on an Importance vs Satisfaction chart — upper-left quadrant is the sweet spot. Prioritizes customer problems, not solutions.
    35|
    36|### ICE Framework
    37|
    38|Useful for prioritizing initiatives and ideas. Considers not only value but also risk and economic factors.
    39|
    40|- **I** (Impact) = Opportunity Score × Number of Customers affected
    41|- **C** (Confidence) = How confident are we? (1-10). Accounts for risk.
    42|- **E** (Ease) = How easy is it to implement? (1-10). Accounts for economic factors.
    43|
    44|**Score** = I × C × E. Higher = prioritize first.
    45|
    46|### RICE Framework
    47|
    48|Splits ICE's Impact into two separate factors. Useful for larger teams that need more granularity.
    49|
    50|- **R** (Reach) = Number of customers affected
    51|- **I** (Impact) = Opportunity Score (value per customer)
    52|- **C** (Confidence) = How confident are we? (0-100%)
    53|- **E** (Effort) = How much effort to implement? (person-months)
    54|
    55|**Score** = (R × I × C) / E
    56|
    57|### 9 Frameworks Overview
    58|
    59|| Framework | Best For | Key Insight |
    60||-----------|----------|-------------|
    61|| Eisenhower Matrix | Personal tasks | Urgent vs Important — for individual PM task management |
    62|| Impact vs Effort | Tasks/initiatives | Simple 2×2 — quick triage, not rigorous for strategic decisions |
    63|| Risk vs Reward | Initiatives | Like Impact vs Effort but accounts for uncertainty |
    64|| **Opportunity Score** | Customer problems | **Recommended.** Importance × (1 − Satisfaction). Normalize to 0–1. |
    65|| Kano Model | Understanding expectations | Must-be, Performance, Attractive, Indifferent, Reverse. For understanding, not prioritizing. |
    66|| Weighted Decision Matrix | Multi-factor decisions | Assign weights to criteria, score each option. Useful for stakeholder buy-in. |
    67|| **ICE** | Ideas/initiatives | Impact × Confidence × Ease. Recommended for quick prioritization. |
    68|| **RICE** | Ideas at scale | (Reach × Impact × Confidence) / Effort. Adds Reach to ICE. |
    69|| MoSCoW | Requirements | Must/Should/Could/Won't. Caution: project management origin. |
    70|
    71|### Templates
    72|
    73|- [Opportunity Score intro (PDF)](https://drive.google.com/file/d/1ENbYPmk1i1AKO7UnfyTuULL5GucTVufW/view)
    74|- [Importance vs Satisfaction Template — Dan Olsen (Google Slides)](https://docs.google.com/presentation/d/1jg-LuF_3QHsf6f1nE1f98i4C0aulnRNMOO1jftgti8M/edit#slide=id.g796641d975_0_3)
    75|- [ICE Template (Google Sheets)](https://docs.google.com/spreadsheets/d/1LUfnsPolhZgm7X2oij-7EUe0CJT-Dwr-/edit?usp=share_link&ouid=111307342557889008106&rtpof=true&sd=true)
    76|- [RICE Template (Google Sheets)](https://docs.google.com/spreadsheets/d/1S-6QpyOz5MCrV7B67LUWdZkAzn38Eahv/edit?usp=sharing&ouid=111307342557889008106&rtpof=true&sd=true)
    77|
    78|---
    79|
    80|### Further Reading
    81|
    82|- [The Product Management Frameworks Compendium + Templates](https://www.productcompass.pm/p/the-product-frameworks-compendium)
    83|- [Kano Model: How to Delight Your Customers Without Becoming a Feature Factory](https://www.productcompass.pm/p/kano-model-how-to-delight-your-customers)
    84|- [Continuous Product Discovery Masterclass (CPDM)](https://www.productcompass.pm/p/cpdm) (video course)
    85|