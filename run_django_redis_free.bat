@echo off
chcp 65001 >nul
echo ========================================
echo Django启动 (Redis-Free模式)
echo ========================================
echo.

REM 获取脚本所在目录并切换到该目录
set SCRIPT_DIR=%~dp0
echo 脚本目录: %SCRIPT_DIR%
cd /d "%SCRIPT_DIR%"
echo 当前目录: %cd%

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

REM 检查Python脚本是否存在
set PYTHON_SCRIPT=simple_django_start.py
echo 调试信息:
echo   当前目录: %cd%
echo   脚本目录: %SCRIPT_DIR%
echo   查找文件: %PYTHON_SCRIPT%
echo.

if not exist "%PYTHON_SCRIPT%" (
    echo 错误: 找不到 %PYTHON_SCRIPT%
    echo 当前目录文件列表:
    dir /b *.py
    echo.
    echo 尝试在脚本目录查找:
    if exist "%SCRIPT_DIR%%PYTHON_SCRIPT%" (
        echo 找到文件在: %SCRIPT_DIR%%PYTHON_SCRIPT%
        set PYTHON_SCRIPT=%SCRIPT_DIR%%PYTHON_SCRIPT%
    ) else (
        echo 脚本目录也没有找到文件
        pause
        exit /b 1
    )
)

echo 找到Python脚本: %PYTHON_SCRIPT%
echo 启动Django (Redis-Free模式)...
echo 注意: 此模式下不会出现Redis连接错误
echo.
python "%PYTHON_SCRIPT%" --no-redis

pause