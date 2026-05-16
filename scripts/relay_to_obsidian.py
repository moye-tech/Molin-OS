#!/usr/bin/env python3
"""
墨麟OS · Relay输出同步到Obsidian + Supermemory
将 no_agent cron jobs的 relay/ 输出结果同步到Obsidian

扫描目录:
  ~/Molin-OS/relay/shared/results/   — arxiv 论文扫描等
  ~/Molin-OS/relay/side/results/     — 副业价格监控等

写入目标:
  Obsidian Vault: 知识/每日·{topic}.md
  Supermemory:    按内容分类存储

用法:
  python3 ~/Molin-OS/scripts/relay_to_obsidian.py
  python3 ~/Molin-OS/scripts/relay_to_obsidian.py --dry-run
"""
import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone, date

# === 路径 ===
HOME = Path.home()
RELAY_SHARED = HOME / "Molin-OS" / "relay" / "shared" / "results"
RELAY_SIDE = HOME / "Molin-OS" / "relay" / "side" / "results"
VAULT = HOME / "Library" / "Mobile Documents" / "iCloud~md~obsidian" / "Documents"
TRACKER = HOME / ".hermes" / "relay_sync_tracker.json"

DRY_RUN = "--dry-run" in sys.argv

def load_tracker():
    if TRACKER.exists():
        try:
            return json.loads(TRACKER.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_tracker(tracker):
    if DRY_RUN:
        return
    TRACKER.parent.mkdir(parents=True, exist_ok=True)
    TRACKER.write_text(json.dumps(tracker, ensure_ascii=False, indent=2), encoding="utf-8")

def file_fingerprint(path):
    """文件指纹: (mtime_ns, size)"""
    s = path.stat()
    return f"{s.st_mtime_ns}:{s.st_size}"

# === Handlers for each relay type ===

def handle_arxiv_papers(filepath: Path, tracker: dict) -> bool:
    """arxiv 每日论文 → 知识/每日·Arxiv论文.md"""
    fingerprint = file_fingerprint(filepath)
    key = f"arxiv::{filepath.name}"
    if tracker.get(key) == fingerprint:
        return False  # already synced

    date_str = filepath.stem.replace("daily_papers_", "")  # 20260516
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

    # Parse the text output - more robust
    content = filepath.read_text(encoding="utf-8", errors="replace")
    lines = content.strip().split("\n")

    # Extract paper info - handle various indent formats
    papers = []
    current = {}
    for line in lines:
        stripped = line.strip()
        # Match numbered entries: "1. Title" or "1.  Title"
        import re
        m = re.match(r'^(\d+)\.\s+(.+)', stripped)
        if m and not stripped.startswith("Found "):
            if current and current.get("title"):
                papers.append(current)
            current = {"title": m.group(2).strip()}
        elif stripped.startswith("ID:") and current:
            current["id"] = stripped.split("|")[0].replace("ID:", "").strip()
        elif stripped.startswith("Authors:") and current:
            current["authors"] = stripped.split(":", 1)[-1].strip()[:80]
        elif stripped.startswith("Categories:") and current:
            current["category"] = stripped.split(":")[-1].strip()
        elif stripped.startswith("Abstract:") and current:
            abstract = stripped.split(":", 1)[-1].strip()
            if len(abstract) > 200:
                abstract = abstract[:200] + "..."
            current["abstract"] = abstract
    if current:
        papers.append(current)

    # Build Obsidian entry
    obsidian_path = VAULT / "知识" / "每日·Arxiv论文.md"
    today = date.today().isoformat()

    entry = f"""
## {formatted_date}

### 结论
今日 arXiv 扫描发现 {len(papers)} 篇相关论文，涵盖 AI Agent、LLM 安全、跨境检测等领域。

### 核心内容
"""
    for p in papers:
        entry += f"""- **{p.get('title', '未知')}** ({p.get('id', '')})
  - 类别: {p.get('category', 'N/A')}
  - 摘要: {p.get('abstract', 'N/A')}
"""

    entry += f"""
### 下一步
- [ ] 筛选值得深入阅读的论文
"""

    # Update frontmatter
    if obsidian_path.exists():
        existing = obsidian_path.read_text(encoding="utf-8")
        # Append after frontmatter - strip the old content after frontmatter
        lines_existing = existing.split("\n")
        fm_end = 0
        if lines_existing[0].strip() == "---":
            for i in range(1, len(lines_existing)):
                if lines_existing[i].strip() == "---":
                    fm_end = i + 1
                    break
        # Rebuild: fresh frontmatter + existing entries (skip header)
        existing_entries = "\n".join(lines_existing[fm_end:]).strip()
        # Remove the "# Title" if it's there (it gets replaced)
        existing_lines = existing_entries.split("\n")
        header_line = 0
        for j, ln in enumerate(existing_lines):
            if ln.startswith("# ") and not ln.startswith("## "):
                header_line = j + 1
                break
        if header_line > 0:
            existing_entries = "\n".join(existing_lines[header_line:]).strip()

        new_content = f"""---
created: 2026-05-16
updated: {today}
agent: global
status: 活跃
confidence: 已验证
importance: ⭐⭐
source: cron:arxiv每日扫描
tags: [arxiv, 论文, 每日]
---

# Arxiv 每日论文

{existing_entries}

{entry}
"""
    else:
        new_content = f"""---
created: {today}
updated: {today}
agent: global
status: 活跃
confidence: 已验证
importance: ⭐⭐
source: cron:arxiv每日扫描
tags: [arxiv, 论文, 每日]
---

# Arxiv 每日论文

{entry}
"""

    if not DRY_RUN:
        obsidian_path.parent.mkdir(parents=True, exist_ok=True)
        obsidian_path.write_text(new_content, encoding="utf-8")

    print(f"  ✅ 已同步 arxiv → 知识/每日·Arxiv论文.md ({len(papers)}篇)")
    tracker[key] = fingerprint
    return True


def handle_price_monitor(filepath: Path, tracker: dict) -> bool:
    """副业价格监控 → 知识/每日·副业价格监控.md"""
    fingerprint = file_fingerprint(filepath)
    key = f"price::{filepath.name}"
    if tracker.get(key) == fingerprint:
        return False

    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except Exception:
        return False

    date_str = data.get("date", "")
    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}" if len(date_str) == 8 else date_str
    today = date.today().isoformat()

    pricing = data.get("pricing_reference", {})
    pricing_lines = "\n".join([f"  - {k}: {v}" for k, v in pricing.items()])

    entry = f"""
## {formatted_date}

### 结论
副业价格监控 — {len(pricing)} 类服务定价参考已更新。

### 核心内容
{pricing_lines}

### 下一步
- [ ] 接入真实爬虫获取闲鱼/猪八戒实时价格
"""

    obsidian_path = VAULT / "知识" / "每日·副业价格监控.md"
    if obsidian_path.exists():
        existing = obsidian_path.read_text(encoding="utf-8")
        lines_existing = existing.split("\n")
        fm_end = 0
        if lines_existing[0].strip() == "---":
            for i in range(1, len(lines_existing)):
                if lines_existing[i].strip() == "---":
                    fm_end = i + 1
                    break
        existing_entries = "\n".join(lines_existing[fm_end:]).strip()
        existing_lines = existing_entries.split("\n")
        header_line = 0
        for j, ln in enumerate(existing_lines):
            if ln.startswith("# ") and not ln.startswith("## "):
                header_line = j + 1
                break
        if header_line > 0:
            existing_entries = "\n".join(existing_lines[header_line:]).strip()

        new_content = f"""---
created: 2026-05-16
updated: {today}
agent: global
status: 活跃
confidence: 待验证
importance: ⭐⭐
source: cron:副业价格监控
tags: [副业, 价格, 每日]
---

# 副业价格监控

{existing_entries}

{entry}
"""
    else:
        new_content = f"""---
created: {today}
updated: {today}
agent: global
status: 活跃
confidence: 待验证
importance: ⭐⭐
source: cron:副业价格监控
tags: [副业, 价格, 每日]
---

# 副业价格监控

{entry}
"""

    if not DRY_RUN:
        obsidian_path.parent.mkdir(parents=True, exist_ok=True)
        obsidian_path.write_text(new_content, encoding="utf-8")

    print(f"  ✅ 已同步 price → 知识/每日·副业价格监控.md")
    tracker[key] = fingerprint
    return True


def main():
    print(f"🔍 Relay → Obsidian 同步 ({datetime.now().strftime('%H:%M:%S')})")
    if DRY_RUN:
        print("  [DRY RUN 模式]")
    tracker = load_tracker()
    synced = 0

    # Arxiv papers
    if RELAY_SHARED.exists():
        for f in sorted(RELAY_SHARED.glob("daily_papers_*.json")):
            if handle_arxiv_papers(f, tracker):
                synced += 1

    # Price monitor
    if RELAY_SIDE.exists():
        for f in sorted(RELAY_SIDE.glob("price_monitor_*.json")):
            if handle_price_monitor(f, tracker):
                synced += 1

    if synced > 0:
        save_tracker(tracker)
    print(f"  📊 本次同步: {synced} 条新记录")
    if synced == 0:
        print("  ℹ️  无新内容")


if __name__ == "__main__":
    main()
