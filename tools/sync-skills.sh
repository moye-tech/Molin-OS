#!/bin/bash
# sync-skills.sh — 将 Hermes OS 仓库的 skills/ 同步到 Hermes Agent
# 用法: bash tools/sync-skills.sh
# 适用场景: 全新部署或技能库恢复

set -e

SKILLS_SRC="${1:-../skills}"
SKILLS_DST="$HOME/.hermes/skills"
BACKUP_DIR="$HOME/.hermes/skills_backup_$(date +%Y%m%d_%H%M)"

echo "=== 墨麟 Hermes OS — 技能同步 ==="
echo "源: $SKILLS_SRC"
echo "目标: $SKILLS_DST"

# 检查源是否存在
if [ ! -d "$SKILLS_SRC" ]; then
    echo "❌ 错误: 技能源目录不存在: $SKILLS_SRC"
    echo "   请从 Hermes-OS 仓库根目录运行: bash tools/sync-skills.sh"
    exit 1
fi

# 备份现有技能
if [ -d "$SKILLS_DST" ]; then
    echo "📦 备份现有技能到 $BACKUP_DIR ..."
    cp -r "$SKILLS_DST" "$BACKUP_DIR"
    echo "   ✅ 备份完成"
fi

# 同步技能
echo "📋 同步技能..."
mkdir -p "$SKILLS_DST"

# 使用 rsync 同步，排除 DESCRIPTION.md 等元文件
rsync -a --delete \
    --include='*/' \
    --include='SKILL.md' \
    --include='*.py' \
    --include='*.json' \
    --include='*.yaml' \
    --include='*.yml' \
    --include='.*' \
    --exclude='*' \
    "$SKILLS_SRC/" "$SKILLS_DST/"

# 统计
SRC_COUNT=$(find "$SKILLS_SRC" -name 'SKILL.md' | wc -l)
DST_COUNT=$(find "$SKILLS_DST" -name 'SKILL.md' | wc -l)

echo ""
echo "=== 同步完成 ==="
echo "源技能: $SRC_COUNT"
echo "目标技能: $DST_COUNT"
echo ""
echo "💡 提示: 技能已同步到 $SKILLS_DST"
echo "   下次 Hermes Agent 启动时自动加载新技能"
echo "   如需恢复旧技能: cp -r $BACKUP_DIR/* $SKILLS_DST/"
