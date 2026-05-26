@echo off
chcp 65001 >nul 2>&1
title TextGuard Backend Server

echo ========================================
echo  TextGuard Backend - Quick Start
echo ========================================
echo.

REM Get script directory (support Chinese path)
set "BACKEND_DIR=%~dp0"
cd /d "%BACKEND_DIR%"

REM ===== Aggressive cleanup of port 3020 =====
echo [INFO] Cleaning up port 3020...

REM First pass: kill all listening processes
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3020" ^| findstr "LISTENING"') do (
    echo       Killing PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Wait for ports to be released
timeout /t 3 /nobreak >nul

REM Second pass: verify and kill again if needed
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3020" ^| findstr "LISTENING"') do (
    echo       [Retry] Killing PID: %%a
    taskkill /F /PID %%a /T >nul 2>&1
)

REM Final wait
timeout /t 2 /nobreak >nul
echo       Port 3020 is ready

REM Check virtual environment
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if dependencies installed
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
)

REM Check .env file
if not exist ".env" (
    echo [WARNING] .env file not found, using default config
)

echo.
echo [INFO] Starting backend server...
echo [INFO] API Docs: http://localhost:3020/docs
echo [INFO] Health Check: http://localhost:3020/api/v1/health
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Start uvicorn server
uvicorn app.main:app --reload --host 0.0.0.0 --port 3020
