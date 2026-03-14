@echo off
chcp 65001 >nul
echo ========================================
echo Django启动 (无Redis模式)
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
echo Redis状态: 已禁用 (无缓存模式)
echo.

REM 检查Python脚本是否存在
set PYTHON_SCRIPT=simple_django_start.py
if not exist "%PYTHON_SCRIPT%" (
    echo 错误: 找不到 %PYTHON_SCRIPT%
    echo 当前目录文件列表:
    dir /b *.py
    pause
    exit /b 1
)

echo 找到Python脚本: %PYTHON_SCRIPT%
echo 启动Django (无Redis模式)...
python "%PYTHON_SCRIPT%" --no-redis

pause