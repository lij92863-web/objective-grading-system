@echo off
cd /d "%~dp0"
start "客观题批改助手" /min python web_app.py 8765
timeout /t 1 >nul
start http://127.0.0.1:8765/
