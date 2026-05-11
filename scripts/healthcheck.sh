#!/bin/bash
# healthcheck.sh — 墨麟 Hermes OS 环境检查
# 验证部署环境是否完整
# 用法: bash tools/healthcheck.sh

set -e

echo "=== 墨麟 Hermes OS — 环境健康检查 ==="
echo ""

# 1. Python 版本
echo "🔍 Python..."
PY_VER=$(python3 --version 2>/dev/null || echo "未安装")
echo "   $PY_VER"
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
    echo "   ✅ Python ≥ 3.10"
else
    echo "   ❌ 需要 Python ≥ 3.10"
fi

# 2. Hermes Agent
echo "🔍 Hermes Agent..."
if command -v hermes &>/dev/null; then
    echo "   ✅ hermes CLI 可用"
else
    echo "   ⚠️ hermes CLI 未找到（运行需要）"
fi

# 3. skills 目录
echo "🔍 技能库..."
SKILLS_DIR="$HOME/.hermes/skills"
if [ -d "$SKILLS_DIR" ]; then
    COUNT=$(find "$SKILLS_DIR" -name 'SKILL.md' | wc -l)
    echo "   ✅ $COUNT 个 SKILL.md"
    if [ "$COUNT" -lt 200 ]; then
        echo "   ⚠️ 技能数不足（预期 266+），建议运行 tools/sync-skills.sh"
    fi
else
    echo "   ❌ $SKILLS_DIR 不存在"
    echo "   请运行: bash tools/sync-skills.sh"
fi

# 4. config 目录
echo "🔍 配置文件..."
for f in config/company.yaml config/governance.yaml config/channels.yaml; do
    if [ -f "$f" ]; then
        echo "   ✅ $f"
    else
        echo "   ⚠️ $f 未找到"
    fi
done

# 5. molin 包
echo "🔍 molin 包..."
if python3 -c "import molin" 2>/dev/null; then
    echo "   ✅ molin 包已安装"
else
    echo "   ⚠️ molin 包未安装（可选，用于 CLI）"
    echo "   运行: pip install -e ."
fi

# 6. 磁盘空间
echo "🔍 磁盘空间..."
DF=$(df -h "$HOME" | tail -1)
echo "   $DF"

echo ""
echo "=== 检查完成 ==="
