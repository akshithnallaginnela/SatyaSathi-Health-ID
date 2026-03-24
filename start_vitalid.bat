@echo off
REM VitalID Application Startup Script (Batch Version)
REM Starts both backend and frontend in separate windows

echo ========================================
echo   Starting VitalID Application
echo ========================================
echo.

REM Check if backend directory exists
if not exist "backend" (
    echo ERROR: backend directory not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "frontend" (
    echo ERROR: frontend directory not found!
    echo Please run this script from the project root directory.
    pause
    exit /b 1
)

echo Starting Backend Server (Port 8000)...
start "VitalID Backend" cmd /k "cd backend && echo === BACKEND SERVER === && echo Starting on http://localhost:8000 && echo. && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak >nul

echo Starting Frontend Server (Port 3000)...
start "VitalID Frontend" cmd /k "cd frontend && echo === FRONTEND SERVER === && echo Starting on http://localhost:3000 && echo. && npm run dev"

echo.
echo ========================================
echo   VitalID Application Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Two command windows have opened:
echo   1. Backend Server (Python/FastAPI)
echo   2. Frontend Server (Vite/React)
echo.
echo To stop servers: Close both command windows or press Ctrl+C in each
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak >nul

REM Open browser
start http://localhost:3000

echo.
echo Browser opened! You can close this window now.
pause
