# NetScope System Architecture Document

## 1. System Vision & Purpose
**NetScope** is a professional-grade Network Intelligence & Cybersecurity Monitoring platform engineered for Windows 11 and Linux environments. It bridges the gap between raw command-line diagnostic utilities and complex enterprise SIEM/NOC tools by providing:
- Real-time network interface metrics and bandwidth tracking.
- Non-elevated, safe local device discovery with ARP resolution and MAC OUI vendor mapping.
- Interactive, dynamic network topology graph powered by React Flow.
- Multi-protocol diagnostics (ICMP Ping, DNS multi-record resolver, Traceroute hop visualizer, Subnetting/CIDR calculator).
- Controlled TCP connect port scanner with service identification and security guardrails.
- Rule-based Security Insights engine flagging configuration anomalies, risky exposed services, and rogue gateway changes.
- WebSocket-streamed live telemetry directly into a sleek, high-contrast cybersecurity operations center dashboard.

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                           NETSCOPE FRONTEND (React 18 + Vite)                     |
|                                                                                   |
|  +--------------------+  +----------------------+  +---------------------------+  |
|  | Modern NOC Navbar  |  |  Interactive Sidebar |  |  Security & Health Alerts |  |
|  +--------------------+  +----------------------+  +---------------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Visual Modules:                                                             |  |
|  | - Network Overview (Speed, Latency, Interfaces, Gateway, Health Score)       |  |
|  | - Device Discovery (LAN sweep, ARP table, Vendor OUI, Hostname, Export)     |  |
|  | - Network Topology (React Flow Dynamic Graph with live connection badges)   |  |
|  | - Diagnostics Suite (Ping, DNS Records, Traceroute Hops, Subnet Calc)       |  |
|  | - Port Diagnostics (Target Auth Guardrail, Port Selector, Banner Grabbing)  |  |
|  | - Traffic Analytics (Recharts Live Bandwidth Throughput, Interface Counters)|  |
|  | - Security Insights (Risk Scorer, Severity Badges, Remediation Playbooks)   |  |
|  | - Learning Center (Interactive Network Protocol & Concept Glossary)         |  |
|  +-----------------------------------------------------------------------------+  |
+--------------------------+-----------------------------------+--------------------+
                           | REST API (HTTP/JSON)              | WebSocket (/ws/network)
                           v                                   v
+-----------------------------------------------------------------------------------+
|                           NETSCOPE BACKEND (Python FastAPI)                       |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | API Router Layer (/api/network, /api/devices, /api/diagnostics, /api/ws)    |  |
|  +-----------------------------------------------------------------------------+  |
|  | Input Validation & Security Guardrails (Pydantic V2, IP/CIDR/Port Sanitizer)|  |
|  +-----------------------------------------------------------------------------+  |
|  | Network Engine Core:                                                        |  |
|  |  * Platform Abstractor (Windows 11 PowerShell/CMD & Linux net-tools)        |  |
|  |  * Interface & Routing Resolver (psutil + socket default gateway lookup)    |  |
|  |  * Background Traffic Monitor (Asyncio 1Hz delta sampling + WS broadcaster) |  |
|  |  * Safe Device Discovery (ARP cache parser + concurrent TCP/ICMP probe)     |  |
|  |  * Port Scanner (Non-blocking asyncio.open_connection + service mapping)    |  |
|  |  * Diagnostic Runners (Safe subprocess ping/tracert without shell=True)     |  |
|  |  * Security Auditor (Gateway spoof check, unencrypted ports, DNS checks)    |  |
|  |  * MAC Vendor Resolver (Embedded IEEE OUI database)                         |  |
|  +-----------------------------------------------------------------------------+  |
|  | Persistence & Migration Layer (SQLAlchemy 2.0 Async + SQLite WAL + Alembic) |  |
+-----------------------------------------------------------------------------------+
                                   |
                                   v
                       +------------------------+
                       | SQLite Database (WAL)  |
                       | netscope.db            |
                       +------------------------+
```

---

## 3. Core Subsystems

### 3.1 Network Engine & Platform Abstraction
Different operating systems handle networking commands and permission levels differently. NetScope provides a unified `PlatformNetworkAdapter` interface:
- **Windows 11 Primary**:
  - Interface enumerator uses `psutil.net_if_addrs()` and `psutil.net_if_stats()`.
  - Default gateway discovery uses `netifaces` logic or socket routing check `socket.connect(('8.8.8.8', 80))` combined with `Get-NetRoute` / `route print`.
  - ARP resolution parses `arp -a` safely without `shell=True`.
  - Ping executes `ping.exe -n {count} -w {timeout_ms} {target}` with regex metric parsing.
  - Traceroute executes `tracert.exe -d -h {max_hops} -w {timeout_ms} {target}`.
- **Linux/POSIX Fallback**:
  - Parses `/proc/net/arp` and `ip route show default`.
  - Executes `ping -c {count} -W {timeout_s} {target}` and `traceroute -n -m {max_hops} {target}`.

### 3.2 Non-Elevated Privilege Security Model
Standard network operations in NetScope are intentionally engineered to run **without Administrator privileges**:
1. Port scanning uses standard user-mode TCP connect sockets (`asyncio.open_connection`). This avoids raw packet crafting (SYN scans) which triggers Windows firewall or requires WinPcap/Npcap.
2. Device discovery combines reading the active ARP table with non-privileged ICMP ping and standard socket connections to common ports (80, 443, 53) across the subnet to populate the ARP cache naturally.
3. Bandwidth monitoring reads standard performance counters via `psutil`.

### 3.3 Background Telemetry & WebSocket Engine
- A dedicated background `asyncio` task runs in the FastAPI lifespan.
- Every `1.5` seconds, it calculates:
  - Download rate (KB/s and MB/s)
  - Upload rate (KB/s and MB/s)
  - Latency to primary DNS / Gateway (ms)
  - Packet drop counter
  - Active connection state
- Updates are pushed over `/ws/network` to all active WebSocket clients.

### 3.4 Data Persistence (SQLite with WAL mode)
- Stored in `backend/data/netscope.db`.
- SQLite configured with `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` for concurrent reader/writer performance without database lock issues.
- Normalized schema maintaining scan history, device inventory, bandwidth telemetry samples, diagnostic audits, and security findings.

---

## 4. Frontend Component & State Architecture
- **State Management**: React custom hooks + Context API for WebSocket streaming, active device inventory, and active scan state.
- **Topology Engine**: React Flow (`@xyflow/react`) featuring custom stylized SVG nodes with status pulses, animated bezier curves for data flow, and interactive node inspector drawer.
- **Analytics Engine**: Recharts responsive area and bar charts with custom tooltips formatted in human-readable network units (bps, Kbps, Mbps, ms).
- **Design System**: Tailored dark-mode cybersecurity theme (Obsidian background `#0B0F17`, Surface `#111827`, Border `#1E293B`, Neon accents `#38BDF8` & `#10B981`).
