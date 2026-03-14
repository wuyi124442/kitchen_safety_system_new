#!/bin/bash

# 厨房安全检测系统维护脚本
# 版本: 1.0

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
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

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/db_backup_$timestamp.sql"
    
    mkdir -p "$BACKUP_DIR"
    
    cd "$PROJECT_DIR"
    
    # 备份PostgreSQL数据库
    docker-compose exec -T postgres pg_dump -U kitchen_user kitchen_safety > "$backup_file"
    
    if [ $? -eq 0 ]; then
        log_success "数据库备份完成: $backup_file"
        gzip "$backup_file"
        log_success "备份文件已压缩: ${backup_file}.gz"
    else
        log_error "数据库备份失败"
        exit 1
    fi
}

# 系统健康检查
health_check() {
    log_info "执行系统健康检查..."
    
    cd "$PROJECT_DIR"
    
    echo ""
    echo -e "${BLUE}容器状态:${NC}"
    docker-compose ps
    
    echo ""
    echo -e "${BLUE}服务健康状态:${NC}"
    local services=("postgres" "redis" "kitchen_safety" "web" "nginx")
    
    for service in "${services[@]}"; do
        local container_id=$(docker-compose ps -q $service)
        if [ -n "$container_id" ]; then
            local status=$(docker inspect --format='{{.State.Status}}' $container_id)
            if [ "$status" = "running" ]; then
                echo -e "  ${GREEN}✓${NC} $service: 运行正常"
            else
                echo -e "  ${RED}✗${NC} $service: 未运行 ($status)"
            fi
        else
            echo -e "  ${RED}✗${NC} $service: 容器不存在"
        fi
    done
}

# 清理日志文件
cleanup_logs() {
    log_info "清理日志文件..."
    
    local days=${1:-7}
    
    if [ -d "$PROJECT_DIR/logs" ]; then
        find "$PROJECT_DIR/logs" -name "*.log" -type f -mtime +$days -delete
    fi
    
    docker system prune -f --filter "until=${days}d" > /dev/null 2>&1
    
    log_success "清理完成 (超过 $days 天的文件)"
}

# 查看日志
view_logs() {
    local service="$1"
    local lines="${2:-100}"
    
    cd "$PROJECT_DIR"
    
    if [ -z "$service" ]; then
        docker-compose logs --tail=$lines
    else
        docker-compose logs --tail=$lines $service
    fi
}

# 重启服务
restart_service() {
    local service="$1"
    
    cd "$PROJECT_DIR"
    
    if [ -z "$service" ]; then
        log_info "重启所有服务..."
        docker-compose restart
    else
        log_info "重启 $service 服务..."
        docker-compose restart $service
    fi
    
    log_success "服务重启完成"
}

# 显示帮助信息
show_help() {
    echo "厨房安全检测系统维护脚本"
    echo ""
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "命令:"
    echo "  backup                    备份数据库"
    echo "  cleanup-logs [days]       清理日志文件 (默认7天)"
    echo "  health-check              系统健康检查"
    echo "  logs [service] [lines]    查看日志"
    echo "  restart [service]         重启服务"
    echo "  help                      显示此帮助信息"
    echo ""
}

# 主函数
main() {
    local command="$1"
    
    case "$command" in
        "backup")
            backup_database
            ;;
        "cleanup-logs")
            cleanup_logs "$2"
            ;;
        "health-check")
            health_check
            ;;
        "logs")
            view_logs "$2" "$3"
            ;;
        "restart")
            restart_service "$2"
            ;;
        "help"|"")
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"