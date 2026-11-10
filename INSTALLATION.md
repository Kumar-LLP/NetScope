# 🚀 NetScope Installation & Deployment Guide

This guide provides instructions for setting up, configuring, and operating **NetScope** on **Windows 11** (primary platform) and **Linux**.

---

## 📋 System Prerequisites

### Windows 11 (Recommended Environment)
- **OS**: Windows 11 (or Windows 10 build 19041+)
- **Python**: 3.10, 3.11, 3.12, 3.13, or 3.14 (ensure `python` is added to system PATH)
- **Node.js**: v18.0.0+ or v20.0.0+ (with npm)
- **Git**: Git for Windows
- **Privileges**: Standard user privileges (NetScope is engineered to operate without requiring Administrator rights)

### Linux (Ubuntu 22.04 LTS / Debian 12)
- **OS**: Linux kernel 5.15+
- **Python**: Python 3.10+ (`python3-venv`, `python3-pip`)
- **Node.js**: v18+ or v20+
- **System Utilities**: `iproute2`, `net-tools`, `iputils-ping`

---

## 🛠️ Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Kumar-LLP/NetScope.git
cd NetScope
```

### 2. Backend Setup

#### On Windows (PowerShell / Command Prompt):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# On CMD: .venv\Scripts\activate.bat

pip install --upgrade pip
pip install -r requirements.txt
```

#### Run Database Migrations (Alembic):
```powershell
alembic upgrade head
```

#### Start the Backend Server:
```powershell
python run.py
# NetScope backend will listen on http://127.0.0.1:8000
```

---

### 3. Frontend Setup

#### In a new terminal window:
```powershell
cd frontend
npm install
npm run build
npm run dev
# NetScope frontend will launch on http://localhost:5173
```

---

## 🐳 Docker Deployment

NetScope includes production-ready Docker and Docker Compose configurations:

```bash
docker compose up --build -d
```
This spins up:
- **Backend API**: Port 8000
- **Frontend Nginx Reverse Proxy**: Port 80 / 5173

---

## ⚙️ Environment Configuration

Backend configuration is controlled via environment variables or a `.env` file in `backend/`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `NETSCOPE_HOST` | `127.0.0.1` | Local host interface binding (security enforced) |
| `NETSCOPE_PORT` | `8000` | HTTP and WebSocket listener port |
| `NETSCOPE_ENV` | `development` | Environment mode (`development` or `production`) |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Explicit allowed web origins |
| `RATE_LIMIT_PER_MINUTE` | `120` | API request rate limit per client IP |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/netscope.db` | SQLAlchemy Async connection string |
| `MAX_DISCOVERY_WORKERS` | `32` | Concurrency limit for subnet discovery probes |
| `MAX_PORT_SCAN_WORKERS` | `50` | Concurrency limit for TCP socket port scans |

---

## 🧪 Verifying Installation

To verify that your installation is operating properly:

1. **API Health Check**:
   ```bash
   curl http://127.0.0.1:8000/api/health
   # Response: {"status":"healthy","version":"1.3.0","platform":"Windows-11-...","db_connected":true}
   ```
2. **Automated Test Suite**:
   ```bash
   cd backend
   pytest -v tests/test_api.py
   # 36 tests should pass cleanly
   ```
3. **Frontend Compilation**:
   ```bash
   cd frontend
   npm run build
   # Should complete with zero errors
   ```
