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
|  * app.network.packet_analysis: Scapy packet capture with Npcap/raw socket check   |
|  * app.security.auditor: Heuristic security analyzer & gateway MAC verification   |
|  * app.security.anomaly: Rule-based network anomaly engine with dynamic baseline   |
|  * app.intelligence.engine: Central correlation engine across all network domains  |
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

### 3. Central Network Intelligence & Anomaly Management
- **Central Intelligence Engine (`app.intelligence.engine`)**:
  - Ingests normalized evidence across discovery sweeps, device observations, traffic metrics, packet statistics, port diagnostics, and DNS queries.
  - Implements explainable correlation rules (`NETINT-IPCONF-01`, `NETINT-DHCP-02`, `NETINT-GW-03`, `NETINT-PORT-04`, `NETINT-LOSS-07`) mapping evidence to explicit confidence ratings.
  - Generates `IntelligenceEventModel` entries with actionable remediation advice and investigation status tracking.
- **Persistent Device Observation Model**:
  - Records granular host activity snapshots in `device_observations`.
  - Distinguishes legitimate DHCP renewal reassignments from simultaneous IP conflict anomalies.
- **Rule-Based Anomaly Engine**:
  - Derives dynamic sliding-window traffic baselines from stored database metrics.
  - Evaluates traffic throughput spikes (in explicit KB/s, MB/s, and Mbps), packet loss surges, and latency surges.
  - Provides lifecycle endpoints (`acknowledge`, `resolve`) and persistent threshold tuning.

### 4. Packet Analysis Module & Driver Detection
- **Zero-Payload Policy**: Inspects packet headers (protocol type, source/destination IP, source/destination port, packet length) only. Payload bytes are strictly discarded to guarantee privacy.
- **Honest Driver Capability Inspection**:
  - Windows: Explicitly inspects for Npcap in WinPcap API-compatible mode (`wpcap.dll`).
  - Linux: Explicitly tests `CAP_NET_RAW` / root socket creation.
  - When drivers are not installed, NetScope informs the operator and operates safely in zero-admin mode without crashing or hanging.
- **Continuous Operation & Thread Safety**: Executes continuous capture loop in dedicated background thread with atomic locks and DB session tracking.

### 5. WebSocket Telemetry & Client Queue Isolation
- **Per-Client Bounded Queues**: `TrafficMonitor` maintains independent `asyncio.Queue(maxsize=10)` queues for each connected WebSocket client.
- **Lag Prevention**: Slow or unresponsive frontend clients automatically drop older frames without delaying other subscribers or blocking the backend broadcaster.

### 6. Data Persistence & Authoritative Alembic Migrations
- **SQLite WAL Mode**: Configured with `PRAGMA journal_mode=WAL` for concurrent reader/writer operations without lock contention.
- **Alembic Authoritative Versioning**: Database initialization is strictly managed via Alembic migrations (`577e827427ad` base + `2ca1594d866b` intelligence extensions), executed automatically on application startup.
- **Granular Data Retention**: Multi-tier retention policies allow independent cleanup cycles for metrics (7d), diagnostics (14d), discovery scans (30d), and security audit records (90d).
