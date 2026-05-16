#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 墨麟 OS · Molin-OS — 一键部署脚本
# =============================================================
# 用法:
#   git clone git@github.com:moye-tech/Molin-OS.git
#   cd Molin-OS
#   bash setup.sh
#
# 支持 macOS (Apple Silicon / Intel) 和 Linux
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ── 颜色 ──
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── 初始化 Git 子模块 ──
echo -e "${CYAN}⟳ 初始化 Git 子模块...${NC}"
if [ -f ".gitmodules" ]; then
    git submodule update --init --recursive 2>/dev/null || \
        echo -e "${YELLOW}  ⚠️ 子模块初始化跳过（网络问题或非 git 仓库），可稍后手动执行: git submodule update --init --recursive${NC}"
fi

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║                                              ║"
echo "║     墨 麟  O S                              ║"
echo "║     Molin-OS · AI 一人公司操作系统             ║"
echo "║                                              ║"
echo "║     20 家子公司 · 559 项技能 · 21 个定时任务    ║"
echo "║                                              ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 检测 OS ──
OS_TYPE="$(uname -s)"
case "$OS_TYPE" in
    Darwin)  OS_NAME="macOS" ;;
    Linux)   OS_NAME="Linux" ;;
    *)       OS_NAME="$OS_TYPE" ;;
esac
echo -e "${CYAN}检测到系统: ${OS_NAME} ($(uname -m))${NC}"
echo ""

# ── Step 1: 检查 Python ──
echo -e "${YELLOW}[1/5]${NC} 检查 Python..."

PYTHON=""
for candidate in python3.11 python3.12 python3; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" --version 2>&1 | awk '{print $2}')
        major=$(echo "$ver" | cut -d. -f1)
        minor=$(echo "$ver" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}✗${NC} Python 3.11+ 未安装"
    echo "      macOS: brew install python@3.11"
    echo "      Linux: sudo apt install python3.11"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python: $($PYTHON --version)"

# ── Step 2: 检查可选依赖 ──
echo -e "${YELLOW}[2/5]${NC} 检查系统工具..."

if command -v ffmpeg &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} FFmpeg: $(ffmpeg -version 2>&1 | head -1 | awk '{print $3}')"
else
    echo -e "  ${YELLOW}⚠${NC} FFmpeg 未安装 (视频功能不可用)"
    echo "      macOS: brew install ffmpeg"
    echo "      Linux: sudo apt install ffmpeg"
fi

if command -v git &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Git: $(git --version | awk '{print $3}')"
else
    echo -e "  ${RED}✗${NC} Git 未安装"
    exit 1
fi

# ── Step 3: 安装 Python 依赖 ──
echo -e "${YELLOW}[3/5]${NC} 安装 Python 依赖..."

# 尝试创建虚拟环境
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR" 2>/dev/null && \
        echo -e "  ${GREEN}✓${NC} 虚拟环境创建完成" || \
        echo -e "  ${YELLOW}⚠${NC} 虚拟环境创建失败，使用系统 Python"
fi

# 激活虚拟环境（如果存在）
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
    PIP="$VENV_DIR/bin/pip"
else
    PIP="$PYTHON -m pip"
fi

$PIP install --upgrade pip -q 2>/dev/null || true

if [ -f requirements.txt ]; then
    $PIP install -r requirements.txt -q 2>/dev/null && \
        echo -e "  ${GREEN}✓${NC} 依赖安装完成" || \
        echo -e "  ${YELLOW}⚠${NC} 部分依赖安装失败 (非致命)"
else
    echo -e "  ${YELLOW}⚠${NC} requirements.txt 未找到"
fi

# 可编辑安装（让 'python -m molib' 可用）
pip install -e . -q 2>/dev/null && \
    echo -e "  ${GREEN}✓${NC} molib 可编辑安装完成" || \
    echo -e "  ${YELLOW}⚠${NC} molib 安装跳过"

# ── Step 4: 配置环境变量 ──
echo -e "${YELLOW}[4/5]${NC} 初始化配置..."

CONFIG_DIR="${HOME}/.hermes"
mkdir -p "$CONFIG_DIR"

if [ ! -f "${CONFIG_DIR}/.env" ] && [ -f .env.example ]; then
    cp .env.example "${CONFIG_DIR}/.env"
    echo -e "  ${GREEN}✓${NC} 环境变量模板已创建: ${CONFIG_DIR}/.env"
    echo -e "  ${YELLOW}  ⚠ 请编辑 ${CONFIG_DIR}/.env 填入你的 API Keys${NC}"
elif [ -f "${CONFIG_DIR}/.env" ]; then
    echo -e "  ${GREEN}✓${NC} 环境变量已存在"
else
    echo -e "  ${YELLOW}⚠${NC} 未找到 .env.example，跳过"
fi

# ── Step 5: 验证安装 ──
echo -e "${YELLOW}[5/5]${NC} 验证安装..."

# 验证 molib 可导入
if python -c "import molib" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} molib 核心引擎可用"
else
    echo -e "  ${YELLOW}⚠${NC} molib 导入失败 (非致命，检查 PYTHONPATH)"
fi

# 检查目录结构
COMPONENTS=0; TOTAL=0
for dir in molib/config molib/agencies molib/infra molib/shared scripts/ config/; do
    TOTAL=$((TOTAL + 1))
    [ -d "$dir" ] && COMPONENTS=$((COMPONENTS + 1))
done
echo -e "  ${GREEN}✓${NC} 目录结构: ${COMPONENTS}/${TOTAL} 完整"

# ── 完成 ──
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗"
echo -e "║                                              ║"
echo -e "║   ✅  墨 麟 OS 部 署 完 成                   ║"
echo -e "║                                              ║"
echo -e "╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}快速开始:${NC}"
echo "    make check                系统健康检查"
echo "    python -m molib help      查看所有命令"
echo "    make test                 运行测试"
echo ""
echo -e "  ${YELLOW}下一步:${NC}"
echo "    1. 编辑 ${CONFIG_DIR}/.env 填入 API Keys"
echo "    2. 确保 Hermes Agent 已安装并运行"
echo "    3. 阅读 README.md 了解完整功能"
echo ""
echo -e "  ${CYAN}文档:${NC} github.com/moye-tech/Molin-OS"
echo ""
