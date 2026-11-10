# 🧪 NetScope Testing & Quality Assurance Guide

This document describes the automated testing framework, test execution procedures, and regression verification suite for NetScope.

---

## 🛠️ Test Environment

- **Framework**: `pytest`, `pytest-asyncio`, `httpx` (AsyncClient)
- **Database Isolation**: Unit and integration tests run against a segregated temporary test database (`sqlite+aiosqlite:///data/test_netscope.db`) created and torn down dynamically for each test run.
- **Mocking**: External operating system calls (`subprocess.run`, raw sockets) are safely mocked where network isolation is required.

---

## 🏃 Running Backend Automated Tests

### Run the Complete Test Suite
```bash
cd backend
pytest -v tests/test_api.py
```

### Run with Coverage Reporting
```bash
cd backend
pytest -v --cov=app tests/test_api.py
```

### Run Specific Test Groups
```bash
# Security guardrail tests
pytest -v -k "security or guardrail or baseline" tests/test_api.py

# Network diagnostics tests
pytest -v -k "ping or dns or traceroute or ip_info" tests/test_api.py
```

---

## 🌐 Running Frontend Verification

### TypeScript Type Checking & Production Build
```bash
cd frontend
npm run build
```
This runs `tsc` for complete static type verification followed by `vite build` to verify chunking and asset generation.

### Development Server Smoke Test
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` and verify all 9 primary navigation views load without console errors.
