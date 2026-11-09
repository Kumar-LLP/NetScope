# NetScope - Automated Windows 11 Startup Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting NetScope Network Intelligence Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

# 1. Check Python Venv
if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Virtual environment not detected. Creating .venv..." -ForegroundColor Yellow
    python -m venv (Join-Path $BackendDir ".venv")
    & $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

# 2. Start Backend Process
Write-Host "[+] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath $VenvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $BackendDir -PassThru -NoNewWindow

# 3. Start Frontend Process
Write-Host "[+] Launching Vite Frontend on http://localhost:5173..." -ForegroundColor Green
$FrontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -PassThru -NoNewWindow

Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " NetScope is running! Press [Ctrl+C] to stop all services." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping NetScope background services..." -ForegroundColor Yellow
    Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "NetScope shutdown complete." -ForegroundColor Green
}
