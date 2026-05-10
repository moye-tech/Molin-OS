#!/bin/bash

# 墨麟AI智能系统 v6.6 - 一键部署脚本
# 最多2个命令：1. ./setup_env.sh  2. ./deploy.sh

set -e  # 遇到错误时退出

echo "🚀 墨麟AI智能系统 v6.6 - 一键部署脚本"
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

# 等待服务健康
wait_for_service() {
    local service_name="$1"
    local timeout="${2:-300}"  # 默认5分钟
    local interval=5
    local elapsed=0

    log_info "等待服务 $service_name 健康..."

    while [ $elapsed -lt $timeout ]; do
        # 使用docker-compose ps检查服务状态
        if docker-compose ps "$service_name" | grep -q "Up (healthy)"; then
            log_success "服务 $service_name 已健康"
            return 0
        elif docker-compose ps "$service_name" | grep -q "Exit"; then
            log_error "服务 $service_name 已退出"
            docker-compose logs "$service_name"
            return 1
        fi

        sleep $interval
        elapsed=$((elapsed + interval))
        log_info "等待 $service_name... ${elapsed}s/${timeout}s"
    done

    log_error "服务 $service_name 健康检查超时（${timeout}秒）"
    docker-compose logs "$service_name"
    return 1
}

# 检查部署模式
get_deployment_mode() {
    if [ -f .env ]; then
        source .env 2>/dev/null || true
    fi

    local mode="${ONE_CLICK_DEPLOY_MODE:-standard}"
    echo "$mode"
}

# 获取Docker Compose命令
get_docker_compose_cmd() {
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
    elif docker compose version &> /dev/null; then
        echo "docker compose"
    else
        log_error "未找到 docker-compose 或 docker compose 命令"
        exit 1
    fi
}

# 主函数
main() {
    local deployment_mode=$(get_deployment_mode)
    local docker_compose_cmd=$(get_docker_compose_cmd)

    log_info "部署模式: $deployment_mode"
    log_info "Docker Compose 命令: $docker_compose_cmd"

    # 1. 检查环境设置
    log_info "检查环境设置..."
    if [ ! -f .env ]; then
        log_warning ".env 文件不存在，运行环境设置脚本..."
        if [ ! -f setup_env.sh ]; then
            log_error "setup_env.sh 不存在"
            exit 1
        fi
        ./setup_env.sh
    fi

    # 2. 加载环境变量
    log_info "加载环境变量..."
    set -a
    source .env
    set +a

    # 3. 验证关键环境变量
    log_info "验证关键环境变量..."
    if [ -z "$DASHSCOPE_API_KEY" ] || [[ "$DASHSCOPE_API_KEY" == *"xxxx"* ]]; then
        log_error "DASHSCOPE_API_KEY 未正确设置，请编辑 .env 文件"
        exit 1
    fi

    # 3.5 加载离线镜像缓存
    log_info "检查是否有离线镜像缓存..."
    if [ -d "./storage/images" ]; then
        for tar_file in ./storage/images/*.tar; do
            if [ -f "$tar_file" ]; then
                log_info "正在加载离线镜像: $tar_file"
                docker load -i "$tar_file"
            fi
        done
    fi

    # 4. 检查基础镜像，如不存在自动准备
    # 3.6 设置租户 ID（多租户隔离）
log_info "设置租户环境: TENANT_ID=${TENANT_ID:-default}"

# 4. 检查基础镜像
    if ! docker image inspect hermes-redis:local > /dev/null 2>&1 || \
       ! docker image inspect hermes-qdrant:local > /dev/null 2>&1 || \
       ! docker image inspect hermes-grafana:local > /dev/null 2>&1; then
        log_warning "基础服务镜像未找到，自动执行镜像准备..."
        if [ -f "./scripts/manage_images.sh" ]; then
            bash ./scripts/manage_images.sh all
        else
            log_error "scripts/manage_images.sh 不存在"
            exit 1
        fi
    fi
    log_success "基础服务镜像已就绪"

    # 5. 构建镜像
    log_info "构建Docker镜像..."
    if [ "$deployment_mode" = "standard" ] || [ "$deployment_mode" = "enhanced" ]; then
        log_info "构建主服务镜像..."
        $docker_compose_cmd build hermes

        # 根据启用的功能构建其他服务
        if [ "${FEISHU_BOT_ENABLED:-false}" = "true" ]; then
            log_info "构建Feishu网关镜像..."
            $docker_compose_cmd --profile feishu build feishu-gateway
        fi

        if [ "${MCP_SERVER_ENABLED:-false}" = "true" ]; then
            log_info "构建MCP服务器镜像..."
            $docker_compose_cmd --profile mcp build mcp-server
        fi

        if [ "${SUPERMEMORY_ENABLED:-false}" = "true" ] && [ -n "$SUPERMEMORY_API_KEY" ]; then
            log_info "构建Supermemory服务..."
            $docker_compose_cmd --profile supermemory build supermemory
        fi
    fi

    # 5. 启动服务
    log_info "启动服务..."

    # 确定要使用的compose文件
    local compose_files="-f docker-compose.yml"
    if [ "$deployment_mode" = "enhanced" ] && [ -f "docker-compose.override.yml" ]; then
        compose_files="$compose_files -f docker-compose.override.yml"
        log_info "使用增强配置（docker-compose.override.yml）"
    fi

    # 确定要启用的profile
    local profiles=""
    if [ "${FEISHU_BOT_ENABLED:-false}" = "true" ]; then
        profiles="$profiles feishu"
    fi
    if [ "${MCP_SERVER_ENABLED:-false}" = "true" ]; then
        profiles="$profiles mcp"
    fi
    if [ "${SUPERMEMORY_ENABLED:-false}" = "true" ] && [ -n "$SUPERMEMORY_API_KEY" ]; then
        profiles="$profiles supermemory"
    fi
    if [ "${APPROVAL_PANEL_ENABLED:-false}" = "true" ]; then
        profiles="$profiles approval"
    fi

    if [ -n "$profiles" ]; then
        profiles=$(echo "$profiles" | tr ' ' ',')
        log_info "启用 profiles: $profiles"
        $docker_compose_cmd $compose_files --profile "$profiles" up -d
    else
        log_info "使用标准配置（无额外profiles）"
        $docker_compose_cmd $compose_files up -d
    fi

    # 6. 等待核心服务健康
    log_info "等待核心服务启动..."

    # 等待Redis
    wait_for_service "redis" 60 || {
        log_error "Redis 启动失败"
        exit 1
    }

    # 等待Qdrant
    wait_for_service "qdrant" 60 || {
        log_error "Qdrant 启动失败"
        exit 1
    }

    # 等待墨麟主服务
    wait_for_service "hermes" 120 || {
        log_error "墨麟主服务启动失败"
        exit 1
    }

    # 等待Grafana
    wait_for_service "grafana" 90 || {
        log_warning "Grafana 启动较慢，继续部署..."
    }

    # 7. 检查可选服务
    log_info "检查可选服务状态..."

    if [ "${FEISHU_BOT_ENABLED:-false}" = "true" ]; then
        if $docker_compose_cmd ps feishu-gateway | grep -q "Up"; then
            log_success "Feishu网关正在运行"
        else
            log_warning "Feishu网关未运行"
        fi
    fi

    if [ "${MCP_SERVER_ENABLED:-false}" = "true" ]; then
        if $docker_compose_cmd ps mcp-server | grep -q "Up"; then
            log_success "MCP服务器正在运行"
        else
            log_warning "MCP服务器未运行"
        fi
    fi

    # 8. 显示部署结果
    echo ""
    echo "🎉 墨麟AI智能系统 v6.6部署完成！"
    echo "======================================"
    echo ""
    echo "🌐 服务访问地址："
    echo "  - 墨麟API:      http://localhost:8000"
    echo "  - Grafana仪表板:   http://localhost:3000"
    echo "  - Qdrant控制台:    http://localhost:6333"
    echo ""

    if [ "${FEISHU_BOT_ENABLED:-false}" = "true" ]; then
        echo "  - Feishu Webhook:  http://localhost:8002"
    fi

    if [ "${MCP_SERVER_ENABLED:-false}" = "true" ]; then
        echo "  - MCP服务器:       http://localhost:8001"
    fi

    if [ "${APPROVAL_PANEL_ENABLED:-false}" = "true" ]; then
        echo "  - 审批面板:        http://localhost:8003"
    fi

    echo ""
    echo "🔧 管理命令："
    echo "  - 查看日志:        $docker_compose_cmd logs -f"
    echo "  - 停止服务:        $docker_compose_cmd down"
    echo "  - 重启服务:        $docker_compose_cmd restart"
    echo "  - 查看状态:        $docker_compose_cmd ps"
    echo ""
    echo "📊 默认登录信息："
    echo "  - Grafana用户名:   admin"
    echo "  - Grafana密码:     查看 .env 文件中的 GRAFANA_PASSWORD"
    echo ""
    echo "⚠️  重要：首次访问Grafana需要修改默认密码"
    echo ""
    log_success "部署完成！"

    # 9. 显示健康检查状态
    log_info "运行健康检查..."
    sleep 10  # 给服务一些时间完全启动

    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        log_success "墨麟API 健康检查通过"
    else
        log_warning "墨麟API 健康检查失败，服务可能仍在启动中"
    fi
}

# 显示使用帮助
show_help() {
    echo "使用方法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -m, --mode     部署模式: standard（标准）, enhanced（增强）"
    echo "  -p, --profiles 指定启用的profiles（逗号分隔）"
    echo "  --no-build     跳过构建阶段，直接启动"
    echo ""
    echo "示例:"
    echo "  $0                          # 标准部署"
    echo "  $0 --mode enhanced          # 增强部署"
    echo "  $0 --profiles feishu,mcp    # 启用Feishu和MCP"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -m|--mode)
            export ONE_CLICK_DEPLOY_MODE="$2"
            shift 2
            ;;
        -p|--profiles)
            export DEPLOYMENT_PROFILES="$2"
            shift 2
            ;;
        --no-build)
            export SKIP_BUILD=true
            shift
            ;;
        *)
            log_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 运行主函数
main "$@"