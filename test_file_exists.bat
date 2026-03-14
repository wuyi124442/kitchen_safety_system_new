@echo off
echo 测试文件存在性...
echo.

echo 当前目录: %cd%
echo.

echo 检查关键文件:
if exist "simple_django_start.py" (
    echo ✓ simple_django_start.py
) else (
    echo ✗ simple_django_start.py
)

if exist "run_django_cn.bat" (
    echo ✓ run_django_cn.bat
) else (
    echo ✗ run_django_cn.bat
)

if exist "run_django_robust.bat" (
    echo ✓ run_django_robust.bat
) else (
    echo ✗ run_django_robust.bat
)

echo.
echo 文件大小信息:
if exist "simple_django_start.py" (
    for %%A in ("simple_django_start.py") do echo simple_django_start.py: %%~zA bytes
)

echo.
pause