# PowerShell版Django启动脚本
# 更好的中文支持

# 设置输出编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "设置Django环境..." -ForegroundColor Green

# 激活conda环境
Write-Host "激活yolo conda环境..." -ForegroundColor Yellow
try {
    conda activate yolo
    if ($LASTEXITCODE -ne 0) {
        throw "无法激活yolo环境"
    }
} catch {
    Write-Host "错误: 无法激活yolo环境" -ForegroundColor Red
    Write-Host "请先运行 activate_yolo_env.bat 创建环境" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "当前conda环境: $env:CONDA_DEFAULT_ENV" -ForegroundColor Cyan

# 设置环境变量
$env:PYTHONPATH = Get-Location
$env:DJANGO_SETTINGS_MODULE = "kitchen_safety_system.web.django_app.settings"
$env:DATABASE_ENGINE = "sqlite3"
$env:DATABASE_NAME = "kitchen_safety.db"

Write-Host "PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Gray
Write-Host "DJANGO_SETTINGS_MODULE: $env:DJANGO_SETTINGS_MODULE" -ForegroundColor Gray

# 进入Django目录
Set-Location "kitchen_safety_system\web\django_app"
Write-Host "当前目录: $(Get-Location)" -ForegroundColor Gray

# 执行Django命令
Write-Host "检查Django配置..." -ForegroundColor Yellow
python manage.py check

Write-Host "创建迁移文件..." -ForegroundColor Yellow
python manage.py makemigrations

Write-Host "应用迁移..." -ForegroundColor Yellow
python manage.py migrate

Write-Host "创建超级用户..." -ForegroundColor Yellow
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings'); django.setup(); from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin123'); print('超级用户: admin/admin123')"

Write-Host "启动Django服务器..." -ForegroundColor Green
Write-Host "Web界面: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "管理后台: http://127.0.0.1:8000/admin" -ForegroundColor Cyan

python manage.py runserver 127.0.0.1:8000

Read-Host "按回车键退出"