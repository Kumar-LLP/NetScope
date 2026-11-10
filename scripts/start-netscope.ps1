# NetScope - Automated Windows 11 Startup Script
# Professional Network Intelligence & Cybersecurity Monitoring Platform

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting NetScope Network Intelligence Platform" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

# 1. Port Conflict Detection & Notice
function Test-PortInUse($Port) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        return ($conns -ne $null)
    } catch {
        return $false
    }
}

if (Test-PortInUse 8000) {
    Write-Host "[!] Warning: Port 8000 is already in use by another process. Attempting cleanup or launch..." -ForegroundColor Yellow
}
if (Test-PortInUse 5173) {
    Write-Host "[!] Warning: Port 5173 is already in use by another process." -ForegroundColor Yellow
}

# 2. Check Python Virtual Environment
if (-not (Test-Path $VenvPython)) {
    Write-Host "[+] Virtual environment not detected. Creating .venv in backend..." -ForegroundColor Yellow
    python -m venv (Join-Path $BackendDir ".venv")
    & $VenvPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

# 3. Start Backend Process (Bound to 127.0.0.1 loopback for local security)
Write-Host "[+] Launching FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath $VenvPython -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000" -WorkingDirectory $BackendDir -PassThru -NoNewWindow

# 4. Wait for Backend Healthcheck
Write-Host "[+] Polling backend healthcheck endpoint (http://127.0.0.1:8000/api/health)..." -ForegroundColor Cyan
$BackendReady = $false
$Retries = 0
while (-not $BackendReady -and $Retries -lt 20) {
    Start-Sleep -Milliseconds 500
    $Retries++
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($res -and ($res.status -eq "healthy" -or $res.status -eq "degraded")) {
            $BackendReady = $true
            Write-Host "[+] Backend is online and database connected! ($($res.platform), version $($res.version))" -ForegroundColor Green
        }
    } catch {
        # continue waiting
    }
}

if (-not $BackendReady) {
    Write-Host "[!] Backend took longer than expected to start. Proceeding anyway..." -ForegroundColor Yellow
}

# 5. Start Frontend Process
Write-Host "[+] Launching Vite Frontend on http://localhost:5173..." -ForegroundColor Green
$FrontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory $FrontendDir -PassThru -NoNewWindow

Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " NetScope is running! Press [Ctrl+C] to stop all services." -ForegroundColor Cyan
Write-Host " Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host " Backend:   http://127.0.0.1:8000/api" -ForegroundColor White
Write-Host " Docs:      http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan

try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host "`nStopping NetScope background services..." -ForegroundColor Yellow
    if ($BackendProcess -and -not $BackendProcess.HasExited) {
        Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($FrontendProcess -and -not $FrontendProcess.HasExited) {
        Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "NetScope shutdown complete." -ForegroundColor Green
}
