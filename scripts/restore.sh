#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 墨麟OS 一键还原脚本
# 支持两种来源：
#   1. 本地硬盘 /Volumes/MolinOS（含密钥，完整还原）
#   2. GitHub moye-tech/Molin-OS（需手动输入密钥，代码+技能恢复）
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[墨麟]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; }

DISK_MOUNT="/Volumes/MolinOS"
HERMES_HOME="${HOME}/.hermes"
MOLIN_REPO_DIR="${HOME}/Molin-OS"
RESTORE_LOG="/tmp/molin_restore_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$RESTORE_LOG") 2>&1

echo ""
echo "═══════════════════════════════════════════"
echo "  墨麟OS 系统还原"
echo "  时间: $(date)"
echo "═══════════════════════════════════════════"
echo ""

# ── 检测还原源 ───────────────────────────────────────────────
detect_source() {
    if mount | grep -q "on ${DISK_MOUNT} " && [ -d "${DISK_MOUNT}/hermes" ]; then
        echo "local"
    else
        echo "github"
    fi
}

# ── Step 1: 安装 Hermes Agent ──────────────────────────────────
install_hermes() {
    log "Step 1: 安装 Hermes Agent"
    if command -v hermes &>/dev/null; then
        log "  Hermes 已安装: $(hermes --version 2>&1 | head -1)"
    else
        log "  正在安装 Hermes..."
        curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
        log "  ✅ Hermes 安装完成"
    fi
}

# ── Step 2: 从本地硬盘还原（含密钥） ───────────────────────────
restore_from_local() {
    log "Step 2: 从本地硬盘还原 ~/.hermes/"
    RSYNC_OPTS="-av"
    EXCLUDE=(
        "--exclude=hermes-agent/venv/"
        "--exclude=hermes-agent/.git/"
        "--exclude=hermes-agent/__pycache__/"
        "--exclude=cache/"
        "--exclude=audio_cache/"
        "--exclude=logs/"
        "--exclude=sessions/"
        "--exclude=.DS_Store"
    )
    rsync ${RSYNC_OPTS} "${EXCLUDE[@]}" "${DISK_MOUNT}/hermes/" "${HERMES_HOME}/"
    log "  ✅ ~/.hermes/ 完整还原（含密钥）"
}

restore_repo_from_local() {
    log "  还原 Git 仓库..."
    if [ -d "${DISK_MOUNT}/Molin-OS/.git" ]; then
        [ -d "${MOLIN_REPO_DIR}" ] && mv "${MOLIN_REPO_DIR}" "${MOLIN_REPO_DIR}.old.$(date +%Y%m%d)"
        rsync -av "${DISK_MOUNT}/Molin-OS/" "${MOLIN_REPO_DIR}/"
        log "  ✅ Git 仓库还原完成"
    fi
}

# ── Step 3: 从 GitHub 还原（需密钥） ───────────────────────────
restore_from_github() {
    log "Step 3: 从 GitHub 克隆仓库"
    if [ -d "${MOLIN_REPO_DIR}" ]; then
        log "  仓库已存在，拉取最新..."
        cd "${MOLIN_REPO_DIR}" && git pull origin main
    else
        git clone https://github.com/moye-tech/Molin-OS.git "${MOLIN_REPO_DIR}"
        log "  ✅ 仓库克隆完成"
    fi

    # 还原技能
    log ""
    log "  还原技能..."
    if [ -d "${MOLIN_REPO_DIR}/skills" ]; then
        mkdir -p "${HERMES_HOME}/skills"
        for skill_dir in "${MOLIN_REPO_DIR}/skills/"*/; do
            skill_name=$(basename "$skill_dir")
            [ "$skill_name" = "*" ] && continue
            [ -d "${HERMES_HOME}/skills/${skill_name}" ] && rm -rf "${HERMES_HOME}/skills/${skill_name}"
            cp -r "$skill_dir" "${HERMES_HOME}/skills/${skill_name}"
        done
        local count=$(ls -1 "${HERMES_HOME}/skills/" | wc -l)
        log "  ✅ ${count} 个技能已还原"
    fi

    # 还原 Cron 配置
    if [ -f "${MOLIN_REPO_DIR}/backup/cron.db" ]; then
        cp "${MOLIN_REPO_DIR}/backup/cron.db" "${HERMES_HOME}/cron.db"
        log "  ✅ Cron 配置已还原"
    fi
}

# ── Step 4: 配置 Python 环境 ──────────────────────────────────
setup_python_env() {
    log "Step 4: 配置 Python 环境"

    # 创建/激活 venv
    if [ ! -d "${HERMES_HOME}/hermes-agent/venv" ]; then
        python3 -m venv "${HERMES_HOME}/hermes-agent/venv"
    fi
    source "${HERMES_HOME}/hermes-agent/venv/bin/activate"

    # 安装 molib
    if [ -d "${MOLIN_REPO_DIR}/molib" ]; then
        pip install -e "${MOLIN_REPO_DIR}/molib" --quiet
        log "  ✅ molib 已安装"
    fi

    # 安装额外依赖
    pip install httpx aiohttp pandas numpy openai markdown loguru schedule flask flask-cors --quiet 2>/dev/null || true

    log "  ✅ Python 环境就绪"
}

# ── Step 5: 配置密钥（仅 GitHub 还原时需要） ──────────────────
setup_secrets() {
    local SOURCE="$1"
    log "Step 5: 配置密钥"

    if [ "$SOURCE" = "local" ]; then
        log "  ✅ 密钥已从本地硬盘还原，跳过"
        return
    fi

    # GitHub 还原：引导用户输入密钥
    warn ""
    warn "  ═════════════════════════════════════"
    warn "  从 GitHub 还原需要手动配置密钥"
    warn "  请准备以下信息："
    warn "  ═════════════════════════════════════"
    warn ""

    ENV_FILE="${HERMES_HOME}/.env"

    # 检查是否已有 .env
    if [ -f "$ENV_FILE" ]; then
        warn "  .env 已存在，将追加缺失项"
    fi

    echo ""
    read -p "  DEEPSEEK_API_KEY: " DEEPSEEK_KEY
    read -p "  DASHSCOPE_API_KEY: " DASHSCOPE_KEY
    read -p "  OPENROUTER_API_KEY: " OPENROUTER_KEY
    read -p "  FEISHU_APP_ID: " FEISHU_ID
    read -p "  FEISHU_APP_SECRET: " FEISHU_SECRET
    read -p "  SUPERMEMORY_API_KEY: " SM_KEY
    read -p "  GITHUB_TOKEN: " GH_TOKEN

    cat >> "$ENV_FILE" <<EOF

# ── 手动还原 $(date) ──
DEEPSEEK_API_KEY=${DEEPSEEK_KEY}
DASHSCOPE_API_KEY=${DASHSCOPE_KEY}
OPENROUTER_API_KEY=${OPENROUTER_KEY}
FEISHU_APP_ID=${FEISHU_ID}
FEISHU_APP_SECRET=${FEISHU_SECRET}
SUPERMEMORY_API_KEY=${SM_KEY}
GITHUB_TOKEN=${GH_TOKEN}
EOF

    log "  ✅ 密钥已写入 ~/.hermes/.env"
}

# ── Step 6: 安装 feishu-cli ────────────────────────────────────
install_feishu_cli() {
    log "Step 6: 安装 feishu-cli"
    if command -v feishu-cli &>/dev/null; then
        log "  feishu-cli 已安装: $(feishu-cli --version 2>&1 | head -1)"
    else
        warn "  feishu-cli 未安装，请从 Molin-OS 仓库手动安装:"
        warn "    cd ~/Molin-OS/bots/feishu-cli && bash install.sh"
    fi
}

# ── Step 7: 还原 Hermes Cron 作业 ─────────────────────────────
restore_cron_jobs() {
    log "Step 7: 还原定时作业"

    # 使用 Hermes CLI 重新创建 cron 作业
    # 作业定义来自 jobs.yaml 或备份的 cron.db
    if [ -f "${HERMES_HOME}/molin/cron/jobs.yaml" ]; then
        log "  发现 jobs.yaml，请手动通过 Hermes 恢复 cron 作业"
        log "  参考: ~/.hermes/molin/cron/jobs.yaml"
    fi

    log "  ℹ️  定时作业需要 Hermes 启动后通过 'hermes cron create' 恢复"
    log "  或使用 Python 脚本从 cron.db 导入"
}

# ── Step 8: 启动 Gateway ──────────────────────────────────────
start_gateway() {
    log "Step 8: 启动 Gateway"
    if pgrep -f "hermes_cli.main gateway" >/dev/null 2>&1; then
        log "  Gateway 已运行"
    else
        log "  正在启动 Gateway..."
        hermes gateway start 2>&1 || {
            warn "  自动启动失败，手动运行: hermes gateway start"
        }
        sleep 3
        if pgrep -f "hermes_cli.main gateway" >/dev/null 2>&1; then
            log "  ✅ Gateway 已启动"
        else
            warn "  Gateway 未启动，请手动检查"
        fi
    fi
}

# ── 验证还原完整性 ────────────────────────────────────────────
verify_restore() {
    log ""
    log "═══ 验证还原完整性 ═══"

    local ok=0
    local fail=0

    check() {
        if [ "$1" -eq 0 ]; then
            log "  ✅ $2"
            ok=$((ok+1))
        else
            err "  ❌ $2"
            fail=$((fail+1))
        fi
    }

    [ -f "${HERMES_HOME}/config.yaml" ]; check $? "config.yaml"
    [ -f "${HERMES_HOME}/.env" ];        check $? ".env"
    [ -d "${HERMES_HOME}/skills" ];      check $? "skills/ ($(ls -1 ${HERMES_HOME}/skills/ 2>/dev/null | wc -l)个)"
    command -v hermes &>/dev/null;       check $? "hermes CLI"
    [ -d "${MOLIN_REPO_DIR}/molib" ];    check $? "molib 代码"
    python3 -c "import molib" 2>/dev/null; check $? "molib Python包"

    log ""
    log "════════════════════════════════════"
    log "  还原完成: ${ok} 通过, ${fail} 失败"
    log "════════════════════════════════════"
}

# ── 主流程 ─────────────────────────────────────────────────────
main() {
    local SOURCE=$(detect_source)
    log "还原源: ${SOURCE}"

    install_hermes

    if [ "$SOURCE" = "local" ]; then
        restore_from_local
        restore_repo_from_local
    else
        restore_from_github
    fi

    setup_python_env
    setup_secrets "$SOURCE"
    install_feishu_cli
    restore_cron_jobs
    start_gateway
    verify_restore

    echo ""
    log "═══ 墨麟OS 还原完毕 ═══"
    if [ "$SOURCE" = "github" ]; then
        warn "请手动恢复 cron 作业: hermes cron create ..."
        warn "参考: ${MOLIN_REPO_DIR}/backup/jobs.yaml"
    fi
    log "日志: ${RESTORE_LOG}"
}

main "$@"
