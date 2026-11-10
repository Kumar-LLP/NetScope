# 📝 NetScope Changelog

All notable changes to the NetScope platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.3.0] - 2026-11-10

### 🚀 Added
- **Packet & Protocol Inspection Engine**:
  - Non-invasive network layer telemetry with opt-in capture.
  - Zero payload capture policy guaranteeing user privacy.
  - Real-time protocol distribution breakdown (TCP, UDP, ICMP, DNS, Other) and recent flows stream.
  - Graceful fallback for non-elevated user mode on Windows 11.
- **Rule-Based Network Anomaly Detection**:
  - Heuristic detection for sudden bandwidth spikes, gateway MAC alterations, packet loss surges, and unknown device bursts.
  - Tunable detection thresholds endpoint (`POST /api/security/anomalies/tune`).
- **Interactive Beginner Learning Center**:
  - Structured educational modules covering IP addressing, MAC/OUI, default gateway, DNS, subnets, latency, and TCP ports.
  - Integrated into slide-out drawer linked to live NetScope telemetry metrics.
- **Server-Side Device Inventory Pagination**:
  - `GET /api/devices/paginated` supporting server-side filtering by search query, status, vendor, category, and sorting.
- **Automated Database History Retention Pruning**:
  - `POST /api/history/cleanup` endpoint to prune metrics and diagnostics older than configurable retention threshold.
- **Extended Test Suite**:
  - Expanded automated test suite to 36 test cases with 100% pass rate.

### 🛡️ Security Hardened
- **Gateway Baseline Correspondence Enforcement**:
  - Enforced strict correspondence between supplied baseline MAC and detected gateway MAC, preventing arbitrary baseline confirmation.
  - Added explicit HTTP 503 and 502 handling for gateway reachability failures.
- **Port Scanner Partial Results Preservation**:
  - Preserved genuine completed port states (`open`, `closed`) upon timeout expiration, eliminating synthetic overwriting.
- **Subnet Mathematical Boundary Calculation**:
  - Replaced naive string `.endswith(".255")` filtering with exact mathematical network/broadcast address evaluation.
- **Database Transaction Exception Handling**:
  - Eliminated silent transaction rollback masking, returning explicit HTTP 500 on database write failure.
- **Authoritative Alembic Migrations**:
  - Bound Alembic configuration to absolute database paths, enabling headless migrations from any working directory.
  - Eliminated silent exception suppressing in database startup migrations.

---

## [1.2.0] - 2026-11-09

### 🚀 Added
- Dynamic code splitting using `React.lazy()` and `Suspense` for sub-second dashboard rendering.
- Offline IEEE OUI MAC vendor database with thousands of manufacturer prefixes.
- Interactive React Flow topology graph with custom node types and draggable layout.
- Real-time WebSocket streaming at 1Hz (`/ws/network`).

### 🛡️ Security Hardened
- Implemented Spreadsheet Formula Injection (CWE-1236) sanitization across CSV exports.
- Enforced strict localhost binding (`127.0.0.1`) and origin CORS policy.
- Added DNS rebinding protection and target IP pinning in TCP port scanner.

---

## [1.0.0] - 2026-11-08

### 🚀 Initial Release
- Hardware bandwidth telemetry and ICMP latency monitoring via `psutil`.
- Non-elevated subnet device discovery via ARP cache and TCP socket probes.
- Diagnostic ping, DNS resolver, traceroute, and IPv4 subnet calculator.
- SQLite WAL mode persistence with SQLAlchemy ORM.
