     1|---
     2|name: ag-cqrs-implementation
     3|description: "Implement Command Query Responsibility Segregation for scalable architectures. Use when separating read and write models, optimizing query performance"
     4|version: 1.0.0
     5|tags: [antigravity, general]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: cqrs-implementation
    12|description: "Implement Command Query Responsibility Segregation for scalable architectures. Use when separating read and write models, optimizing query performance, or building event-sourced systems."
    13|risk: unknown
    14|source: community
    15|date_added: "2026-02-27"
    16|---
    17|
    18|# CQRS Implementation
    19|
    20|Comprehensive guide to implementing CQRS (Command Query Responsibility Segregation) patterns.
    21|
    22|## Use this skill when
    23|
    24|- Separating read and write concerns
    25|- Scaling reads independently from writes
    26|- Building event-sourced systems
    27|- Optimizing complex query scenarios
    28|- Different read/write data models are needed
    29|- High-performance reporting is required
    30|
    31|## Do not use this skill when
    32|
    33|- The domain is simple and CRUD is sufficient
    34|- You cannot operate separate read/write models
    35|- Strong immediate consistency is required everywhere
    36|
    37|## Instructions
    38|
    39|- Identify read/write workloads and consistency needs.
    40|- Define command and query models with clear boundaries.
    41|- Implement read model projections and synchronization.
    42|- Validate performance, recovery, and failure modes.
    43|- If detailed patterns are required, open `resources/implementation-playbook.md`.
    44|
    45|## Resources
    46|
    47|- `resources/implementation-playbook.md` for detailed CQRS patterns and templates.
    48|
    49|## Limitations
    50|- Use this skill only when the task clearly matches the scope described above.
    51|- Do not treat the output as a substitute for environment-specific validation, testing, or expert review.
    52|- Stop and ask for clarification if required inputs, permissions, safety boundaries, or success criteria are missing.
    53|