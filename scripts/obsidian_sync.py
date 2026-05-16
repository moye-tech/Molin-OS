#!/usr/bin/env python3
"""墨麟OS → Obsidian iCloud 知识库 同步脚本 v4 — MECE 4分类 + 聚合 Daily"""
from __future__ import annotations
import os, sys, json, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

HOME = Path.home()
BEIJING_TZ = timezone(timedelta(hours=8))

def _load_env_path() -> Optional[Path]:
    for env_file in [HOME / ".hermes" / ".env", HOME / ".hermes" / "profiles" / "media" / ".env"]:
        if env_file.exists():
            for line in env_file.read_text().split("\n"):
                line = line.strip()
                if line.startswith("OBSIDIAN_VAULT_PATH="):
                    val = line.split("=", 1)[1].strip().strip("'\"")
                    return Path(val)
    return None

VAULT = _load_env_path() or Path(
    f"{HOME}/Library/Mobile Documents/iCloud~md~obsidian/Documents"
)

# ═══════════════════════════════════════════════
# v4 Agent 定义 — 4 MECE 分类
# ═══════════════════════════════════════════════

AGENTS = {
    "edu":    {"name": "元瑶教育", "desc": "教育内容、课程设计、学习辅导"},
    "global": {"name": "梅凝出海", "desc": "海外市场本地化运营、跨境营销"},
    "media":  {"name": "银月传媒", "desc": "全媒体内容创作、社交媒体运营"},
    "shared": {"name": "玄骨中枢", "desc": "CRM客户管理、运维部署、财务记账"},
    "side":   {"name": "宋玉创业", "desc": "创业项目、副业探索、市场调研"},
}

CATEGORIES = ["决策", "知识", "流程", "成果"]
CATEGORY_DESC = {
    "决策": "不可逆的选择（技术选型、架构定稿）",
    "知识": "沉淀积累（研究、架构、思维模型）",
    "流程": "可执行步骤（SOP、配置、操作手册）",
    "成果": "可交付物（报告、产出物、数据）",
}

# ═══════════════════════════════════════════════
# 同步源配置
# ═══════════════════════════════════════════════

SOURCE_DIRS = [
    {
        "name": "每日报告",
        "path": HOME / ".hermes" / "daily_reports",
        "pattern": "*.md",
        "target_base": "报告",
    },
    {
        "name": "Molin 产出",
        "path": HOME / "Molin-OS" / "output" / "reports",
        "pattern": "*.md",
        "target_base": "Agents",
        "agent_resolver": "filename_prefix",
    },
    {
        "name": "Supermemory 导出",
        "path": HOME / ".hermes" / "profiles",
        "pattern": "memory_export_*.md",
        "target_base": "Agents",
        "agent_resolver": "parent_dir_name",
    },
]


def _resolve_agent_from_filename(filename: str) -> Optional[str]:
    """media_design_2026-05-15.md → media"""
    for agent_id in AGENTS:
        if filename.startswith(f"{agent_id}_"):
            return agent_id
    return None


def _resolve_category_from_filename(filename: str) -> str:
    """media_knowledge_2026-05-15.md → 知识"""
    stem = Path(filename).stem
    parts = stem.split("_")
    for agent_id in AGENTS:
        if parts[0] == agent_id and len(parts) > 1:
            cat = parts[1]
            # 旧命名映射
            MAPPING = {
                "design": "成果",
                "report": "成果",
                "daily": "成果",
                "knowledge": "知识",
                "process": "流程",
                "decision": "决策",
                "sop": "流程",
                "output": "成果",
                "content": "知识",
                "research": "知识",
            }
            if cat in MAPPING:
                return MAPPING[cat]
            # 检查是否是日期
            if re.match(r"^\d{4}-\d{2}-\d{2}$", cat):
                return "成果"
            return cat
    return "知识"


def _resolve_agent_from_parent_dir(path: Path) -> Optional[str]:
    """profiles/media/memory_export_xxx.md → media"""
    parent_name = path.parent.name
    for agent_id in AGENTS:
        if parent_name == agent_id:
            return agent_id
    return None


def _detect_date(path: Path) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.stem)
    if m:
        return m.group(1)
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=BEIJING_TZ)
    return mtime.strftime("%Y-%m-%d")


def _make_frontmatter(agent_id: str, category: str, date: str,
                      source: str = "", tags: Optional[list[str]] = None) -> str:
    tags = tags or [agent_id, category, "auto-sync"]
    tag_str = ", ".join(tags)
    return (
        "---\n"
        f"created: {date}\n"
        f"updated: {date}\n"
        f"agent: {agent_id}\n"
        f"category: {category}\n"
        f"status: 活跃\n"
        f"confidence: 待验证\n"
        f"importance: ⭐⭐\n"
        f"source: {source or 'Molin-OS AutoSync'}\n"
        f"tags: [{tag_str}]\n"
        "---\n\n"
    )


def init_vault():
    """创建 vault 目录结构（v4: 4 分类 + 聚合 Daily）"""
    print(f"🔧 初始化 vault 结构 v4: {VAULT}\n")

    agents_dir = VAULT / "Agents"
    for agent_id, agent_info in AGENTS.items():
        agent_dir = agents_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        for cat in CATEGORIES:
            (agent_dir / cat).mkdir(parents=True, exist_ok=True)

        readme = agent_dir / "README.md"
        if not readme.exists():
            cat_list = "\n".join(
                f"- **{cat}/** — {CATEGORY_DESC.get(cat, cat)}"
                for cat in CATEGORIES
            )
            readme.write_text(
                f"# {agent_info['name']}\n\n"
                f"_{agent_info['desc']}_\n\n"
                f"## 分类\n\n{cat_list}\n"
            )
            print(f"  📄 {readme.relative_to(VAULT)}")

    # 聚合 Daily — 单文件模式
    daily_dir = VAULT / "Daily"
    daily_dir.mkdir(parents=True, exist_ok=True)
    # 旧 Daily/agent/ 目录不再创建

    sys_dir = VAULT / "System"
    sys_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n✅ Vault 结构 v4 初始化完成!")


def _make_daily_section(agent_id: str, content: str, date: str) -> str:
    """构建日聚合报的 Agent 分区"""
    name = AGENTS[agent_id]["name"]
    section = (
        f"\n## {name}\n\n"
        f"{content}\n"
    )
    return section


def sync_source(source_cfg: dict, agent_filter: Optional[str], dry_run: bool = False):
    src_dir = source_cfg["path"]
    if not src_dir.exists():
        return 0

    files = sorted(src_dir.glob(source_cfg["pattern"]))
    if not files:
        return 0

    print(f"\n📁 [{source_cfg['name']}] ({len(files)} 文件)")

    # 按 agent + date 汇总 Daily 内容
    daily_entries: dict[str, dict[str, list[str]]] = {}
    # agent_id → {date: [lines]}

    count = 0
    for f in files:
        if source_cfg["agent_resolver"] == "filename_prefix":
            agent_id = _resolve_agent_from_filename(f.name)
        elif source_cfg["agent_resolver"] == "parent_dir_name":
            agent_id = _resolve_agent_from_parent_dir(f)
        else:
            agent_id = None

        if not agent_id or agent_id not in AGENTS:
            print(f"  ⏭️  跳过 {f.name}（无法识别 agent）")
            continue
        if agent_filter and agent_id != agent_filter:
            continue

        category = _resolve_category_from_filename(f.name)
        if category not in CATEGORIES:
            category = "知识"

        date = _detect_date(f)

        # 按 target 类型处理
        if source_cfg["target_base"] == "Daily":
            # 收集到 daily_entries 中，最后一次性写入 Daily/<date>.md
            daily_entries.setdefault(agent_id, {}).setdefault(date, [])
            content = f.read_text(encoding="utf-8")
            # 提取标题和摘要
            lines = content.strip().split("\n")
            title = ""
            body_summary = ""
            for line in lines:
                if line.startswith("# "):
                    title = line[2:].strip()
                elif line.strip() and not line.startswith("---"):
                    body_summary = line.strip()[:100]
                    break
            entry = f"- **{title or f.stem}** — {body_summary}" if body_summary else f"- **{title or f.stem}**"
            daily_entries[agent_id][date].append(entry)
            count += 1

            if dry_run:
                print(f"  📋 [DRY RUN] {f.name} → Daily/{date}.md ({agent_id})")
        else:
            # Agents/ 目录 — 按分类写入
            target_dir = VAULT / category
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f.name

            content = f.read_text(encoding="utf-8")
            has_fm = content.strip().startswith("---")

            if has_fm:
                # 已有 frontmatter，追加 agent/category
                lines = content.split("\n")
                insert_pos = 1
                while insert_pos < len(lines) and not lines[insert_pos].strip().startswith("---"):
                    insert_pos += 1
                if insert_pos < len(lines):
                    lines.insert(insert_pos, f"agent: {agent_id}")
                    lines.insert(insert_pos + 1, f"category: {category}")
                new_content = "\n".join(lines)
            else:
                frontmatter = _make_frontmatter(
                    agent_id, category, date,
                    source=source_cfg["name"],
                    tags=[agent_id, category, "auto-sync"],
                )
                new_content = f"{frontmatter}{content.strip()}\n"

            if dry_run:
                print(f"  📋 [DRY RUN] {f.name} → {target_path.relative_to(VAULT)} (cat={category})")
            else:
                target_path.write_text(new_content, encoding="utf-8")
                print(f"  ✅ {f.name} → {target_path.relative_to(VAULT)}")
            count += 1

    # 写入聚合 Daily 文件
    if daily_entries and not dry_run:
        for agent_id, dates in daily_entries.items():
            for date, entries in dates.items():
                daily_path = VAULT / "报告" / f"{date}.md"
                agent_name = AGENTS[agent_id]["name"]
                section = f"\n## {agent_name}\n\n" + "\n".join(entries) + "\n"

                if daily_path.exists():
                    existing = daily_path.read_text(encoding="utf-8")
                    # 检查是否已有该 agent 分区
                    if f"## {agent_name}" in existing:
                        # 替换已有分区
                        existing = re.sub(
                            rf"\n## {agent_name}\n.*?(?=\n## |\n---|\Z)",
                            section,
                            existing,
                            flags=re.DOTALL,
                        )
                    else:
                        existing += section
                    daily_path.write_text(existing, encoding="utf-8")
                else:
                    frontmatter = (
                        "---\n"
                        f"date: {date}\n"
                        f"type: daily\n"
                        f"tags: [daily, log]\n"
                        "---\n\n"
                        f"# {date} · 墨麟日报\n"
                        f"{section}"
                    )
                    daily_path.write_text(frontmatter, encoding="utf-8")
                print(f"  ✅ 聚合 Daily/{date}.md ← {agent_name}")

    return count


def sync_all(agent_filter: Optional[str] = None, dry_run: bool = False):
    print(f"🔗 Obsidian Vault v4: {VAULT}")
    print(f"{'📋 预览模式' if dry_run else '🚀 同步模式'}")
    if agent_filter:
        print(f"🔍 仅 agent: {agent_filter} ({AGENTS[agent_filter]['name']})")

    total = 0
    for src_cfg in SOURCE_DIRS:
        total += sync_source(src_cfg, agent_filter, dry_run)

    verb = "将同步" if dry_run else "已同步"
    print(f"\n🎉 {verb} {total} 个文件到 Obsidian vault（v4 结构）")


def main():
    args = sys.argv[1:]
    if "--init" in args:
        init_vault()
        return
    dry_run = "--dry-run" in args
    agent_filter = None
    for arg in args:
        if arg.startswith("--agent="):
            agent_filter = arg.split("=", 1)[1]
            if agent_filter not in AGENTS:
                print(f"❌ 未知 agent: {agent_filter}")
                print(f"可用: {', '.join(AGENTS)}")
                sys.exit(1)
    sync_all(agent_filter, dry_run)


if __name__ == "__main__":
    main()
