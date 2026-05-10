# Goofish SSL Troubleshooting

## Problem: Python requests SSLEOFError on h5api.m.goofish.com

```
SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)')
```

### Root Cause
Python's OpenSSL-based `ssl` module (used by `requests`/`urllib3`) fails the TLS handshake with `h5api.m.goofish.com`. The goofish edge server terminates the connection during the handshake before Python can complete it.

### What Works
- **curl** — uses macOS native SecureTransport, not OpenSSL. Always works.
- **Python 3.12 from Homebrew** (`/opt/homebrew/Cellar/python@3.12/`) — the `ws_listener.py` uses this and connects successfully.
- **Python 3.11.15** (Hermes venv) — FAILS. The `xianyu_bot.py cron` runs here and cannot get a token.

### Workaround Status
- `ws_listener.py` works (Python 3.12) — WebSocket listener is operational
- `xianyu_bot.py cron` fails (Python 3.11) — cron health checks use alternative path (check ws_listener PID and log instead of direct API calls)
- `curl` fallback available for one-off API probes

### Proven Failures
| Approach | Result |
|----------|--------|
| `requests.get(url, verify=False)` | 404 (works for basic GET, but token endpoint still fails) |
| Custom `SSLAdapter` with `check_hostname=False` | TimeoutError during handshake |
| `urllib3` with `DEFAULT:@SECLEVEL=1` ciphers | TimeoutError during handshake |
| `requests` with vanilla session + default SSL | SSLEOFError |

### File Locations
- Working: `ws_listener.py` → `/Users/moye/.hermes/xianyu_bot/ws_listener.py` (Python 3.12)
- Broken: `xianyu_bot.py cron` → `/Users/moye/.hermes/molin/bots/xianyu_bot.py` (Python 3.11)
- Venv 3.12: `/Users/moye/Molin-OS/molib/xianyu/.venv/`
