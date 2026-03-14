@echo off
chcp 65001 >nul
echo Setting up Django environment...

REM Activate conda environment
echo Activating yolo conda environment...
call conda activate yolo
if %errorlevel% neq 0 (
    echo Error: Cannot activate yolo environment
    echo Please run activate_yolo_env.bat first to create the environment
    pause
    exit /b 1
)

echo Current conda environment: %CONDA_DEFAULT_ENV%

REM Ensure we are in the correct directory
echo Current directory: %cd%

REM Check if simple_django_start.py exists
if not exist "simple_django_start.py" (
    echo Error: simple_django_start.py file not found
    echo Please make sure to run this script from the project root directory
    pause
    exit /b 1
)

echo Starting Django using simplified script...
python simple_django_start.py

pause