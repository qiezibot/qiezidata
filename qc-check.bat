@echo off
REM 开机自检脚本：确保 QQ Bot 和 STT 配置不丢失
REM 配合 Task Scheduler 开机启动运行

set CONFIG=%~dp0..\openclaw.json
set TMPFILE=%TEMP%\qc_check_temp.json

REM 检测配置中是否有 qqbot.appId
findstr /C:"\"appId\": \"1904006743\"" "%CONFIG%" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [QC] ⚠️ QQ Bot 配置丢失，正在恢复...
    
    REM 备份原配置
    copy "%CONFIG%" "%CONFIG%.bak" /Y >nul 2>&1
    
    REM 用 Node.js 注入配置
    node -e "
        const fs = require('fs');
        let cfg = JSON.parse(fs.readFileSync('%CONFIG:\=\\%', 'utf-8'));
        cfg.channels = cfg.channels || {};
        cfg.channels.qqbot = {
            appId: '1904006743',
            clientSecret: '8TpCayOoGiBfAgCkJsS3fIwaFwdL4oZK',
            enabled: true,
            stt: {
                enabled: true,
                baseUrl: 'http://127.0.0.1:18766/v1',
                apiKey: 'sk-not-needed',
                model: 'vosk'
            }
        };
        fs.writeFileSync('%CONFIG:\=\\%', JSON.stringify(cfg, null, 2), 'utf-8');
        console.log('[QC] ✅ QQ Bot + STT 配置已恢复');
    "
) else (
    echo [QC] ✅ QQ Bot 配置正常
)

REM 同时检查 STT 服务是否在运行
echo [QC] 检查 Vosk STT 服务...
curl -s http://127.0.0.1:18766/health >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [QC] ⚠️ STT 服务未运行，正在启动...
    start "vosk-stt-server" /MIN /B node "%~dp0vosk-stt-server.mjs" 18766
) else (
    echo [QC] ✅ STT 服务运行正常
)

echo [QC] 开机自检完成
