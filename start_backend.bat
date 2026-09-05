@echo off
echo =================================================================
echo   DhanSetu: The Autonomous 3-Way Bridge for Payment Reconciliation (Backend API)
echo =================================================================
cd /d "%~dp0backend"
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
