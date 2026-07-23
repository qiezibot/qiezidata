$wshell = New-Object -ComObject WScript.Shell
$t = [DateTime]::Now.AddSeconds(-10)
Write-Host "自动发送已启动 - 此窗口最小化后不影响使用" -ForegroundColor Green
Write-Host "在其他任意窗口打字，停3秒会自动按Enter" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 退出" -ForegroundColor Yellow

while($true){
    $key = $false
    for($i=8;$i -le 222;$i++){
        if([Console]::KeyAvailable){ $key=$true; break }
    }
    if($key){
        [Console]::ReadKey($true) | Out-Null
        $t = [DateTime]::Now
    } else {
        $d = ([DateTime]::Now - $t).TotalSeconds
        if($d -ge 3){
            [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
            $t = [DateTime]::Now.AddSeconds(-10)
        }
        Start-Sleep -Milliseconds 500
    }
}
