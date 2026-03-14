@echo off
REM 设置控制台代码页为UTF-8以支持中文显示
chcp 65001 >nul

echo 设置Django环境...

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

REM 确保在正确的目录中
echo 当前目录: %cd%

REM 检查simple_django_start.py是否存在
if not exist "simple_django_start.py" (
    echo 错误: 找不到 simple_django_start.py 文件
    echo 请确保在项目根目录中运行此脚本
    pause
    exit /b 1
)

echo 使用简化脚本启动Django...
python simple_django_start.py

pause