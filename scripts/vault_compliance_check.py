#!/usr/bin/env python3
"""墨麟OS Vault 合规检查 — 每周自动扫描 v4 结构"""
import os, re, sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

HOME = Path.home()
VAULT = Path(os.environ.get("OBSIDIAN_VAULT_PATH",
    f"{HOME}/Library/Mobile Documents/iCloud~md~obsidian/Documents"))
BEIJING_TZ = timezone(timedelta(hours=8))
NOW = datetime.now(BEIJING_TZ)

AGENTS = ["media", "global", "edu", "shared", "side"]
CATEGORIES = ["决策", "知识", "流程", "成果"]
REQUIRED_FM = ["created", "updated", "agent", "category", "status", "confidence", "importance", "source", "tags"]
AGENT_NAMES = {"media":"银月传媒","global":"梅凝出海","edu":"元瑶教育","shared":"玄骨中枢","side":"宋玉创业"}

RULES = [
    ("❌ 无 frontmatter", lambda c,f: not c.startswith("---")),
    ("❌ 行号残留", lambda c,f: bool(re.search(r'^\s*\d+\|', c, re.MULTILINE))),
    ("❌ 时间戳文件名", lambda c,f: bool(re.search(r'\d{8}_\d{6}|^\d{4}-\d{2}-\d{2}_', f))),
]

def check_file(fp, filename):
    with open(fp) as f:
        content = f.read()
    issues = []
    
    for name, check in RULES:
        if check(content, filename):
            issues.append(name)
    
    # Frontmatter field check
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            for field in REQUIRED_FM:
                if f"{field}:" not in fm:
                    issues.append(f"❌ 缺字段 {field}")
                    break
    
    return issues

def main():
    now = time.time()  # for file age checks
    total_files = 0
    issue_files = 0
    issues_by_type = {}
    
    report_lines = [f"# Vault 合规检查报告 · {NOW.strftime('%Y-%m-%d %H:%M')}", ""]
    
    for agent in AGENTS:
        agent_name = AGENT_NAMES.get(agent, agent)
        agent_issues = []
        
        for cat in CATEGORIES:
            d = VAULT / "Agents" / agent / cat
            if not d.exists():
                continue
            for f in sorted(d.iterdir()):
                if not f.name.endswith(".md"):
                    continue
                if f.name in ("README.md",):
                    continue
                
                total_files += 1
                issues = check_file(f, f.name)
                if issues:
                    issue_files += 1
                    for iss in issues:
                        issues_by_type[iss] = issues_by_type.get(iss, 0) + 1
                    agent_issues.append(f"  - {cat}/{f.name}: {'; '.join(issues)}")
        
        if agent_issues:
            report_lines.append(f"## {agent_name} ({agent})")
            report_lines.extend(agent_issues)
            report_lines.append("")
    
    # Summary
    report_lines.insert(1, f"\n总计: {total_files} 文件, {issue_files} 有问题\n")
    if issue_files == 0:
        report_lines.insert(2, "✅ 全部合规！")
    else:
        report_lines.insert(2, f"⚠️  {issue_files}/{total_files} 文件存在问题")
        report_lines.insert(3, "")
        report_lines.insert(4, "### 问题统计")
        for iss, count in sorted(issues_by_type.items(), key=lambda x: -x[1]):
            report_lines.insert(5, f"- {iss}: {count} 次")
        report_lines.insert(6, "")
    
    # Conversation record check (7-day retention)
    report_lines.append("\n---\n## 对话记录老化检查\n")
    conv_old = 0
    conv_total = 0
    for agent in AGENTS:
        d = VAULT / "Agents" / agent / "对话记录"
        if not d.exists():
            continue
        for f in sorted(d.iterdir()):
            if not f.name.endswith(".md"):
                continue
            conv_total += 1
            age = now - f.stat().st_mtime
            if age > 7 * 86400:
                report_lines.append(f"- ⚠️  {agent}/对话记录/{f.name} ({age/86400:.0f}天) 超过7天")
                conv_old += 1
    if conv_old > 0:
        report_lines.append(f"\n⚠️  {conv_old}/{conv_total} 对话记录超过保留期")
    else:
        report_lines.append(f"✅  {conv_total} 条对话记录均在7天保留期内")
    
    report_lines.append("")
    
    report = "\n".join(report_lines)
    
    # Write report to Daily/
    date_str = NOW.strftime("%Y-%m-%d")
    report_dir = VAULT / "Daily"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"合规检查_{date_str}.md"
    report_path.write_text(report, encoding="utf-8")
    
    print(report)
    
    # Exit with status: 0 = all clean, 1 = issues found
    return 0 if issue_files == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
