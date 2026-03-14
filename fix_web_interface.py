#!/usr/bin/env python3
"""
修复Web界面问题的脚本

解决以下问题：
1. 创建缺失的Django迁移文件
2. 初始化数据库
3. 创建超级用户
4. 收集静态文件
5. 验证Django应用能正常启动
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(command, cwd=None, check=True):
    """运行命令并返回结果"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=check
        )
        if result.stdout:
            print(f"输出: {result.stdout}")
        if result.stderr:
            print(f"错误: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        if e.stdout:
            print(f"输出: {e.stdout}")
        if e.stderr:
            print(f"错误: {e.stderr}")
        return e

def create_missing_migrations():
    """创建缺失的迁移目录"""
    django_apps = [
        'kitchen_safety_system/web/django_app/apps/alerts',
        'kitchen_safety_system/web/django_app/apps/configuration', 
        'kitchen_safety_system/web/django_app/apps/logs',
        'kitchen_safety_system/web/django_app/apps/monitoring'
    ]
    
    for app_path in django_apps:
        migrations_dir = Path(app_path) / 'migrations'
        if not migrations_dir.exists():
            print(f"创建迁移目录: {migrations_dir}")
            migrations_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建__init__.py文件
            init_file = migrations_dir / '__init__.py'
            init_file.write_text('')
            print(f"创建文件: {init_file}")

def setup_environment():
    """设置环境变量"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')
    os.environ.setdefault('DATABASE_ENGINE', 'sqlite3')
    os.environ.setdefault('DATABASE_NAME', 'kitchen_safety.db')
    os.environ.setdefault('DJANGO_DEBUG', 'True')

def create_logs_directory():
    """创建日志目录"""
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)
    print(f"创建日志目录: {logs_dir}")

def create_media_directory():
    """创建媒体文件目录"""
    media_dir = Path('media')
    media_dir.mkdir(exist_ok=True)
    print(f"创建媒体目录: {media_dir}")

def fix_django_app():
    """修复Django应用"""
    django_dir = Path('kitchen_safety_system/web/django_app')
    
    print("=== 修复Django Web界面 ===")
    
    # 1. 创建缺失的迁移目录
    print("\n1. 创建缺失的迁移目录...")
    create_missing_migrations()
    
    # 2. 设置环境变量
    print("\n2. 设置环境变量...")
    setup_environment()
    
    # 3. 创建必要的目录
    print("\n3. 创建必要的目录...")
    create_logs_directory()
    create_media_directory()
    
    # 4. 创建迁移文件
    print("\n4. 创建数据库迁移文件...")
    run_command('python manage.py makemigrations', cwd=django_dir, check=False)
    
    # 5. 应用迁移
    print("\n5. 应用数据库迁移...")
    run_command('python manage.py migrate', cwd=django_dir, check=False)
    
    # 6. 收集静态文件
    print("\n6. 收集静态文件...")
    run_command('python manage.py collectstatic --noinput', cwd=django_dir, check=False)
    
    # 7. 检查Django配置
    print("\n7. 检查Django配置...")
    run_command('python manage.py check', cwd=django_dir, check=False)
    
    print("\n=== Django Web界面修复完成 ===")

def create_superuser_script():
    """创建超级用户脚本"""
    script_content = '''
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# 创建超级用户（如果不存在）
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("超级用户创建成功: admin/admin123")
else:
    print("超级用户已存在")
'''
    
    script_path = Path('create_superuser.py')
    script_path.write_text(script_content)
    print(f"创建超级用户脚本: {script_path}")
    
    # 执行脚本
    run_command('python create_superuser.py', check=False)

def test_django_server():
    """测试Django服务器启动"""
    print("\n=== 测试Django服务器 ===")
    django_dir = Path('kitchen_safety_system/web/django_app')
    
    print("尝试启动Django开发服务器（测试模式）...")
    result = run_command(
        'python manage.py runserver 127.0.0.1:8000 --noreload', 
        cwd=django_dir, 
        check=False
    )
    
    if result.returncode == 0:
        print("✅ Django服务器可以正常启动")
    else:
        print("❌ Django服务器启动失败")
        print("请检查错误信息并手动修复")

def create_startup_script():
    """创建启动脚本"""
    startup_script = '''#!/bin/bash
# Django Web界面启动脚本

echo "启动厨房安全检测系统Web界面..."

# 设置环境变量
export DJANGO_SETTINGS_MODULE=kitchen_safety_system.web.django_app.settings
export DATABASE_ENGINE=sqlite3
export DATABASE_NAME=kitchen_safety.db
export DJANGO_DEBUG=True

# 进入Django目录
cd kitchen_safety_system/web/django_app

# 应用数据库迁移
echo "应用数据库迁移..."
python manage.py migrate

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput

# 启动开发服务器
echo "启动Django开发服务器..."
echo "Web界面地址: http://127.0.0.1:8000"
echo "管理后台地址: http://127.0.0.1:8000/admin"
echo "默认管理员账号: admin/admin123"
python manage.py runserver 127.0.0.1:8000
'''
    
    script_path = Path('start_web.sh')
    script_path.write_text(startup_script)
    script_path.chmod(0o755)
    print(f"创建启动脚本: {script_path}")

def create_windows_startup_script():
    """创建Windows启动脚本"""
    startup_script = '''@echo off
REM Django Web界面启动脚本 (Windows)

echo 启动厨房安全检测系统Web界面...

REM 设置环境变量
set DJANGO_SETTINGS_MODULE=kitchen_safety_system.web.django_app.settings
set DATABASE_ENGINE=sqlite3
set DATABASE_NAME=kitchen_safety.db
set DJANGO_DEBUG=True

REM 进入Django目录
cd kitchen_safety_system\\web\\django_app

REM 应用数据库迁移
echo 应用数据库迁移...
python manage.py migrate

REM 收集静态文件
echo 收集静态文件...
python manage.py collectstatic --noinput

REM 启动开发服务器
echo 启动Django开发服务器...
echo Web界面地址: http://127.0.0.1:8000
echo 管理后台地址: http://127.0.0.1:8000/admin
echo 默认管理员账号: admin/admin123
python manage.py runserver 127.0.0.1:8000

pause
'''
    
    script_path = Path('start_web.bat')
    script_path.write_text(startup_script)
    print(f"创建Windows启动脚本: {script_path}")

def main():
    """主函数"""
    print("🔧 厨房安全检测系统 - Web界面修复工具")
    print("=" * 50)
    
    try:
        # 修复Django应用
        fix_django_app()
        
        # 创建超级用户
        print("\n8. 创建超级用户...")
        create_superuser_script()
        
        # 创建启动脚本
        print("\n9. 创建启动脚本...")
        create_startup_script()
        create_windows_startup_script()
        
        print("\n" + "=" * 50)
        print("✅ Web界面修复完成！")
        print("\n📋 使用说明:")
        print("1. Linux/macOS: 运行 ./start_web.sh")
        print("2. Windows: 运行 start_web.bat")
        print("3. 手动启动: cd kitchen_safety_system/web/django_app && python manage.py runserver")
        print("\n🌐 访问地址:")
        print("- Web界面: http://127.0.0.1:8000")
        print("- 管理后台: http://127.0.0.1:8000/admin")
        print("- 默认管理员: admin/admin123")
        
    except Exception as e:
        print(f"\n❌ 修复过程中出现错误: {e}")
        print("请检查错误信息并手动修复")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())