#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 墨麟OS GitHub 双向同步脚本
# 每次系统更新后运行，确保 GitHub 仓库与本地系统一致
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

REPO_DIR="${HOME}/Molin-OS"
HERMES_HOME="${HOME}/.hermes"
LOG_FILE="/tmp/molin_sync_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== 墨麟OS 双向同步 $(date) ==="

cd "${REPO_DIR}"

# ── Step 0: 拉取 GitHub 最新代码 ─────────────────────────
echo ""
echo "── Step 0: 从 GitHub 拉取最新 ──"
if git pull --rebase origin main 2>&1; then
    echo "   ✅ 已拉取最新代码"
else
    echo "   ⚠️  拉取失败（网络问题或冲突），继续本地同步"
fi

# ── Step 1: 同步技能 ─────────────────────────────────────
echo ""
echo "── Step 1: 同步技能 ──"
mkdir -p "${REPO_DIR}/skills"
# 清空并重导
find "${REPO_DIR}/skills" -mindepth 1 -not -name '.gitkeep' -exec rm -rf {} + 2>/dev/null || true

count=0
for skill_dir in "${HERMES_HOME}/skills/"*/; do
    skill_name=$(basename "$skill_dir")
    [ "$skill_name" = "*" ] && continue
    cp -r "$skill_dir" "${REPO_DIR}/skills/${skill_name}"
    count=$((count + 1))
done
echo "   ✅ 同步 ${count} 个技能"

# ── Step 2: 同步 molib 代码 ──────────────────────────────
echo ""
echo "── Step 2: 同步 molib 代码 ──"
# molib 已在 repo 中，直接 add
git add molib/ registry/ molin-skills/ 2>/dev/null || true

# ── Step 3: 同步配置和脚本 ───────────────────────────────
echo ""
echo "── Step 3: 同步配置 ──"
mkdir -p "${REPO_DIR}/backup"

# Cron 配置
if [ -f "${HERMES_HOME}/cron.db" ]; then
    cp "${HERMES_HOME}/cron.db" "${REPO_DIR}/backup/cron.db"
fi

# Xianyu bot 配置
if [ -f "${HERMES_HOME}/xianyu_bot/config.json" ]; then
    mkdir -p "${REPO_DIR}/backup/xianyu_bot"
    cp "${HERMES_HOME}/xianyu_bot/config.json" "${REPO_DIR}/backup/xianyu_bot/"
    # 不含 cookies.json（密钥）
fi

# 备份脚本
mkdir -p "${REPO_DIR}/scripts"
cp "${HERMES_HOME}/scripts/molin_backup.sh" "${REPO_DIR}/scripts/" 2>/dev/null || true
cp "${HERMES_HOME}/scripts/molin_sync.sh" "${REPO_DIR}/scripts/" 2>/dev/null || true

git add backup/ scripts/ skills/ 2>/dev/null || true

# ── Step 4: 提交变更 ─────────────────────────────────────
echo ""
echo "── Step 4: 提交变更 ──"
if git diff --cached --quiet && git diff --quiet; then
    echo "   ℹ️  无变更，跳过提交"
else
    git commit -m "sync: 双向同步 $(date +%Y-%m-%d_%H:%M) — ${count}技能"
    echo "   ✅ 已提交变更"
fi

# ── Step 5: 推送到 GitHub ────────────────────────────────
echo ""
echo "── Step 5: 推送到 GitHub ──"
if git push origin main 2>&1; then
    echo "   ✅ 已推送到 GitHub — 仓库与本地一致"
else
    echo "   ❌ 推送失败，稍后重试"
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  同步完成 $(date)"
echo "  日志: ${LOG_FILE}"
echo "═══════════════════════════════════════════════"
