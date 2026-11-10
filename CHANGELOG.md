# 📝 NetScope Changelog

All notable changes to the NetScope platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] - 2026-11-10

### 🚀 Added
- **Central Network Intelligence Correlation Engine**:
  - Implemented multi-domain correlation engine in `backend/app/intelligence/engine.py` consuming evidence from ARP discovery, traffic throughput, packet analysis, port diagnostics, DNS responses, and gateway state.
  - Generates strictly evidence-backed, explainable security events (`IntelligenceEventModel`) with categories, severity, confidence, affected hosts, explanations, and remediation recommendations.
  - Endpoints: `POST /api/intelligence/evaluate`, `GET /api/intelligence/events`, and `POST /api/intelligence/events/{event_id}/status`.
- **Persistent Device Observation & DHCP Tracking Model**:
  - Introduced `DeviceObservationModel` tracking device IP, MAC, interface, timestamp, discovery source, response status, and confidence.
  - Maintains complete observation history enabling IP conflict detection and seamless DHCP lease reassignment tracking.
- **Enterprise Anomaly Management Lifecycle**:
  - Separated evaluation (`POST /api/security/anomalies/evaluate`) from listing (`GET /api/security/anomalies` active vs `GET /api/security/anomalies/history`).
  - Added operational lifecycle management: `POST /api/security/anomalies/{id}/acknowledge` and `POST /api/security/anomalies/{id}/resolve` with optional audit notes.
  - Sliding-window baseline derivation from database metrics, alert suppression for duplicate occurrences, and persistent threshold tuning via `application_settings`.
- **Packet Capture Driver Inspection & Session History**:
  - Genuine driver validation detecting Npcap on Windows (WinPcap API) and raw socket privileges on Linux; graceful degradation to zero-admin layer-3 mode with user-friendly notices.
  - Continuous loop packet capture with thread-safe atomic counters and graceful thread termination.
  - Persistent capture session tracking in `packet_capture_sessions` table with duration, protocol distributions, and bytes.
  - UI displays live driver capability notices and searchable session history table.
- **Granular Multi-Tier Data Retention Cleanup**:
  - Enhanced `POST /api/history/cleanup` supporting distinct retention periods: time-series metrics (7 days default), ping/DNS diagnostics (14 days), discovery scans and observations (30 days), and resolved security records (90 days).
- **Client-Isolated High-Performance WebSocket Streaming**:
  - Isolated WebSocket client queues bounded to `maxsize=10` with dedicated async sender tasks in `TrafficMonitor`, guaranteeing slow UI clients never block or lag other subscribers.
- **Expanded Regression Test Suite (47 Automated Tests - 100% Pass Rate)**:
  - Added programmatic Alembic upgrade test verifying 15 tables from an empty database.
  - Added regression tests for packet capture driver checks, port scan status persistence, offline device reconciliation, observation model DHCP tracking, anomaly lifecycle, central intelligence evaluation, and queue isolation.

### 🛡️ Security Hardened
- **Authoritative Alembic Migrations**:
  - Replaced empty migration with a real, idempotent initial base migration (`577e827427ad`) and incremental migration (`2ca1594d866b`).
  - Programmatic migrations executed on application startup via `run_alembic_migrations()`, removing conflicting runtime table creation.
- **Port Scan History Status Integrity**:
  - Accurately persists actual scan outcomes (`completed`, `partial`, `timed_out`) into `network_scans.status`.
- **Security Auditor & Heuristic Accuracy**:
  - Corrected Rule SEC-001 (Gateway MAC divergence) confidence to `high`, explicitly documenting the distinction between MAC divergence observation and underlying cause (ARP poisoning vs legitimate AP roaming/router replacement).
  - Corrected Rule SEC-003 (DNS Transport Security): Resolver IP address (e.g., 1.1.1.1) is no longer claimed as proof of transport encryption; explicitly warns of standard OS UDP port 53 plaintext transport exposure.
- **Throughput Unit Mathematical Precision**:
  - Standardized all bandwidth formulas across anomaly detection: explicit calculations for Kilobytes per second (`KB/s`), Megabytes per second (`MB/s`), and Megabits per second (`Mbps`).
- **Discovery Offline Reconciliation**:
  - Enforced that existing inventory hosts are only reconciled offline if a discovery sweep completes cleanly with status `completed`, preventing aborted or partial scans from causing false offline alerts.
- **Database Persistence Error Propagation**:
  - Removed swallowed exceptions across security auditing, anomaly detection, and packet capture persistence, raising explicit HTTP 500 errors on database failure.

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
