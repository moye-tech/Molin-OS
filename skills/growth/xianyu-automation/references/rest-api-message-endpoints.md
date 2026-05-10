# Xianyu REST API Message Endpoints — Confirmed Dead Ends

2026-05-10 discovery: All REST endpoints for message retrieval return 404 on the Xianyu (goofish) platform.

## Tested Endpoints (all 404)

```
https://www.goofish.com/imweb/chat/unreadMsgCount  → 404
https://www.goofish.com/imweb/im/sessionList        → 404
https://www.goofish.com/imweb/im/session/list       → 404
https://www.goofish.com/imweb/chat/sessions         → 404
https://api.goofish.com/im/session/list             → 404
https://www.goofish.com/imweb/im/unread             → 404
```

## Conclusion

Message retrieval on Xianyu is strictly WebSocket-only. The `xianyu_bot.py` WebSocket listener connects to `wss://wss-goofish.dingtalk.com/` and receives messages via `/s/chat` events. There is no REST API workaround.

## Impact on Cron Jobs

Cron-based polling (every 30 min) cannot detect new messages. The cron `xianyu_bot.py cron` command is limited to:

1. Token validation (API connectivity check)
2. Reading state.json for cumulative statistics
3. Reporting whether the WS listener daemon is running

For real-time message detection and auto-reply, the WebSocket listener MUST be running as a long-lived daemon process.
