@echo off
rem Abre el explorador de consultas BDAutos (no depende del PATH)
cd /d "%~dp0"
set "PY="
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\pythonw.exe" set "PY=%%D\pythonw.exe"
if not defined PY for /d %%D in ("C:\Program Files\Python3*") do if exist "%%D\pythonw.exe" set "PY=%%D\pythonw.exe"
if not defined PY set "PY=pythonw"
start "" "%PY%" "%~dp0app_consultas.py"
