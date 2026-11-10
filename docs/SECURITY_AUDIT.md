# NetScope Application Security & Architecture Audit

**Target:** NetScope – Network Intelligence & Cybersecurity Monitoring Platform  
**Audit Scope:** Backend Services, Network Engine, REST APIs, Database Layer, Docker Reverse Proxy, Frontend Application  
**Auditor:** Antigravity Senior Application Security & Architecture Review  
**Date:** November 10, 2026  
**Status:** **SECURE / HARDENED (LOW RISK PROFILE)**

---

## 1. Threat Model & Security Posture

NetScope is designed as a hybrid network diagnostic tool and cybersecurity auditing platform. Because network utilities interact with external hosts, operating system networking stacks, and command-line system binaries, the attack surface requires stringent defensive controls.

### Core Threat Vectors Assessed
1. **Command Injection & Shell Escaping**: Exploitation of diagnostic utilities (`ping`, `traceroute`, `arp`) via malicious hostnames or IP inputs.
2. **Arbitrary Network Scanning & WAN Abuse**: Unauthorized scanning of external third-party internet targets.
3. **Foreign Private Subnet Reconnaissance**: Probing arbitrary RFC 1918 subnets outside the host's active local interface network.
4. **Subnet Flooding & DoS**: Flooding internal subnets through oversized CIDR sweeps (e.g. `/16` or `/8`).
5. **Gateway ARP Poisoning & MITM Attacks**: Untrusted initial baseline trusting a compromised attacker during ARP spoofing.
6. **DNS Rebinding Attacks (TOCTOU)**: Exploiting hostnames that resolve to both authorized local and unauthorized public targets.
7. **Spreadsheet Formula Injection (CWE-1236)**: Malicious hostnames or device labels triggering formula execution upon CSV export in spreadsheet applications.
8. **Information Exposure via Configuration APIs**: Accidental leakage of internal database URLs or authorized subnet filters.
9. **SQL Injection & Data Tampering**: Manipulation of SQLite database records storing metrics and audit logs.
10. **Cross-Origin & Reverse Proxy Exposure**: Unrestricted cross-origin requests or misconfigured Docker reverse proxies.

---

## 2. Security Controls & Defensive Implementations

### 2.1 Server-Side Network Scope Authorization (Anti-Abuse)
* **Rule**: Client checkboxes (`authorized: true`) are never treated as sufficient proof of authorization.
* **Strict Interface-Bound Subnet Scoping in `discovery.py`**:
  - `get_authorized_networks()` enumerates all active local interface IPv4 addresses and netmasks via `psutil`.
  - Subnet sweeps are strictly restricted to subnets that are physically attached to an active host adapter.
  - Foreign or unrelated RFC 1918 subnets (e.g., `10.254.254.0/24` when the host is on `192.168.1.0/24`) are **strictly rejected with HTTP 403 Forbidden**.
  - Public WAN CIDRs (e.g. `8.8.8.0/24`) are **strictly rejected with HTTP 403 Forbidden**.
  - Oversized subnets (> 256 addresses, e.g. `/16` or `/8`) are **strictly rejected with HTTP 422 Unprocessable Entity**.
* **Strict Port Boundary & Scoping in `ports.py`**:
  - Targets are resolved and validated server-side via `is_target_authorized_scope()`.
  - Authorized targets are strictly restricted to: Loopback (`127.0.0.1`, `::1`), host IP, and active interface subnets.
  - External public WAN targets (e.g. `8.8.8.8`, `google.com`) are **strictly rejected with HTTP 403 Forbidden**.
  - Concurrency limit `MAX_CONCURRENT_ACTIVE_SCANS = 2` prevents socket exhaustion.

### 2.2 Operator-Confirmed Gateway MAC Baseline Protection
* **Defense Against Initial MITM Poisoning**:
  - Auto-trusting the initial observed Gateway MAC is vulnerable if an ARP poisoner is already active when the application starts.
  - In NetScope, the detected gateway MAC is initially marked **`unconfirmed`** (`SEC-001-INFO`).
  - The human operator must explicitly inspect the MAC (verifying it against physical router labels or configuration) and click **"Confirm Baseline"** via `POST /api/security/gateway-baseline/confirm`.
  - Once confirmed, any divergence between the confirmed baseline and active ARP tables immediately triggers a **CRITICAL severity alert (`SEC-001`)** with `confirmed` confidence.
  - Operators can reset or re-baseline at any time via `POST /api/security/gateway-baseline/reset`.
  - Strict input validation requires standard 6-byte hexadecimal format via regex `^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$` and normalizes MACs to uppercase.

### 2.3 Anti-Rebinding DNS Pinning & Scope Validation
* To defeat Time-of-Check to Time-of-Use (TOCTOU) DNS Rebinding attacks, hostnames submitted for port scanning are resolved comprehensively using `socket.getaddrinfo`.
* If **ANY** resolved IP address points to an unauthorized public WAN or foreign IP address, the entire scan request is rejected immediately with HTTP 403 Forbidden.
* Once verified, the validated numeric IP is pinned and passed strictly to the socket connection routines, preventing secondary DNS resolutions from pointing elsewhere.

### 2.4 Spreadsheet Formula Injection Sanitization (CWE-1236)
* Exported reports (devices, security findings, and scan history) pass all fields through `sanitize_csv_field()`.
* If any string value begins with dangerous spreadsheet execution prefixes (`=`, `+`, `-`, `@`, `\t`, `\r`, `\n`), it is prepended with a single apostrophe `'`.
* This ensures that spreadsheet applications treat the values strictly as literal strings rather than executable expressions or DDE formulas.

### 2.5 Information Disclosure Elimination in Settings
* `GET /api/settings` strips sensitive internal operational state (`authorized_networks`, `authorized_targets`, `database_url`, `cors_origins`).
* Only safe public operational parameters (`project_name`, `version`, `environment`, `telemetry_interval`, `max_concurrent_port_scans`) are returned to clients.

### 2.6 Security Finding Persistence & Lifecycle Management
* **Database Models & Endpoints**:
  - Findings are persisted in the SQLite `security_findings` table with unique constraint on `(rule_id, title, status)`.
  - Supports operator workflow:
    - `POST /api/security/audit/run`: Explicitly triggers heuristic evaluation and updates persistent findings.
    - `GET /api/security/findings`: Purely read-only access to active findings in SQLite.
    - `POST /api/security/findings/{id}/acknowledge`: Marks active finding as acknowledged.
    - `POST /api/security/findings/{id}/resolve`: Marks finding as resolved.
    - `GET /api/security/findings/history`: Audits complete chronological finding history with filtering by status and severity.

### 2.7 HTTP Security Headers Middleware
* `X-Content-Type-Options: nosniff`
* `X-Frame-Options: DENY`
* `X-XSS-Protection: 1; mode=block`
* `Referrer-Policy: strict-origin-when-cross-origin`
* `Permissions-Policy: geolocation=(), camera=(), microphone=()`

---

## 3. Heuristic Rules & Confidence Matrix

| Rule ID | Name | Severity | Confidence Logic |
| :--- | :--- | :--- | :--- |
| **SEC-001** | Gateway ARP Baseline Divergence | CRITICAL | Confirmed when active MAC diverges from operator baseline |
| **SEC-002** | IP Address Conflict / Spoofing | HIGH | Confirmed when multiple active MACs report identical IP simultaneously; informational when historical |
| **SEC-003** | Public WAN Interface Exposure | HIGH | Confirmed when host adapter IP is outside RFC 1918 and loopback |
| **SEC-004** | Insecure Legacy Telnet Service | HIGH | Confirmed on port 23 response |
| **SEC-005** | Cleartext FTP Authentication | HIGH | Confirmed on port 21 response |
| **SEC-006** | Unencrypted Web HTTP Exposure | MEDIUM | Potential on open port 80 / 8080 |
| **SEC-007** | SMB File Sharing Exposure | MEDIUM | Potential on open port 445 |
| **SEC-008** | Legacy NetBIOS Exposure | LOW | Potential on open port 139 |
| **SEC-009** | Remote Desktop Protocol Exposure | LOW | Potential on open port 3389 |
