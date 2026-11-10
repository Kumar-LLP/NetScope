# 📐 NetScope System Architecture & Engineering Design

This document details the architectural principles, component interactions, and data flows of the **NetScope Network Intelligence & Cybersecurity Monitoring Platform**.

---

## 🏗️ High-Level Architectural Diagram

```
+-----------------------------------------------------------------------------------+
|                        FRONTEND PRESENTATION LAYER (React 18 + Vite)              |
|                                                                                   |
|  * React Single Page Application (SPA) with lazy-loaded route chunking            |
|  * Tailwind CSS cyber-themed dark NOC styling                                     |
|  * Recharts live telemetry visualization & React Flow interactive topology canvas |
|  * WebSocket client handling real-time push events at 1Hz                         |
+--------------------------+-----------------------------------+--------------------+
                           | REST API (HTTP/JSON)              | WebSocket (/ws/network)
                           v                                   v
+-----------------------------------------------------------------------------------+
|                         BACKEND SERVICE LAYER (FastAPI + Asyncio)                 |
|                                                                                   |
|  * app.api.endpoints: REST routes, Pydantic request/response validation           |
|  * app.network.discovery: Safe multi-probe subnet discovery engine                |
|  * app.network.ports: Non-blocking TCP port scanner with anti-rebinding IP pinning|
|  * app.network.interfaces: Cross-platform adapter enumeration (psutil + socket)   |
|  * app.network.diagnostics: Subprocess-isolated ping/traceroute + DNS resolver    |
|  * app.network.packet_analysis: Zero-payload header inspection & protocol stats   |
|  * app.security.auditor: Heuristic security analyzer & gateway MAC verification   |
|  * app.security.anomaly: Rule-based network anomaly detection engine              |
|  * app.network.learning: Interactive educational content provider                 |
+-----------------------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------------------+
|                       DATA PERSISTENCE LAYER (SQLAlchemy + SQLite)                |
|                                                                                   |
|  * SQLite database with Write-Ahead Logging (WAL) mode enabled                    |
|  * SQLAlchemy 2.0 Async ORM engine (`aiosqlite`)                                  |
|  * Alembic migration tracking with deterministic version history                  |
|  * Models: DiscoveredDevice, MetricSnapshot, SecurityFinding, GatewayBaseline,    |
|            PacketLog, NetworkAnomaly                                              |
+-----------------------------------------------------------------------------------+
```

---

## ⚙️ Key Subsystems

### 1. Network Discovery Engine
- **Non-Elevated Safety**: Operates without requiring Administrator or root privileges.
- **Dual-Mechanism Discovery**:
  1. Concurrently issues non-blocking TCP SYN socket connection attempts to low-impact ports (80, 443, 22, 445, 139) with a short timeout.
  2. Queries the operating system's ARP cache via `arp -a` (Windows) or `/proc/net/arp` (Linux) to retrieve MAC addresses of active hosts.
- **Subnet Boundary Enforcement**: Mathematical calculation of network and broadcast boundaries using Python's `ipaddress` module to prevent scanning out-of-scope broadcast domains.

### 2. Controlled Port Scanner
- **Target Verification & Anti-Rebinding**:
  - Resolves target hostnames upfront to IPv4 addresses.
  - Validates that the resolved IP does not rebind to forbidden subnets or arbitrary cloud endpoints.
  - Pins the resolved IP address throughout the scan duration.
- **Distinct State Reporting**: Accurately classifies port responses as `open`, `closed`, `filtered`, `timed_out`, or `error`.
- **Preserved Partial Results**: On deadline expiration or user cancellation, all completed port states are preserved; only unfinished ports are marked `timed_out`.

### 3. Security Auditor & Anomaly Detection
- **Gateway MAC Baseline**:
  - Verifies that any manually confirmed gateway MAC matches the live detected gateway interface.
  - Detects gateway MAC alterations indicative of Layer 2 ARP spoofing attacks.
- **Rule-Based Anomaly Engine**:
  - Evaluates sliding window traffic metrics for abnormal throughput surges, unexpected packet loss spikes, and sudden clusters of new unauthenticated devices.
  - Provides tunable thresholds via `POST /api/security/anomalies/tune`.

### 4. Packet Analysis Module
- **Zero-Payload Policy**: Inspects packet headers (protocol type, source/destination IP, source/destination port, packet length) only. Payload bytes are strictly discarded to guarantee privacy.
- **Cross-Platform Graceful Fallback**: Detects whether raw socket capture permissions are available; falls back smoothly to safe socket heuristics when running in non-elevated user mode.

### 5. Data Persistence & Migrations
- **SQLite WAL Mode**: Configured with `PRAGMA journal_mode=WAL` for concurrent reader/writer operations without lock contention.
- **Alembic Versioning**: All schema alterations are codified in `backend/alembic/versions/` and upgraded using `alembic upgrade head`.
