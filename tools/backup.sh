#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# 墨麟 Hermes OS — 备份脚本
# 用法: bash tools/backup.sh
# ═══════════════════════════════════════════════════════════
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${HOME}/.molin/backups"
BACKUP_FILE="${BACKUP_DIR}/molin_backup_${TIMESTAMP}.tar.gz"

mkdir -p "${BACKUP_DIR}"

echo "📦 备份墨麟系统..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cd "${REPO_DIR}"

tar -czf "${BACKUP_FILE}" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='.env' \
    --exclude='*.egg-info' \
    skills/ \
    config/ \
    molin/ \
    docs/ \
    tools/ \
    cron/ \
    tests/ \
    README.md \
    Makefile \
    setup.sh \
    requirements.txt \
    setup.py \
    .env.example \
    2>/dev/null

SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "✅ 备份完成: ${BACKUP_FILE} (${SIZE})"

# 保留最近 10 个备份
ls -t "${BACKUP_DIR}"/molin_backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
echo "   备份目录: ${BACKUP_DIR} (保留最近10个)"
