#!/usr/bin/env python3
"""
直接启动Django的脚本 - 避免autoreload问题
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 设置项目根目录
    project_root = Path(__file__).resolve().parent
    
    # 检查是否禁用Redis
    disable_redis = len(sys.argv) > 1 and sys.argv[1] == '--no-redis'
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'kitchen_safety_system.web.django_app.settings'
    os.environ['DATABASE_ENGINE'] = 'sqlite3'
    os.environ['DATABASE_NAME'] = 'kitchen_safety.db'
    
    if disable_redis:
        os.environ['REDIS_DISABLED'] = 'true'
    
    redis_status = "DISABLED" if disable_redis else "ENABLED"
    print(f"Setting up Django environment (Redis: {redis_status})...")
    print(f"Project root: {project_root}")
    if disable_redis:
        print("Redis: DISABLED - Using memory cache")
    
    # Django目录
    django_dir = project_root / 'kitchen_safety_system' / 'web' / 'django_app'
    manage_py = django_dir / 'manage.py'
    
    if not manage_py.exists():
        print(f"Error: manage.py not found at {manage_py}")
        return 1
    
    print(f"Django directory: {django_dir}")
    
    try:
        # 运行Django命令
        print("Running Django check...")
        subprocess.run([sys.executable, str(manage_py), 'check'], 
                      cwd=django_dir, check=True)
        
        print("Creating migrations...")
        subprocess.run([sys.executable, str(manage_py), 'makemigrations'], 
                      cwd=django_dir, check=False)  # 不强制成功，可能没有新迁移
        
        print("Applying migrations...")
        subprocess.run([sys.executable, str(manage_py), 'migrate'], 
                      cwd=django_dir, check=True)
        
        print("Creating superuser...")
        # 使用Django shell创建超级用户
        create_superuser_script = """
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists: admin/admin123')
"""
        
        subprocess.run([sys.executable, str(manage_py), 'shell', '-c', create_superuser_script], 
                      cwd=django_dir, check=False)
        
        print("Starting Django server...")
        print("Web interface: http://127.0.0.1:8000")
        print("Admin backend: http://127.0.0.1:8000/admin")
        if disable_redis:
            print("Note: Running in Redis-free mode (no cache)")
        
        # 启动Django服务器
        subprocess.run([sys.executable, str(manage_py), 'runserver', '127.0.0.1:8000'], 
                      cwd=django_dir)
        
    except subprocess.CalledProcessError as e:
        print(f"Django command failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())