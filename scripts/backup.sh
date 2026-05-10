#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 墨麟OS 完整系统备份脚本
# 双目标同步：GitHub（代码+技能） + 本地硬盘（全量带密钥）
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/molin_backup_${TIMESTAMP}.log"
HERMES_HOME="${HOME}/.hermes"
REPO_DIR="${HOME}/Molin-OS"
DISK_MOUNT="/Volumes/MolinOS"
DISK_BACKUP_DIR="${DISK_MOUNT}/hermes"
RETENTION_DAYS=7

# ── Logging ────────────────────────────────────────────────────
exec > >(tee -a "$LOG_FILE") 2>&1
echo "=== 墨麟OS 备份开始 $(date) ==="

# ── 检查本地硬盘是否挂载 ───────────────────────────────────────
check_disk() {
    if mount | grep -q "on ${DISK_MOUNT} "; then
        echo "✅ 本地硬盘已挂载: ${DISK_MOUNT}"
        return 0
    else
        echo "⚠️  本地硬盘未挂载: ${DISK_MOUNT} — 跳过本地备份"
        return 1
    fi
}

# ── Step 1: 导出技能到 Git 仓库 ────────────────────────────────
sync_skills_to_repo() {
    echo ""
    echo "── Step 1: 导出技能到仓库 ──"

    # 清空仓库技能目录，保留 .gitkeep
    if [ -d "${REPO_DIR}/skills" ]; then
        find "${REPO_DIR}/skills" -mindepth 1 -not -name '.gitkeep' -exec rm -rf {} + 2>/dev/null || true
    fi
    mkdir -p "${REPO_DIR}/skills"

    # 复制所有 Hermes 技能（SKILL.md + 引用文件）
    local count=0
    for skill_dir in "${HERMES_HOME}/skills/"*/; do
        skill_name=$(basename "$skill_dir")
        # 跳过非目录、隐藏文件
        [ "$skill_name" = "*" ] && continue
        cp -r "$skill_dir" "${REPO_DIR}/skills/${skill_name}"
        count=$((count + 1))
    done
    echo "   ✅ 导出 ${count} 个技能到仓库"

    # 检测是否有变更
    cd "${REPO_DIR}"
    if git diff --quiet && git diff --cached --quiet; then
        echo "   ℹ️  技能无变更，跳过提交"
    else
        git add skills/
        git commit -m "backup: 技能同步 $(date +%Y-%m-%d) — ${count}个技能"
        echo "   ✅ 已提交技能变更"
    fi
}

# ── Step 2: 导出 Cron 配置到仓库 ───────────────────────────────
sync_cron_to_repo() {
    echo ""
    echo "── Step 2: 导出 Cron 配置 ──"

    mkdir -p "${REPO_DIR}/backup"

    # hermes cron list 可能不可用在非交互环境，从数据库直接读
    if [ -f "${HERMES_HOME}/cron.db" ]; then
        cp "${HERMES_HOME}/cron.db" "${REPO_DIR}/backup/cron.db"
        echo "   ✅ 已导出 cron.db"
    fi

    # 也保存 cron jobs.yaml 模板
    if [ -f "${HERMES_HOME}/molin/cron/jobs.yaml" ]; then
        cp "${HERMES_HOME}/molin/cron/jobs.yaml" "${REPO_DIR}/backup/jobs.yaml"
        echo "   ✅ 已导出 jobs.yaml 模板"
    fi

    cd "${REPO_DIR}"
    git add backup/ 2>/dev/null || true
    if git diff --cached --quiet; then
        echo "   ℹ️  Cron 配置无变更"
    else
        git commit -m "backup: Cron配置同步 $(date +%Y-%m-%d)"
        echo "   ✅ 已提交 Cron 配置"
    fi
}

# ── Step 3: Push 到 GitHub ─────────────────────────────────────
push_to_github() {
    echo ""
    echo "── Step 3: 推送到 GitHub ──"
    cd "${REPO_DIR}"

    # 先拉取远端防止冲突
    git pull --rebase origin main 2>&1 || echo "   ⚠️  pull 失败（继续尝试 push）"

    if git push origin main 2>&1; then
        echo "   ✅ 已推送到 GitHub"
    else
        echo "   ❌ GitHub 推送失败，检查网络/权限"
        return 1
    fi
}

# ── Step 4: Rsync 到本地硬盘 ───────────────────────────────────
sync_to_disk() {
    echo ""
    echo "── Step 4: 同步到本地硬盘 ──"

    if ! check_disk; then
        return 1
    fi

    mkdir -p "${DISK_BACKUP_DIR}"

    # 排除列表：缓存、临时文件、日志（保留配置和密钥）
    local EXCLUDE=(
        "--exclude=hermes-agent/venv/"
        "--exclude=hermes-agent/.git/"
        "--exclude=hermes-agent/__pycache__/"
        "--exclude=cache/"
        "--exclude=audio_cache/"
        "--exclude=logs/"
        "--exclude=sessions/"
        "--exclude=.DS_Store"
        "--exclude=*.pyc"
        "--exclude=__pycache__/"
    )

    rsync -av --delete "${EXCLUDE[@]}" "${HERMES_HOME}/" "${DISK_BACKUP_DIR}/" 2>&1 | tail -5

    # 写入时间戳
    date > "${DISK_BACKUP_DIR}/.last_backup"
    echo "${TIMESTAMP}" > "${DISK_BACKUP_DIR}/.backup_version"

    echo "   ✅ 本地硬盘同步完成 → ${DISK_BACKUP_DIR}"
    du -sh "${DISK_BACKUP_DIR}"
}

# ── Step 5: 清理旧备份 ─────────────────────────────────────────
cleanup_old_backups() {
    echo ""
    echo "── Step 5: 清理旧日志 ──"
    find /tmp -name "molin_backup_*.log" -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    echo "   ✅ 清理 ${RETENTION_DAYS} 天前的备份日志"
}

# ── 备份完成摘要 ───────────────────────────────────────────────
summary() {
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "  墨麟OS 备份完成"
    echo "  时间: $(date)"
    echo "  日志: ${LOG_FILE}"
    echo "═══════════════════════════════════════════════"
}

# ── 主流程 ─────────────────────────────────────────────────────
main() {
    # Step 1-2: 导出到仓库
    sync_skills_to_repo
    sync_cron_to_repo

    # Step 3: Push GitHub
    push_to_github || echo "⚠️  GitHub 推送失败（本地备份继续）"

    # Step 4: Rsync 本地硬盘
    sync_to_disk || echo "⚠️  本地硬盘未挂载，跳过"

    # Step 5: 清理
    cleanup_old_backups

    # 完成
    summary
}

main "$@"
