#!/bin/bash
G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; NC='\033[0m'
declare -A NAMES
NAMES[media]="🎬 全媒体" NAMES[edu]="📚 教育" NAMES[side]="⚡ 副业"
NAMES[shared]="🏛️ 共享"  NAMES[global]="🌏 出海"

echo ""; echo "═══ 墨麟OS v3.0 · 系统状态 ═══"
echo ""; echo "Hermes Agent:"
for p in media edu side shared global; do
    S=$(hermes -p "$p" gateway status 2>/dev/null | grep -o "running\|stopped" || echo "unknown")
    [ "$S" = "running" ] && echo -e "  ${G}● ${NAMES[$p]}${NC}" || echo -e "  ${R}○ ${NAMES[$p]} (离线)${NC}"
done

echo ""; echo "本地服务:"
lsof -i:3000 -t &>/dev/null && echo -e "  ${G}● Web管理界面 (3000)${NC}" || echo -e "  ${R}○ Web管理界面 (离线)${NC}"
lsof -i:3001 -t &>/dev/null && echo -e "  ${G}● Open-Design  (3001)${NC}" || echo -e "  ${Y}○ Open-Design  (未启动)${NC}"
pgrep -f "memory_bridge.py" &>/dev/null && echo -e "  ${G}● Memory Bridge${NC}"  || echo -e "  ${R}○ Memory Bridge (离线)${NC}"
echo ""
