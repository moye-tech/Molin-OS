#!/usr/bin/env python3
"""
Molin-OS CloakBrowser Integration Script

Provides shared stealth browser access for all 5 agents through cloakserve CDP.
Usage:
    python3 cloakserve_test.py <seed> [url] [proxy]

Examples:
    python3 cloakserve_test.py media-yinyue
    python3 cloakserve_test.py global-meining https://myip.link socks5://user:pass@host:1080
"""

import json
import sys
import urllib.request

CLOAKSERVE_URL = "http://localhost:9222"


def check_status():
    """Check cloakserve status."""
    try:
        req = urllib.request.Request(CLOAKSERVE_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            print(f"cloakserve status: {data['status']}")
            print(f"Active processes: {data['active']}")
            if data['processes']:
                for name, info in data['processes'].items():
                    print(f"  [{name}] pid={info['pid']} port={info['port']} "
                          f"connections={info['connections']} tz={info.get('timezone','-')}")
            return True
    except Exception as e:
        print(f"cloakserve not reachable: {e}")
        return False


def get_version(seed=None):
    """Get CDP version info, optionally with a seed."""
    url = f"{CLOAKSERVE_URL}/json/version"
    if seed:
        url += f"?fingerprint={seed}"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f"CDP version: {data.get('Browser', '?')}")
        print(f"WS URL: {data.get('webSocketDebuggerUrl', '?')}")
        return data


def get_pages(seed=None):
    """List CDP targets."""
    url = f"{CLOAKSERVE_URL}/json/list"
    if seed:
        url += f"?fingerprint={seed}"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
        print(f"Targets: {len(data)}")
        for t in data:
            print(f"  [{t.get('id','?')[:12]}] {t.get('title','')} — {t.get('url','')}")
        return data


if __name__ == "__main__":
    seed = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("CloakServe — Molin-OS Stealth Browser Pool")
    print("=" * 60)

    if not check_status():
        sys.exit(1)

    print()
    print("--- Version Info ---")
    get_version(seed)

    print()
    print("--- Pages ---")
    get_pages(seed)

    print()
    print("✓ CloakServe is running and ready for use")
    print(f"  Connect: playwright.chromium.connect_over_cdp('{CLOAKSERVE_URL}')")
    if seed:
        print(f"  With seed: ?fingerprint={seed}")
