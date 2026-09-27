@echo off
cd /d "C:\Users\Royal fleming dsouza\.opencode\jarvis"
:loop
"C:\Users\Royal fleming dsouza\laya-venv\Scripts\python.exe" jarvis_server.py >> server-out.log 2>&1
timeout /t 3 >nul
goto loop
