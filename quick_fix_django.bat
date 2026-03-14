@echo off
chcp 65001 >nul
echo ========================================
echo Django快速修复工具
echo ========================================
echo.

echo 正在检查和修复常见问题...
echo.

REM 1. 检查并创建缺失的Python脚本
if not exist "simple_django_start.py" (
    echo 创建 simple_django_start.py...
    echo 请等待，正在从备份恢复文件...
    
    REM 这里可以添加创建脚本的逻辑
    echo 错误: simple_django_start.py 缺失
    echo 请重新下载项目文件或联系技术支持
    pause
    exit /b 1
) else (
    echo ✓ simple_django_start.py 存在
)

REM 2. 检查conda环境
echo 检查conda环境...
call conda activate yolo >nul 2>&1
if %errorlevel% neq 0 (
    echo 创建yolo环境...
    if exist "environment.yml" (
        conda env create -f environment.yml
    ) else (
        conda create -n yolo python=3.9 -y
    )
) else (
    echo ✓ yolo环境存在
)

REM 3. 检查Django项目结构
echo 检查Django项目结构...
if not exist "kitchen_safety_system\web\django_app\static" (
    echo 创建静态文件目录...
    mkdir "kitchen_safety_system\web\django_app\static\css" 2>nul
    echo /* 基础样式 */ > "kitchen_safety_system\web\django_app\static\css\base.css"
    echo ✓ 静态文件目录已创建
) else (
    echo ✓ 静态文件目录存在
)

REM 4. 设置正确的权限和路径
echo 设置环境变量...
set PYTHONPATH=%cd%
set DJANGO_SETTINGS_MODULE=kitchen_safety_system.web.django_app.settings

echo.
echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 现在可以尝试运行:
echo 1. run_django_robust.bat (推荐)
echo 2. start_django.bat (选择健壮版本)
echo 3. run_django.ps1 (PowerShell版本)
echo.

pause