#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 墨麟OS (Molin OS) — 一键部署脚本
# =============================================================
# 用法: bash setup.sh
#
# 在任意Linux服务器上，克隆仓库后执行此脚本即可完成部署:
#   git clone https://github.com/moye-tech/-Hermes-OS.git
#   cd -Hermes-OS
#   bash setup.sh
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

MOLIN_HOME="${HOME}/.molin"
PYTHON="${PYTHON:-python3}"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║     墨麟OS (Molin OS) 部署脚本          ║"
echo "║     28实体 · 339技能 · ¥52K/月          ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: 检查环境 ──
echo -e "${YELLOW}[1/6]${NC} 检查运行环境..."

if ! command -v $PYTHON &>/dev/null; then
    echo -e "${RED}✗${NC} Python3 未安装。请先安装: sudo apt install python3"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python: $($PYTHON --version)"

if ! command -v ffmpeg &>/dev/null; then
    echo -e "  ${YELLOW}⚠${NC} FFmpeg 未安装 (视频功能将不可用)"
    echo "     安装: sudo apt install ffmpeg"
else
    echo -e "  ${GREEN}✓${NC} FFmpeg: $(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3)"
fi

if ! command -v git &>/dev/null; then
    echo -e "${RED}✗${NC} Git 未安装"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Git: $(git --version)"

# ── Step 2: 创建虚拟环境 ──
echo -e "${YELLOW}[2/6]${NC} 创建 Python 虚拟环境..."
VENV_DIR="${MOLIN_HOME}/venv"

if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
    echo -e "  ${GREEN}✓${NC} 虚拟环境创建完成: $VENV_DIR"
else
    echo -e "  ${GREEN}✓${NC} 虚拟环境已存在"
fi

source "${VENV_DIR}/bin/activate"

# ── Step 3: 安装依赖 ──
echo -e "${YELLOW}[3/6]${NC} 安装 Python 依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "  ${GREEN}✓${NC} 依赖安装完成"

# ── Step 4: 配置文件 ──
echo -e "${YELLOW}[4/6]${NC} 初始化配置..."

# 创建配置目录
mkdir -p "${MOLIN_HOME}/config"
mkdir -p "${MOLIN_HOME}/audit"
mkdir -p "${MOLIN_HOME}/cron"
mkdir -p "${MOLIN_HOME}/logs"
mkdir -p "${MOLIN_HOME}/vectors"

# 复制环境变量模板
if [ ! -f "${MOLIN_HOME}/.env" ]; then
    cp .env.example "${MOLIN_HOME}/.env"
    echo -e "  ${GREEN}✓${NC} 环境变量已初始化: ${MOLIN_HOME}/.env"
    echo -e "  ${YELLOW}  ⚠ 请编辑 ${MOLIN_HOME}/.env 填入API Keys${NC}"
else
    echo -e "  ${GREEN}✓${NC} 环境变量已存在"
fi

# ── Step 5: 安装CLI ──
echo -e "${YELLOW}[5/6]${NC} 安装墨麟OS命令行工具..."
pip install -e . -q 2>/dev/null || true

# 创建可执行脚本（支持两种入口：新版 molib 和 旧版 molin）
mkdir -p "${MOLIN_HOME}/bin"
cat > "${MOLIN_HOME}/bin/molin" << 'SCRIPT'
#!/usr/bin/env bash
source "${HOME}/.molin/venv/bin/activate"
# 优先使用新版 molib.CLI，兼容旧版 molin
if python3 -c "import molib" 2>/dev/null; then
    python3 -m molib.cli "$@"
else
    python3 -m molin.cli "$@"
fi
SCRIPT
chmod +x "${MOLIN_HOME}/bin/molin"

# 创建快捷方式
ln -sf "${MOLIN_HOME}/bin/molin" "${MOLIN_HOME}/bin/moyu" 2>/dev/null || true

echo -e "  ${GREEN}✓${NC} CLI 已安装: ${MOLIN_HOME}/bin/molin"
echo -e "  ${GREEN}✓${NC} 别名: ${MOLIN_HOME}/bin/moyu"

# 添加到 PATH (如果尚未添加)
if ! grep -q "${MOLIN_HOME}/bin" "${HOME}/.bashrc" 2>/dev/null; then
    echo "export PATH=\"${MOLIN_HOME}/bin:\$PATH\"" >> "${HOME}/.bashrc"
    echo -e "  ${GREEN}✓${NC} PATH 已更新 (source ~/.bashrc 生效)"
fi

# ── Step 6: 验证安装 ──
echo -e "${YELLOW}[6/6]${NC} 验证安装..."
if python3 -c "import molib; print(f'  墨麟OS引擎: v{molib.__version__}')" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} 核心引擎可用"
else
    echo -e "  ${YELLOW}⚠${NC} 新版引擎导入失败 (使用旧版兼容)"
    python3 -c "import molin; print(f'  墨麟旧版: v{molin.__version__}')" 2>/dev/null || \
        echo -e "  ${YELLOW}⚠${NC} 旧版也无法导入 (非致命，仅影响CLI)"
fi

# 验证系统目录
echo -n "  ${GREEN}✓${NC} 系统组件: "
COMPONENTS=("CEO引擎" "VP管理层" "子公司Worker" "共享层" "闲鱼集成")
CHECKS=("molib/ceo" "molib/management" "molib/agencies/workers" "molib/shared" "molib/xianyu")
OK=0
for dir in "${CHECKS[@]}"; do
    if [ -d "$dir" ]; then ((OK++)); fi
done
echo "${OK}/${#CHECKS[@]} 可用"

# ── 完成 ──
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗"
echo -e "║   ✅ 墨麟OS (Molin OS) 部署完成！       ║"
echo -e "╚══════════════════════════════════════════╝${NC}"
echo ""
echo "  快速开始:"
echo "    source ~/.bashrc                    # 加载环境"
echo "    molin --help                        # 查看命令"
echo "    molin health                        # 健康检查"
echo "    molin vps                           # 查看5位VP"
echo "    molin workers                       # 查看22家子公司"
echo "    molin '帮我写一篇小红书文章'          # 执行任务"
echo ""
echo "  启动API服务:"
echo "    python3 -m molib.ceo.main           # FastAPI @ 127.0.0.1:5050"
echo ""
echo "  重要: 编辑 ${MOLIN_HOME}/.env 配置API Keys"
echo "  完整文档: ./docs/墨麟HermesOS-系统架构v5.0-飞书文档.md"
echo ""