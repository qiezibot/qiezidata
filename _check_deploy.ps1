$url = "https://qiezidata-production.up.railway.app/debug"
try {
    $resp = Invoke-WebRequest -Uri $url -TimeoutSec 30 -UseBasicParsing
    Write-Host "HTTP $($resp.StatusCode)"
    Write-Host $resp.Content
} catch {
    Write-Host "Error: $($_.Exception.Message)"
}
