#!/usr/bin/env bash
# NetScope - Automated Linux/macOS Startup Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"

echo "=========================================================="
echo "  Starting NetScope Network Intelligence Platform"
echo "=========================================================="

if [ ! -f "$VENV_PYTHON" ]; then
    echo "[!] Setting up Python virtual environment..."
    python3 -m venv "$BACKEND_DIR/.venv"
    "$VENV_PYTHON" -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

echo "[+] Starting FastAPI backend on http://127.0.0.1:8000..."
cd "$BACKEND_DIR"
"$VENV_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "[+] Starting Vite frontend on http://localhost:5173..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "Stopping NetScope background services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "NetScope shutdown complete."
}

trap cleanup EXIT INT TERM

wait
