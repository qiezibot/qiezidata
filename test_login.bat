@echo off
set BASE=https://qiezidata-production.up.railway.app

echo === Debug endpoint ===
curl.exe -s "%BASE%/debug" | findstr /V "^$"

echo.
echo === 1. Login as admin/admin123 ===
curl.exe -s -c "%TEMP%\cookies_admin.txt" -X POST "%BASE%/api/login" -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"admin123\"}"

echo.
echo Fetch main page as admin...
curl.exe -s -b "%TEMP%\cookies_admin.txt" "%BASE%/" > "%TEMP%\admin_page.html"
echo (saved to %%TEMP%%\admin_page.html)

echo.
echo === 2. Login as qiezi/qiezi123 ===
curl.exe -s -c "%TEMP%\cookies_qiezi.txt" -X POST "%BASE%/api/login" -H "Content-Type: application/json" -d "{\"username\":\"qiezi\",\"password\":\"qiezi123\"}"

echo.
echo Fetch main page as qiezi...
curl.exe -s -b "%TEMP%\cookies_qiezi.txt" "%BASE%/" > "%TEMP%\qiezi_page.html"
echo (saved to %%TEMP%%\qiezi_page.html)

echo.
echo === 3. Try chengzi with various passwords ===
echo Trying chengzi/chengzi123...
curl.exe -s -c "%TEMP%\cookies_chengzi.txt" -X POST "%BASE%/api/login" -H "Content-Type: application/json" -d "{\"username\":\"chengzi\",\"password\":\"chengzi123\"}"

echo.
echo Done. Results:
echo.
