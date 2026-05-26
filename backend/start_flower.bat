@echo off
chcp 65001 >nul 2>&1
echo =======================================
echo  TextGuard Celery Flower 监控面板
echo =======================================

cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未找到虚拟环境
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

pip show flower >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装 Flower ...
    pip install flower -i https://mirrors.aliyun.com/pypi/simple/
)

echo 启动 Flower 监控面板: http://localhost:5555
celery -A app.celery_app:celery_app flower --port=5555

pause
