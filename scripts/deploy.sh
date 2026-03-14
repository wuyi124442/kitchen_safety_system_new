#!/bin/bash

# 厨房安全检测系统部署脚本
# 版本: 2.0
# 作者: Kitchen Safety Team

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
BACKUP_DIR="$PROJECT_DIR/backups"

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

log_debug() {
    echo -e "${PURPLE}[DEBUG]${NC} $1"
}

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    echo "=================================================================="
    echo "           厨房安全检测系统 - 容器化部署脚本"
    echo "=================================================================="
    echo -e "${NC}"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行，请启动 Docker 服务"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 检查环境配置
check_environment() {
    log_info "检查环境配置..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warning ".env 文件不存在，从模板创建..."
        cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
        log_warning "请编辑 .env 文件并配置正确的参数"
        log_warning "特别注意修改以下配置："
        echo "  - POSTGRES_PASSWORD"
        echo "  - DJANGO_SECRET_KEY"
        echo "  - DJANGO_ALLOWED_HOSTS"
        echo "  - EMAIL_* 配置 (如果启用邮件报警)"
        read -p "配置完成后按回车继续..."
    fi
    
    # 检查关键配置
    source "$ENV_FILE"
    
    if [ "$DJANGO_SECRET_KEY" = "your-very-secure-secret-key-change-in-production-environment" ]; then
        log_error "请修改 DJANGO_SECRET_KEY 为安全的密钥"
        exit 1
    fi
    
    if [ "$POSTGRES_PASSWORD" = "kitchen_pass_secure_2024" ]; then
        log_warning "建议修改 POSTGRES_PASSWORD 为更安全的密码"
    fi
    
    log_success "环境配置检查完成"
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    local directories=(
        "$PROJECT_DIR/logs"
        "$PROJECT_DIR/logs/video_clips"
        "$PROJECT_DIR/data"
        "$PROJECT_DIR/models"
        "$BACKUP_DIR"
        "$PROJECT_DIR/nginx/logs"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_debug "创建目录: $dir"
        fi
    done
    
    log_success "目录创建完成"
}

# 备份数据
backup_data() {
    log_info "备份现有数据..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/backup_$timestamp.tar.gz"
    
    if [ -d "$PROJECT_DIR/logs" ] || [ -d "$PROJECT_DIR/data" ]; then
        tar -czf "$backup_file" -C "$PROJECT_DIR" logs data 2>/dev/null || true
        log_success "数据备份完成: $backup_file"
    else
        log_info "没有需要备份的数据"
    fi
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    
    cd "$PROJECT_DIR"
    
    # 构建主应用镜像
    docker-compose build --no-cache
    
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd "$PROJECT_DIR"
    
    # 启动基础服务 (数据库和缓存)
    log_info "启动数据库和缓存服务..."
    docker-compose up -d postgres redis
    
    # 等待数据库就绪
    log_info "等待数据库就绪..."
    sleep 10
    
    # 启动应用服务
    log_info "启动应用服务..."
    docker-compose up -d kitchen_safety web
    
    # 等待应用就绪
    log_info "等待应用就绪..."
    sleep 15
    
    # 启动Nginx
    log_info "启动Nginx代理..."
    docker-compose up -d nginx
    
    log_success "所有服务启动完成"
}

# 检查服务状态
check_services() {
    log_info "检查服务状态..."
    
    cd "$PROJECT_DIR"
    
    # 显示容器状态
    echo ""
    docker-compose ps
    echo ""
    
    # 检查健康状态
    local services=("postgres" "redis" "kitchen_safety" "web" "nginx")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        local status=$(docker-compose ps -q $service | xargs docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "no-health-check")
        
        if [ "$status" = "healthy" ] || [ "$status" = "no-health-check" ]; then
            log_success "$service: 运行正常"
        else
            log_error "$service: 状态异常 ($status)"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        log_success "所有服务运行正常"
        show_access_info
    else
        log_error "部分服务状态异常，请检查日志"
        show_troubleshooting
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo -e "${CYAN}=================================================================="
    echo "                    部署完成 - 访问信息"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${GREEN}Web管理界面:${NC} http://localhost"
    echo -e "${GREEN}API接口:${NC}     http://localhost/api/"
    echo -e "${GREEN}健康检查:${NC}   http://localhost/health"
    echo ""
    echo -e "${YELLOW}默认管理员账户:${NC}"
    echo "  用户名: admin"
    echo "  密码: admin123 (请及时修改)"
    echo ""
    echo -e "${BLUE}常用命令:${NC}"
    echo "  查看日志: docker-compose logs -f [service_name]"
    echo "  重启服务: docker-compose restart [service_name]"
    echo "  停止服务: docker-compose down"
    echo "  更新服务: ./scripts/deploy.sh --update"
    echo ""
}

# 显示故障排除信息
show_troubleshooting() {
    echo ""
    echo -e "${YELLOW}=================================================================="
    echo "                      故障排除指南"
    echo -e "==================================================================${NC}"
    echo ""
    echo -e "${RED}常见问题:${NC}"
    echo "1. 端口冲突: 检查80, 8000, 8001, 5432, 6379端口是否被占用"
    echo "2. 权限问题: 确保当前用户有Docker权限"
    echo "3. 内存不足: 确保系统有至少4GB可用内存"
    echo "4. 磁盘空间: 确保有足够的磁盘空间存储镜像和数据"
    echo ""
    echo -e "${BLUE}调试命令:${NC}"
    echo "  查看所有日志: docker-compose logs"
    echo "  查看特定服务: docker-compose logs [service_name]"
    echo "  进入容器: docker-compose exec [service_name] bash"
    echo "  重新构建: docker-compose build --no-cache"
    echo ""
}

# 更新部署
update_deployment() {
    log_info "更新部署..."
    
    cd "$PROJECT_DIR"
    
    # 备份数据
    backup_data
    
    # 拉取最新代码 (如果是git仓库)
    if [ -d ".git" ]; then
        log_info "拉取最新代码..."
        git pull
    fi
    
    # 重新构建镜像
    build_images
    
    # 重启服务
    log_info "重启服务..."
    docker-compose down
    start_services
    check_services
    
    log_success "更新完成"
}

# 清理部署
cleanup_deployment() {
    log_warning "这将删除所有容器、镜像和数据卷"
    read -p "确定要继续吗? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "清理部署..."
        
        cd "$PROJECT_DIR"
        
        # 停止并删除容器
        docker-compose down -v --remove-orphans
        
        # 删除镜像
        docker-compose down --rmi all
        
        # 清理未使用的资源
        docker system prune -f
        
        log_success "清理完成"
    else
        log_info "取消清理操作"
    fi
}

# 显示帮助信息
show_help() {
    echo "厨房安全检测系统部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --deploy, -d     执行完整部署 (默认)"
    echo "  --update, -u     更新现有部署"
    echo "  --status, -s     检查服务状态"
    echo "  --cleanup, -c    清理部署"
    echo "  --help, -h       显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 执行完整部署"
    echo "  $0 --update       # 更新部署"
    echo "  $0 --status       # 检查状态"
    echo ""
}

# 主函数
main() {
    local action=${1:-deploy}
    
    show_banner
    
    case "$action" in
        "--deploy"|"-d"|"deploy")
            check_requirements
            check_environment
            create_directories
            backup_data
            build_images
            start_services
            check_services
            ;;
        "--update"|"-u"|"update")
            check_requirements
            update_deployment
            ;;
        "--status"|"-s"|"status")
            check_services
            ;;
        "--cleanup"|"-c"|"cleanup")
            cleanup_deployment
            ;;
        "--help"|"-h"|"help")
            show_help
            ;;
        *)
            log_error "未知选项: $action"
            show_help
            exit 1
            ;;
    esac
}

# 信号处理
trap 'log_info "接收到中断信号，正在退出..."; exit 0' SIGINT SIGTERM

# 执行主函数
main "$@"