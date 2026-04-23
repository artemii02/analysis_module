$ErrorActionPreference = "Stop"

$processes = Get-Process ngrok -ErrorAction SilentlyContinue
if (-not $processes) {
    Write-Host "ngrok is not running."
    exit 0
}

$processes | Stop-Process -Force
Write-Host "ngrok stopped."
