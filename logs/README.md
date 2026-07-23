# 📋 OpenClaw 日志系统

## 日志目录结构

```
logs/
├── README.md            ← 本文件
├── openclaw.log         ← OpenClaw 服务主日志（stdout/stderr）
├── gateway.log          ← gateway 启动日志
├── qqbot.log            ← QQ 机器人日志
├── vosk-stt.log         ← 语音识别服务日志
├── cron.log             ← 定时任务日志
├── startup-check.log    ← 启动检查日志
├── prev/                ← 归档的旧日志（每天轮转）
│   ├── openclaw-2026-05-16.log
│   ├── qqbot-2026-05-16.log
│   └── ...
└── old.sh               ← 每日轮转脚本
```

## 启动顺序

1. `C:\u-claw\portable\data\.openclaw\workspace\startup_check.cjs` — 启动检查
2. `openclaw gateway start` — 启动 gateway
3. 各服务（QQbot、STT 等）由 gateway 管理或手动启动

## 常用命令

```powershell
# 查看最新日志（实时）
Get-Content logs\openclaw.log -Tail 20 -Wait

# 查看最近 N 行
Get-Content logs\openclaw.log -Tail 50

# 搜索关键错误
Select-String "error|Error|ERROR" logs\*.log

# 清空日志（保留文件）
Clear-Content logs\openclaw.log

# 手动轮转
.\logs\old.sh
```

## 日志格式

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [SERVICE] message
```

Level: INFO | WARN | ERROR | DEBUG
Service: GATEWAY | QQBOT | STT | STARTUP | CRON

---

_最后由 茄子 于 2026-05-16 创建_
