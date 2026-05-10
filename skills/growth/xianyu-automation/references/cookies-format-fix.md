# Cookies Format Fix — 2026-05-10

## Problem

`xianyu_bot.py cron` fails with:
```
❌ cron检查异常: "name='_m_h5_tk', domain=None, path=None"
```

## Root Cause

`trans_cookies()` in `goofish_utils.py` parses cookies with:
```python
def trans_cookies(cookies_str):
    cookies = dict()
    for i in cookies_str.split("; "):
        try:
            cookies[i.split('=')[0]] = '='.join(i.split('=')[1:])
        except:
            continue
    return cookies
```

It expects `key1=val1; key2=val2` format (standard HTTP Cookie header).

The cookies file was saved as JSON:
```json
{"_m_h5_tk": "f88c865...", "_m_h5_tk_enc": "bfe880a...", ...}
```

When the JSON string is fed to `trans_cookies()`, it produces garbage keys like `{"_m_h5_tk"` with no valid cookie values. The downstream `XianyuApis` constructor then fails trying to build Cookie objects from these malformed entries.

## Fix

Convert JSON cookies to semicolon-separated format:

```python
import json, os

cookie_path = os.path.expanduser("~/.xianyu_cookies_new.txt")
with open(cookie_path) as f:
    cookies_json = json.load(f)

cookie_str = "; ".join(f"{k}={v}" for k, v in cookies_json.items() if v)
with open(cookie_path, "w") as f:
    f.write(cookie_str)
```

## Verification

After conversion, run:
```bash
cd ~/xianyu_agent && .venv/bin/python3 ~/.hermes/molin/bots/xianyu_bot.py cron
```

Expected output:
```
[timestamp] ✅ 闲鱼Token有效
```

## Prevention

When exporting Xianyu cookies from browser DevTools, ensure they are saved as `key=value; key=value` header format, NOT as JSON. If the export tool produces JSON, convert before saving to `~/.xianyu_cookies_new.txt`.
