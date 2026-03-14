@echo off
REM 厨房安全检测系统 Windows 部署脚本
REM 版本: 1.0

setlocal enabledelayedexpansion

echo ================================================================
echo            厨房安全检测系统 - Windows 部署脚本
echo ================================================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未安装或未启动，请先安装并启动 Docker Desktop
    pause
    exit /b 1
)

REM 检查Docker Compose是否可用
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [错误] Docker Compose 未安装
        pause
        exit /b 1
    )
)

echo [信息] Docker 环境检查通过

REM 检查.env文件
if not exist ".env" (
    echo [警告] .env 文件不存在，从模板创建...
    copy ".env.example" ".env"
    echo [警告] 请编辑 .env 文件并配置正确的参数
    echo [警告] 特别注意修改以下配置：
    echo   - POSTGRES_PASSWORD
    echo   - DJANGO_SECRET_KEY
    echo   - DJANGO_ALLOWED_HOSTS
    pause
)

REM 创建必要目录
if not exist "logs" mkdir logs
if not exist "logs\video_clips" mkdir logs\video_clips
if not exist "data" mkdir data
if not exist "models" mkdir models
if not exist "backups" mkdir backups

echo [信息] 开始构建Docker镜像...
docker-compose build

if errorlevel 1 (
    echo [错误] 镜像构建失败
    pause
    exit /b 1
)

echo [信息] 启动服务...

REM 启动数据库和缓存服务
echo [信息] 启动数据库和缓存服务...
docker-compose up -d postgres redis

REM 等待数据库就绪
echo [信息] 等待数据库就绪...
timeout /t 10 /nobreak >nul

REM 启动应用服务
echo [信息] 启动应用服务...
docker-compose up -d kitchen_safety web

REM 等待应用就绪
echo [信息] 等待应用就绪...
timeout /t 15 /nobreak >nul

REM 启动Nginx
echo [信息] 启动Nginx代理...
docker-compose up -d nginx

echo.
echo [成功] 部署完成！
echo.
echo ================================================================
echo                    访问信息
echo ================================================================
echo.
echo Web管理界面: http://localhost
echo API接口:     http://localhost/api/
echo 健康检查:   http://localhost/health
echo.
echo 默认管理员账户:
echo   用户名: admin
echo   密码: admin123 (请及时修改)
echo.
echo 常用命令:
echo   查看状态: docker-compose ps
echo   查看日志: docker-compose logs -f [service_name]
echo   重启服务: docker-compose restart [service_name]
echo   停止服务: docker-compose down
echo.

pause