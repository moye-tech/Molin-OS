     1|---
     2|name: pm-test-scenarios
     3|description: "Generate comprehensive test scenarios covering happy path, edge cases, error states, and performance boundaries."
     4|version: 1.0.0
     5|tags: [pm, product-management, execution]
     6|category: productivity
     7|source: https://github.com/phuryn/pm-skills
     8|---
     9|
    10|---
    11|name: test-scenarios
    12|description: "Create comprehensive test scenarios from user stories with test objectives, starting conditions, user roles, step-by-step actions, and expected outcomes. Use when writing QA test cases, creating test plans, defining acceptance tests, or preparing for feature validation."
    13|---
    14|# Test Scenarios
    15|
    16|Create comprehensive test scenarios from user stories with test objectives, starting conditions, user roles, step-by-step test actions, and expected outcomes.
    17|
    18|**Use when:** Writing QA test cases, creating test plans, defining acceptance test scenarios, or validating user story implementations.
    19|
    20|**Arguments:**
    21|- `$PRODUCT`: The product or system name
    22|- `$USER_STORY`: The user story to test (title and acceptance criteria)
    23|- `$CONTEXT`: Additional testing context or constraints
    24|
    25|## Step-by-Step Process
    26|
    27|1. **Review the user story** and acceptance criteria
    28|2. **Define test objectives** - What specific behavior to validate
    29|3. **Establish starting conditions** - System state, data setup, configurations
    30|4. **Identify user roles** - Who performs the test actions
    31|5. **Create test steps** - Break down interactions step-by-step
    32|6. **Define expected outcomes** - Observable results after each step
    33|7. **Consider edge cases** - Invalid inputs, boundary conditions
    34|8. **Output detailed test scenarios** - Ready for QA execution
    35|
    36|## Scenario Template
    37|
    38|**Test Scenario:** [Clear scenario name]
    39|
    40|**Test Objective:** [What this test validates]
    41|
    42|**Starting Conditions:**
    43|- [System state required]
    44|- [Data or configuration needed]
    45|- [User setup or permissions]
    46|
    47|**User Role:** [Who performs the test]
    48|
    49|**Test Steps:**
    50|1. [First action and its expected result]
    51|2. [Second action and observable outcome]
    52|3. [Third action and system behavior]
    53|4. [Completion action and final state]
    54|
    55|**Expected Outcomes:**
    56|- [Observable result 1]
    57|- [Observable result 2]
    58|- [Observable result 3]
    59|
    60|## Example Test Scenario
    61|
    62|**Test Scenario:** View Recently Viewed Products on Product Page
    63|
    64|**Test Objective:** Verify that the 'Recently viewed' section displays correctly and excludes the current product.
    65|
    66|**Starting Conditions:**
    67|- User is logged in or has browser history enabled
    68|- User has viewed at least 2 products in the current session
    69|- User is now on a product page different from previously viewed items
    70|
    71|**User Role:** Online Shopper
    72|
    73|**Test Steps:**
    74|1. Navigate to any product page → Section should appear at bottom with previously viewed items
    75|2. Scroll to bottom of page → "Recently viewed" section is visible with product cards
    76|3. Verify product thumbnails → Images, titles, and prices are displayed correctly
    77|4. Check current product → Current product is NOT in the recently viewed list
    78|5. Click on a product card → User navigates to the corresponding product page
    79|
    80|**Expected Outcomes:**
    81|- Recently viewed section appears only after viewing at least 1 prior product
    82|- Section displays 4-8 product cards with complete information
    83|- Current product is excluded from the list
    84|- Each card shows "Viewed X minutes/hours ago" timestamp
    85|- Clicking cards navigates to correct product pages
    86|- Performance: Section loads within 2 seconds
    87|
    88|## Output Deliverables
    89|
    90|- Comprehensive test scenarios for each acceptance criterion
    91|- Clear test objectives aligned with user story intent
    92|- Detailed step-by-step test actions
    93|- Observable expected outcomes after each step
    94|- Edge case and error scenario coverage
    95|- Ready for QA team execution and documentation
    96|