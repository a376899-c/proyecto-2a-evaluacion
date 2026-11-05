@echo off
set "PATH=%SystemRoot%\System32;%SystemRoot%;%SystemRoot%\System32\WindowsPowerShell\v1.0;%LOCALAPPDATA%\Microsoft\WindowsApps;%PATH%"
"%SystemRoot%\System32\chcp.com" 65001 >nul
echo Instalando lo que falte y corriendo el proyecto BDAutos...
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar_y_correr.ps1"
echo.
pause
