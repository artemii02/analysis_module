@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\stop_ngrok.ps1"
exit /b %ERRORLEVEL%
