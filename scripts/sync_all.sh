#!/usr/bin/env bash
# 墨麟OS 记忆同步管道 — 报告同步 + 架构采集

set -e
SCRIPTS_DIR="/Users/laomo/Molin-OS/scripts"

# 加载环境变量
if [ -f "$HOME/.hermes/.env" ]; then
    set -a
    source "$HOME/.hermes/.env"
    set +a
fi

DRY_RUN=""
if [ "$1" = "--dry-run" ]; then
    DRY_RUN="--dry-run"
fi

echo "╔══════════════════════════════════════╗"
echo "║   墨麟OS 记忆同步管道                ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Step 1: 实时记忆同步（对话提取 + 分类 + 双端写入）
echo "🧠 [1/3] 实时记忆同步..."
/opt/homebrew/bin/python3.11 "$SCRIPTS_DIR/sync_memory.py"
echo ""

# Step 2: 报告同步到 Obsidian
echo "📋 [2/3] 同步报告到 Obsidian..."
/opt/homebrew/bin/python3.11 "$SCRIPTS_DIR/obsidian_sync.py" $DRY_RUN
echo ""

# Step 3: 架构采集
echo "🏗️  [3/3] 采集系统架构..."
export SUPERMEMORY_API_KEY
/opt/homebrew/bin/python3.11 "$SCRIPTS_DIR/collect_architecture.py"
echo ""

# Step 4: Relay输出同步到Obsidian
echo "📡 [4/4] 同步 Relay 产出到 Obsidian..."
/opt/homebrew/bin/python3.11 "$SCRIPTS_DIR/relay_to_obsidian.py"
echo ""

echo "✅ 记忆同步管道完成"
