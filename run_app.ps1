
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

# Ensure asyncpg is installed (required for PostgreSQL/Supabase)
Write-Host "Checking asyncpg..." -ForegroundColor Yellow
& $pythonCmd -m pip install asyncpg --quiet

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
