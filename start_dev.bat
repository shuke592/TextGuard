@echo off
chcp 65001 >nul 2>&1
title TextGuard Development Environment

echo ========================================
echo  TextGuard - Development Quick Start
echo ========================================
echo.

REM Get project root directory
set "PROJECT_ROOT=%~dp0"

REM ========== Step 1: Clean up old processes ==========
echo [1/4] Cleaning up old processes...

REM First pass: kill all listening processes on 3020 and 3022
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3020" ^| findstr "LISTENING"') do (
    echo       Killing port 3020 process (PID: %%a)
    taskkill /F /PID %%a /T >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3022" ^| findstr "LISTENING"') do (
    echo       Killing port 3022 process (PID: %%a)
    taskkill /F /PID %%a /T >nul 2>&1
)

timeout /t 3 /nobreak >nul

REM Second pass: verify and kill again
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3020" ^| findstr "LISTENING"') do (
    echo       [Retry] Killing port 3020 (PID: %%a)
    taskkill /F /PID %%a /T >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3022" ^| findstr "LISTENING"') do (
    echo       [Retry] Killing port 3022 (PID: %%a)
    taskkill /F /PID %%a /T >nul 2>&1
)

timeout /t 2 /nobreak >nul
echo       Ports cleared

REM ========== Step 2: Check dependencies ==========
echo [2/4] Checking dependencies...

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

REM Check backend venv
if not exist "%PROJECT_ROOT%backend\venv\Scripts\activate.bat" (
    echo [ERROR] Backend virtual environment not found
    echo Please run: cd backend ^&^& python -m venv venv
    pause
    exit /b 1
)

REM Check frontend node_modules
if not exist "%PROJECT_ROOT%frontend\node_modules" (
    echo [WARNING] Frontend dependencies not installed
    echo Installing now...
    cd /d "%PROJECT_ROOT%frontend"
    npm install --registry=https://registry.npmmirror.com
)

echo       Dependencies OK

REM ========== Step 3: Start Backend ==========
echo [3/4] Starting Backend Server...
cd /d "%PROJECT_ROOT%backend"
start "TextGuard-Backend" cmd /k "call start_backend.bat"

REM Wait for backend to be ready (max 20 seconds)
echo       Waiting for backend to be ready...
set /a count=0
:check_backend
timeout /t 2 /nobreak >nul
set /a count+=1
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:3020/api/v1/health > "%TEMP%\tg_check.txt" 2>nul
set /p http_code=<"%TEMP%\tg_check.txt"
del "%TEMP%\tg_check.txt" >nul 2>&1
if "%http_code%"=="200" (
    echo       Backend is ready!
    goto backend_ok
)
if %count% GEQ 10 (
    echo       [WARNING] Backend health check timeout, but continuing...
    goto backend_ok
)
goto check_backend
:backend_ok

REM ========== Step 4: Start Frontend ==========
echo [4/4] Starting Frontend Server...
cd /d "%PROJECT_ROOT%frontend"
start "TextGuard-Frontend" cmd /k "call start_frontend.bat"

echo.
echo ========================================
echo  All services started successfully!
echo ========================================
echo.
echo Backend:  http://localhost:3020/docs
echo Frontend: http://localhost:3022
echo.
echo Default Login:
echo   Employee ID: admin
echo   Password:    admin123
echo.
echo Close the terminal windows to stop services
echo ========================================
echo.
pause
