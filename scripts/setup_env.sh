#!/bin/bash

# 墨麟AI智能系统 v6.6 - 环境设置脚本
# 一键部署的第一步：环境设置和验证

set -e  # 遇到错误时退出

echo "🚀 墨麟AI智能系统 v6.6 - 环境设置脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令 '$1' 未找到，请先安装"
        return 1
    fi
    log_info "命令 '$1' 可用"
    return 0
}

# 生成随机密码
generate_password() {
    local length=${1:-24}
    tr -dc 'A-Za-z0-9!@#$%^&*()_+-=[]{}|;:,.<>?~' </dev/urandom | head -c "$length"
}

# 验证环境变量
validate_env_var() {
    local var_name="$1"
    local var_value="${!var_name}"

    if [ -z "$var_value" ]; then
        log_warning "环境变量 $var_name 未设置"
        return 1
    fi

    # 检查是否有占位符值
    if [[ "$var_value" == *"xxxx"* ]] || [[ "$var_value" == *"你的"* ]]; then
        log_warning "环境变量 $var_name 包含占位符值: $var_value"
        return 1
    fi

    return 0
}

# 主函数
main() {
    log_info "开始环境设置..."

    # 1. 检查必要命令
    log_info "检查必要命令..."
    check_command "docker" || exit 1
    check_command "docker-compose" || {
        log_warning "docker-compose 未找到，尝试使用 docker compose..."
        if ! docker compose version &> /dev/null; then
            log_error "docker compose 也不可用，请安装 Docker Compose"
            exit 1
        fi
        log_info "使用 docker compose"
        DOCKER_COMPOSE_CMD="docker compose"
    }
    DOCKER_COMPOSE_CMD=${DOCKER_COMPOSE_CMD:-"docker-compose"}

    # 2. 检查 .env 文件
    log_info "检查配置文件..."
    if [ ! -f .env ]; then
        log_warning ".env 文件不存在，从 .env.example 创建..."
        if [ ! -f .env.example ]; then
            log_error ".env.example 也不存在，请确保项目完整"
            exit 1
        fi

        cp .env.example .env
        log_success "已创建 .env 文件"

        # 生成安全密码
        log_info "生成安全密码..."
        sed -i.bak "s/墨麟Redis2026StrongPass/$(generate_password 32)/" .env
        sed -i.bak "s/YourGrafanaStrongPassword2026!/$(generate_password 24)/" .env
        sed -i.bak "s/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/$(generate_password 32)/" .env

        # 清理备份文件
        rm -f .env.bak
        log_success "已生成安全密码"
    else
        log_info ".env 文件已存在"
    fi

    # 3. 加载环境变量
    log_info "加载环境变量..."
    if [ -f .env ]; then
        set -a  # 自动导出所有变量
        source .env
        set +a
        log_success "环境变量已加载"
    else
        log_error "无法加载 .env 文件"
        exit 1
    fi

    # 4. 验证关键环境变量
    log_info "验证关键环境变量..."
    critical_vars=("DASHSCOPE_API_KEY" "REDIS_PASSWORD" "GRAFANA_PASSWORD")

    all_valid=true
    for var in "${critical_vars[@]}"; do
        if ! validate_env_var "$var"; then
            all_valid=false
        fi
    done

    if [ "$all_valid" = false ]; then
        log_warning "一些关键环境变量未正确设置"
        echo ""
        echo "请编辑 .env 文件并设置以下变量："
        echo "1. DASHSCOPE_API_KEY: 阿里云 DashScope API Key"
        echo "2. CLAUDE_API_KEY: Anthropic Claude API Key（可选但推荐）"
        echo "3. 其他变量根据需求设置"
        echo ""
        read -p "按 Enter 继续（环境变量将在部署前验证）..."
    fi

    # 5. 创建必要的目录
    log_info "创建必要目录..."
    mkdir -p storage/{data,redis,qdrant,grafana-data,supermemory}
    mkdir -p config subsidiaries plugins tools
    log_success "目录结构已创建"

    # 6. 检查配置文件
    log_info "检查配置文件..."
    config_files=("config/subsidiaries.toml" "config/models.toml" "config/routing.toml" "config/memory.toml")

    for config_file in "${config_files[@]}"; do
        if [ ! -f "$config_file" ]; then
            log_warning "配置文件 $config_file 不存在，将使用默认配置"
        else
            log_info "配置文件 $config_file 存在"
        fi
    done

    # 7. 验证 Docker 可访问性
    log_info "验证 Docker 可访问性..."
    if ! docker info &> /dev/null; then
        log_error "无法连接到 Docker 守护进程"
        log_error "请确保 Docker 正在运行且当前用户有权限访问"
        exit 1
    fi
    log_success "Docker 可访问"

    # 8. 检查端口占用
    log_info "检查端口占用..."
    ports=("8000" "3000" "6333" "8001" "8002" "8003" "8004")
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "端口 $port 已被占用，可能会导致冲突"
        fi
    done

    # 9. 显示配置摘要
    echo ""
    echo "📋 环境设置完成摘要"
    echo "=================="
    echo "✅ Docker 和 Docker Compose 可用"
    echo "✅ .env 文件已配置"
    echo "✅ 目录结构已创建"
    echo "✅ 配置文件已检查"
    echo ""
    echo "下一步：运行部署脚本"
    echo "./deploy.sh"
    echo ""

    log_success "环境设置完成！"
}

# 运行主函数
main "$@"