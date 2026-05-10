# Xianyu Cron Report Schema

File: `~/.hermes/state/xianyu_cron_report_latest.json`

```json
{
  "job": "闲鱼消息检测",
  "cron_id": "1a6bd56a00cc",
  "schedule": "15,45 9-21 * * *",
  "executed_at": "2026-05-10 18:50:00",
  "status": "operational|degraded|offline",
  "api_connected": true,
  "token_valid": true,
  "ws_listener_running": true,
  "ws_listener_pid": 33898,
  "daemon_alive": false,
  "new_messages": 0,
  "messages_processed": 0,
  "auto_replies_sent": 0,
  "deal_signals": 0,
  "escalations": 0,
  "blockers": ["description of active blockers"],
  "blocker_count": 0,
  "notes": {
    "ws_listener": "运行中 (Python 3.12, PID 33898)",
    "ssl_fix": "description",
    "last_good_run": "timestamp",
    "message_polling": "description"
  },
  "resolved_since_last": ["item1", "item2"],
  "infra_initialized": true,
  "state_dir": "~/.hermes/xianyu_bot/",
  "last_run": "timestamp",
  "next_run": "next scheduled time"
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `operational` (all green), `degraded` (some issues), `offline` (nothing working) |
| `api_connected` | bool | Whether goofish API was reachable (token endpoint responded) |
| `token_valid` | bool | Whether the active token returned SUCCESS |
| `ws_listener_running` | bool | Whether ws_listener.py process is alive |
| `ws_listener_pid` | int | Process ID of the ws_listener, or 0 if not running |
| `daemon_alive` | bool | Whether the enhanced daemon marker exists |
| `new_messages` | int | Messages since last cron run (from state diff or ws.log) |
| `blockers` | [string] | Active issues preventing full operation |
| `resolved_since_last` | [string] | Issues that were fixed since previous cron run |

## Patrol Card Template

The cron output follows `feishu-message-formatter` cron template:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🐟 闲鱼状态巡检 · 日期 时间
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 本轮结果
• 新消息：N 条
• 自动回复：N 条
• 成交信号：N 条
• 待审批：N 条

⚠️ 需关注
• 事项 — 建议

✅ 已就绪/正常运行
• 状态项

🔜 下次巡检：时间

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Rules:
- No Markdown (no #, **, | tables, [links](), `code`)
- Pure text + emoji + ━━━ separators
- Skip ⚠️ section if nothing to report
- Max 20 lines total
