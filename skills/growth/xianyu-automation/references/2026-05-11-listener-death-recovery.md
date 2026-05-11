# 2026-05-11 Listener Death & Recovery

## Timeline

| Time | Event |
|------|-------|
| May 10 22:16 | Last ws.log entry before listener died |
| May 10 22:16 ~ May 11 10:47 | Listener dead (~12.5h gap) |
| May 11 10:45 | Cron kicked off, detected dead listener |
| May 11 10:47 | Restarted successfully |

## Root Cause: Working Directory Dependency

First restart attempt from `~/.hermes/xianyu_bot/` failed:
```
FileNotFoundError: [Errno 2] No such file or directory: 'static/goofish_js_version_2.js'
```

`goofish_utils.py` at `/Users/moye/Molin-OS/molib/xianyu/utils/goofish_utils.py` line 14:
```python
xianyu_js = execjs.compile(open(r'static/goofish_js_version_2.js', 'r', encoding='utf-8').read())
```

The file exists at `/Users/moye/Molin-OS/molib/xianyu/static/goofish_js_version_2.js` but the relative path broke when CWD was `~/.hermes/xianyu_bot/`.

**Fix:** `cd /Users/moye/Molin-OS/molib/xianyu && python /Users/moye/.hermes/xianyu_bot/ws_listener.py`

## SSL EOF Error Pattern (Recurring)

The Xianyu API at `h5api.m.goofish.com` frequently terminates SSL connections with `UNEXPECTED_EOF_WHILE_READING`. Example from ws.log:

```
WebSocket连接断开，5秒后重连: HTTPSConnectionPool(host='h5api.m.goofish.com', port=443): 
Max retries exceeded ... (Caused by SSLError(SSLEOFError(8, 
'[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1010)')))
```

The listener auto-recovers by reconnecting after 5s. This is platform-side noise — do NOT treat as a local config issue.

## State Detection Checklist (For Cron)

Do NOT trust `state.json` fields when checking liveness:

```
state.json.ws_connected: true   ← STALE, don't trust
state.json.ws_listener_pid: 44223 ← STALE, process dead

kill -0 44223 → "No such process" ← use THIS
tail -1 ws.log → "2026-05-10 22:16:43" ← 12.5h ago, dead
```

Both `kill -0` and ws.log timestamp must independently confirm the listener is alive.

## Successful Restart Log (2026-05-11 10:47)

```
2026-05-11 10:47:20,296 [xianyu-ws] Loaded 17 cookie fields
2026-05-11 10:47:20,333 [xianyu-ws] Verifying token with SSL fix...
2026-05-11 10:47:20,536 [xianyu-ws] Token OK
2026-05-11 10:47:20,536 [xianyu-ws] Starting WebSocket listener...
2026-05-11 10:47:20,570 [xianyu-ws] 正在连接闲鱼WebSocket...
2026-05-11 10:47:20,701 [xianyu-ws] ✅ WebSocket 已连接
2026-05-11 10:47:20,958 [xianyu-ws] 初始化完成: None
```

New PID: 79907. Token verified. WS connected. Listener ready.
