@echo off
chcp 65001 >nul 2>&1
echo =======================================
echo  TextGuard Celery Worker 启动
echo =======================================

cd /d "%~dp0"

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo [错误] 未找到虚拟环境，请先运行 install.bat 安装依赖
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo 正在启动 Celery Worker ...
echo Broker: Redis DB 8
echo Backend: Redis DB 9
echo.

celery -A app.celery_app:celery_app worker --loglevel=info --pool=solo -c 1

pause
