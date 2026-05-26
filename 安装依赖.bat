@echo off
chcp 65001 >nul 2>&1
title TextGuard - Install Dependencies

echo ========================================
echo  TextGuard - Dependency Installation
echo ========================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM ========== Backend Dependencies ==========
echo [1/2] Installing Backend Dependencies...
echo.

cd /d "%PROJECT_DIR%backend"

if not exist "venv" (
    echo       Creating Python virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat
echo       Installing packages (using Aliyun mirror)...
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
if %errorlevel% neq 0 (
    echo [ERROR] Backend dependency installation failed
    pause
    exit /b 1
)
echo.
echo       Backend dependencies installed successfully!
echo.

REM ========== Frontend Dependencies ==========
echo [2/2] Installing Frontend Dependencies...
echo.

cd /d "%PROJECT_DIR%frontend"

echo       Installing packages (using npmmirror)...
npm install --registry=https://registry.npmmirror.com
if %errorlevel% neq 0 (
    echo [ERROR] Frontend dependency installation failed
    pause
    exit /b 1
)
echo.
echo       Frontend dependencies installed successfully!
echo.

echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Run "start_dev.bat" to start all services
echo   2. Or run backend/start_backend.bat separately
echo.
pause
