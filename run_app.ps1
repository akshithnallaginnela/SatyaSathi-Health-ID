
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

# Delete old SQLite database files to force fresh migration
Write-Host "Resetting database for clean migration..." -ForegroundColor Yellow
Get-ChildItem -Path "$backendDir\*.db" | Remove-Item -Force -ErrorAction SilentlyContinue

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
Write-Host "`nNEW MODEL-DRIVEN SYSTEM:" -ForegroundColor Cyan
Write-Host "• Upload a blood report in My ID tab" -ForegroundColor Cyan
Write-Host "• Dashboard will show ONLY model-predicted tasks" -ForegroundColor Cyan
Write-Host "• Tasks = iron, sugar, exercise recommendations" -ForegroundColor Cyan
Write-Host "• No hardcoded 'Log Morning BP' tasks" -ForegroundColor Cyan
    