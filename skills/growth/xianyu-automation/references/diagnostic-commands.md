# Xianyu Listener Diagnostic Commands

Proven command recipes from patrol sessions. Keep commands copy-pasteable.

## Quick Health Check

```bash
# 1. API token check
python /Users/moye/.hermes/scripts/xianyu_check.py

# 2. Is listener alive?
cat ~/.hermes/xianyu_bot/state.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ws_listener_pid','NONE'))"
# → use PID from output
ps -p <PID> -o pid,stat,etime,command
lsof -p <PID> -a -i    # MUST return socket entries

# 3. Recent log activity?
tail -5 ~/.hermes/xianyu_bot/ws.log
date '+%Y-%m-%d %H:%M:%S'
# → compare timestamps, must be within 5 min

# 4. Message stats
cat ~/.hermes/xianyu_bot/state.json | python3 -m json.tool
```

## Fake-Alive Detection Pattern

```
Symptom:
  ps -p <pid> → Ss (alive, sleeping)
  lsof -p <pid> -a -i → NO OUTPUT (no sockets!)
  tail ws.log → last entry >5 min ago

Conclusion: FAKE-ALIVE. Process is a zombie. Kill and restart.
```

Real case: 2026-05-11, PID 79907 ran for ~2h with zero sockets. ws.log showed
last entry "初始化完成: None" at 10:50, then nothing. lsof confirmed no network.

## Token Validation Error Signatures

```
# Server overload (transient, recovers on its own)
ret: ["FAIL_SYS_USER_VALIDATE", "RGV587_ERROR::SM::哎哟喂,被挤爆啦,请稍后重试"]

# Real token expiry (needs manual cookie refresh)
ret: ["FAIL_SYS_USER_VALIDATE"]  (no "被挤爆啦" substring)

# TLS version mismatch (wrong venv)
SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol')
```

## Restart Sequence (background=true required)

```bash
# Kill old
kill <old_pid> 2>/dev/null; sleep 1

# Start new (use terminal background=true)
cd /Users/moye/Molin-OS/molib/xianyu
/Users/moye/Molin-OS/molib/xianyu/.venv/bin/python3 \
  /Users/moye/.hermes/xianyu_bot/ws_listener.py

# Verify after 5s
sleep 5
lsof -p <new_pid> -a -i | head -3
tail -3 ~/.hermes/xianyu_bot/ws.log
# Expected: "Loaded N cookie fields" → "Token OK" → "✅ WebSocket 已连接"

# Update state
cat > ~/.hermes/xianyu_bot/state.json << 'EOF'
{"messages_handled": 0, "replies_sent": 0, "last_activity": "...", "ws_listener_pid": <new_pid>, "ws_connected": true}
EOF
```

## Venv Note

The xianyu module patches `requests` for TLS 1.2 compatibility with Xianyu's API.
This patch is only in the xianyu venv:
```
/Users/moye/Molin-OS/molib/xianyu/.venv/bin/python3
```

The Hermes venv at `/Users/moye/.hermes/hermes-agent/venv/bin/python` does NOT
have this patch. Using it may work for basic API calls but will intermittently
fail with SSL errors on the WebSocket connection.
