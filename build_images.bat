@echo off
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   TextGuard - Build Docker Images Locally
echo   Output .tar files, upload to server to deploy
echo ============================================================
echo.

REM ---- Check Docker Desktop ----
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Desktop is not running. Please start it first.
    pause
    exit /b 1
)
echo [OK] Docker Desktop ready

REM ---- Check required files ----
if not exist "backend\Dockerfile" (
    echo [ERROR] backend\Dockerfile not found. Run this script from project root.
    pause
    exit /b 1
)
if not exist "frontend\Dockerfile" (
    echo [ERROR] frontend\Dockerfile not found.
    pause
    exit /b 1
)
if exist "frontend\ssl" (
    echo [OK] SSL certificate directory found (HTTPS mode)
) else (
    echo [INFO] No SSL directory found, building in HTTP mode
)
echo [OK] Project files check passed
echo.

REM ---- Create output directory ----
if not exist "docker-images" mkdir docker-images

REM ---- Build backend image ----
echo ============================================================
echo [1/4] Building backend image: textguard-backend:latest
echo       (First build downloads python:3.11-slim, ~3-5 min)
echo ============================================================
docker build -t textguard-backend:latest -f backend\Dockerfile backend\
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Backend image build FAILED!
    pause
    exit /b 1
)
echo [OK] Backend image built successfully
echo.

REM ---- Build frontend image ----
echo ============================================================
echo [2/4] Building frontend image: textguard-frontend:latest
echo       (First build downloads node:18-alpine, ~3-5 min)
echo ============================================================
docker build -t textguard-frontend:latest -f frontend\Dockerfile frontend\
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Frontend image build FAILED!
    pause
    exit /b 1
)
echo [OK] Frontend image built successfully
echo.

REM ---- Export backend image ----
echo ============================================================
echo [3/4] Exporting backend image to docker-images\textguard-backend.tar
echo       (~300-500MB, please wait...)
echo ============================================================
docker save -o docker-images\textguard-backend.tar textguard-backend:latest
if %errorlevel% neq 0 (
    echo [ERROR] Backend image export FAILED!
    pause
    exit /b 1
)
echo [OK] Backend image exported
echo.

REM ---- Export frontend image ----
echo ============================================================
echo [4/4] Exporting frontend image to docker-images\textguard-frontend.tar
echo       (~30-80MB, please wait...)
echo ============================================================
docker save -o docker-images\textguard-frontend.tar textguard-frontend:latest
if %errorlevel% neq 0 (
    echo [ERROR] Frontend image export FAILED!
    pause
    exit /b 1
)
echo [OK] Frontend image exported
echo.

REM ---- Show results ----
echo ============================================================
echo   BUILD COMPLETE! Image files:
echo ============================================================
echo.
for %%F in (docker-images\textguard-backend.tar) do (
    set "size=%%~zF"
    set /a "sizeMB=!size! / 1048576"
    echo   textguard-backend.tar   !sizeMB! MB
)
for %%F in (docker-images\textguard-frontend.tar) do (
    set "size=%%~zF"
    set /a "sizeMB=!size! / 1048576"
    echo   textguard-frontend.tar  !sizeMB! MB
)
echo.
echo ============================================================
echo   NEXT STEPS:
echo ============================================================
echo.
echo   1. Upload these files to server /opt/TextGuard/:
echo.
echo      docker-images\textguard-backend.tar
echo      docker-images\textguard-frontend.tar
echo      docker-compose.yml
echo      deploy.sh
echo      backend\.env.production
echo.
echo   2. SSH to server and run:
echo.
echo      cd /opt/TextGuard
echo      bash deploy.sh
echo.
echo ============================================================
pause
