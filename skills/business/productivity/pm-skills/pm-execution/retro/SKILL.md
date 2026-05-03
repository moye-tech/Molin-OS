     1|---
     2|name: pm-retro
     3|description: "Facilitate sprint retrospectives — capture what went well, what didn't, and actionable improvements."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: retro
    12|description: "Facilitate a structured sprint retrospective — what went well, what didn't, and prioritized action items with owners and deadlines. Use when running a retrospective, reflecting on a sprint, creating action items from team feedback, or learning how to run effective retros."
    13|---
    14|
    15|## Sprint Retrospective Facilitator
    16|
    17|Run a structured retrospective that surfaces insights and produces actionable improvements.
    18|
    19|### Context
    20|
    21|You are facilitating a retrospective for **$ARGUMENTS**.
    22|
    23|If the user provides files (sprint data, velocity charts, team feedback, or previous retro notes), read them first.
    24|
    25|### Instructions
    26|
    27|1. **Choose a retro format** based on context (or let the user pick):
    28|
    29|   **Format A — Start / Stop / Continue**:
    30|   - **Start**: What should we begin doing?
    31|   - **Stop**: What should we stop doing?
    32|   - **Continue**: What's working well that we should keep?
    33|
    34|   **Format B — 4Ls (Liked / Learned / Lacked / Longed For)**:
    35|   - **Liked**: What did the team enjoy?
    36|   - **Learned**: What new knowledge was gained?
    37|   - **Lacked**: What was missing?
    38|   - **Longed For**: What do we wish we had?
    39|
    40|   **Format C — Sailboat**:
    41|   - **Wind (propels us)**: What's driving us forward?
    42|   - **Anchor (holds us back)**: What's slowing us down?
    43|   - **Rocks (risks)**: What dangers lie ahead?
    44|   - **Island (goal)**: Where are we trying to get to?
    45|
    46|2. **If the user provides raw feedback** (e.g., sticky notes, survey responses, Slack messages):
    47|   - Group similar items into themes
    48|   - Identify the most frequently mentioned topics
    49|   - Note sentiment patterns (frustration, energy, confusion)
    50|
    51|3. **Analyze the sprint performance**:
    52|   - Sprint goal: achieved or not?
    53|   - Velocity vs. commitment (over-committed? under-committed?)
    54|   - Blockers encountered and how they were resolved
    55|   - Collaboration patterns (what worked, what didn't)
    56|
    57|4. **Generate prioritized action items**:
    58|
    59|   | Priority | Action Item | Owner | Deadline | Success Metric |
    60|   |---|---|---|---|---|
    61|   | 1 | [Specific, actionable improvement] | [Name/Role] | [Date] | [How we'll know it worked] |
    62|
    63|   - Limit to 2-3 action items (more won't get done)
    64|   - Each must be specific, assignable, and measurable
    65|   - Reference previous retro actions if available — were they completed?
    66|
    67|5. **Create the retro summary**:
    68|   ```
    69|   ## Sprint [X] Retrospective — [Date]
    70|
    71|   ### Sprint Performance
    72|   - Goal: [Achieved / Partially / Missed]
    73|   - Committed: [X pts] | Completed: [Y pts]
    74|
    75|   ### Key Themes
    76|   1. [Theme] — [summary]
    77|
    78|   ### Action Items
    79|   1. [Action] — [Owner] — [By date]
    80|
    81|   ### Carry-over from Last Retro
    82|   - [Previous action] — [Status: Done / In Progress / Not Started]
    83|   ```
    84|
    85|Save as markdown. Keep the tone constructive — the goal is improvement, not blame.
    86|