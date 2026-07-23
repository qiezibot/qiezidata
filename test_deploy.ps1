$baseUrl = "https://qiezidata-production.up.railway.app"

function Login-Test {
    param($username, $password, $expectAdmin)
    
    Write-Host "`n=== Testing login: $username ==="
    
    $body = @{username=$username;password=$password} | ConvertTo-Json
    $bodyBytes = [Text.Encoding]::UTF8.GetBytes($body)
    
    try {
        $login = Invoke-WebRequest -Uri "$baseUrl/api/login" -Method POST -Body $bodyBytes -ContentType "application/json" -SessionVariable sv -UseBasicParsing
        Write-Host "Login status: $($login.StatusCode)"
        $cookies = $sv.Cookies.GetCookies($baseUrl)
        foreach ($c in $cookies) { Write-Host "Cookie: $($c.Name)=$($c.Value)" }
    } catch {
        Write-Host "Login FAILED: $_"
        return $false
    }
    
    try {
        $main = Invoke-WebRequest -Uri "$baseUrl/" -WebSession $sv -UseBasicParsing
        Write-Host "Main page status: $($main.StatusCode)"
        Write-Host "Content length: $($main.Content.Length)"
        
        $hasUserMgmt = $main.Content -match "用户管理"
        $hasDashboard = $main.Content -match "仪表盘"
        Write-Host "Contains '用户管理': $hasUserMgmt"
        Write-Host "Contains '仪表盘': $hasDashboard"
        
        if ($expectAdmin) {
            if ($hasUserMgmt -and $hasDashboard) {
                Write-Host "RESULT: PASS - Admin sees all links" -ForegroundColor Green
                return $true
            } else {
                Write-Host "RESULT: FAIL - Admin should see both links" -ForegroundColor Red
                return $false
            }
        } else {
            if (-not $hasUserMgmt -and -not $hasDashboard) {
                Write-Host "RESULT: PASS - Non-admin sees limited links" -ForegroundColor Green
                return $true
            } else {
                Write-Host "RESULT: FAIL - Non-admin should NOT see admin links" -ForegroundColor Red
                return $false
            }
        }
    } catch {
        Write-Host "Main page fetch FAILED: $_"
        return $false
    }
}

Write-Host "===================="
Write-Host "Deployment Test Suite"
Write-Host "===================="

# Test 0: Debug endpoint
try {
    $debug = Invoke-WebRequest -Uri "$baseUrl/debug" -UseBasicParsing
    Write-Host "`n=== Debug endpoint ==="
    Write-Host "Status: $($debug.StatusCode)"
    Write-Host "Body: $($debug.Content.Substring(0, [Math]::Min(300, $debug.Content.Length)))..."
} catch {
    Write-Host "DEBUG FAILED: $_"
}

# Test chengzi password - try various known passwords
$passwords = @("chengzi123", "chengzi", "123456", "12345678", "password")
foreach ($pw in $passwords) {
    try {
        $body = @{username="chengzi";password=$pw} | ConvertTo-Json
        $bodyBytes = [Text.Encoding]::UTF8.GetBytes($body)
        $login = Invoke-WebRequest -Uri "$baseUrl/api/login" -Method POST -Body $bodyBytes -ContentType "application/json" -SessionVariable sv -UseBasicParsing -ErrorAction Stop
        Write-Host "`nchengzi password '$pw' => login works! Status: $($login.StatusCode)"
        break
    } catch {
        Write-Host "chengzi password '$pw' => failed"
    }
}

# Test 1: Admin login
Login-Test -username "admin" -password "admin123" -expectAdmin $true

# Test 2: qiezi login
Login-Test -username "qiezi" -password "qiezi123" -expectAdmin $false

Write-Host "`n===================="
Write-Host "Tests Complete"
Write-Host "===================="
