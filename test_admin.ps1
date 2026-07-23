$loginUrl = 'https://qiezidata-production.up.railway.app/login'

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession

# Test 1: Login as admin
$body = @{username='admin';password='admin123'} | ConvertTo-Json
$headers = @{'Content-Type'='application/json'}
try {
    $resp = Invoke-WebRequest -Uri $loginUrl -Method POST -Body $body -ContentType 'application/json' -WebSession $session -UseBasicParsing -ErrorAction Stop
    Write-Host "Admin login status: $($resp.StatusCode)"
    Write-Host "Admin login response: $($resp.Content)"
} catch {
    Write-Host "Admin login error: $_"
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        Write-Host "Error body: $($reader.ReadToEnd())"
    }
}

# Access home page with admin session
Write-Host "--- Admin Home Page ---"
$homeResp = Invoke-WebRequest -Uri 'https://qiezidata-production.up.railway.app/' -WebSession $session -UseBasicParsing
Write-Host "Home page length: $($homeResp.Content.Length)"
$content = $homeResp.Content
if ($content.Length -gt 4000) { $content = $content.Substring(0, 4000) }
Write-Host $content
