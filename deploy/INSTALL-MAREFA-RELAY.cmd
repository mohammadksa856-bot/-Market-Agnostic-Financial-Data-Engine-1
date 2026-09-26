@echo off
setlocal
set "INSTALLER=%~dp0install-windows-tadawul-relay-task.ps1"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%"
if errorlevel 1 (
  echo.
  echo Installation failed. Right-click this file and choose "Run as administrator", then try again.
  pause
  exit /b 1
)
echo.
echo The relay is installed and running. You may close this window.
pause
