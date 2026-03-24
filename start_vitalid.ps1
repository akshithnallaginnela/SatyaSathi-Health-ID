# VitalID Application Startup Script
# Starts both backend and frontend in separate windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting VitalID Application" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend directory exists
if (-Not (Test-Path "backend")) {
    Write-Host "ERROR: backend directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Red
    pause
    exit 1
}

# Check if frontend directory exists
if (-Not (Test-Path "frontend")) {
    Write-Host "ERROR: frontend directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Starting Backend Server (Port 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; Write-Host '=== BACKEND SERVER ===' -ForegroundColor Cyan; Write-Host 'Starting on http://localhost:8000' -ForegroundColor Green; Write-Host ''; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "Waiting 3 seconds for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Starting Frontend Server (Port 3000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; Write-Host '=== FRONTEND SERVER ===' -ForegroundColor Cyan; Write-Host 'Starting on http://localhost:3000' -ForegroundColor Green; Write-Host ''; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VitalID Application Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Two PowerShell windows have opened:" -ForegroundColor White
Write-Host "  1. Backend Server (Python/FastAPI)" -ForegroundColor White
Write-Host "  2. Frontend Server (Vite/React)" -ForegroundColor White
Write-Host ""
Write-Host "To stop servers: Close both PowerShell windows or press Ctrl+C in each" -ForegroundColor White
Write-Host ""
Write-Host "Opening browser in 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Open browser
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "Browser opened! You can close this window now." -ForegroundColor Green
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
