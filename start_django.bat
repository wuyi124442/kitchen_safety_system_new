@echo off
chcp 65001 >nul
title Kitchen Safety Detection System - Django Launcher

echo ========================================
echo Kitchen Safety Detection System
echo Django Web Interface Launcher
echo ========================================
echo.

echo Please select startup method:
echo.
echo 1. English version (run_django.bat)
echo 2. Chinese version (run_django_cn.bat) 
echo 3. Robust version (run_django_robust.bat) - Recommended
echo 4. No Redis version (run_django_no_redis.bat) - Fix Redis errors
echo 5. Simple No Redis (run_django_simple_no_redis.bat) - Most reliable
echo 6. PowerShell version (run_django.ps1) - Best Chinese support
echo 7. Fix encoding issues (fix_chinese_encoding.bat)
echo 8. Exit
echo.

set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" (
    echo Starting English version...
    call run_django.bat
) else if "%choice%"=="2" (
    echo Starting Chinese version...
    call run_django_cn.bat
) else if "%choice%"=="3" (
    echo Starting Robust version...
    call run_django_robust.bat
) else if "%choice%"=="4" (
    echo Starting No Redis version...
    call run_django_no_redis.bat
) else if "%choice%"=="5" (
    echo Starting Simple No Redis version...
    call run_django_simple_no_redis.bat
) else if "%choice%"=="6" (
    echo Starting PowerShell version...
    powershell -ExecutionPolicy Bypass -File run_django.ps1
) else if "%choice%"=="7" (
    echo Running encoding fix...
    call fix_chinese_encoding.bat
) else if "%choice%"=="8" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice, please try again.
    pause
    goto :eof
)

pause