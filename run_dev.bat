@echo off
echo =================================================================
echo   FINANCE OS: Autonomous AI Finance Controller
echo   Launching Backend API (Port 8000) & Frontend UI (Port 5173)...
echo =================================================================

start "FINANCE OS - Backend API (Port 8000)" cmd /k "%~dp0start_backend.bat"
start "FINANCE OS - Frontend Dashboard (Port 5173)" cmd /k "%~dp0start_frontend.bat"

echo.
echo Both services are launching!
echo Backend API Swagger Docs: http://127.0.0.1:8000/docs
echo Frontend Web Dashboard:   http://localhost:5173
echo =================================================================
pause
