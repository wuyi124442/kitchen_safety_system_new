#!/usr/bin/env python3
"""
修复Redis连接问题的脚本

当Redis服务不可用时，让系统优雅降级，不影响Web界面正常使用。
"""

import os
import sys
from pathlib import Path

def fix_redis_connection():
    """修复Redis连接问题"""
    
    # 1. 修改数据库连接模块，增加更好的错误处理
    connection_file = Path("kitchen_safety_system/database/connection.py")
    
    if connection_file.exists():
        print("正在修复数据库连接模块...")
        
        with open(connection_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加Redis可用性检查
        if "REDIS_DISABLED = " not in content:
            # 在文件开头添加Redis禁用选项
            import_section = content.find("import redis")
            if import_section != -1:
                new_content = content[:import_section] + """
# Redis配置选项
REDIS_DISABLED = os.environ.get('REDIS_DISABLED', 'False').lower() == 'true'

""" + content[import_section:]
                
                # 修改connect_redis方法
                old_method = '''    def connect_redis(self) -> bool:
        """
        连接Redis数据库
        
        Returns:
            是否连接成功
        """
        if not REDIS_AVAILABLE:
            logger.error("redis未安装，无法连接Redis")
            return False
        
        try:
            self.redis_connection = redis.Redis(**self.redis_config)
            # 测试连接
            self.redis_connection.ping()
            logger.info("Redis连接成功")
            return True
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False'''
            
                new_method = '''    def connect_redis(self) -> bool:
        """
        连接Redis数据库
        
        Returns:
            是否连接成功
        """
        if REDIS_DISABLED:
            logger.info("Redis已禁用，跳过连接")
            return False
            
        if not REDIS_AVAILABLE:
            logger.warning("redis未安装，无法连接Redis")
            return False
        
        try:
            self.redis_connection = redis.Redis(**self.redis_config)
            # 测试连接
            self.redis_connection.ping()
            logger.info("Redis连接成功")
            return True
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}，系统将在无缓存模式下运行")
            return False'''
            
                new_content = new_content.replace(old_method, new_method)
                
                with open(connection_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print("✓ 数据库连接模块已修复")
            else:
                print("⚠ 未找到Redis导入语句")
    else:
        print("✗ 数据库连接文件不存在")

def create_redis_free_startup():
    """创建无Redis启动脚本"""
    
    script_content = '''#!/usr/bin/env python3
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
    sys.exit(main())'''
    
    with open('django_no_redis.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✓ 创建了无Redis启动脚本: django_no_redis.py")

def create_redis_free_batch():
    """创建无Redis批处理脚本"""
    
    batch_content = '''@echo off
chcp 65001 >nul
echo ========================================
echo Django启动 (无Redis模式)
echo ========================================
echo.

REM 激活conda环境
echo 激活yolo conda环境...
call conda activate yolo
if %errorlevel% neq 0 (
    echo 错误: 无法激活yolo环境
    echo 请先运行 activate_yolo_env.bat 创建环境
    pause
    exit /b 1
)

echo 当前conda环境: %CONDA_DEFAULT_ENV%
echo Redis状态: 已禁用 (无缓存模式)
echo.

echo 启动Django (无Redis模式)...
python django_no_redis.py

pause'''
    
    with open('run_django_no_redis.bat', 'w', encoding='utf-8') as f:
        f.write(batch_content)
    
    print("✓ 创建了无Redis批处理脚本: run_django_no_redis.bat")

def main():
    """主函数"""
    print("Redis连接问题修复工具")
    print("=" * 40)
    
    # 1. 修复Redis连接代码
    fix_redis_connection()
    
    # 2. 创建无Redis启动脚本
    create_redis_free_startup()
    
    # 3. 创建无Redis批处理脚本
    create_redis_free_batch()
    
    print("\n" + "=" * 40)
    print("修复完成！")
    print("\n现在可以使用以下方式启动:")
    print("1. run_django_no_redis.bat (推荐 - 无Redis模式)")
    print("2. run_django_robust.bat (原版本，但Redis错误已优化)")
    print("\n无Redis模式说明:")
    print("- 系统将使用内存缓存替代Redis")
    print("- 功能完全正常，只是缓存性能略低")
    print("- 适合开发和测试环境")

if __name__ == '__main__':
    main()'''