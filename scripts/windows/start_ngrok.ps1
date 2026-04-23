param(
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"

if ($Port -le 0) {
    if ($env:NGROK_PORT) {
        $Port = [int]$env:NGROK_PORT
    } else {
        $Port = 8000
    }
}

$ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrok) {
    Write-Host "ngrok was not found in PATH."
    Write-Host "Install ngrok for Windows: https://ngrok.com/downloads/windows"
    exit 1
}

$configDir = Join-Path $env:LOCALAPPDATA "ngrok"
New-Item -ItemType Directory -Force -Path $configDir | Out-Null

if ($env:NGROK_AUTHTOKEN) {
    Write-Host "Configuring ngrok authtoken..."
    & $ngrok.Source config add-authtoken $env:NGROK_AUTHTOKEN | Out-Null
}

$healthUrl = "http://127.0.0.1:$Port/assessment/v1/health"
Write-Host "Waiting for local API: $healthUrl"
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    try {
        Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 5 | Out-Null
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

try {
    Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 5 | Out-Null
} catch {
    Write-Host "Local API is not ready on port $Port."
    Write-Host "Start the module first with start_hf_api.bat or start.bat."
    exit 1
}

Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "Starting ngrok tunnel for http://127.0.0.1:$Port ..."
Start-Process -WindowStyle Minimized -FilePath $ngrok.Source -ArgumentList @("http", "http://127.0.0.1:$Port") | Out-Null

$reportDir = Join-Path (Get-Location) "training\reports"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$txtPath = Join-Path $reportDir "ngrok_public_url.txt"
$jsonPath = Join-Path $reportDir "ngrok_public_url.json"

$publicUrl = $null
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline -and -not $publicUrl) {
    try {
        $endpoints = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/endpoints" -TimeoutSec 5
        if ($endpoints.endpoints) {
            foreach ($endpoint in $endpoints.endpoints) {
                if ($endpoint.public_url) {
                    $publicUrl = [string]$endpoint.public_url
                    break
                }
                if ($endpoint.url -like "https://*") {
                    $publicUrl = [string]$endpoint.url
                    break
                }
            }
        }
    } catch {
    }

    if (-not $publicUrl) {
        try {
            $tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 5
            if ($tunnels.tunnels) {
                $publicUrl = [string](($tunnels.tunnels | Where-Object { $_.public_url -like "https://*" } | Select-Object -First 1).public_url)
            }
        } catch {
        }
    }

    if (-not $publicUrl) {
        Start-Sleep -Seconds 2
    }
}

if (-not $publicUrl) {
    Write-Host "Failed to obtain a public ngrok URL."
    exit 1
}

$payload = [ordered]@{
    public_base_url = $publicUrl
    health_url      = "$publicUrl/assessment/v1/health"
    questions_url   = "$publicUrl/assessment/v1/questions"
    report_url      = "$publicUrl/assessment/v1/report"
    docs_url        = "$publicUrl/docs"
    openapi_url     = "$publicUrl/openapi.json"
    generated_at    = (Get-Date).ToString("o")
}

Set-Content -LiteralPath $txtPath -Value $publicUrl -Encoding UTF8
($payload | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $jsonPath -Encoding UTF8

Write-Host ""
Write-Host "Public base URL: $publicUrl"
Write-Host "Health:          $($payload.health_url)"
Write-Host "Swagger:         $($payload.docs_url)"
Write-Host "OpenAPI:         $($payload.openapi_url)"
Write-Host ""
Write-Host "Saved URL  to $txtPath"
Write-Host "Saved JSON to $jsonPath"
