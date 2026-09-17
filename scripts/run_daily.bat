@echo off
setlocal
cd /d "%~dp0\.."
if not exist "logs" mkdir logs
".venv\Scripts\python.exe" run_daily.py >> "logs\daily.log" 2>&1
exit /b %ERRORLEVEL%
