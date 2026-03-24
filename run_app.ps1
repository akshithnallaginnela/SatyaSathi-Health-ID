
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'
$workspaceRoot = Split-Path -Parent $projectRoot
if (-not (Test-Path $backendDir)) {
    throw "Backend folder not found: $backendDir"
}
if (-not (Test-Path $frontendDir)) {
    throw "Frontend folder not found: $frontendDir"
}

# Detect best Python to use
$pythonCmd = "python"
if (Test-Path "$backendDir\.venv\Scripts\python.exe") {
    $pythonCmd = "$backendDir\.venv\Scripts\python.exe"
} elseif (Test-Path "$workspaceRoot\.venv\Scripts\python.exe") {
    $pythonCmd = "$workspaceRoot\.venv\Scripts\python.exe"
}

Write-Host "Using Python from: $pythonCmd" -ForegroundColor Cyan

$backendCmd = @(
    "Set-Location '$backendDir'" 
    "& '$pythonCmd' -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
) -join '; '

$frontendCmd = @(
    "Set-Location '$frontendDir'"
    "npm run dev"
) -join '; '

Start-Process powershell -ArgumentList @('-NoExit', '-Command', $backendCmd)
Start-Sleep 3
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
    