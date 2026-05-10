# Xianyu Cron Report template

Every cron run saves its report to `~/.hermes/state/xianyu_cron_report_latest.json`.

## JSON Schema

```json
{
  "job": "闲鱼消息检测",
  "cron_id": "<uuid>",
  "schedule": "15,45 9-21 * * *",
  "executed_at": "YYYY-MM-DD HH:MM:SS",
  "status": "healthy | degraded | down",
  "api_connected": true,
  "token_valid": true,
  "ws_listener_running": false,
  "daemon_alive": false,
  "new_messages": 0,
  "messages_processed": 0,
  "auto_replies_sent": 0,
  "deal_signals": 0,
  "escalations": 0,
  "blockers": ["human-readable blocker descriptions"],
  "blocker_count": 0,
  "notes": {
    "api_error": "error detail if applicable",
    "token_status": "token check result",
    "message_polling": "explanation of why message count is 0",
    "cookies_status": "cookies freshness note"
  },
  "resolved_since_last": [
    {"item": "issue name", "detail": "what was fixed"}
  ],
  "infra_initialized": true,
  "state_dir": "~/.hermes/xianyu_bot/",
  "last_run": "previous run timestamp",
  "next_run": "next expected run"
}
```

## Status semantics

| status | Meaning | Card emoji |
|:-------|:--------|:-----------|
| `healthy` | API connected, WS running, no blockers | 🐟 |
| `degraded` | API connected but WS not running, or API failed but infra intact | 🐟 |
| `down` | API failed AND critical infra missing (no cookies, no bot file) | ❌ |

## Blocker priority

1. WebSocket 监听未运行 → `real-time messages blocked`
2. API Token 获取失败 → `health check blocked`
3. Cookies 文件缺失 → `authentication blocked`
4. Python 依赖缺失 → `execution blocked`
