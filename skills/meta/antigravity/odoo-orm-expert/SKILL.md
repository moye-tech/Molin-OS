     1|---
     2|name: ag-odoo-orm-expert
     3|description: "Master Odoo ORM patterns: search, browse, create, write, domain filters, computed fields, and performance-safe query techniques."
     4|version: 1.0.0
     5|tags: [antigravity, general]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: odoo-orm-expert
    12|description: "Master Odoo ORM patterns: search, browse, create, write, domain filters, computed fields, and performance-safe query techniques."
    13|risk: safe
    14|source: "self"
    15|---
    16|
    17|# Odoo ORM Expert
    18|
    19|## Overview
    20|
    21|This skill teaches you Odoo's Object Relational Mapper (ORM) in depth. It covers reading/writing records, building domain filters, working with relational fields, and avoiding common performance pitfalls like N+1 queries.
    22|
    23|## When to Use This Skill
    24|
    25|- Writing `search()`, `browse()`, `create()`, `write()`, or `unlink()` calls.
    26|- Building complex domain filters for views or server actions.
    27|- Implementing computed, stored, and related fields.
    28|- Debugging slow queries or optimizing bulk operations.
    29|
    30|## How It Works
    31|
    32|1. **Activate**: Mention `@odoo-orm-expert` and describe what data operation you need.
    33|2. **Get Code**: Receive correct, idiomatic Odoo ORM code with explanations.
    34|3. **Optimize**: Ask for performance review on existing ORM code.
    35|
    36|## Examples
    37|
    38|### Example 1: Search with Domain Filters
    39|
    40|```python
    41|# Find all confirmed sale orders for a specific customer, created this year
    42|import datetime
    43|
    44|start_of_year = datetime.date.today().replace(month=1, day=1).strftime('%Y-%m-%d')
    45|
    46|orders = self.env['sale.order'].search([
    47|    ('partner_id', '=', partner_id),
    48|    ('state', '=', 'sale'),
    49|    ('date_order', '>=', start_of_year),
    50|], order='date_order desc', limit=50)
    51|
    52|# Note: pass dates as 'YYYY-MM-DD' strings in domains,
    53|# NOT as fields.Date objects — the ORM serializes them correctly.
    54|```
    55|
    56|### Example 2: Computed Field
    57|
    58|```python
    59|total_order_count = fields.Integer(
    60|    string='Total Orders',
    61|    compute='_compute_total_order_count',
    62|    store=True
    63|)
    64|
    65|@api.depends('sale_order_ids')
    66|def _compute_total_order_count(self):
    67|    for record in self:
    68|        record.total_order_count = len(record.sale_order_ids)
    69|```
    70|
    71|### Example 3: Safe Bulk Write (avoid N+1)
    72|
    73|```python
    74|# ✅ GOOD: One query for all records
    75|partners = self.env['res.partner'].search([('country_id', '=', False)])
    76|partners.write({'country_id': self.env.ref('base.us').id})
    77|
    78|# ❌ BAD: Triggers a separate query per record
    79|for partner in partners:
    80|    partner.country_id = self.env.ref('base.us').id
    81|```
    82|
    83|## Best Practices
    84|
    85|- ✅ **Do:** Use `mapped()`, `filtered()`, and `sorted()` on recordsets instead of Python loops.
    86|- ✅ **Do:** Use `sudo()` sparingly and only when you understand the security implications.
    87|- ✅ **Do:** Prefer `search_count()` over `len(search(...))` when you only need a count.
    88|- ✅ **Do:** Use `with_context(...)` to pass context values cleanly rather than modifying `self.env.context` directly.
    89|- ❌ **Don't:** Call `search()` inside a loop — this is the #1 Odoo performance killer.
    90|- ❌ **Don't:** Use raw SQL unless absolutely necessary; use ORM for all standard operations.
    91|- ❌ **Don't:** Pass Python `datetime`/`date` objects directly into domain tuples — always stringify them as `'YYYY-MM-DD'`.
    92|
    93|## Limitations
    94|
    95|- Does not cover **`cr.execute()` raw SQL** patterns in depth — use the Odoo performance tuner skill for SQL-level optimization.
    96|- **Stored computed fields** can cause significant write overhead at scale; this skill does not cover partitioning strategies.
    97|- Does not cover **transient models** (`models.TransientModel`) or wizard patterns.
    98|- ORM behavior can differ slightly between Odoo SaaS and On-Premise due to config overrides.
    99|