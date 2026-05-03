     1|---
     2|name: pm-user-stories
     3|description: "Create user stories with acceptance criteria following INVEST principles. Map stories to epics and personas."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: user-stories
    12|description: "Create user stories following the 3 C's (Card, Conversation, Confirmation) and INVEST criteria with descriptions, design links, and acceptance criteria. Use when writing user stories, breaking down features into backlog items, or defining acceptance criteria."
    13|---
    14|# User Stories
    15|
    16|Create user stories following the 3 C's (Card, Conversation, Confirmation) and INVEST criteria. Generates stories with descriptions, design links, and acceptance criteria.
    17|
    18|**Use when:** Writing user stories, breaking down features into stories, creating backlog items, or defining acceptance criteria.
    19|
    20|**Arguments:**
    21|- `$PRODUCT`: The product or system name
    22|- `$FEATURE`: The new feature to break into stories
    23|- `$DESIGN`: Link to design files (Figma, Miro, etc.)
    24|- `$ASSUMPTIONS`: Key assumptions or context
    25|
    26|## Step-by-Step Process
    27|
    28|1. **Analyze the feature** based on provided design and context
    29|2. **Identify user roles** and distinct user journeys
    30|3. **Apply 3 C's framework:**
    31|   - Card: Simple title and one-liner
    32|   - Conversation: Detailed discussion of intent
    33|   - Confirmation: Clear acceptance criteria
    34|4. **Respect INVEST criteria:** Independent, Negotiable, Valuable, Estimable, Small, Testable
    35|5. **Use plain language** a primary school graduate can understand
    36|6. **Link to design files** for visual reference
    37|7. **Output user stories** in structured format
    38|
    39|## Story Template
    40|
    41|**Title:** [Feature name]
    42|
    43|**Description:** As a [user role], I want to [action], so that [benefit].
    44|
    45|**Design:** [Link to design files]
    46|
    47|**Acceptance Criteria:**
    48|1. [Clear, testable criterion]
    49|2. [Observable behavior]
    50|3. [System validates correctly]
    51|4. [Edge case handling]
    52|5. [Performance or accessibility consideration]
    53|6. [Integration point]
    54|
    55|## Example User Story
    56|
    57|**Title:** Recently Viewed Section
    58|
    59|**Description:** As an Online Shopper, I want to see a 'Recently viewed' section on the product page to easily revisit items I considered.
    60|
    61|**Design:** [Figma link]
    62|
    63|**Acceptance Criteria:**
    64|1. The 'Recently viewed' section is displayed at the bottom of the product page for every user who has previously viewed at least 1 product.
    65|2. It is not displayed for users visiting the first product page of their session.
    66|3. The current product itself is excluded from the displayed items.
    67|4. The section showcases product cards or thumbnails with images, titles, and prices.
    68|5. Each product card indicates when it was viewed (e.g., 'Viewed 5 minutes ago').
    69|6. Clicking on a product card leads the user to the corresponding product page.
    70|
    71|## Output Deliverables
    72|
    73|- Complete set of user stories for the feature
    74|- Each story includes title, description, design link, and 4-6 acceptance criteria
    75|- Stories are independent and can be developed in any order
    76|- Stories are sized for one sprint cycle
    77|- Stories reference related design documentation
    78|
    79|---
    80|
    81|### Further Reading
    82|
    83|- [How to Write User Stories: The Ultimate Guide](https://www.productcompass.pm/p/how-to-write-user-stories)
    84|