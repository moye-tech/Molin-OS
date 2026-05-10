#!/usr/bin/env python3
"""Reverse proxy: route requests by path prefix to different backends.
Stdlib only — no dependencies. Free ngrok tier only gives 1 URL; this
multiplexes multiple services through one port.

Usage:
    python3 proxy.py 8080

Backend routing:
    /feishu/* → http://127.0.0.1:8765
    everything else → http://127.0.0.1:8648

Edit BACKENDS dict to change routing rules.
"""
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
    print(f"Reverse proxy on :{port}")
    print(f"  /feishu/* → {BACKENDS['/feishu']}")
    print(f"  default   → {DEFAULT_BACKEND}")
    http.server.HTTPServer(("127.0.0.1", port), Proxy).serve_forever()
