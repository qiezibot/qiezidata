@echo off
REM 启动 Vosk STT Server（后台静默运行）
REM 防止重复启动
tasklist /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq vosk-stt-server*" 2>NUL | find /I /N "node.exe" >NUL
if %ERRORLEVEL% EQU 0 (
    echo Vosk STT Server already running.
    exit /b 0
)

start "vosk-stt-server" /MIN /B node "%~dp0vosk-stt-server.mjs" 18766
echo Vosk STT Server started on port 18766
