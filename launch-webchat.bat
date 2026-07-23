@echo off
chcp 65001 >nul
echo 正在启动 OpenClaw WebChat + 自动发送...

:: 用带远程调试端口的Chrome打开WebChat
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 http://localhost:18789/webchat

:: 等待页面加载
timeout /t 3 /nobreak >nul

echo.
echo 现在在浏览器里按 F12 打开开发者工具
echo 在 Console 里粘贴以下代码，回车即可激活自动发送：
echo.
echo ====== 复制下面的代码 ======
echo.
type "%~dp0autosend-inject.js"
echo.
echo ====== 复制结束 ======
echo.
pause
