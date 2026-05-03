     1|---
     2|name: pm-sprint-plan
     3|description: "Plan and structure sprints with story point estimation, capacity planning, and velocity tracking."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: sprint-plan
    12|description: "Plan a sprint with capacity estimation, story selection, dependency mapping, and risk identification. Use when preparing for sprint planning, estimating team capacity, selecting stories, or balancing sprint scope against velocity."
    13|---
    14|
    15|## Sprint Planning
    16|
    17|Plan a sprint by estimating team capacity, selecting and sequencing stories, and identifying risks.
    18|
    19|### Context
    20|
    21|You are helping plan a sprint for **$ARGUMENTS**.
    22|
    23|If the user provides files (backlogs, velocity data, team rosters, or previous sprint reports), read them first.
    24|
    25|### Instructions
    26|
    27|1. **Estimate team capacity**:
    28|   - Number of team members and their availability (PTO, meetings, on-call)
    29|   - Historical velocity (average story points per sprint from last 3 sprints)
    30|   - Capacity buffer: reserve 15-20% for unexpected work, bugs, and tech debt
    31|   - Calculate available capacity in story points or ideal hours
    32|
    33|2. **Review and select stories**:
    34|   - Pull from the prioritized backlog (highest priority first)
    35|   - Verify each story meets the Definition of Ready (clear AC, estimated, no blockers)
    36|   - Flag stories that need refinement before committing
    37|   - Stop adding stories when capacity is reached
    38|
    39|3. **Map dependencies**:
    40|   - Identify stories that depend on other stories or external teams
    41|   - Sequence dependent stories appropriately
    42|   - Flag external dependencies and owners
    43|   - Identify the critical path
    44|
    45|4. **Identify risks and mitigations**:
    46|   - Stories with high uncertainty or complexity
    47|   - External dependencies that could slip
    48|   - Knowledge concentration (only one person can do it)
    49|   - Suggest mitigations for each risk
    50|
    51|5. **Create the sprint plan summary**:
    52|
    53|   ```
    54|   Sprint Goal: [One sentence describing what success looks like]
    55|   Duration: [2 weeks / 1 week / etc.]
    56|   Team Capacity: [X story points]
    57|   Committed Stories: [Y story points across Z stories]
    58|   Buffer: [remaining capacity]
    59|
    60|   Stories:
    61|   1. [Story title] — [points] — [owner] — [dependencies]
    62|   ...
    63|
    64|   Risks:
    65|   - [Risk] → [Mitigation]
    66|   ```
    67|
    68|6. **Define the sprint goal**: A single, clear sentence that captures the sprint's primary value delivery.
    69|
    70|Think step by step. Save as markdown.
    71|
    72|---
    73|
    74|### Further Reading
    75|
    76|- [Product Owner vs Product Manager: What's the difference?](https://www.productcompass.pm/p/product-manager-vs-product-owner)
    77|