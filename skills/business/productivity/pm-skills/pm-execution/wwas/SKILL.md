     1|---
     2|name: pm-wwas
     3|description: "What Would Awesome Success look like — define the ideal outcome before planning execution."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: wwas
    12|description: "Create product backlog items in Why-What-Acceptance format — independent, valuable, testable items with strategic context. Use when writing structured backlog items, breaking features into work items, or using the WWA format."
    13|---
    14|# Why-What-Acceptance (WWA)
    15|
    16|Create product backlog items in Why-What-Acceptance format. Produces independent, valuable, testable items with strategic context.
    17|
    18|**Use when:** Writing backlog items, creating product increments, breaking features into work items, or communicating strategic intent to teams.
    19|
    20|**Arguments:**
    21|- `$PRODUCT`: The product or system name
    22|- `$FEATURE`: The new feature or capability
    23|- `$DESIGN`: Link to design files (Figma, Miro, etc.)
    24|- `$ASSUMPTIONS`: Key assumptions and strategic context
    25|
    26|## Step-by-Step Process
    27|
    28|1. **Define the strategic Why** - Connect work to business and team objectives
    29|2. **Describe the What** - Keep descriptions concise, reference designs
    30|3. **Write Acceptance Criteria** - High-level, not detailed specifications
    31|4. **Ensure independence** - Items can be developed in any order
    32|5. **Keep items negotiable** - Invite team conversation, not constraints
    33|6. **Make items valuable** - Each delivers measurable user or business value
    34|7. **Ensure testability** - Outcomes are observable and verifiable
    35|8. **Size appropriately** - Small enough for one sprint estimate
    36|
    37|## Item Template
    38|
    39|**Title:** [What will be delivered]
    40|
    41|**Why:** [1-2 sentences connecting to strategic context and team objectives]
    42|
    43|**What:** [Short description and design link. 1-2 paragraphs maximum. A reminder of discussion, not detailed specification.]
    44|
    45|**Acceptance Criteria:**
    46|- [Observable outcome 1]
    47|- [Observable outcome 2]
    48|- [Observable outcome 3]
    49|- [Observable outcome 4]
    50|
    51|## Example WWA Item
    52|
    53|**Title:** Implement Real-Time Spending Tracker
    54|
    55|**Why:** Users need immediate feedback on spending to make conscious budget decisions. This directly supports our goal to improve financial awareness and reduce overspending.
    56|
    57|**What:** Add a real-time spending tracker that updates as users log expenses. The tracker displays their current week's spending against their set budget. Designs available in [Figma link]. This is a reminder of our discussions - detailed specifications will emerge during development conversations with the team.
    58|
    59|**Acceptance Criteria:**
    60|- Spending totals update within 2 seconds of logging an expense
    61|- Budget progress is visually indicated with a progress bar
    62|- Users can see remaining budget amount at a glance
    63|- System handles multiple expense categories correctly
    64|
    65|## Output Deliverables
    66|
    67|- Complete set of backlog items for the feature
    68|- Each item includes Why, What, and Acceptance Criteria sections
    69|- Items are independent and deliverable in any order
    70|- Items are sized for estimation and completion in one sprint
    71|- Strategic context is clear for team decision-making
    72|- Design references are included for implementation guidance
    73|
    74|---
    75|
    76|### Further Reading
    77|
    78|- [How to Write User Stories: The Ultimate Guide](https://www.productcompass.pm/p/how-to-write-user-stories)
    79|