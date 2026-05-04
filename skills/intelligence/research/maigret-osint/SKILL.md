---

name: maigret-osint
description: OSINT username search across 3,000+ sites using maigret (23K stars). Find a person's online presence by username — social media, forums, developer platforms. Use for competitive research, due diligence, or influencer vetting.
version: 1.0.0
tags: [osint, research, investigation, social-media, reconnaissance, maigret]
category: research
related_skills: [last30days, blogwatcher, polymarket]
metadata:
  hermes:
    source: https://github.com/soxoj/maigret
    install: pip install maigret
    molin_owner: 墨思（情报研究）
---

# Maigret OSINT — 跨平台账号搜索

## Overview

Search for a person's online presence across 3,000+ websites using just their username. Maigret is the premier OSINT username search engine — used commercially by Social Links and UserSearch.

## When to Use

- Researching a freelancer/client before doing business
- Finding a competitor's online footprint
- Vetting an influencer for brand partnerships
- Investigating a suspicious account
- Finding all platforms where a brand is active

**Don't use for:** Real-time monitoring (use blogwatcher), deep content analysis (use last30days), academic research (use arxiv).

## Quick Start

```bash
# Install
pip install maigret

# Basic search
maigret <username>

# Search with specific site filters
maigret <username> --tags social,forum

# Search + recursive (find linked accounts)
maigret <username> --recursive

# Generate PDF report
maigret <username> --pdf

# Generate HTML report
maigret <username> --html
```

## Key Features

| Feature | Command |
|---------|---------|
| Basic search | `maigret <username>` |
| Recursive search | `maigret <username> --recursive` |
| Site filtering | `maigret <username> --tags social,news` |
| Country filter | `maigret <username> --country CN` |
| PDF report | `maigret <username> --pdf` |
| HTML report | `maigret <username> --html` |
| Tor support | `maigret <username> --tor` |
| Proxy support | `maigret <username> --proxy socks5://...` |

## Use Cases for 一人公司

1. **Client vetting**: Before taking a 猪八戒 project, check the client's username across platforms. Are they legit? Do they have a history of disputes?

2. **Competitor intelligence**: Find all platforms where your Xianyu competitors are active. What else are they selling? Where do they market?

3. **Influencer research**: Before reaching out to a KOL for collaboration, check their footprint. How consistent is their brand? Are they active on the platforms they claim?

4. **Brand monitoring**: Search your own brand name to find unauthorized listings, impersonation accounts, or missed opportunities.

## Integration with Hermes

When the user asks "research this person/username":
1. Run maigret search
2. Parse results — note which platforms found a match
3. Cross-reference with last30days for engagement data on found platforms
4. Produce a structured profile

## Limitations

- Rate limiting on some sites (use --timeout and --retries)
- CAPTCHA on some sites (maigret detects but can't always bypass)
- Some sites may block automated access
- Chinese platforms (WeChat, QQ, Douyin) have limited support
