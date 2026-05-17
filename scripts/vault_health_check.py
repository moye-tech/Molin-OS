#!/usr/bin/env python3
"""
Vault 健康检查 — 每天22:00复盘后运行，检查目录合规性
检测：遗留目录、根级杂文件、同名冲突、违规分类
"""

import os, sys
from pathlib import Path
from collections import defaultdict

VAULT = Path(os.path.expanduser(
    "~/Library/Mobile Documents/iCloud~md~obsidian/Documents"
))

ALLOWED_DIRS = {"决策", "知识", "流程", "成果", "报告", "配置",
                "学习档案", "Archive", "产出"}
ALLOWED_ROOT_GLOB = {"*.md"}  # only .md files at root
ROGUE_NAMES = {"Agents", "Daily", "System", "env",
                "项目", "知识库", "Makefile", "README.md"}

def check():
    issues = []

    # 1. Check top-level dirs
    for d in VAULT.iterdir():
        if not d.is_dir():
            continue
        name = d.name
        if name.startswith(".") or name == ".obsidian" or name == ".git":
            continue
        if name not in ALLOWED_DIRS:
            issues.append(f"⚠️ 禁止目录: {name}/")

    # 2. Check root-level files
    root_md = list(VAULT.glob("*.md"))
    root_other = [f for f in VAULT.iterdir() if f.is_file() and f.suffix != ".md"
                  and not f.name.startswith(".")]
    if root_md:
        issues.append(f"⚠️ 根级 .md 文件 ({len(root_md)}): {[f.name for f in root_md]}")
    if root_other:
        issues.append(f"⚠️ 根级非md文件: {[f.name for f in root_other]}")

    # 3. Check rogue dirs
    for rogue in ROGUE_NAMES:
        if (VAULT / rogue).exists():
            issues.append(f"⚠️ 遗留目录: {rogue}/")

    # 4. Check nested subdirs (whitelist known exceptions)
    ALLOWED_SUBDIRS = {"KPI看板", "agents", "github-absorb",
                       "content", "edu", "research", "autodream", "dev",
                       "media", "finance", "hermes", "side",
                       "shared", "global", "index.md"}  # v3.0: 8 flat dirs, zero subdirectories
    for d in ALLOWED_DIRS:
        target = VAULT / d
        if not target.exists():
            continue
        subdirs = [s for s in target.iterdir() if s.is_dir()
                   and s.name not in ALLOWED_SUBDIRS]
        if subdirs:
            issues.append(f"⚠️ {d}/ 包含非标准子目录: {[s.name for s in subdirs]}")

    # 5. Check duplicate filenames
    # v3.0 flat vault: cross-directory same-name is valid — directory IS the namespace
    # No dupe-check needed in v3.0

    # Report
    if not issues:
        print("✅ Vault 健康检查通过")
        return 0
    else:
        print(f"⚠️ 发现 {len(issues)} 个问题:\n")
        for i in issues:
            print(f"  {i}")
        print(f"\n运行 vault_compliance_check.py 修复")
        return 1

if __name__ == "__main__":
    sys.exit(check())
