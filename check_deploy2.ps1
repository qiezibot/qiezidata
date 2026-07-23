$ErrorActionPreference = "Stop"
$baseUrl = "https://qiezidata-production.up.railway.app"

Write-Output "Waiting 10s for warmup..."
Start-Sleep 10

Write-Output "=== Step 0: Check /debug endpoint ==="
try {
    $r = Invoke-WebRequest -Uri "$baseUrl/debug" -UseBasicParsing -TimeoutSec 20
    Write-Output "HTTP $($r.StatusCode)"
    $content = $r.Content
    if ($content) {
        $trimmed = $content.Substring(0, [Math]::Min($content.Length, 800))
        Write-Output $trimmed
    }
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
}
