# NetScope Implementation & Development Plan

## Roadmap Overview
NetScope development is organized into 6 strictly structured, testable engineering phases. Each phase is verified end-to-end with automated tests and running application checks before advancing.

```
[ Phase 1: Foundation & Scaffold ]
       |
       v
[ Phase 2: Core Network Engine & Telemetry ]
       |
       v
[ Phase 3: Device Discovery & React Flow Topology ]
       |
       v
[ Phase 4: Diagnostic Suite & Port Scanner ]
       |
       v
[ Phase 5: Security Insights & Auditing Engine ]
       |
       v
[ Phase 6: Polish, Verification & Delivery ]
```

---

## Phase 1: Foundation & Environment Setup
- **Objectives**: Initialize backend virtual environment, install production dependencies, set up Vite + React + Tailwind frontend, create database structure, and verify API/Frontend baseline.
- **Backend Deliverables**:
  - Python virtual environment (`.venv`).
  - FastAPI application entry point (`backend/app/main.py`) with CORS, lifespan handlers, and `/api/health`.
  - SQLite database initialized in WAL mode with SQLAlchemy models (`backend/app/models/`).
  - Core configuration via Pydantic Settings (`backend/app/core/config.py`).
- **Frontend Deliverables**:
  - Vite React TypeScript scaffold (`frontend/`).
  - Tailwind CSS with cybersecurity color system and custom fonts (Inter + JetBrains Mono).
  - Main Layout (Sidebar with navigation, Topbar with live status badge, Main content area).
- **Verification Gate**:
  - Backend starts cleanly on `http://127.0.0.1:8000/docs`.
  - Frontend launches on `http://localhost:5173` displaying the layout skeleton and calling `/api/health`.

---

## Phase 2: Core Network Engine & Live Telemetry
- **Objectives**: Implement genuine interface detection, default gateway detection, public/local IP lookup, and real-time bandwidth monitoring with WebSockets.
- **Backend Deliverables**:
  - `backend/app/network/interfaces.py`: Enumerate physical and virtual network interfaces using `psutil` and socket heuristics.
  - `backend/app/network/gateway.py`: Detect default gateway, subnet mask, and DNS servers.
  - `backend/app/monitoring/traffic.py`: Sample throughput at 1Hz, calculate delta upload/download speeds.
  - WebSocket endpoint `/ws/network`: Stream live telemetry to connected UI clients.
- **Frontend Deliverables**:
  - **Overview Dashboard**: Display active interface, local/public IP, gateway, DNS, live speed meters (Upload/Download Mbps), ping latency, and network health score.
  - Live charts powered by Recharts (Throughput area chart).
- **Verification Gate**:
  - Real-time bandwidth numbers reflect real file transfers / internet traffic.
  - Automated tests verifying interface enumeration and gateway detection.

---

## Phase 3: Device Discovery & Interactive Topology
- **Objectives**: Discover local devices without administrative privileges and display them on an interactive React Flow graph.
- **Backend Deliverables**:
  - `backend/app/network/discovery.py`: Safe ARP table parsing + async concurrent ping sweep to discover active LAN hosts.
  - `backend/app/network/vendor.py`: Embedded IEEE OUI vendor database for MAC-to-manufacturer lookup.
  - `backend/app/network/topology.py`: Graph generator returning nodes (Host, Interfaces, Gateway, Devices, DNS, Internet) and edges.
  - Endpoints: `POST /api/devices/discover`, `GET /api/devices`, `GET /api/topology`.
- **Frontend Deliverables**:
  - **Device Discovery Page**: Subnet range selector, Start/Stop scan button, progress bar, export to CSV/JSON, interactive table with vendor icons.
  - **Network Topology Page**: React Flow visualization with custom nodes, animated packet flow, zoom/pan controls, and device detail drawer on click.
- **Verification Gate**:
  - Local router, laptop/desktop, and other connected home/lab devices successfully discovered.
  - Topology correctly connects Host -> Gateway -> Internet with active device satellites.

---

## Phase 4: Network Diagnostic Suite & Port Scanner
- **Objectives**: Build multi-tool diagnostics (Ping, DNS, Traceroute, Subnet Calculator) and controlled TCP Port Scanner.
- **Backend Deliverables**:
  - `backend/app/network/diagnostics.py`:
    - Ping runner with min/max/avg latency and packet loss.
    - DNS resolver for A, AAAA, MX, NS, CNAME, TXT records.
    - Traceroute with hop-by-hop latency and IP discovery.
    - Subnet calculator (CIDR, broadcast, usable host range, wildcard mask).
  - `backend/app/network/ports.py`:
    - Async TCP connect scanner (`asyncio.open_connection`) with configurable timeouts.
    - Common port profiles (Web, Database, Management, Top 20, Custom range).
    - Service name resolution and initial banner grabbing.
- **Frontend Deliverables**:
  - **Diagnostics Page**: Tabbed interface for Ping, DNS, Traceroute, and Subnet Calculator with formatted terminal-style output.
  - **Port Diagnostics Page**: Target input, Authorization Confirmation modal, port profile chips, progress bar, and status table (Open, Closed, Filtered).
- **Verification Gate**:
  - Ping to `1.1.1.1` returns verified latency.
  - DNS lookup for `google.com` resolves verified A and MX records.
  - Localhost port scan correctly flags running FastAPI port (8000) as Open.

---

## Phase 5: Security Insights & Traffic Analytics
- **Objectives**: Automated rule-based network auditing and in-depth interface traffic breakdowns.
- **Backend Deliverables**:
  - `backend/app/security/auditor.py`:
    - Gateway MAC change detection (potential ARP spoofing).
    - Insecure open service detection (Telnet 23, FTP 21, HTTP 80 without SSL).
    - Risky exposed ports on LAN (RDP 3389, SMB 445, MySQL 3306).
    - Suspicious DNS resolver check.
    - Duplicate IP conflict detection.
  - Endpoints: `GET /api/security/findings`, `GET /api/analytics/interfaces`.
- **Frontend Deliverables**:
  - **Security Insights Page**: High/Medium/Low/Info severity cards with impact analysis, technical evidence, and actionable remediation steps.
  - **Traffic Analytics Page**: Per-interface historical bytes sent/received, packet error rates, and cumulative charts.
  - **Beginner Learning Mode**: Slide-out glossary and interactive tooltips explaining core networking terms.
- **Verification Gate**:
  - Running audits triggers findings with accurate severity and remediation tips.

---

## Phase 6: Polish, Testing, Packaging & Delivery
- **Objectives**: End-to-end regression testing, UI polishing, error handling, startup automation scripts, and GitHub portfolio preparation.
- **Deliverables**:
  - Comprehensive Pytest test suite with mocked network fixtures.
  - Frontend build verification (`npm.cmd run build`).
  - Windows PowerShell startup script `start-netscope.ps1` and Linux script `start-netscope.sh`.
  - Comprehensive `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `.env.example`.
  - Complete verification report and demo walk-through.
