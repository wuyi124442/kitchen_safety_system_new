#!/bin/bash
set -e

# 厨房安全检测系统 Docker 启动脚本

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

# 等待数据库连接
wait_for_db() {
    log_info "等待数据库连接..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(
        host=os.environ.get('DATABASE_HOST', 'postgres'),
        port=os.environ.get('DATABASE_PORT', '5432'),
        database=os.environ.get('DATABASE_NAME', 'kitchen_safety'),
        user=os.environ.get('DATABASE_USER', 'kitchen_user'),
        password=os.environ.get('DATABASE_PASSWORD', 'kitchen_pass')
    )
    conn.close()
    print('数据库连接成功')
    exit(0)
except Exception as e:
    print(f'数据库连接失败: {e}')
    exit(1)
" 2>/dev/null; then
            log_success "数据库连接成功"
            return 0
        fi
        
        log_warning "数据库连接失败，重试 $attempt/$max_attempts"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "数据库连接超时"
    exit 1
}

# 等待Redis连接
wait_for_redis() {
    log_info "等待Redis连接..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "
import os
import redis
try:
    r = redis.Redis(
        host=os.environ.get('REDIS_HOST', 'redis'),
        port=int(os.environ.get('REDIS_PORT', '6379')),
        decode_responses=True
    )
    r.ping()
    print('Redis连接成功')
    exit(0)
except Exception as e:
    print(f'Redis连接失败: {e}')
    exit(1)
" 2>/dev/null; then
            log_success "Redis连接成功"
            return 0
        fi
        
        log_warning "Redis连接失败，重试 $attempt/$max_attempts"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "Redis连接超时"
    exit 1
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    if python -c "
import sys
sys.path.append('/app')
from kitchen_safety_system.database.setup_database import setup_database
try:
    setup_database()
    print('数据库初始化成功')
except Exception as e:
    print(f'数据库初始化失败: {e}')
    sys.exit(1)
"; then
        log_success "数据库初始化完成"
    else
        log_error "数据库初始化失败"
        exit 1
    fi
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    local config_files=(
        "/app/config/default_config.yaml"
        "/app/config/system_config.json"
        "/app/config/yolo_config.yaml"
    )
    
    for config_file in "${config_files[@]}"; do
        if [ ! -f "$config_file" ]; then
            log_warning "配置文件不存在: $config_file"
        else
            log_info "配置文件存在: $config_file"
        fi
    done
}

# 检查模型文件
check_models() {
    log_info "检查模型文件..."
    
    local model_files=(
        "/app/yolo/yolo11n.pt"
        "/app/yolo/yolov8n.pt"
    )
    
    for model_file in "${model_files[@]}"; do
        if [ ! -f "$model_file" ]; then
            log_warning "模型文件不存在: $model_file"
        else
            log_info "模型文件存在: $model_file"
        fi
    done
}

# 创建必要目录
create_directories() {
    log_info "创建必要目录..."
    
    local directories=(
        "/app/logs"
        "/app/logs/video_clips"
        "/app/data"
        "/app/models"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
}

# 启动主应用
start_main_app() {
    log_info "启动厨房安全检测系统主应用..."
    exec python -m kitchen_safety_system.main start
}

# 启动Web应用
start_web_app() {
    log_info "启动Django Web应用..."
    
    # Django数据库迁移
    log_info "执行Django数据库迁移..."
    python kitchen_safety_system/web/manage.py migrate --noinput
    
    # 收集静态文件
    log_info "收集静态文件..."
    python kitchen_safety_system/web/manage.py collectstatic --noinput
    
    # 启动Django服务器
    exec python kitchen_safety_system/web/manage.py runserver 0.0.0.0:8001
}

# 运行测试
run_tests() {
    log_info "运行系统测试..."
    python -m pytest tests/ -v
}

# 显示帮助信息
show_help() {
    echo "厨房安全检测系统 Docker 启动脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动主检测应用 (默认)"
    echo "  web       启动Django Web应用"
    echo "  test      运行系统测试"
    echo "  shell     启动交互式shell"
    echo "  help      显示此帮助信息"
    echo ""
}

# 主函数
main() {
    local command=${1:-start}
    
    log_info "厨房安全检测系统启动中..."
    log_info "命令: $command"
    
    # 创建必要目录
    create_directories
    
    # 检查配置和模型文件
    check_config
    check_models
    
    case "$command" in
        "start")
            wait_for_db
            wait_for_redis
            init_database
            start_main_app
            ;;
        "web")
            wait_for_db
            wait_for_redis
            start_web_app
            ;;
        "test")
            wait_for_db
            wait_for_redis
            run_tests
            ;;
        "shell")
            exec /bin/bash
            ;;
        "help")
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 信号处理
trap 'log_info "接收到停止信号，正在关闭..."; exit 0' SIGTERM SIGINT

# 执行主函数
main "$@"