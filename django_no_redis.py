#!/usr/bin/env python3
"""
无Redis模式的Django启动脚本
"""

import os
import sys
from pathlib import Path

def main():
    """主函数"""
    # 设置项目根目录
    project_root = Path(__file__).resolve().parent
    
    # 设置环境变量 - 禁用Redis
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'kitchen_safety_system.web.django_app.settings'
    os.environ['DATABASE_ENGINE'] = 'sqlite3'
    os.environ['DATABASE_NAME'] = 'kitchen_safety.db'
    os.environ['REDIS_DISABLED'] = 'true'  # 禁用Redis
    
    # 添加项目根目录到Python路径
    sys.path.insert(0, str(project_root))
    
    print("Setting up Django environment (Redis-free mode)...")
    print(f"Project root: {project_root}")
    print("Redis: DISABLED")
    
    try:
        # 导入Django
        import django
        from django.core.management import execute_from_command_line
        
        # 设置Django
        django.setup()
        print("✓ Django setup successful")
        
        # 进入Django目录
        django_dir = project_root / 'kitchen_safety_system' / 'web' / 'django_app'
        os.chdir(django_dir)
        print(f"Changed to Django directory: {django_dir}")
        
        # 运行Django命令
        print("Running Django check...")
        execute_from_command_line(['manage.py', 'check'])
        
        print("Creating migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        print("Applying migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("Creating superuser...")
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
                print("Superuser created: admin/admin123")
            else:
                print("Superuser already exists: admin/admin123")
        except Exception as e:
            print(f"Warning: Could not create superuser: {e}")
        
        print("Starting Django server (Redis-free mode)...")
        print("Web interface: http://127.0.0.1:8000")
        print("Admin backend: http://127.0.0.1:8000/admin")
        print("Note: Caching is disabled (no Redis)")
        
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())