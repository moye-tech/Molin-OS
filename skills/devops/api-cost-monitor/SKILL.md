---
name: api-cost-monitor
description: Monitor AI provider API balances and daily consumption. Check DeepSeek/DashScope balances, run cost reports, alert when thresholds breached. Use for daily cron cost checks.
version: 1.0.0
tags:
- api
- cost
- monitoring
- cron
metadata:
  hermes:
    molin_owner: CEO
    cron_safe: true
---

# API Cost Monitor

Monitor AI provider balances and daily consumption. Designed for daily cron execution.

## Trigger

When tasked with checking API balances, daily consumption, or cost monitoring for AI providers (DeepSeek, DashScope, etc.).

## Provider Balance Check

### DeepSeek
- Endpoint: `https://api.deepseek.com/user/balance`
- Auth: `Authorization: Bearer $DEEPSEEK_API_KEY` (from `~/.hermes/.env`)
- Response format: `{"is_available":true,"balance_infos":[{"currency":"CNY","total_balance":"XX.XX","granted_balance":"0.00","topped_up_balance":"XX.XX"}]}`
- Alert threshold: < ¥50

### DashScope (阿里百炼)
- Balance endpoints all return empty for low-usage accounts (likely free-tier accounts with no billing relationship)
- Endpoints tried: `/api/v1/balance`, `/api/v1/billing/balance`, `/api/v1/billing/overview`, `/api/v1/bills`
- All returned empty 200 responses
- When empty, treat as "balance unknown, usage negligible" — do NOT raise alert
- API key: `DASHSCOPE_API_KEY` from `~/.hermes/.env`

## Consumption Report

Use `python -m molib cost report` for consumption data.

Key fields:
- `daily`: today's spend, calls, budget, usage_pct
- `by_provider`: cumulative per-provider spend and call count (all-time, not daily)
- `by_model`: cumulative per-model spend
- `history`: array of daily entries with date, spent, calls

Pitfalls:
- `--date YYYY-MM-DD` flag does NOT filter — returns same full dataset
- `by_provider` totals are all-time cumulative, not daily
- To get yesterday's consumption: sum all `history` entries for that date
- Daily budget default: ¥100

## Thresholds

- Balance alert: any provider < ¥50 → T4 alert card
- Consumption alert: yesterday > 80% of daily budget → include alert in daily report
- If both balance is low AND spending is high: escalate urgency

## Output Format

Use `cron-output-formatter` skill for final output. The cron card template with ⚠️ alerts section handles both balance warnings and consumption overages.

## Reference

- [DeepSeek balance API response example](references/deepseek-balance-response.json)
