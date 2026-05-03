     1|---
     2|name: ag-kpi-dashboard-design
     3|description: "Comprehensive patterns for designing effective Key Performance Indicator (KPI) dashboards that drive business decisions."
     4|version: 1.0.0
     5|tags: [antigravity, devops]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: kpi-dashboard-design
    12|description: "Comprehensive patterns for designing effective Key Performance Indicator (KPI) dashboards that drive business decisions."
    13|risk: unknown
    14|source: community
    15|date_added: "2026-02-27"
    16|---
    17|
    18|# KPI Dashboard Design
    19|
    20|Comprehensive patterns for designing effective Key Performance Indicator (KPI) dashboards that drive business decisions.
    21|
    22|## Do not use this skill when
    23|
    24|- The task is unrelated to kpi dashboard design
    25|- You need a different domain or tool outside this scope
    26|
    27|## Instructions
    28|
    29|- Clarify goals, constraints, and required inputs.
    30|- Apply relevant best practices and validate outcomes.
    31|- Provide actionable steps and verification.
    32|- If detailed examples are required, open `resources/implementation-playbook.md`.
    33|
    34|## Use this skill when
    35|
    36|- Designing executive dashboards
    37|- Selecting meaningful KPIs
    38|- Building real-time monitoring displays
    39|- Creating department-specific metrics views
    40|- Improving existing dashboard layouts
    41|- Establishing metric governance
    42|
    43|## Core Concepts
    44|
    45|### 1. KPI Framework
    46|
    47|| Level           | Focus            | Update Frequency  | Audience   |
    48|| --------------- | ---------------- | ----------------- | ---------- |
    49|| **Strategic**   | Long-term goals  | Monthly/Quarterly | Executives |
    50|| **Tactical**    | Department goals | Weekly/Monthly    | Managers   |
    51|| **Operational** | Day-to-day       | Real-time/Daily   | Teams      |
    52|
    53|### 2. SMART KPIs
    54|
    55|```
    56|Specific: Clear definition
    57|Measurable: Quantifiable
    58|Achievable: Realistic targets
    59|Relevant: Aligned to goals
    60|Time-bound: Defined period
    61|```
    62|
    63|### 3. Dashboard Hierarchy
    64|
    65|```
    66|├── Executive Summary (1 page)
    67|│   ├── 4-6 headline KPIs
    68|│   ├── Trend indicators
    69|│   └── Key alerts
    70|├── Department Views
    71|│   ├── Sales Dashboard
    72|│   ├── Marketing Dashboard
    73|│   ├── Operations Dashboard
    74|│   └── Finance Dashboard
    75|└── Detailed Drilldowns
    76|    ├── Individual metrics
    77|    └── Root cause analysis
    78|```
    79|
    80|## Common KPIs by Department
    81|
    82|### Sales KPIs
    83|
    84|```yaml
    85|Revenue Metrics:
    86|  - Monthly Recurring Revenue (MRR)
    87|  - Annual Recurring Revenue (ARR)
    88|  - Average Revenue Per User (ARPU)
    89|  - Revenue Growth Rate
    90|
    91|Pipeline Metrics:
    92|  - Sales Pipeline Value
    93|  - Win Rate
    94|  - Average Deal Size
    95|  - Sales Cycle Length
    96|
    97|Activity Metrics:
    98|  - Calls/Emails per Rep
    99|  - Demos Scheduled
   100|  - Proposals Sent
   101|  - Close Rate
   102|```
   103|
   104|### Marketing KPIs
   105|
   106|```yaml
   107|Acquisition:
   108|  - Cost Per Acquisition (CPA)
   109|  - Customer Acquisition Cost (CAC)
   110|  - Lead Volume
   111|  - Marketing Qualified Leads (MQL)
   112|
   113|Engagement:
   114|  - Website Traffic
   115|  - Conversion Rate
   116|  - Email Open/Click Rate
   117|  - Social Engagement
   118|
   119|ROI:
   120|  - Marketing ROI
   121|  - Campaign Performance
   122|  - Channel Attribution
   123|  - CAC Payback Period
   124|```
   125|
   126|### Product KPIs
   127|
   128|```yaml
   129|Usage:
   130|  - Daily/Monthly Active Users (DAU/MAU)
   131|  - Session Duration
   132|  - Feature Adoption Rate
   133|  - Stickiness (DAU/MAU)
   134|
   135|Quality:
   136|  - Net Promoter Score (NPS)
   137|  - Customer Satisfaction (CSAT)
   138|  - Bug/Issue Count
   139|  - Time to Resolution
   140|
   141|Growth:
   142|  - User Growth Rate
   143|  - Activation Rate
   144|  - Retention Rate
   145|  - Churn Rate
   146|```
   147|
   148|### Finance KPIs
   149|
   150|```yaml
   151|Profitability:
   152|  - Gross Margin
   153|  - Net Profit Margin
   154|  - EBITDA
   155|  - Operating Margin
   156|
   157|Liquidity:
   158|  - Current Ratio
   159|  - Quick Ratio
   160|  - Cash Flow
   161|  - Working Capital
   162|
   163|Efficiency:
   164|  - Revenue per Employee
   165|  - Operating Expense Ratio
   166|  - Days Sales Outstanding
   167|  - Inventory Turnover
   168|```
   169|
   170|## Dashboard Layout Patterns
   171|
   172|### Pattern 1: Executive Summary
   173|
   174|```
   175|┌─────────────────────────────────────────────────────────────┐
   176|│  EXECUTIVE DASHBOARD                        [Date Range ▼]  │
   177|├─────────────┬─────────────┬─────────────┬─────────────────┤
   178|│   REVENUE   │   PROFIT    │  CUSTOMERS  │    NPS SCORE    │
   179|│   $2.4M     │    $450K    │    12,450   │       72        │
   180|│   ▲ 12%     │    ▲ 8%     │    ▲ 15%    │     ▲ 5pts     │
   181|├─────────────┴─────────────┴─────────────┴─────────────────┤
   182|│                                                             │
   183|│  Revenue Trend                    │  Revenue by Product     │
   184|│  ┌───────────────────────┐       │  ┌──────────────────┐   │
   185|│  │    /\    /\          │       │  │ ████████ 45%     │   │
   186|│  │   /  \  /  \    /\   │       │  │ ██████   32%     │   │
   187|│  │  /    \/    \  /  \  │       │  │ ████     18%     │   │
   188|│  │ /            \/    \ │       │  │ ██        5%     │   │
   189|│  └───────────────────────┘       │  └──────────────────┘   │
   190|│                                                             │
   191|├─────────────────────────────────────────────────────────────┤
   192|│  🔴 Alert: Churn rate exceeded threshold (>5%)              │
   193|│  🟡 Warning: Support ticket volume 20% above average        │
   194|└─────────────────────────────────────────────────────────────┘
   195|```
   196|
   197|### Pattern 2: SaaS Metrics Dashboard
   198|
   199|```
   200|┌─────────────────────────────────────────────────────────────┐
   201|│  SAAS METRICS                     Jan 2024  [Monthly ▼]     │
   202|├──────────────────────┬──────────────────────────────────────┤
   203|│  ┌────────────────┐  │  MRR GROWTH                          │
   204|│  │      MRR       │  │  ┌────────────────────────────────┐  │
   205|│  │    $125,000    │  │  │                          /──   │  │
   206|│  │     ▲ 8%       │  │  │                    /────/      │  │
   207|│  └────────────────┘  │  │              /────/            │  │
   208|│  ┌────────────────┐  │  │        /────/                  │  │
   209|│  │      ARR       │  │  │   /────/                       │  │
   210|