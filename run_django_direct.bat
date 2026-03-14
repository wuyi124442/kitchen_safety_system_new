@echo off
chcp 65001 >nul
echo ========================================
echo Django直接启动 (Redis-Free模式)
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

REM 设置环境变量 - 完全禁用Redis
set REDIS_DISABLED=true
set DJANGO_SETTINGS_MODULE=kitchen_safety_system.web.django_app.settings
set DATABASE_ENGINE=sqlite3
set DATABASE_NAME=kitchen_safety.db

echo 环境配置:
echo   Redis状态: 已禁用 (无缓存模式)
echo   数据库: SQLite3
echo   缓存: 内存缓存 (DummyCache)
echo.

echo 启动Django (直接模式 - 避免autoreload问题)...
echo.

python start_django_direct.py --no-redis

if %errorlevel% neq 0 (
    echo.
    echo 启动失败，请检查错误信息
)

pause