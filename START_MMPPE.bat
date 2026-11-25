@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title MMPPE Symposium Demo Launcher

where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo [MMPPE ERROR] Windows PowerShell is required to prepare MMPPE.
  echo This Windows installation does not expose powershell.exe.
  echo.
  pause
  exit /b 1
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap\bootstrap.ps1"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo MMPPE setup/startup did not complete. Error code: %RC%
  echo See bootstrap\logs\bootstrap.log for details.
  echo.
  pause
  exit /b %RC%
)
exit /b 0
