@echo off
echo =================================================================
echo   FINANCE OS: Autonomous AI Finance Controller (Backend Server)
echo =================================================================
cd /d "%~dp0backend"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
