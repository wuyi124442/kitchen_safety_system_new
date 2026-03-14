@echo off
REM 厨房安全检测系统 Windows 维护脚本
REM 版本: 1.0

setlocal enabledelayedexpansion

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="backup" goto backup
if "%1"=="health-check" goto health_check
if "%1"=="logs" goto logs
if "%1"=="restart" goto restart
if "%1"=="cleanup-logs" goto cleanup_logs

goto help

:backup
echo [信息] 备份数据库...
if not exist "backups" mkdir backups

REM 生成时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

set "backup_file=backups\db_backup_%timestamp%.sql"

docker-compose exec -T postgres pg_dump -U kitchen_user kitchen_safety > "%backup_file%"

if errorlevel 1 (
    echo [错误] 数据库备份失败
    exit /b 1
) else (
    echo [成功] 数据库备份完成: %backup_file%
)
goto end

:health_check
echo [信息] 执行系统健康检查...
echo.
echo 容器状态:
docker-compose ps
echo.
echo 服务健康状态:

for %%s in (postgres redis kitchen_safety web nginx) do (
    for /f %%i in ('docker-compose ps -q %%s') do (
        if "%%i" neq "" (
            for /f %%j in ('docker inspect --format="{{.State.Status}}" %%i') do (
                if "%%j"=="running" (
                    echo   [✓] %%s: 运行正常
                ) else (
                    echo   [✗] %%s: 未运行 (%%j)
                )
            )
        ) else (
            echo   [✗] %%s: 容器不存在
        )
    )
)
goto end

:logs
if "%2"=="" (
    docker-compose logs --tail=100
) else (
    if "%3"=="" (
        docker-compose logs --tail=100 %2
    ) else (
        docker-compose logs --tail=%3 %2
    )
)
goto end

:restart
if "%2"=="" (
    echo [信息] 重启所有服务...
    docker-compose restart
) else (
    echo [信息] 重启 %2 服务...
    docker-compose restart %2
)
echo [成功] 服务重启完成
goto end

:cleanup_logs
set "days=%2"
if "%days%"=="" set "days=7"

echo [信息] 清理 %days% 天前的日志文件...

REM 清理应用日志
if exist "logs" (
    forfiles /p logs /s /m *.log /d -%days% /c "cmd /c del @path" 2>nul
)

REM 清理Docker日志
docker system prune -f --filter "until=%days%d" >nul 2>&1

echo [成功] 日志清理完成
goto end

:help
echo 厨房安全检测系统维护脚本
echo.
echo 用法: %0 [命令] [参数]
echo.
echo 命令:
echo   backup                    备份数据库
echo   cleanup-logs [days]       清理日志文件 (默认7天)
echo   health-check              系统健康检查
echo   logs [service] [lines]    查看日志
echo   restart [service]         重启服务
echo   help                      显示此帮助信息
echo.
echo 示例:
echo   %0 backup                           # 备份数据库
echo   %0 cleanup-logs 3                   # 清理3天前的日志
echo   %0 logs kitchen_safety 50           # 查看主服务最近50行日志
echo   %0 restart web                      # 重启Web服务
echo.

:end