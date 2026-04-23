$ErrorActionPreference = "Stop"

$healthUrl = "http://127.0.0.1:8000/assessment/v1/health"
$isReady = $false

try {
    Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 5 | Out-Null
    $isReady = $true
} catch {
}

if (-not $isReady) {
    Write-Host "Starting local HF API in a new window..."
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "`"$PSScriptRoot\..\..\start_hf_api.bat`"" | Out-Null
} else {
    Write-Host "Local HF API is already running."
}

& "$PSScriptRoot\start_ngrok.ps1" -Port 8000
exit $LASTEXITCODE
