#!/usr/bin/env bash
# MolinOS Ultra — 每日 Git 自动备份脚本
# 由 cron 调用，每天 02:00 自动备份系统变更
# v2.0 — 修复: 添加 pull --rebase 前置 + GITHUB_TOKEN 认证 + 超时处理

set -e
REPO="$HOME/MolinOS-Ultra"
LOG="$HOME/.hermes/logs/git-backup.log"

echo "[$(date '+%Y-%m-%d %H:%M')] 开始备份..." >> "$LOG"

cd "$REPO"

# 从环境变量或 .env 读取 GITHUB_TOKEN
if [ -z "$GITHUB_TOKEN" ] && [ -f "$HOME/Molin-OS/.env" ]; then
    GITHUB_TOKEN=$(grep '^GITHUB_TOKEN=' "$HOME/Molin-OS/.env" | cut -d= -f2)
fi

# 重构 remote URL 嵌入 token（用于认证）
if [ -n "$GITHUB_TOKEN" ]; then
    CURRENT_URL=$(git remote get-url origin)
    if echo "$CURRENT_URL" | grep -vq "$GITHUB_TOKEN"; then
        TOKEN_URL="https://moye-tech:${GITHUB_TOKEN}@github.com/moye-tech/MolinOS-Ultra.git"
        git remote set-url origin "$TOKEN_URL"
        echo "  token 认证远程 URL 已设置" >> "$LOG"
    fi
fi

# 同步最新系统文件
cp -r "$HOME/Molin-OS/scripts/"*.py "$REPO/scripts/" 2>/dev/null
cp -r "$HOME/Molin-OS/scripts/"*.sh "$REPO/scripts/" 2>/dev/null

# 提交、拉取、推送
git add -A
if git diff --cached --quiet; then
    echo "  无变更" >> "$LOG"
else
    git commit -m "auto-backup $(date '+%Y-%m-%d %H:%M')" >> "$LOG" 2>&1

    # pull --rebase 以处理远端分叉
    git pull --rebase origin main >> "$LOG" 2>&1 || {
        echo "  ⚠️ pull --rebase 冲突，尝试跳过本地备份提交" >> "$LOG"
        git rebase --abort 2>/dev/null
        git reset --soft HEAD~1 2>/dev/null
    }

    # push（超时 30 秒）
    perl -e 'alarm 30; exec @ARGV' -- git push origin main >> "$LOG" 2>&1 && \
        echo "  ✅ 已推送 $(date '+%Y-%m-%d %H:%M')" >> "$LOG" || \
        echo "  ⚠️ 推送超时或失败，下次运行继续" >> "$LOG"
fi

# 恢复 clean remote URL（不暴露 token 在 log 中）
if [ -n "$GITHUB_TOKEN" ]; then
    git remote set-url origin "https://github.com/moye-tech/MolinOS-Ultra.git"
fi

echo "" >> "$LOG"
