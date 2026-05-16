#!/usr/bin/env python3
"""墨麟OS 对话记忆提取器 — 读取各 Agent 的历史对话，提取关键记忆写入 Obsidian"""

from __future__ import annotations
import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

HOME = Path.home()
BEIJING_TZ = timezone(timedelta(hours=8))
NOW = datetime.now(BEIJING_TZ)

VAULT = Path(
    os.environ.get(
        "OBSIDIAN_VAULT_PATH",
        f"{HOME}/Library/Mobile Documents/iCloud~md~obsidian/Documents",
    )
)

AGENTS = {
    "edu": {"name": "元瑶教育", "categories": ["content", "curriculum", "analysis", "sop"]},
    "global": {"name": "梅凝出海", "categories": ["content", "localization", "analytics", "sop"]},
    "media": {"name": "银月传媒", "categories": ["content", "design", "schedule", "sop"]},
    "shared": {"name": "玄骨中枢", "categories": ["crm", "ops", "finance", "sop"]},
    "side": {"name": "宋玉创业", "categories": ["projects", "research", "sop"]},
}


def extract_key_info(text: str) -> dict:
    """从对话文本中提取关键信息"""
    info = {
        "configs": [],
        "decisions": [],
        "learnings": [],
        "preferences": [],
        "commands": [],
    }
    lines = text.split("\n")
    for line in lines:
        l = line.strip()
        if not l or len(l) < 10:
            continue
        # 配置相关
        if re.search(r"config|配置|设置|setup|install", l, re.I):
            info["configs"].append(l[:200])
        # 决策相关
        elif re.search(r"决定|选择|改用|改用|采用|迁移|migrate|switch|改用", l):
            info["decisions"].append(l[:200])
        # 学习/经验
        elif re.search(r"发现|注意|问题|error|fail|修复|fixed|bug|注意|记住", l, re.I):
            info["learnings"].append(l[:200])
        # 偏好
        elif re.search(r"喜欢|prefer|倾向|习惯|always|never|不用|不要", l, re.I):
            info["preferences"].append(l[:200])
        # 命令
        elif l.startswith(("hermes", "git", "npm", "pip", "curl", "python")):
            info["commands"].append(l[:200])
    return info


def summarize_session(session_path: Path, agent_id: str) -> Optional[str]:
    """读取单个 session 文件，提取摘要"""
    try:
        data = json.loads(session_path.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None

    # 提取用户消息和助手回复
    user_msgs = []
    assistant_msgs = []
    
    # 尝试从不同格式提取
    if isinstance(data, dict):
        messages = data.get("messages", data.get("conversation", []))
        if isinstance(messages, str):
            try:
                messages = json.loads(messages)
            except:
                messages = []
    elif isinstance(data, list):
        messages = data
    else:
        messages = []

    if not isinstance(messages, list):
        messages = []

    for msg in messages:
        if isinstance(msg, dict):
            role = str(msg.get("role", "")).lower()
            content = str(msg.get("content", "") or msg.get("text", "") or "")
            if role == "user" and content:
                user_msgs.append(content[:500])
            elif role in ("assistant", "model") and content:
                assistant_msgs.append(content[:500])

    if not user_msgs:
        return None

    # 提取关键信息
    all_text = "\n".join(user_msgs + assistant_msgs)
    info = extract_key_info(all_text)

    # 构建摘要
    summary_parts = [f"## 对话摘要 ({session_path.stem})"]
    
    # 用户主要需求
    key_requests = [m[:150] for m in user_msgs if len(m) > 20][:3]
    if key_requests:
        summary_parts.append("\n### 用户请求\n")
        for r in key_requests:
            summary_parts.append(f"- {r}")

    # 配置项
    if info["configs"]:
        summary_parts.append("\n### 配置项\n")
        for c in info["configs"][:5]:
            summary_parts.append(f"- `{c}`")

    # 决策
    if info["decisions"]:
        summary_parts.append("\n### 决策\n")
        for d in info["decisions"][:5]:
            summary_parts.append(f"- {d}")

    # 经验教训
    if info["learnings"]:
        summary_parts.append("\n### 经验\n")
        for l in info["learnings"][:5]:
            summary_parts.append(f"- {l}")

    summary_parts.append("")
    return "\n".join(summary_parts)


def process_agent(agent_id: str):
    """处理单个 Agent 的所有对话"""
    agent_info = AGENTS[agent_id]
    sessions_dir = HOME / ".hermes" / "profiles" / agent_id / "sessions"
    
    if not sessions_dir.exists():
        print(f"  ⏭️  {agent_info['name']}: 无对话目录")
        return 0

    session_files = sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not session_files:
        print(f"  ⏭️  {agent_info['name']}: 无对话文件")
        return 0

    summaries = []
    for sf in session_files:
        summary = summarize_session(sf, agent_id)
        if summary:
            summaries.append(summary)

    if not summaries:
        print(f"  ⏭️  {agent_info['name']}: 无可提取的内容")
        return 0

    # 写入 Agent 的 memory 目录
    content_dir = VAULT / "Agents" / agent_id / "对话"
    content_dir.mkdir(parents=True, exist_ok=True)

    # 生成总览文件
    now_str = NOW.strftime("%Y-%m-%d %H:%M")
    date_str = NOW.strftime("%Y-%m-%d")

    overview = [
        "---",
        f"date: {date_str}",
        f"agent: {agent_id}",
        "category: content",
        f"category_name: {agent_info['name']} 对话记忆",
        f"tags: [{agent_id}, conversation, memory, auto-extract]",
        "source: 对话记忆提取器",
        "---",
        "",
        f"# {agent_info['name']} — 对话记忆 ({date_str})",
        "",
        f"_从 {len(session_files)} 个对话中提取_\n",
    ]

    for s in summaries:
        overview.append(s)

    filename = f"{agent_id}_conversation_memory_{date_str}.md"
    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / filename).write_text("\n".join(overview), encoding="utf-8")

    print(f"  ✅ {agent_info['name']}: {len(summaries)}/{len(session_files)} 对话已提取 → Agents/{agent_id}/memory/{filename}")
    return len(summaries)


def main():
    print(f"🔍 从对话历史提取记忆...")
    print(f"   Vault: {VAULT}")
    print()

    total = 0
    for agent_id in AGENTS:
        count = process_agent(agent_id)
        total += count

    print(f"\n✅ 共提取 {total} 条对话记忆到 Obsidian vault")
    print(f"   打开 Obsidian → Agents/<agent>/content/ 查看")


if __name__ == "__main__":
    main()
