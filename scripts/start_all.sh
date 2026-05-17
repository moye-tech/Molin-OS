#!/bin/bash
# 墨麟OS v3.0 · 一键启动脚本
# 用法: bash ~/Molin-OS/scripts/start_all.sh

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║     墨麟OS v3.0 · 全服务启动                   ║"
echo "╚════════════════════════════════════════════════╝"

set -a; source "$HOME/Molin-OS/.env" 2>/dev/null || true; set +a

declare -A NAMES
NAMES[media]="🎬 全媒体" NAMES[edu]="📚 教育" NAMES[side]="⚡ 副业"
NAMES[shared]="🏛️ 共享"  NAMES[global]="🌏 出海"

# ① 启动5个Hermes Agent
echo ""; echo "── ① 启动5个Hermes Agent ──"
for profile in media edu side shared global; do
    hermes -p "$profile" gateway stop 2>/dev/null || true
    sleep 1
    hermes -p "$profile" gateway start --daemon 2>/dev/null
    sleep 2
    STATUS=$(hermes -p "$profile" gateway status 2>/dev/null | grep -o "running\|stopped" || echo "unknown")
    if [ "$STATUS" = "running" ]; then
        echo -e "  ${GREEN}✅ ${NAMES[$profile]} 在线${NC}"
    else
        echo -e "  ${RED}❌ ${NAMES[$profile]} 启动失败（tail /tmp/hermes-${profile}.log）${NC}"
    fi
done

# ② 启动Web管理界面
echo ""; echo "── ② hermes-web-ui (port 3000) ──"
if ! lsof -i:3000 -t &>/dev/null; then
    hermes-web-ui start --port 3000 >> /tmp/molin-webui.log 2>&1 &
    sleep 3
fi
lsof -i:3000 -t &>/dev/null && \
    echo -e "  ${GREEN}✅ Web管理界面: http://localhost:3000${NC}" || \
    echo -e "  ${YELLOW}⚠️ hermes-web-ui 未启动${NC}"

# ③ 启动Open-Design
echo ""; echo "── ③ Open-Design (port 3001) ──"
if [ -d "$HOME/open-design" ] && ! lsof -i:3001 -t &>/dev/null; then
    cd ~/open-design && pnpm dev --port 3001 >> /tmp/molin-opendesign.log 2>&1 &
    sleep 5
fi
lsof -i:3001 -t &>/dev/null && \
    echo -e "  ${GREEN}✅ AI设计引擎: http://localhost:3001${NC}" || \
    echo -e "  ${YELLOW}⚠️ Open-Design 未启动${NC}"

# ④ 启动记忆桥接守护进程
echo ""; echo "── ④ Memory Bridge (每20分钟同步) ──"
if ! pgrep -f "memory_bridge.py" &>/dev/null; then
    python3.11 "$HOME/Molin-OS/tools/memory_bridge.py" watch \
        >> "$HOME/Molin-OS/logs/memory_bridge.log" 2>&1 &
    sleep 2
fi
pgrep -f "memory_bridge.py" &>/dev/null && \
    echo -e "  ${GREEN}✅ Memory Bridge 运行中${NC}" || \
    echo -e "  ${YELLOW}⚠️ Memory Bridge 未启动${NC}"

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║  🎉 墨麟OS 全部服务已启动                      ║"
echo "╟────────────────────────────────────────────────╢"
echo "║  Web管理界面:  http://localhost:3000           ║"
echo "║  AI设计引擎:   http://localhost:3001           ║"
echo "║  知识库:       iCloud Obsidian Vault (v3.0 flat) ║"
echo "╟────────────────────────────────────────────────╢"
echo "║  飞书机器人: 墨麟·全媒体/教育/副业/共享/出海   ║"
echo "╟────────────────────────────────────────────────╢"
echo "║  状态查看: bash ~/Molin-OS/scripts/status.sh  ║"
echo "╚════════════════════════════════════════════════╝"
