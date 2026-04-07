@echo off
echo ========================================
echo   Tennis Reservation Server Starter
echo ========================================
echo.

echo [1/3] Activating Python virtual environment...
cd /d "%~dp0backend"
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found. Run setup_venv.ps1 first.
    pause
    exit /b 1
)

echo.
echo [2/3] Starting FastAPI server on port 8000...
echo Press Ctrl+C to stop
echo.
uvicorn server:app --host 0.0.0.0 --port 8000

pause