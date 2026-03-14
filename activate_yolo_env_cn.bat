@echo off
REM 设置控制台代码页为UTF-8以支持中文显示
chcp 65001 >nul

echo 正在激活yolo conda环境...

REM 检查conda是否已安装
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: conda未安装或未在PATH中
    echo 请先安装Anaconda或Miniconda
    pause
    exit /b 1
)

REM 检查yolo环境是否存在
conda env list | findstr "yolo" >nul
if %errorlevel% neq 0 (
    echo yolo环境不存在，正在创建...
    
    REM 检查environment.yml是否存在
    if exist "environment.yml" (
        echo 使用environment.yml创建环境...
        conda env create -f environment.yml
    ) else (
        echo 手动创建yolo环境...
        conda create -n yolo python=3.9 -y
        call conda activate yolo
        pip install -r requirements.txt
    )
) else (
    echo yolo环境已存在
)

REM 激活环境
echo 激活yolo环境...
call conda activate yolo

echo yolo环境已激活！
python --version
echo 当前环境: %CONDA_DEFAULT_ENV%

pause