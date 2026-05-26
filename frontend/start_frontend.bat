@echo off
chcp 65001 >nul 2>&1
title TextGuard Frontend Server

echo ========================================
echo  TextGuard Frontend - Quick Start
echo ========================================
echo.

REM Get script directory (support Chinese path)
set "FRONTEND_DIR=%~dp0"
cd /d "%FRONTEND_DIR%"

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check node_modules
if not exist "node_modules" (
    echo [INFO] Installing dependencies...
    npm install --registry=https://registry.npmmirror.com
)

echo.
echo [INFO] Starting frontend dev server...
echo [INFO] Frontend: http://localhost:3022
echo [INFO] Backend Proxy: http://localhost:3020
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Start Vite dev server
npm run dev
