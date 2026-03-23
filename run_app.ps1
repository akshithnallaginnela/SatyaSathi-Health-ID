
$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'
$workspaceRoot = Split-Path -Parent $projectRoot
$venvActivate = Join-Path $workspaceRoot '.venv\Scripts\Activate.ps1'

if (-not (Test-Path $backendDir)) {
    throw "Backend folder not found: $backendDir"
}
if (-not (Test-Path $frontendDir)) {
    throw "Frontend folder not found: $frontendDir"
}

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
Start-Process powershell -ArgumentList @('-NoExit', '-Command', $frontendCmd)

Write-Host 'Started backend (http://localhost:8000) and frontend (http://localhost:3000).' -ForegroundColor Green
Write-Host 'Upload dummy report from: backend/uploads/dummy_health_report.png' -ForegroundColor Cyan
    