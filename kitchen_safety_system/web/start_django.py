#!/usr/bin/env python
"""
Django Web服务器启动脚本
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 设置项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DJANGO_APP_DIR = BASE_DIR / 'kitchen_safety_system' / 'web' / 'django_app'

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import django
        import rest_framework
        import corsheaders
        import redis
        import psycopg2
        logger.info("所有依赖已安装")
        return True
    except ImportError as e:
        logger.error(f"缺少依赖: {e}")
        logger.error("请运行: pip install -r requirements.txt")
        return False


def setup_environment():
    """设置环境变量"""
    # 设置Django设置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')
    
    # 设置默认环境变量
    env_vars = {
        'DJANGO_DEBUG': 'True',
        'DJANGO_SECRET_KEY': 'django-insecure-kitchen-safety-dev-key-change-in-production',
        'DB_NAME': 'kitchen_safety_db',
        'DB_USER': 'kitchen_safety_user',
        'DB_PASSWORD': 'kitchen_safety_password',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
    }
    
    for key, default_value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = default_value
            logger.info(f"设置环境变量 {key} = {default_value}")


def run_migrations():
    """运行数据库迁移"""
    logger.info("运行数据库迁移...")
    
    try:
        # 切换到Django应用目录
        os.chdir(DJANGO_APP_DIR)
        
        # 创建迁移文件
        subprocess.run([
            sys.executable, 'manage.py', 'makemigrations'
        ], check=True)
        
        # 运行迁移
        subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], check=True)
        
        logger.info("数据库迁移完成")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"数据库迁移失败: {e}")
        return False


def collect_static():
    """收集静态文件"""
    logger.info("收集静态文件...")
    
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'collectstatic', '--noinput'
        ], check=True)
        
        logger.info("静态文件收集完成")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"静态文件收集失败: {e}")
        return False


def init_system():
    """初始化系统数据"""
    logger.info("初始化系统数据...")
    
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'init_system'
        ], check=True)
        
        logger.info("系统数据初始化完成")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"系统数据初始化失败: {e}")
        return False


def start_server(host='127.0.0.1', port=8000, debug=True):
    """启动Django开发服务器"""
    logger.info(f"启动Django服务器 http://{host}:{port}")
    
    try:
        cmd = [sys.executable, 'manage.py', 'runserver', f'{host}:{port}']
        
        if not debug:
            cmd.append('--insecure')
        
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"服务器启动失败: {e}")
    except KeyboardInterrupt:
        logger.info("服务器已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='启动厨房安全检测系统Django后台')
    parser.add_argument('--host', default='127.0.0.1', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8000, help='服务器端口')
    parser.add_argument('--skip-migrations', action='store_true', help='跳过数据库迁移')
    parser.add_argument('--skip-static', action='store_true', help='跳过静态文件收集')
    parser.add_argument('--skip-init', action='store_true', help='跳过系统初始化')
    parser.add_argument('--production', action='store_true', help='生产模式')
    
    args = parser.parse_args()
    
    logger.info("启动厨房安全检测系统Django后台...")
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 设置生产模式环境变量
    if args.production:
        os.environ['DJANGO_DEBUG'] = 'False'
        logger.info("生产模式已启用")
    
    # 运行数据库迁移
    if not args.skip_migrations:
        if not run_migrations():
            logger.error("数据库迁移失败，请检查数据库连接")
            sys.exit(1)
    
    # 收集静态文件
    if not args.skip_static:
        collect_static()
    
    # 初始化系统数据
    if not args.skip_init:
        init_system()
    
    # 启动服务器
    start_server(args.host, args.port, not args.production)


if __name__ == '__main__':
    main()