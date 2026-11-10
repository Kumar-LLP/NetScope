<div align="center">

# 🌐 NetScope
### Professional Network Intelligence & Cybersecurity Monitoring Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2%2B-61DAFB.svg?style=for-the-badge&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3%2B-3178C6.svg?style=for-the-badge&logo=typescript)](https://typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4%2B-38B2AC.svg?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2011%20%7C%20Linux-purple.svg?style=for-the-badge)]()

<p align="center">
  <b>NetScope</b> is a professional-grade Network Operations Center (NOC) and cybersecurity telemetry workstation.<br>
  Built with high-frequency async delta sampling, zero-admin safe subnet sweeping, embedded IEEE OUI vendor identification, dynamic React Flow topology graphs, and automated security insight heuristics.
</p>

[✨ Live Features](#-core-functional-modules) •
[🚀 Quick Start](#-quick-start-guide) •
[📐 Architecture](#-system-architecture) •
[🛡️ Security Guardrails](#️-security-guardrails--permissions) •
[📋 QA & Security Reports](#-qa-security--technical-documentation) •
[📊 API Documentation](#-rest--websocket-api-reference)

---

</div>

## 🌟 Key Highlights

- ⚡ **Real Hardware Telemetry**: Direct interface metrics sampled via `psutil` with zero fabricated or mocked live figures.
- 🔍 **Safe Device Discovery**: Subnet host sweeps combining concurrent non-blocking TCP socket probes with OS ARP cache inspection without requiring Administrator privileges on Windows 11.
- 🏢 **Local IEEE OUI Vendor Database**: Offline manufacturer resolution (Apple, Intel, TP-Link, Cisco, Lenovo, Samsung, Dell, etc.) with zero cloud dependency.
- 🕸️ **Interactive Dynamic Topology**: Interactive React Flow network canvas rendering draggable nodes, animated bezier data lines, and node inspection drawers.
- 🧰 **Diagnostic Suite**: Genuine system ICMP Ping, multi-record DNS resolution (A, AAAA, MX, NS, TXT, CNAME), Traceroute hop discovery, and IPv4 CIDR subnetting calculator.
- 🎯 **Controlled Port Scanner**: Multi-threaded TCP connect port scanner with anti-rebinding DNS validation, IP pinning, predefined service profiles (Top 20, Web, Databases, Remote CLI), banner grabbing, and authorization confirmation guardrails.
- 🛡️ **Automated Security Insights**: Heuristic analysis engine with structured confidence ratings detecting gateway MAC changes (ARP poisoning risk), duplicate IP conflicts, and unencrypted management services (Telnet 23, FTP 21).
- 🔒 **Defense-in-Depth & CWE-1236 Protection**: Neutralizes Spreadsheet Formula Injection across CSV exports, validates MAC address structures, and prevents internal configuration disclosure.
- ⚡ **Dynamic Code Splitting**: Frontend route chunking with `React.lazy()` and `<React.Suspense>` for lightning-fast sub-second initial dashboard loads.
- 📡 **Real-Time WebSocket Stream**: Live telemetry pushed every 1.5 seconds over `/ws/network` directly into high-contrast dark NOC charts powered by Recharts.
- 🎓 **Beginner Learning Mode**: Built-in interactive networking guide explaining IP, MAC, DNS, Gateway, Subnet, Ports, Latency, and TCP/UDP.

---

## 📐 System Architecture

```
+-----------------------------------------------------------------------------------+
|                           NETSCOPE FRONTEND (React 18 + Vite)                     |
|                                                                                   |
|   Overview  •  Device Discovery  •  Topology Graph  •  Diagnostics  •  Security   |
+--------------------------+-----------------------------------+--------------------+
                           | REST API (HTTP/JSON)              | WebSocket (/ws/network)
                           v                                   v
+-----------------------------------------------------------------------------------+
|                           NETSCOPE BACKEND (Python FastAPI)                       |
|                                                                                   |
|  * Platform Abstractor (Windows 11 PowerShell/CMD & Linux net-tools)              |
|  * Interface & Routing Resolver (psutil + socket default gateway lookup)          |
|  * Background Traffic Monitor (Asyncio 1Hz delta sampling + WS broadcaster)       |
|  * Safe Device Discovery (ARP cache parser + concurrent TCP/ICMP probe)           |
|  * Port Scanner (Non-blocking asyncio.open_connection + service banner grab)      |
|  * Security Auditor (Gateway spoof check, unencrypted ports, DNS checks)          |
|  * MAC Vendor Resolver (Embedded IEEE OUI database)                               |
+-----------------------------------------------------------------------------------+
                                   |
                                   v
                       +------------------------+
                       | SQLite Database (WAL)  |
                       | netscope.db            |
                       +------------------------+
```

---

## ✨ Core Functional Modules

| Module | Features & Capabilities | Engineering Implementation |
| :--- | :--- | :--- |
| **1. Network Overview** | Real-time health score (0-100), active interface detection, local & public IP, gateway MAC, DNS resolvers, and live download/upload speedometer. | `psutil` + `socket` routing lookup + 1.5s delta throughput calculation. |
| **2. Device Discovery** | Local subnet CIDR scanning, active host identification, MAC address resolution, hardware vendor detection, hostname lookup, CSV & JSON export. | Safe ARP table inspection + concurrent non-blocking socket sweeps (`asyncio.Semaphore`). |
| **3. Interactive Topology** | Visual graph connecting Internet -> DNS -> Gateway -> Local Host -> Discovered LAN stations with live link indicators and click-to-inspect drawer. | React Flow (`@xyflow/react`) dynamic custom nodes with animated bezier edges. |
| **4. Network Diagnostics** | System ICMP Ping with min/avg/max latency, DNS multi-record resolver (A, AAAA, MX, NS, TXT), hop-by-hop Traceroute, IPv4 CIDR calculator. | Tokenized `subprocess.run` (zero shell injection) + `dnspython` + `ipaddress`. |
| **5. Port Diagnostics** | Controlled TCP connect scanner, quick port profiles (Web, DB, Remote, Top 20), service name mapping, banner grabbing, authorization modal. | `asyncio.open_connection` with strict target confirmation and 50-socket concurrency throttle. |
| **6. Traffic Analytics** | Real-time throughput area graphs, per-interface packet counters, link status, and historical latency jitter charts. | Recharts responsive canvas synced via live `/ws/network` WebSocket. |
| **7. Security Insights** | Rule-based security evaluation flagging gateway MAC anomalies (ARP poisoning risk), duplicate IP conflicts, and unencrypted cleartext services. | Built-in `SecurityAuditor` with severity scoring, evidence logging, and remediation playbooks. |

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python**: Version 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Node.js**: Version 18, 20, 22, or 24 with `npm`.
- **Operating System**: Windows 11 (Primary) or Linux / macOS.

### Automated One-Click Startup (Windows 11)
Run the included PowerShell automation script:
```powershell
.\scripts\start-netscope.ps1
```
*This script automatically checks the virtual environment, launches both FastAPI backend and Vite frontend, and opens `http://localhost:5173` in your default browser.*

### Manual Startup

#### 1. Backend Setup:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend Swagger UI will be available at `http://127.0.0.1:8000/docs`.*

#### 2. Frontend Setup:
```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```
*Frontend Operations Center will be available at `http://localhost:5173`.*

---

## 🧪 Testing & Verification

NetScope includes an automated test suite verifying database operations, API validation, CIDR subnetting, port scanning guardrails, and interface enumerators:

```powershell
cd backend
.\.venv\Scripts\pytest.exe tests/ -v
```

### Verified Test Results (36 / 36 Passed - 100%):
- `test_health_endpoint`: **PASSED** (Verifies FastAPI lifespan and SQLite WAL connectivity).
- `test_interfaces_endpoint`: **PASSED** (Verifies physical/virtual NIC enumeration via psutil).
- `test_overview_endpoint`: **PASSED** (Verifies health score calculation and gateway routing).
- `test_ip_info_calculator`: **PASSED** (Verifies IPv4 CIDR binary decomposition and usable host range).
- `test_port_scan_unauthorized_rejected`: **PASSED** (Verifies HTTP 400 when unauthorized).
- `test_port_scan_authorized_loopback`: **PASSED** (Verifies socket connect scanner on 127.0.0.1:8000).
- `test_security_findings_endpoint`: **PASSED** (Verifies security rule evaluation SEC-001 through SEC-009).
- `test_stop_scan_and_progress_endpoints`: **PASSED** (Verifies scan cancellation token and async progress reporting).
- `test_connectivity_benchmark_endpoint`: **PASSED** (Verifies 4-tier network benchmark execution).
- `test_input_validation_command_injection_rejected`: **PASSED** (Verifies shell metacharacter rejection with HTTP 422).
- `test_history_endpoint`: **PASSED** (Verifies persistent SQLite audit trail retrieval).
- `test_metrics_history_endpoint`: **PASSED** (Verifies time-series telemetry storage for Recharts).
- `test_ip_calc_edge_cases`: **PASSED** (Verifies mathematical calculation for /0, /8, /31, /32, and IPv6 /64).
- `test_port_scan_security_guardrails`: **PASSED** (Verifies server-side rejection of external WAN targets and invalid ports).
- `test_discovery_security_scope_and_size_guardrails`: **PASSED** (Verifies server-side rejection of WAN CIDRs and oversized ranges).
- `test_security_headers_present`: **PASSED** (Verifies OWASP headers: X-Content-Type-Options, CSP, X-Frame-Options).
- `test_unrelated_private_network_rejection`: **PASSED** (Verifies server-side rejection of foreign RFC 1918 subnets not attached to host).
- `test_gateway_baseline_lifecycle`: **PASSED** (Verifies operator gateway MAC baseline inspection, confirmation, and reset).
- `test_security_findings_lifecycle`: **PASSED** (Verifies finding acknowledge, resolve, and audit history retrieval).
- `test_device_inventory_patch`: **PASSED** (Verifies custom device classification, custom naming, and trust tagging).
- `test_interface_selection`: **PASSED** (Verifies runtime switching of monitored network interface adapter).
- `test_report_exports`: **PASSED** (Verifies downloadable CSV and JSON exports for devices, security, and history).
- `test_topology_read_only`: **PASSED** (Verifies read-only topology graph generation without triggering unexpected scans).
- `test_gateway_baseline_mac_validation`: **PASSED** (Verifies strict 6-byte hexadecimal regex validation and uppercase MAC normalization).
- `test_csv_formula_injection_sanitization`: **PASSED** (Verifies neutralization of CWE-1236 Spreadsheet Formula Injection via single quote prefix).
- `test_dns_rebinding_rejected`: **PASSED** (Verifies anti-rebinding TOCTOU protection by rejecting dual-stack resolutions containing WAN IPs).
- `test_settings_endpoint_no_information_disclosure`: **PASSED** (Verifies omission of internal database credentials and scanning bounds from `/api/settings`).
- `test_interface_selection_validation`: **PASSED** (Verifies server-side 404/400 validation for nonexistent or down adapters).
- `test_ip_info_binary_host_representation`: **PASSED** (Verifies mathematical accuracy of binary host IP visualization vs network address).
- `test_security_audit_run_endpoint`: **PASSED** (Verifies explicit security audit evaluation with confirmed/potential confidence ratings).
- `test_port_scanner_partial_results_on_timeout`: **PASSED** (Verifies preservation of finished ports when scan times out).
- `test_packet_analysis_endpoints`: **PASSED** (Verifies packet capture status, start, and stop routines).
- `test_anomaly_detection_endpoints`: **PASSED** (Verifies network anomaly queries and threshold tuning).
- `test_learning_mode_topics`: **PASSED** (Verifies educational topics linked to live telemetry keys).
- `test_paginated_device_inventory`: **PASSED** (Verifies server-side pagination, search, and sorting).
- `test_history_cleanup_endpoint`: **PASSED** (Verifies retention cleanup of old metrics and diagnostics).

---

## 📋 Comprehensive Technical Documentation Suite

For complete architectural specifications, API schemas, and security reports:
- [🚀 Installation & Setup Guide](INSTALLATION.md)
- [📖 User & Operations Guide](USER_GUIDE.md)
- [📐 Architecture Blueprint](ARCHITECTURE.md)
- [📡 REST & WebSocket API Specification](API_DOCUMENTATION.md)
- [🛡️ Security Audit & Threat Model](SECURITY_AUDIT.md)
- [⚠️ Known Limitations & Boundaries](KNOWN_LIMITATIONS.md)
- [🗄️ Database Architecture & Migrations](DATABASE.md)
- [🧪 Testing & QA Automation Guide](TESTING.md)
- [📊 Test Execution Log (36/36 Passed)](TEST_RESULTS.md)
- [🤝 Contributing Guidelines](CONTRIBUTING.md)
- [📝 Project Changelog](CHANGELOG.md)

---

## 🛡️ Security Guardrails & Permissions

- **Non-Elevated Privilege Safe**: Does not require Administrator privileges on Windows 11. Scans use standard user-mode TCP sockets and system utilities.
- **Zero Shell Interpolation**: All external invocations (`ping`, `tracert`, `arp`) pass explicit tokenized argument arrays. Shell interpolation (`shell=True`) is strictly prohibited.
- **Strict Target Authorization**: Port diagnostics require explicit user confirmation acknowledging target ownership before execution.
- **Zero Payload Capture**: NetScope measures byte counts and header metadata. It never captures, inspects, or logs plaintext traffic payloads or credentials.

---

## 📄 License
This project is open-source software licensed under the [MIT License](LICENSE).
