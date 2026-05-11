# Cron Patrol Example — 2026-05-11 13:46

## Raw State Before Patrol
- ws_listener: DOWN (PID 79910 killed at 12:48, token_invalid)
- ws.log: last modified 3454 seconds ago (stale ~57 min)
- state.json: api_status="token_invalid", ws_connected=false
- activity.log: last entry 12:48 — "需人工: 重新登录获取cookies"

## Patrol Actions
1. Token check: `xianyu_check.py` → `{"token_ok": true}` (server congestion cleared)
2. Process check: no ws_listener process found
3. Restart: `cd /Users/moye/Molin-OS/molib/xianyu && python ws_listener.py` (background=true)
4. Verify: ws.log shows "Token OK" → "✅ WebSocket 已连接" → "初始化完成"
5. Update state.json, activity.log, cron_report_latest.json

## Patrol Card Output
```
📦 闲鱼消息巡检 · 2026-05-11 13:46
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 本轮结果
• API Token：有效
• WebSocket：运行中 (PID 87583，13:46 连接成功)
• 新消息：0 条 · 自动回复：0 条
• 成交信号：0 个 · 待审批：0 项

⚠️ 需关注
• 12:46-13:45 Token失效（闲鱼服务器拥挤），监听中断约1小时，现已自动恢复
• 中断期间如有买家消息未实时回复 — 建议手动检查

✅ 已就绪
• WebSocket 监听已重启
• Token 重新验证通过

🔜 下次执行：14:15
```

## Key Lesson
- "被挤爆啦" errors are transient server-side congestion, not auth issues
- Token check script may return `token_ok=true` even when ws_listener's token verification failed earlier
- Always re-check token before assuming cookies need refresh
- Working directory for ws_listener.py is critical — must be Molin-OS/molib/xianyu/
