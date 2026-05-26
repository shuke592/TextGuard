@echo off
chcp 65001 >nul
echo ============================================================
echo   TextGuard 一键推送到 GitHub + Gitee
echo ============================================================
echo.

REM 检查是否有 Git 仓库
if not exist ".git" (
    echo [ERROR] 当前目录不是 Git 仓库，请先执行 git init
    pause
    exit /b 1
)

REM 显示当前状态
echo [INFO] 当前 Git 状态：
git status --short
echo.

REM 询问是否继续
set /p confirm="是否推送到远程仓库？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消推送。
    pause
    exit /b 0
)

echo.
echo [1/2] 正在推送到 GitHub (origin)...
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] GitHub 推送失败！请检查网络或认证信息。
    echo   提示：GitHub 需要使用 Personal Access Token 作为密码
    echo   获取Token: https://github.com/settings/tokens
    pause
    exit /b 1
)
echo [OK] GitHub 推送成功！
echo.

echo [2/2] 正在推送到 Gitee (gitee)...
git push gitee main
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gitee 推送失败！请检查网络或认证信息。
    pause
    exit /b 1
)
echo [OK] Gitee 推送成功！
echo.

echo ============================================================
echo   推送完成！
echo   GitHub: https://github.com/shuke592/TextGuard
echo   Gitee:  https://gitee.com/shuke592/TextGuard
echo ============================================================
pause
