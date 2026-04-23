@echo off
setlocal

echo [1/3] Starting PostgreSQL...
docker compose up -d postgres
if errorlevel 1 goto :error

echo [2/3] Starting final HF/LoRA analysis module in Docker...
echo First launch may take several minutes while the base model is downloaded from Hugging Face cache.
docker compose up -d --build analysis-module
if errorlevel 1 goto :error

echo [3/3] Waiting for API healthcheck...
:wait_app
docker compose exec -T analysis-module python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/assessment/v1/health').read()" >nul 2>&1
if errorlevel 1 (
  timeout /t 2 /nobreak >nul
  goto wait_app
)

echo.
echo Swagger: http://127.0.0.1:8000/docs
echo Health:  http://127.0.0.1:8000/assessment/v1/health
echo.
goto :end

:error
echo Startup failed.
exit /b 1

:end
endlocal
