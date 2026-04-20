@echo off
setlocal
set "MODEL=qwen2.5:3b"

echo [1/4] Starting PostgreSQL and Ollama...
docker compose up -d postgres ollama
if errorlevel 1 goto :error

echo [2/4] Waiting for Ollama API...
:wait_ollama
docker compose exec -T ollama ollama list >nul 2>&1
if errorlevel 1 (
  timeout /t 2 /nobreak >nul
  goto wait_ollama
)

echo [3/4] Ensuring local model %MODEL% is available...
docker compose exec -T ollama ollama list | findstr /C:"%MODEL%" >nul
if errorlevel 1 (
  echo Downloading model %MODEL%. This may take several minutes on the first run...
  docker compose exec -T ollama ollama pull %MODEL%
  if errorlevel 1 goto :error
) else (
  echo Model %MODEL% is already available.
)

echo [4/4] Starting analysis module...
docker compose up -d --build analysis-module
if errorlevel 1 goto :error

echo Waiting for API healthcheck...
:wait_app
docker compose exec -T analysis-module python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/assessment/v1/health').read()" >nul 2>&1
if errorlevel 1 (
  timeout /t 2 /nobreak >nul
  goto wait_app
)

echo.
echo Demo UI: http://127.0.0.1:8000/demo
echo Health:  http://127.0.0.1:8000/assessment/v1/health
echo.
goto :end

:error
echo Startup failed.
exit /b 1

:end
endlocal
