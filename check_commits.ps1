$r = (New-Object Net.WebClient).DownloadString('https://api.github.com/repos/qiezibot/qiezidata/commits?per_page=5') | ConvertFrom-Json
foreach ($c in $r) {
    $sha = $c.sha.Substring(0,8)
    $msg = $c.commit.message.Split("`n")[0]
    Write-Host ('=== ' + $sha + ' ===')
    Write-Host ('  ' + $msg)
    Write-Host ('  By: ' + $c.commit.author.name + ' at ' + $c.commit.author.date)
    Write-Host ''
}
