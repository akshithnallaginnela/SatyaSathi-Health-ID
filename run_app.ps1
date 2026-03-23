
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'
$workspaceRoot = Split-Path -Parent $projectRoot
$venvActivate = Join-Path $workspaceRoot '.venv\Scripts\Activate.ps1'
$venvPython = Join-Path $workspaceRoot '.venv\Scripts\python.exe'

if (-not (Test-Path $backendDir)) {
    throw "Backend folder not found: $backendDir"
}
if (-not (Test-Path $frontendDir)) {
    throw "Frontend folder not found: $frontendDir"
}

# Kill any existing Python/Node processes
Write-Host "Cleaning up existing processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -match "python|node"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2

# Keep existing database for data persistence
# Only delete if you want a fresh start: Remove-Item "$backendDir\*.db" -Force
Write-Host "Using existing database (data persists)..." -ForegroundColor Yellow

# Clear old incomplete tasks from database
Write-Host "Clearing old tasks from database..." -ForegroundColor Yellow
$clearCmd = @(
    "Set-Location '$backendDir'"
    "& '$venvPython' clear_tasks.py"
) -join '; '
& powershell -Command $clearCmd

$backendCmd = @(
    "Set-Location '$backendDir'" 
    "if (Test-Path '$venvActivate') { . '$venvActivate' }"
    "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
) -join '; '

$frontendCmd = @(
    "Set-Location '$frontendDir'"
    "npm run dev"
) -join '; '

Start-Process powershell -ArgumentList @('-NoExit', '-Command', $backendCmd)
Start-Sleep 2
Start-Process powershell -ArgumentList @('-NoExit', '-Command', $frontendCmd)

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✓ Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "✓ Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nFULL DATA FUSION SYSTEM:" -ForegroundColor Cyan
Write-Host "• Log BP or Sugar -> AI instantly generates tasks + diet + preventive care" -ForegroundColor Cyan
Write-Host "• Upload a blood report -> Additional hemoglobin/platelet insights added" -ForegroundColor Cyan
Write-Host "• ALL data sources (BP, Sugar, BMI, Report, Lifestyle) are considered" -ForegroundColor Cyan
Write-Host "• Health Index score calculated from ALL your health data" -ForegroundColor Cyan
    