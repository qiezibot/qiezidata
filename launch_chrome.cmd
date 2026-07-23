@echo off
taskkill /f /im chrome.exe >nul 2>&1
timeout /t 3 /nobreak >nul
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --no-first-run https://github.com/settings/tokens
