$url = "https://qiezidata-production.up.railway.app/debug"
try {
    $r = Invoke-WebRequest -Uri $url -TimeoutSec 20 -UseBasicParsing
    Write-Output ("HTTP " + $r.StatusCode)
    Write-Output $r.Content
} catch {
    Write-Output ("ERROR: " + $_.Exception.Message)
}
