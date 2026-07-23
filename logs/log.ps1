# logs/log.ps1 - 日志工具函数
# 用途：统一日志写入，所有服务共用

$script:LOG_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:LOG_PREV_DIR = Join-Path $script:LOG_DIR "prev"

# 确保目录存在
if (-not (Test-Path $script:LOG_PREV_DIR)) { New-Item -ItemType Directory -Path $script:LOG_PREV_DIR -Force | Out-Null }

function Write-Log {
    param(
        [string]$Service = "MAIN",
        [string]$Level = "INFO",
        [string]$Message,
        [string]$LogFile = ""
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$timestamp] [$Level] [$Service] $Message"
    
    if ($LogFile -eq "") { $LogFile = Join-Path $script:LOG_DIR "$Service.log" }
    Add-Content -Path $LogFile -Value $line
    Write-Host $line
}

function Write-Info  { param([string]$Service, [string]$Message) Write-Log -Service $Service -Level "INFO"  -Message $Message }
function Write-Warn  { param([string]$Service, [string]$Message) Write-Log -Service $Service -Level "WARN"  -Message $Message }
function Write-Error { param([string]$Service, [string]$Message) Write-Log -Service $Service -Level "ERROR" -Message $Message }
function Write-Debug { param([string]$Service, [string]$Message) Write-Log -Service $Service -Level "DEBUG" -Message $Message }

function Rotate-Logs {
    param([int]$KeepDays = 7)
    
    $today = Get-Date -Format "yyyy-MM-dd"
    $oldest = (Get-Date).AddDays(-$KeepDays)
    
    # 轮转当前日志到 prev/
    Get-ChildItem -Path $script:LOG_DIR -Filter "*.log" | Where-Object { $_.Name -ne "README.md" } | ForEach-Object {
        $destName = "$($_.BaseName)-$today.log"
        $destPath = Join-Path $script:LOG_PREV_DIR $destName
        Copy-Item -Path $_.FullName -Destination $destPath -Force
        Clear-Content -Path $_.FullName
    }
    
    # 删除过期日志
    Get-ChildItem -Path $script:LOG_PREV_DIR -Filter "*.log" | Where-Object { $_.LastWriteTime -lt $oldest } | Remove-Item -Force
    
    Write-Info -Service "LOGROTATE" -Message "日志轮转完成，保留 $KeepDays 天"
}

function Show-LastLines {
    param([string]$LogFile = "", [int]$Lines = 20, [switch]$Watch)
    
    if ($LogFile -eq "") {
        $LogFile = Join-Path $script:LOG_DIR "openclaw.log"
    } else {
        $LogFile = Join-Path $script:LOG_DIR $LogFile
    }
    
    if (-not (Test-Path $LogFile)) {
        Write-Warn "日志文件不存在: $LogFile"
        return
    }
    
    if ($Watch) {
        Get-Content $LogFile -Tail $Lines -Wait
    } else {
        Get-Content $LogFile -Tail $Lines
    }
}
