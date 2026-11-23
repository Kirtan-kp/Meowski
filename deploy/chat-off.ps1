# Turns Mochi's chat service OFF (the website then shows "Mochi is napping").
# Add -QuitDocker to also close Docker Desktop and free memory.
param([switch]$QuitDocker)
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose -f docker-compose.yml -f deploy/docker-compose.tunnel.yml stop
Write-Host "Chat is OFF. Your data (uploads, history) is kept."
if ($QuitDocker) {
    Get-Process "Docker Desktop" -ErrorAction SilentlyContinue | Stop-Process
    wsl --shutdown 2>$null
    Write-Host "Docker Desktop closed."
}
