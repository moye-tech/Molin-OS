#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# 墨麟 Hermes OS — 健康检查脚本
# 用法: bash tools/healthcheck.sh
# ═══════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🩺 墨麟 Hermes OS 健康检查"
echo "============================"
echo ""

FAILS=0

check() {
    local name="$1"
    shift
    if "$@" &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} ${name}"
    else
        echo -e "  ${RED}✗${NC} ${name}"
        FAILS=$((FAILS + 1))
    fi
}

# 环境检查
check "Python 3.10+"  python3 -c "import sys; assert sys.version_info >= (3,10)"
check "Git"            git --version
check "pip"            pip --version

# 依赖检查
check "PyYAML"         python3 -c "import yaml"
check "requests"       python3 -c "import requests"

# 可选依赖
if command -v ffmpeg &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} FFmpeg (视频引擎可用)"
else
    echo -e "  ${YELLOW}⚠${NC} FFmpeg (视频引擎不可用)"
fi

# 墨麟核心
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cd "${REPO_DIR}"

if python3 -c "from molin.core.engine import engine; r=engine.health_check(); print(r['status'])" 2>/dev/null | grep -q "healthy"; then
    echo -e "  ${GREEN}✓${NC} 墨麟核心引擎 (健康)"
else
    echo -e "  ${RED}✗${NC} 墨麟核心引擎 (异常)"
    FAILS=$((FAILS + 1))
fi

# 配置文件
check "公司配置"      test -f config/company.yaml
check "治理配置"      test -f config/governance.yaml
check "渠道配置"      test -f config/channels.yaml
check "环境变量模板"  test -f .env.example

# 知识库
SKILLS_COUNT=$(find skills/ -name "SKILL.md" 2>/dev/null | wc -l)
if [ "$SKILLS_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} 知识库 (${SKILLS_COUNT} SKILL.md)"
else
    echo -e "  ${RED}✗${NC} 知识库 (空)"
    FAILS=$((FAILS + 1))
fi

# 总结
echo ""
if [ "$FAILS" -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过 — 墨麟系统运行正常${NC}"
else
    echo -e "${RED}❌ ${FAILS} 项检查未通过${NC}"
fi
