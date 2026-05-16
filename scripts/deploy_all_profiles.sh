#!/bin/bash
# 墨麟OS v3.0 · 五Agent批量部署脚本
# 用法：bash ~/Molin-OS/scripts/deploy_all_profiles.sh [--only ]

set -e
MOLIN="$HOME/Molin-OS"
PROFILES_DIR="$HOME/.hermes/profiles"
TARGET="${2:-all}"   # --only media 等

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

log_ok()   { echo -e "  ${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }

# 公共技能（所有Profile共享）
SHARED_SKILLS=(
  "feishu-cli-shared"
  "feishu-message-formatter"
  "molin-ceo-persona"
  "molin-governance"
  "self-learning-loop"
)

# 各Profile专属技能
declare -A PROFILE_SKILLS
PROFILE_SKILLS[media]="xiaohongshu-content-engine seo-machine agent-marketing-content-creator analytics-tracking content-strategy github-trending-scanner world-monitor blogwatcher"
PROFILE_SKILLS[edu]="agent-edu-course-designer agent-sales-deal-strategist agent-marketing-growth-hacker crm-automation ads-engine"
PROFILE_SKILLS[side]="xianyu-automation zhubajie-automation order-manager dev-skill-pack"
PROFILE_SKILLS[shared]="competitor-analysis karpathy-autoresearch finance-report legal-review data-analysis"
PROFILE_SKILLS[global]="localize-to-traditional taiwan-market-skill shopee-automation line-channel"

# SOUL文件映射
declare -A SOUL_FILES
SOUL_FILES[media]="SOUL_MEDIA.md"
SOUL_FILES[edu]="SOUL_EDU.md"
SOUL_FILES[side]="SOUL_SIDE.md"
SOUL_FILES[shared]="SOUL_SHARED.md"
SOUL_FILES[global]="SOUL_GLOBAL.md"

# Agent显示名称
declare -A AGENT_DISPLAY
AGENT_DISPLAY[media]="🎬 全媒体运营"
AGENT_DISPLAY[edu]="📚 教育行业"
AGENT_DISPLAY[side]="⚡ 副业专线"
AGENT_DISPLAY[shared]="🏛️ 共享服务层"
AGENT_DISPLAY[global]="🌏 出海专线"

deploy_one() {
  local PROFILE="$1"
  local PDIR="$PROFILES_DIR/$PROFILE"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "🚀 部署: $PROFILE（${AGENT_DISPLAY[$PROFILE]}）"

  # 创建Profile（已存在则跳过）
  hermes profile create "$PROFILE" 2>/dev/null || true
  mkdir -p "$PDIR/skills" "$PDIR/context"

  # 注入公共技能（软链接）
  local shared_count=0
  for skill in "${SHARED_SKILLS[@]}"; do
    local src="$MOLIN/skills/$skill"
    local dst="$PDIR/skills/$skill"
    if [ -d "$src" ]; then
      [ -L "$dst" ] && rm "$dst"; [ -d "$dst" ] && rm -rf "$dst"
      ln -sf "$src" "$dst" && ((shared_count++))
    else
      log_warn "共享技能目录不存在（跳过）: $skill"
    fi
  done
  log_ok "公共技能: ${shared_count}/${#SHARED_SKILLS[@]}个"

  # 注入专属技能（软链接）
  local profile_count=0
  for skill in ${PROFILE_SKILLS[$PROFILE]}; do
    local src="$MOLIN/skills/$skill"
    local dst="$PDIR/skills/$skill"
    if [ -d "$src" ]; then
      [ -L "$dst" ] && rm "$dst"; [ -d "$dst" ] && rm -rf "$dst"
      ln -sf "$src" "$dst" && ((profile_count++))
    fi
  done
  log_ok "专属技能: ${profile_count}个"

  # 部署SOUL.md
  local soul="$MOLIN/config/$PROFILE/${SOUL_FILES[$PROFILE]}"
  if [ -f "$soul" ]; then
    cp "$soul" "$PDIR/SOUL.md"
    log_ok "SOUL.md: $(wc -l < "$PDIR/SOUL.md")行"
  else
    log_warn "SOUL文件未找到: $soul"
  fi

  # 部署cron_jobs.yaml
  local cron="$MOLIN/config/$PROFILE/cron_jobs.yaml"
  if [ -f "$cron" ]; then
    cp "$cron" "$PDIR/cron_jobs.yaml"
    local jobs
    jobs=$(grep -c "^  - id:" "$PDIR/cron_jobs.yaml" 2>/dev/null || echo "0")
    log_ok "Cron: ${jobs}个定时任务"
  fi

  # 初始化CONTEXT.md占位
  [ ! -f "$PDIR/CONTEXT.md" ] && cat > "$PDIR/CONTEXT.md" << CTXEOF
# ${AGENT_DISPLAY[$PROFILE]} · 背景上下文
更新时间: $(date '+%Y-%m-%d %H:%M:%S')
此文件由 memory_bridge.py 每20分钟自动更新。
CTXEOF

  local total
  total=$(ls "$PDIR/skills/" 2>/dev/null | wc -l | tr -d ' ')
  echo -e "  ${GREEN}✅ $PROFILE 部署完成（技能总数: ${total}）${NC}"
}

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  墨麟OS v3.0 · Profile批量部署          ║"
echo "╚════════════════════════════════════════╝"

if [ "$TARGET" = "all" ]; then
  for p in media edu side shared global; do deploy_one "$p"; done
else
  deploy_one "$TARGET"
fi

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  🎉 部署完成！下一步:                   ║"
echo "║  配置飞书: Step 10                     ║"
echo "║  启动系统: bash scripts/start_all.sh   ║"
echo "╚════════════════════════════════════════╝"
