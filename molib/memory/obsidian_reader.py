#!/usr/bin/env python3
"""
Molin-OS Memory Reader — Obsidian 结构化知识检索

从 产出/ 目录读取历史产出（v3.0 flat vault，文件命名: 产出/业务线｜type·date.md），
支持关键词匹配和后续可升级的 embedding 检索。
"""

import os
import re
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

VAULT = Path(os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
))

AGENT_OUTPUTS = VAULT / "产出"


def search_obsidian(query: str, agent_name: str = None, days_back: int = 30,
                    top_k: int = 5) -> list[dict]:
    """
    检索 Obsidian 中 Agent 的历史输出。

    Args:
        query: 检索关键词
        agent_name: Agent ID (如 content, finance)，None=全部
        days_back: 回溯天数
        top_k: 返回结果上限

    Returns:
        [{source, agent, date, title, content, score, sections}]
    """
    results = []
    cutoff = datetime.now() - timedelta(days=days_back)

    # 确定搜索路径
    if agent_name:
        search_paths = [AGENT_OUTPUTS / agent_name]
    else:
        search_paths = sorted(AGENT_OUTPUTS.glob("*/"))

    for agent_dir in search_paths:
        if not agent_dir.is_dir():
            continue
        agent_id = agent_dir.name

        for fpath in sorted(agent_dir.glob("*.md")):
            fname = fpath.name

            # 日期过滤（文件名中的日期）
            date_match = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
            if date_match:
                fdate = datetime.strptime(date_match.group(1), "%Y-%m-%d")
                if fdate < cutoff:
                    continue

            content = fpath.read_text(encoding="utf-8", errors="replace")

            # 关键词匹配评分
            query_lower = query.lower()
            content_lower = content.lower()

            score = 0
            # 标题匹配加分
            for line in content.split("\n"):
                line_lower = line.lower()
                if query_lower in line_lower:
                    if line.startswith("#"):
                        score += 5
                    elif line.startswith("##"):
                        score += 3
                    else:
                        score += 1

            if score == 0:
                continue

            # 提取结构化区块
            sections = _extract_sections(content)

            results.append({
                "source": "obsidian",
                "agent": agent_id,
                "date": date_match.group(1) if date_match else "unknown",
                "title": fname.replace(".md", ""),
                "filepath": str(fpath.relative_to(VAULT)),
                "content": content[:2000],  # 截断防爆token
                "score": score,
                "sections": sections,
            })

    # 按分数排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def search_section(query: str, agent_name: Optional[str] = None,
                   section_type: str = "洞察|结论|可复用知识") -> list[dict]:
    """
    专门检索某类区块（洞察/结论/可复用知识）。

    这是提供给 Agent 的"只取精华"接口。
    """
    results = search_obsidian(query, agent_name, days_back=90, top_k=20)

    filtered = []
    for r in results:
        relevant = []
        for s in r.get("sections", []):
            if re.search(section_type, s["heading"], re.IGNORECASE):
                relevant.append(s)
        if relevant:
            r["matched_sections"] = relevant
            filtered.append(r)

    return filtered[:5]


def _extract_sections(markdown: str) -> list[dict]:
    """从 markdown 中提取 ## 级区块"""
    sections = []
    current = None

    for line in markdown.split("\n"):
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = {"heading": line[3:].strip(), "content": ""}
        elif line.startswith("### "):
            if current:
                current["content"] += line + "\n"
        elif line.startswith("# ") and not line.startswith("## "):
            continue  # 跳过一级标题
        else:
            if current:
                current["content"] += line + "\n"

    if current:
        sections.append(current)

    return sections


def list_agent_outputs(agent_name: str, limit: int = 10) -> list[str]:
    """列出某 Agent 最近的输出文件"""
    agent_dir = AGENT_OUTPUTS / agent_name
    if not agent_dir.exists():
        return []
    files = sorted(agent_dir.glob("*.md"), reverse=True)
    return [str(f.relative_to(VAULT)) for f in files[:limit]]
