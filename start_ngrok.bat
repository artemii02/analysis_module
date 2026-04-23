@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\start_ngrok.ps1" %*
exit /b %ERRORLEVEL%
