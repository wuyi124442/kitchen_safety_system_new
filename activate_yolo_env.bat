@echo off
REM Set console code page to UTF-8 for Chinese character support
chcp 65001 >nul

echo Activating yolo conda environment...

REM Check if conda is installed
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: conda not installed or not in PATH
    echo Please install Anaconda or Miniconda first
    pause
    exit /b 1
)

REM Check if yolo environment exists
conda env list | findstr "yolo" >nul
if %errorlevel% neq 0 (
    echo yolo environment does not exist, creating...
    
    REM Check if environment.yml exists
    if exist "environment.yml" (
        echo Creating environment using environment.yml...
        conda env create -f environment.yml
    ) else (
        echo Creating yolo environment manually...
        conda create -n yolo python=3.9 -y
        call conda activate yolo
        pip install -r requirements.txt
    )
) else (
    echo yolo environment already exists
)

REM Activate environment
echo Activating yolo environment...
call conda activate yolo

echo yolo environment activated!
python --version
echo Current environment: %CONDA_DEFAULT_ENV%

pause