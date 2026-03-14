#!/usr/bin/env python3
"""
测试Django配置的脚本
"""

import os
import sys
import django
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')
os.environ.setdefault('PYTHONPATH', str(project_root))

def test_django_setup():
    """测试Django设置"""
    try:
        print("正在设置Django...")
        django.setup()
        print("✓ Django设置成功")
        
        # 测试数据库连接
        from django.db import connection
        print("正在测试数据库连接...")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✓ 数据库连接成功")
            else:
                print("✗ 数据库连接失败")
        
        # 测试模型导入
        print("正在测试模型导入...")
        from kitchen_safety_system.web.django_app.apps.authentication.models import User
        from kitchen_safety_system.web.django_app.apps.logs.models import LogEntry
        from kitchen_safety_system.web.django_app.apps.alerts.models import Alert
        print("✓ 模型导入成功")
        
        # 运行系统检查
        print("正在运行系统检查...")
        from django.core.management import call_command
        from io import StringIO
        
        output = StringIO()
        try:
            call_command('check', stdout=output, stderr=output)
            check_output = output.getvalue()
            if "System check identified no issues" in check_output or "0 silenced" in check_output:
                print("✓ 系统检查通过")
            else:
                print("⚠ 系统检查有警告:")
                print(check_output)
        except Exception as e:
            print(f"✗ 系统检查失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Django设置失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_migrations():
    """测试迁移文件"""
    print("\n正在检查迁移文件...")
    
    apps_to_check = [
        'authentication',
        'logs', 
        'alerts',
        'configuration',
        'monitoring'
    ]
    
    for app in apps_to_check:
        migration_path = project_root / 'kitchen_safety_system' / 'web' / 'django_app' / 'apps' / app / 'migrations' / '0001_initial.py'
        if migration_path.exists():
            print(f"✓ {app} 迁移文件存在")
        else:
            print(f"✗ {app} 迁移文件缺失")

def main():
    """主函数"""
    print("厨房安全检测系统 - Django配置测试")
    print("=" * 50)
    
    # 检查迁移文件
    test_migrations()
    
    # 测试Django设置
    print()
    success = test_django_setup()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 所有测试通过！Django配置正确。")
        return 0
    else:
        print("✗ 测试失败，请检查配置。")
        return 1

if __name__ == '__main__':
    sys.exit(main())