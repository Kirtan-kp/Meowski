# Turns Mochi's chat service ON: starts Docker Desktop (if needed), Meowski and the free tunnel,
# waits until it answers, then publishes the new tunnel address for the website.
# Run it by double-clicking chat-on.bat (or: powershell -ExecutionPolicy Bypass -File deploy\chat-on.ps1)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)   # the Meowski folder
$compose = @("-f", "docker-compose.yml", "-f", "deploy/docker-compose.tunnel.yml")

function Step($t) { Write-Host "`n== $t" -ForegroundColor Cyan }

# 1. Docker Desktop
Step "Checking Docker"
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    $exe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $exe)) { throw "Docker Desktop was not found. Install it or start it yourself, then run this again." }
    Write-Host "Starting Docker Desktop (this can take a minute)..."
    Start-Process $exe
    $ok = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 3
        docker info *> $null
        if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    }
    if (-not $ok) { throw "Docker did not start in 3 minutes. Open Docker Desktop manually and run this again." }
}
Write-Host "Docker is running."

# 2. Meowski + tunnel
Step "Starting Meowski and the tunnel"
docker compose @compose up -d
if ($LASTEXITCODE -ne 0) { throw "docker compose failed. Check that .env has PROXY_SECRET, LLM_API_KEY, POSTGRES_PASSWORD and METRICS_TOKEN." }

# 3. Find the tunnel address
Step "Waiting for the tunnel address"
$url = $null
for ($i = 0; $i -lt 30 -and -not $url; $i++) {
    Start-Sleep -Seconds 2
    $log = docker compose @compose logs cloudflared 2>&1 | Out-String
    $m = [regex]::Matches($log, "https://(?!api\.)[a-z0-9-]+\.trycloudflare\.com")
    if ($m.Count -gt 0) { $url = $m[$m.Count - 1].Value }
}
if (-not $url) { throw "No tunnel address in the log yet. Run: docker compose -f docker-compose.yml -f deploy/docker-compose.tunnel.yml logs cloudflared" }
Write-Host "Tunnel address: $url"

# 4. Wait until Meowski answers through the tunnel
Step "Waiting for Meowski to answer (first start can take a few minutes)"
$healthy = $false
for ($i = 0; $i -lt 60 -and -not $healthy; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "$url/api/v1/health" -UseBasicParsing -TimeoutSec 8
        if ($r.StatusCode -eq 200) { $healthy = $true }
    } catch { Start-Sleep -Seconds 5 }
}
if ($healthy) { Write-Host "Meowski is answering." -ForegroundColor Green }
else { Write-Host "Meowski did not answer yet. Run: docker compose -f docker-compose.yml -f deploy/docker-compose.tunnel.yml ps" -ForegroundColor Yellow }

# 5. Tell the website the new address
Step "Publishing the address for the website"
$gist = $env:MOCHI_GIST_ID
if ($gist -and (Get-Command gh -ErrorAction SilentlyContinue)) {
    gh api --method PATCH "/gists/$gist" -f "files[api-origin.txt][content]=$url" *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Gist updated. The website picks up the new address within about 5 minutes." -ForegroundColor Green
    } else {
        Write-Host "Could not update the gist. Run 'gh auth login', or paste the address into the gist by hand." -ForegroundColor Yellow
    }
} else {
    Write-Host "Paste this address into your gist file (api-origin.txt), or into API_ORIGIN in Cloudflare Pages:" -ForegroundColor Yellow
}
Set-Clipboard -Value $url
Write-Host "`nAddress copied to the clipboard: $url"
Write-Host "Chat is ON. Keep this PC awake. Run chat-off.bat when you are done."
