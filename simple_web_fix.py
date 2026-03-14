#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的Web界面修复脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, cwd=None):
    """运行命令"""
    print(f"执行: {command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    print("🔧 修复Django Web界面")
    
    # 确保在项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 添加项目根目录到Python路径
    sys.path.insert(0, str(project_root))
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(project_root)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'kitchen_safety_system.web.django_app.settings'
    os.environ['DATABASE_ENGINE'] = 'sqlite3'
    os.environ['DATABASE_NAME'] = 'kitchen_safety.db'
    
    django_dir = project_root / 'kitchen_safety_system' / 'web' / 'django_app'
    
    print(f"Django目录: {django_dir}")
    print(f"项目根目录: {project_root}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    
    # 创建必要目录
    (project_root / 'logs').mkdir(exist_ok=True)
    (project_root / 'media').mkdir(exist_ok=True)
    (project_root / 'staticfiles').mkdir(exist_ok=True)
    
    # 尝试运行Django命令
    commands = [
        f'python -c "import sys; sys.path.insert(0, \'{project_root}\'); import django; print(\'Django version:\', django.get_version())"',
        f'python -c "import sys; sys.path.insert(0, \'{project_root}\'); import kitchen_safety_system; print(\'Module found\')"',
        f'python manage.py check --settings=kitchen_safety_system.web.django_app.settings',
        f'python manage.py makemigrations --settings=kitchen_safety_system.web.django_app.settings',
        f'python manage.py migrate --settings=kitchen_safety_system.web.django_app.settings',
    ]
    
    for cmd in commands:
        print(f"\n--- 执行: {cmd} ---")
        success = run_command(cmd, cwd=django_dir)
        if not success:
            print(f"命令失败: {cmd}")
            break
    
    print("\n✅ 修复完成")

if __name__ == '__main__':
    main()