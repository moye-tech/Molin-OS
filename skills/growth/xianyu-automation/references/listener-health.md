# Listener Health & Restart — Operational Notes

Captured 2026-05-10 after the WebSocket listener (ws_listener.py PID 33898) died silently between
18:37–20:45 and needed manual restart.

## Detection

The listener daemon can exit without logging a crash. Detect death via:

1. **Process check:** `ps aux | grep ws_listener | grep -v grep` — returns empty if dead
2. **Log staleness:** `tail -1 ~/.hermes/xianyu_bot/ws.log` — last entry older than 5 minutes = dead or stuck

## Restart Command (EXACT — do not vary)

```bash
/Users/moye/Molin-OS/molib/xianyu/.venv/bin/python3 \
  /Users/moye/.hermes/xianyu_bot/ws_listener.py \
  > /dev/null 2>&1 &
```

Workdir: `/Users/moye/Molin-OS/molib/xianyu`

## Python Interpreter Pitfall

Only the xianyu venv works. Others crash:

| Interpreter | Result | Why |
|:------------|:-------|:----|
| `/Users/moye/Molin-OS/molib/xianyu/.venv/bin/python3` (Python 3.12) | ✅ Works | Has execjs, websocket-client, requests |
| `/opt/homebrew/bin/python3.12` (Homebrew) | ❌ `ModuleNotFoundError: No module named 'execjs'` | Bare system Python, no site packages |
| Hermes-agent venv (`~/.hermes/hermes-agent/venv/bin/python3`) | ❌ Incompatible TLS | Python 3.11, different SSL stack |

The execjs module is in `/Users/moye/Molin-OS/molib/xianyu/.venv/lib/python3.12/site-packages/execjs`.

## Healthy Startup Log

```
[xianyu-ws] Loaded 17 cookie fields
[xianyu-ws] Verifying token with SSL fix...
[xianyu-ws] Token OK
[xianyu-ws] Starting WebSocket listener...
[xianyu-ws] 正在连接闲鱼WebSocket...
[xianyu-ws] ✅ WebSocket 已连接
[xianyu-ws] 初始化完成: None
```

The `None` in "初始化完成: None" is normal — it's `listen_forever()` returning after listener setup.
Do NOT interpret it as an error.

## Cron Health Check Workflow

Every cron cycle should follow this exact sequence:

1. `python ~/.hermes/scripts/xianyu_check.py` — verify API token
2. `ps aux | grep ws_listener | grep -v grep` — check process alive
3. `tail -1 ~/.hermes/xianyu_bot/ws.log` — check recent activity
4. If process dead or log stale → restart using exact command above
5. Read `~/.hermes/xianyu_bot/state.json` and `~/.hermes/xianyu_bot/activity.log`
6. Generate inspection card per feishu-message-formatter

## State Files Updated Each Cycle

- `~/.hermes/state/xianyu_cron_report_latest.json` — full status snapshot (JSON)
- `~/.hermes/xianyu_bot/state.json` — minimal: `{messages_handled, replies_sent, last_activity, ws_listener_pid, ws_connected}`
- `~/.hermes/xianyu_bot/activity.log` — append one-line summary
