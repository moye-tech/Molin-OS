---
name: molin-bases
description: Create and query Molin-OS data tables (.mbase files) with filters, formulas, and views. Use when working with structured data, creating database-like views, or when the user mentions bases, tables, filters, or formulas in Molin-OS.
version: 1.0.0
min_hermes_version: 0.13.0
dependencies: [molin-cli, molin-markdown]
tags: [molin-os, database, tables, views, data]
category: data
---

# Molin Bases Skill

Create and edit Molin Base files (.mbase) — structured data views for Molin-OS. 对标 Obsidian Bases (.base files)。

## File Format

Molin Base files use `.mbase` extension with valid YAML:

```yaml
# Schema definition
schema:
  columns:
    - name: id
      type: string
    - name: title
      type: string
    - name: status
      type: select
      options: [draft, review, published]
    - name: priority
      type: number
    - name: created_at
      type: date
    - name: tags
      type: tags

# Filters
filters:
  and:
    - 'status != "archived"'
  or: []

# Formulas
formulas:
  is_overdue: 'created_at < today() - 7'
  priority_label: 'if(priority > 3, "High", "Normal")'

# Views
views:
  - type: table
    name: "Active Items"
    columns: [title, status, priority, created_at]
    sort:
      field: priority
      direction: DESC
    filters:
      and:
        - 'status != "done"'
    limit: 50

  - type: cards
    name: "By Status"
    groupBy: status
    columns: [title, priority_label]

  - type: kanban
    name: "Workflow"
    groupBy: status
    columns: [title, tags]
```

## Data Sources

Molin Bases can query from:
- **skills** — ~/.hermes/skills/ (via MQL indexer)
- **notes** — Obsidian vault Markdown files
- **experiences** — ExperienceVault entries
- **memory** — Hermes persistent memory
- **custom** — JSON/CSV files in ~/.hermes/data/

## Query Integration

Bases integrate with MQL:

```bash
# Create a base from MQL query
python -m molib base create --name "Engineering Skills" \
  --query "FROM skills WHERE category = 'engineering' SORT BY name ASC"

# Query a base
python -m molib base query --name "Engineering Skills" \
  --filter "priority > 3"
```

## View Types

| Type | Description | Use Case |
|------|-------------|----------|
| table | Row/column grid | Data browsing, exports |
| cards | Card layout | Visual browsing, galleries |
| kanban | Board with columns | Workflow management |
| list | Simple list | Quick reference |
| calendar | Calendar view | Date-based planning |
| chart | Chart visualization | Analytics, trends |

## Filter Syntax

```yaml
# Single filter
filters: 'status == "done"'

# AND — all conditions
filters:
  and:
    - 'status == "active"'
    - 'priority > 3'

# OR — any condition
filters:
  or:
    - 'tag == "urgent"'
    - 'priority == 5'

# NOT — exclude
filters:
  not:
    - 'status == "archived"'

# Nested
filters:
  or:
    - and:
        - 'category == "engineering"'
        - 'priority > 3'
    - 'tag == "critical"'
```

## Formula Functions

| Function | Description |
|----------|-------------|
| `today()` | Current date |
| `now()` | Current datetime |
| `if(cond, a, b)` | Conditional |
| `count(list)` | Count items |
| `sum(list)` | Sum values |
| `avg(list)` | Average |
| `min(list)` / `max(list)` | Min/max |
| `contains(text, sub)` | String contains |
| `length(text)` | String length |

## Python API

```python
from molib.shared.data.bases import MolinBase

# Create
base = MolinBase("my-base")
base.set_schema([...])
base.add_view("table", "Main View", ...)
base.save()

# Query
results = base.query("status == 'active'")
for row in results:
    print(row["title"])

# Load from MQL
base = MolinBase.from_mql(
    "FROM skills WHERE category = 'tools'"
)
```

## Workflow

1. **Define schema** — what columns/fields does your data have?
2. **Add source data** — import from MQL, JSON, CSV, or manual
3. **Configure views** — table, cards, kanban, calendar
4. **Add filters** — narrow down what's visible
5. **Create formulas** — computed fields
6. **Save** — writes to `~/.hermes/bases/<name>.mbase`
7. **Verify** — query the base to confirm results
