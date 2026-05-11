---
name: ngrok-tunnel
description: Set up ngrok tunnels for local services on macOS — authentication, multi-port reverse proxy for free tier, common errors, and verification.
---

# Ngrok Tunnel Setup

## Prerequisites
- ngrok binary at `~/bin/ngrok` (v3.39.1)
- Valid authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
- Config at `~/Library/Application Support/ngrok/ngrok.yml`

## Critical: Authtoken Format
ngrok authtoken format is NOT an API key. Common mistakes:
- `3DXT5rUH4dwMV...` → API key → ERR_NGROK_107 (properly formed but invalid)
- `cr_3CG0diOF...` → API key with prefix → ERR_NGROK_105 (doesn't look like authtoken)
- Valid token: set via `ngrok config add-authtoken <token>` — format varies by version

## Free Tier Limitation
ngrok free tier provides **1 public URL per agent instance**. Running two `ngrok http` processes won't work — the second fails because port 4040 (API) is already in use. Using `ngrok start --all` with multiple tunnel configs assigns the **same URL** to all tunnels.

### Solution: Python Reverse Proxy
Use a stdlib reverse proxy to multiplex multiple backends through one port:

```python
#!/usr/bin/env python3
"""Tiny reverse proxy: route by path prefix to different backends."""
import http.server
import urllib.request
import sys

BACKENDS = {
    "/feishu": "http://127.0.0.1:8765",
}
DEFAULT_BACKEND = "http://127.0.0.1:8648"

class Proxy(http.server.BaseHTTPRequestHandler):
    def do_request(self):
        path = self.path
        backend = DEFAULT_BACKEND
        for prefix, target in BACKENDS.items():
            if path.startswith(prefix):
                backend = target
                break
        url = backend + path
        body = None
        cl = self.headers.get('Content-Length')
        if cl:
            body = self.rfile.read(int(cl))
        req = urllib.request.Request(url, data=body, method=self.command)
        skip = {'host', 'content-length', 'connection', 'transfer-encoding'}
        for k, v in self.headers.items():
            if k.lower() not in skip:
                req.add_header(k, v)
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            self.send_response(resp.status)
            for k, v in resp.headers.items():
                if k.lower() not in {'transfer-encoding', 'connection'}:
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_request

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    http.server.HTTPServer(("127.0.0.1", port), Proxy).serve_forever()
```

## Startup Sequence (after reboot)
```bash
# 1. Start proxy (background)
python3 /tmp/ngrok_proxy.py 8080 &

# 2. Start ngrok (background)
~/bin/ngrok http 8080 &

# 3. Wait 20-60s for tunnel to establish on slow networks
sleep 30

# 4. Get public URL
curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys,json; t=json.load(sys.stdin)['tunnels'][0]; print(t['public_url'])"

# 5. Verify
curl -s 'https://<url>/feishu/webhook' -X POST -H 'Content-Type: application/json' -d '{"type":"url_verification","challenge":"test"}'
```

## Common ngrok Error Codes
| Code | Meaning | Fix |
|------|---------|-----|
| ERR_NGROK_105 | Token format wrong | Use actual authtoken, not API key |
| ERR_NGROK_107 | Token valid format but invalid/revoked | Get fresh token from dashboard |
| ERR_NGROK_4018 | No authtoken configured | Run `ngrok config add-authtoken <token>` |
| ERR_NGROK_218 | Missing API version header | Add `Ngrok-Version: 2` header for API calls |
| ERR_NGROK_6024 | Browser interstitial active | Switch to localhost.run/cloudflared for browser access; API clients pass through |
| context deadline exceeded | Cloudflare API unreachable | Network issue; wait, retry, or use different tunnel provider |

### ERR_NGROK_6024 Diagnosis
```bash
# Quick check: does the HTML contain ngrok assets?
curl -s "https://<url>" -H "User-Agent: Mozilla/5.0" | grep -c "assets.ngrok.com"
# >0 → interstitial active (browser UAs blocked)
# =0 → clean pass through

# API clients (no browser UA) bypass the interstitial automatically
```

## Network Patience
On this Mac (poor connectivity): ngrok may take **20-60 seconds** to establish a tunnel. The process will run with zero log output during this time. Check `http://127.0.0.1:4040/api/tunnels` to confirm. If still empty after 60s, kill and retry.

## Verification Checklist
- [ ] `curl http://127.0.0.1:4040/api/tunnels` returns tunnel with `public_url`
- [ ] `curl https://<url>/feishu/webhook -X POST -d '{"type":"url_verification","challenge":"ping"}'` returns `{"challenge":"ping"}`
- [ ] `curl -s -o /dev/null -w '%{http_code}' https://<url>/` returns 200
- [ ] Feishu developer console accepts the callback URL
- [ ] After reboot: proxy + ngrok must be restarted (URL will change)

## Free Alternatives Without Interstitial

ngrok free tier injects a browser interstitial that cannot be bypassed server-side. When you need
a clean tunnel with zero warning pages for human browser access, use one of these alternatives:

### localhost.run (SSH tunnel)
```bash
# Start (background mode, persists until killed or SSH drops)
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
    -R 80:localhost:8080 nokey@localhost.run 2>&1
# Output: https://<random-chars>.lhr.life
```
- ✅ No interstitial, no account needed, zero config
- ❌ URL changes each restart; free tier has rate limits (429s on rapid API calls)
- Persistence: register free account at localhost.run → permanent subdomain

### cloudflared TryCloudflare
```bash
cloudflared tunnel --url http://localhost:8080
```
- ✅ No interstitial, already installed (`/opt/homebrew/bin/cloudflared`)
- ❌ TryCloudflare API occasionally returns 500; needs `brew install cloudflare/cloudflare/cloudflared`
- Persistence: create a named tunnel with Cloudflare account for fixed domain

## Hermes Web UI Access Token

When accessing the Hermes dashboard through a tunnel, the login page requires an access token:
- Located at `~/.hermes-web-ui/.token` (auto-generated on first launch, 64-char hex)
- Override with `AUTH_TOKEN` env var or disable with `AUTH_DISABLED=1`
- The Web UI server is a Node.js process at `~/.npm-global/lib/node_modules/hermes-web-ui/dist/server/index.js`

ngrok free tier shows a "Visit Site" interstitial on browser visits — it detects browser User-Agent.
`curl` without a browser UA bypasses it; browsers always hit it unless cookie is set from prior click.
For full troubleshooting see `references/ngrok-free-tier-issues.md`.
