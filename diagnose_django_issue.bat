@echo off
chcp 65001 >nul
echo ========================================
echo Django启动问题诊断工具
echo ========================================
echo.

echo 1. 检查当前目录...
echo 当前目录: %cd%
echo.

echo 2. 检查Python脚本文件...
if exist "simple_django_start.py" (
    echo ✓ simple_django_start.py 存在
) else (
    echo ✗ simple_django_start.py 不存在
)

if exist "test_django_config.py" (
    echo ✓ test_django_config.py 存在
) else (
    echo ✗ test_django_config.py 不存在
)
echo.

echo 3. 检查批处理文件...
if exist "run_django.bat" (
    echo ✓ run_django.bat 存在
) else (
    echo ✗ run_django.bat 不存在
)

if exist "run_django_cn.bat" (
    echo ✓ run_django_cn.bat 存在
) else (
    echo ✗ run_django_cn.bat 不存在
)

if exist "run_django_robust.bat" (
    echo ✓ run_django_robust.bat 存在
) else (
    echo ✗ run_django_robust.bat 不存在
)
echo.

echo 4. 检查conda环境...
call conda activate yolo
if %errorlevel% equ 0 (
    echo ✓ yolo环境激活成功
    echo 当前环境: %CONDA_DEFAULT_ENV%
) else (
    echo ✗ yolo环境激活失败
    echo 请运行 activate_yolo_env.bat 创建环境
)
echo.

echo 5. 检查Python可用性...
python --version
if %errorlevel% equ 0 (
    echo ✓ Python可用
) else (
    echo ✗ Python不可用
)
echo.

echo 6. 列出当前目录的Python文件...
echo Python文件列表:
dir /b *.py
echo.

echo 7. 检查Django项目结构...
if exist "kitchen_safety_system\web\django_app\settings.py" (
    echo ✓ Django设置文件存在
) else (
    echo ✗ Django设置文件不存在
)

if exist "kitchen_safety_system\web\django_app\static" (
    echo ✓ 静态文件目录存在
) else (
    echo ✗ 静态文件目录不存在
)
echo.

echo 8. 建议的解决方案...
echo.
echo 如果simple_django_start.py不存在:
echo   - 请确保在项目根目录中运行脚本
echo   - 检查文件是否被意外删除
echo.
echo 如果yolo环境激活失败:
echo   - 运行: activate_yolo_env.bat
echo   - 或手动创建: conda create -n yolo python=3.9
echo.
echo 如果仍有问题:
echo   - 使用健壮版本: run_django_robust.bat
echo   - 或使用PowerShell版本: run_django.ps1
echo.

pause