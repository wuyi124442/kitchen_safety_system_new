@echo off
REM 健壮版本的Django启动脚本
chcp 65001 >nul

echo 设置Django环境...

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
echo 脚本目录: %SCRIPT_DIR%

REM 切换到脚本目录
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

REM 检查Python脚本是否存在
set PYTHON_SCRIPT=simple_django_start.py
if not exist "%PYTHON_SCRIPT%" (
    echo 错误: 找不到 %PYTHON_SCRIPT%
    echo 文件列表:
    dir /b *.py
    pause
    exit /b 1
)

echo 找到Python脚本: %PYTHON_SCRIPT%
echo 使用简化脚本启动Django...
python "%PYTHON_SCRIPT%"

pause