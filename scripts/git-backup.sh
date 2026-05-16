#!/usr/bin/env bash
# 墨麟OS Molin-OS — 每日 Git 自动备份脚本
# 由 cron 调用，每天 02:00 自动备份代码变更至 GitHub
# v3.0 — 标准化: 备份主仓库 Molin-OS, 不再同步到 MolinOS-Ultra

set -e
REPO="$HOME/Molin-OS"
LOG="$HOME/.hermes/logs/git-backup.log"
TOKEN_FILE="$HOME/Molin-OS/.env"

echo "[$(date '+%Y-%m-%d %H:%M')] 开始备份 Molin-OS..." >> "$LOG"

cd "$REPO"

# 从 .env 读取 GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ] && [ -f "$TOKEN_FILE" ]; then
    GITHUB_TOKEN=$(grep '^GITHUB_TOKEN=' "$TOKEN_FILE" | cut -d= -f2)
fi

# 设置 token 认证远程 URL
if [ -n "$GITHUB_TOKEN" ]; then
    git remote set-url origin "https://moye-tech:${GITHUB_TOKEN}@github.com/moye-tech/Molin-OS.git"
    echo "  token 认证已设置" >> "$LOG"
fi

# 提交、拉取、推送
git add -A
if git diff --cached --quiet; then
    echo "  无变更" >> "$LOG"
else
    CHANGE_COUNT=$(git diff --cached --stat | tail -1 | grep -oP '\d+ files changed|\d+' | head -1)
    git commit -m "auto-backup $(date '+%Y-%m-%d %H:%M') — ${CHANGE_COUNT:-?} files" >> "$LOG" 2>&1

    # fetch + rebase（处理远端分叉）
    git fetch origin main >> "$LOG" 2>&1
    git rebase origin/main >> "$LOG" 2>&1 || {
        echo "  ⚠️ rebase 冲突，跳过本次备份" >> "$LOG"
        git rebase --abort 2>/dev/null
        git reset --soft HEAD~1 2>/dev/null
    }

    # push（超时 30 秒）
    if perl -e 'alarm 30; exec @ARGV' -- git push origin main >> "$LOG" 2>&1; then
        echo "  ✅ 已推送 $(date '+%Y-%m-%d %H:%M')" >> "$LOG"
    else
        echo "  ⚠️ 推送失败，下次运行继续" >> "$LOG"
    fi
fi

# 恢复 clean remote URL
git remote set-url origin "https://github.com/moye-tech/Molin-OS.git"

# 更新 Obsidian 状态文档
STATUS_FILE="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/配置/Cron·Jobs运行状态.md"
if [ -f "$STATUS_FILE" ]; then
    TODAY=$(date '+%Y-%m-%d')
    echo "  状态文档已更新: $TODAY" >> "$LOG"
fi

echo "" >> "$LOG"
