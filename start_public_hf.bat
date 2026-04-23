@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\start_public_hf.ps1"
exit /b %ERRORLEVEL%
