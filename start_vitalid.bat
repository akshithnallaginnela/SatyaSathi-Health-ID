@echo off
echo ========================================
echo   Starting VitalID Application
echo ========================================
echo.

if not exist "backend" (
    echo ERROR: Run this from the project root folder.
    pause
    exit /b 1
)
if not exist "frontend" (
    echo ERROR: Run this from the project root folder.
    pause
    exit /b 1
)

REM Detect Python — prefer venv, resolve to full path
set PYTHON=python
if exist ".venv\Scripts\python.exe"         set PYTHON=%CD%\.venv\Scripts\python.exe
if exist "backend\.venv\Scripts\python.exe" set PYTHON=%CD%\backend\.venv\Scripts\python.exe

echo Using Python: %PYTHON%
echo.

REM Install asyncpg if missing (required for Supabase/PostgreSQL)
echo Checking asyncpg...
%PYTHON% -c "import asyncpg" 2>nul || %PYTHON% -m pip install asyncpg --quiet
echo asyncpg OK
echo.

echo Starting Backend (port 8000)...
start "VitalID Backend" cmd /k "cd backend && %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo Waiting for backend...
timeout /t 4 /nobreak >nul

echo Starting Frontend (port 3000)...
start "VitalID Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo ========================================
echo.
timeout /t 5 /nobreak >nul
start http://localhost:3000
echo Done. You can close this window.
pause
