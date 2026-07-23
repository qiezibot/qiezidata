@echo off
chcp 65001 >nul
title OpenClaw 启动

set LOG_DIR=C:\u-claw\portable\data\.openclaw\workspace\logs
set STARTUP_LOG=%LOG_DIR%\startup-check.log

echo [%DATE% %TIME%] [INFO] [STARTUP] === OpenClaw 启动开始 === >> %STARTUP_LOG%

echo.
echo ===========================================
echo   🍆 OpenClaw 启动器 - 茄子的小管家
echo ===========================================
echo.

:: 1. 启动检查
echo [%DATE% %TIME%] [INFO] [STARTUP] 运行启动检查... >> %STARTUP_LOG%
cd /d C:\u-claw\portable\data\.openclaw\workspace
node startup_check.cjs
if %ERRORLEVEL% neq 0 (
    echo [%DATE% %TIME%] [WARN] [STARTUP] 启动检查有警告，继续启动 >> %STARTUP_LOG%
)

:: 2. 启动 gateway
echo [%DATE% %TIME%] [INFO] [STARTUP] 启动 OpenClaw gateway... >> %STARTUP_LOG%
echo.
echo [2/2] 启动 OpenClaw gateway...
start "OpenClaw Gateway" cmd /c "cd /d C:\u-claw\portable && openclaw gateway start >> %LOG_DIR%\gateway.log 2>&1"

echo.
echo ===========================================
echo   ✅ 启动命令已执行
echo   查看日志: type %LOG_DIR%\startup-check.log
echo   实时监控: powershell -Command "Get-Content %LOG_DIR%\gateway.log -Tail 10 -Wait"
echo ===========================================
echo.

:: 写完成日志
echo [%DATE% %TIME%] [INFO] [STARTUP] === OpenClaw 启动完成 === >> %STARTUP_LOG%
