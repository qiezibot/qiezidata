$ErrorActionPreference = "Continue"
$baseUrl = "https://qiezidata-production.up.railway.app"

Write-Output "=== Checking $baseUrl ==="

# Try multiple endpoints
$endpoints = @("/debug", "/", "/api/health", "/health")
foreach ($ep in $endpoints) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri "$baseUrl$ep" -UseBasicParsing -TimeoutSec 15 -Method GET
        Write-Output "--- $ep -> HTTP $($r.StatusCode) ---"
        if ($r.Content) {
            $c = $r.Content
            if ($c.Length -gt 600) { $c = $c.Substring(0, 600) + "...(truncated)" }
            Write-Output $c
        }
    } catch {
        Write-Output "--- $ep -> ERROR: $($_.Exception.Message) ---"
    }
}
