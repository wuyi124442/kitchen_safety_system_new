@echo off
chcp 65001 >nul
echo ========================================
echo Django启动 (Redis-Free模式) - 简化版
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

REM 直接运行Python脚本，不检查路径
echo 启动Django (Redis-Free模式)...
echo 注意: 此模式下不会出现Redis连接错误
echo.

python simple_django_start.py --no-redis

if %errorlevel% neq 0 (
    echo.
    echo 启动失败，尝试诊断...
    echo 当前目录: %cd%
    echo Python脚本列表:
    dir /b *.py | findstr django
    echo.
    echo 如果看不到 simple_django_start.py，请确保在正确的目录运行此脚本
)

pause