#!/usr/bin/env python3
"""
墨麟OS → Obsidian iCloud 知识库 同步脚本

将 Molin-OS 产出的报告/日报同步到 Obsidian iCloud vault。
支持: 日报、周报、GitHub雷达、系统健康报告等。

用法:
    python3 sync.py                          # 全部同步
    python3 sync.py --dry-run                # 预览模式
    python3 sync.py --type daily             # 仅日报
    python3 sync.py --type github-radar      # 仅 GitHub 雷达
"""

import os
import sys
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ═══════════════════════════════════════════
# 路径配置
# ═══════════════════════════════════════════

HOME = Path.home()

# 尝试从 .env 加载 OBSIDIAN_VAULT_PATH
def _load_env_path():
    env_file = HOME / ".hermes" / ".env"
    if env_file.exists():
        for line in env_file.read_text().split("\n"):
            line = line.strip()
            if line.startswith("OBSIDIAN_VAULT_PATH="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                return Path(val)
    return None

VAULT = _load_env_path() or Path(
    f"{HOME}/Library/Mobile Documents/iCloud~md~obsidian/Documents"
)
MOLIN_OUTPUT = HOME / "Molin-OS" / "output" / "reports"
HERMES_DAILY = HOME / ".hermes" / "daily_reports"

BEIJING_TZ = timezone(timedelta(hours=8))


# ═══════════════════════════════════════════
# 同步规则
# ═══════════════════════════════════════════

SYNC_RULES = [
    {
        "name": "github-radar",
        "source_dir": HERMES_DAILY,
        "target_dir": VAULT / "10-Daily",
        "pattern": "github_radar_*.md",
        "frontmatter": lambda f: {
            "date": _extract_date_from_filename(f),
            "tags": ["daily", "github", "tech-radar"],
            "source": "墨研竞情 · GitHub Trending 自动",
        },
        "title_prefix": "📡 GitHub 技术雷达 · ",
    },
    {
        "name": "daily-briefing",
        "source_dir": HERMES_DAILY,
        "target_dir": VAULT / "10-Daily",
        "pattern": "briefing_*.md",
        "frontmatter": lambda f: {
            "date": _extract_date_from_filename(f),
            "tags": ["daily", "briefing"],
            "source": "墨研竞情 · 每日简报",
        },
        "title_prefix": "📋 每日简报 · ",
    },
    {
        "name": "reports",
        "source_dir": MOLIN_OUTPUT,
        "target_dir": VAULT / "20-Reports",
        "pattern": "*.md",
        "frontmatter": lambda f: {
            "date": datetime.now(BEIJING_TZ).strftime("%Y-%m-%d"),
            "tags": ["report"],
            "source": "Molin-OS WorkerChain",
        },
        "title_prefix": "",
    },
]


def _extract_date_from_filename(filepath: Path) -> str:
    """从文件名中提取日期，如 github_radar_2026-05-11.md → 2026-05-11"""
    import re
    m = re.search(r"(\d{4}-\d{2}-\d{2})", filepath.stem)
    if m:
        return m.group(1)
    return datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")


def sync_file(src: Path, target_dir: Path, rule: dict, dry_run: bool = False):
    """同步单个文件到 Obsidian vault，添加 frontmatter。"""
    target_dir.mkdir(parents=True, exist_ok=True)

    # 读取源内容
    content = src.read_text(encoding="utf-8")

    # 提取标题（第一行 # 开头）
    lines = content.strip().split("\n")
    title_line = ""
    body_lines = lines[:]
    if lines and lines[0].startswith("# "):
        title_line = lines[0][2:].strip()
        body_lines = lines[1:]

    # 构建 frontmatter
    fm = rule["frontmatter"](src)
    title = fm.get("date", "") + " " + (title_line or src.stem)
    if rule.get("title_prefix") and not title_line.startswith(rule["title_prefix"]):
        title = rule["title_prefix"] + title_line if title_line else rule["title_prefix"] + src.stem

    frontmatter = "---\n"
    for k, v in fm.items():
        if isinstance(v, list):
            frontmatter += f"{k}: [{', '.join(v)}]\n"
        else:
            frontmatter += f"{k}: {v}\n"
    frontmatter += "---\n\n"

    # 目标文件名
    target_name = src.name
    target_path = target_dir / target_name

    # 写入
    new_content = f"# {title}\n\n{frontmatter}{chr(10).join(body_lines)}"

    if dry_run:
        print(f"  📋 [DRY RUN] {src.name} → {target_path}")
        return

    target_path.write_text(new_content, encoding="utf-8")
    print(f"  ✅ {src.name} → {target_path}")


def sync_all(rules: list, dry_run: bool = False):
    """执行全部同步规则。"""
    print(f"🔗 Obsidian Vault: {VAULT}")
    print(f"📂 源目录: {HERMES_DAILY}, {MOLIN_OUTPUT}")
    print()

    count = 0
    for rule in rules:
        src_dir = rule["source_dir"]
        if not src_dir.exists():
            continue

        matching = sorted(src_dir.glob(rule["pattern"]))
        if not matching:
            continue

        print(f"📁 {rule['name']} ({len(matching)} 文件):")
        for f in matching:
            sync_file(f, rule["target_dir"], rule, dry_run)
            count += 1
        print()

    action = "将同步" if dry_run else "已同步"
    print(f"🎉 {action} {count} 个文件到 Obsidian vault")


def main():
    dry_run = "--dry-run" in sys.argv
    type_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--type="):
            type_filter = arg.split("=", 1)[1]

    rules = SYNC_RULES
    if type_filter:
        rules = [r for r in SYNC_RULES if r["name"] == type_filter]
        if not rules:
            print(f"❌ 未知类型: {type_filter}")
            print(f"可用: {', '.join(r['name'] for r in SYNC_RULES)}")
            sys.exit(1)

    sync_all(rules, dry_run=dry_run)


if __name__ == "__main__":
    main()
