@echo off
chcp 65001 >nul
echo ========================================
echo Django启动 (无Redis模式) - 简化版
echo ========================================
echo.

REM 获取脚本所在目录并切换到该目录
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"
echo 当前目录: %cd%

REM 激活conda环境
echo 激活yolo conda环境...
call conda activate yolo
if %errorlevel% neq 0 (
    echo 错误: 无法激活yolo环境
    pause
    exit /b 1
)

echo 当前conda环境: %CONDA_DEFAULT_ENV%

REM 设置环境变量
set PYTHONPATH=%cd%
set DJANGO_SETTINGS_MODULE=kitchen_safety_system.web.django_app.settings
set DATABASE_ENGINE=sqlite3
set DATABASE_NAME=kitchen_safety.db
set REDIS_DISABLED=true

echo PYTHONPATH: %PYTHONPATH%
echo DJANGO_SETTINGS_MODULE: %DJANGO_SETTINGS_MODULE%
echo Redis状态: 已禁用

REM 进入Django目录
cd kitchen_safety_system\web\django_app
echo Django目录: %cd%

echo 检查Django配置...
python manage.py check

echo 创建迁移文件...
python manage.py makemigrations

echo 应用迁移...
python manage.py migrate

echo 创建超级用户...
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings'); django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123'); print('超级用户: admin/admin123')"

echo.
echo ========================================
echo 启动Django服务器 (无Redis模式)
echo ========================================
echo Web界面: http://127.0.0.1:8000
echo 管理后台: http://127.0.0.1:8000/admin
echo 默认账户: admin / admin123
echo Redis: 已禁用 (使用内存缓存)
echo.

python manage.py runserver 127.0.0.1:8000

pause