@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0chat-off.ps1" -QuitDocker
echo.
pause
