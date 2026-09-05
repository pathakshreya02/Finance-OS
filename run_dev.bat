@echo off
echo =================================================================
echo   DhanSetu: The Autonomous 3-Way Bridge for Payment Reconciliation
echo   Launching Backend API (Port 8000) & Frontend UI (Port 5173)...
echo =================================================================

start "DhanSetu - Backend API (Port 8000)" cmd /k "%~dp0start_backend.bat"
start "DhanSetu - Frontend Dashboard (Port 5173)" cmd /k "%~dp0start_frontend.bat"

echo.
echo Both services are launching!
echo Backend API Swagger Docs: http://127.0.0.1:8000/docs
echo Frontend Web Dashboard:   http://localhost:5173
echo =================================================================
pause
