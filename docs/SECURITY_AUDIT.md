# NetScope Application Security & Architecture Audit

**Target:** NetScope – Network Intelligence & Cybersecurity Monitoring Platform  
**Audit Scope:** Backend Services, Network Engine, REST APIs, Database Layer, Docker Reverse Proxy, Frontend Application  
**Auditor:** Antigravity Senior Application Security & Architecture Review  
**Date:** November 9, 2026  
**Status:** **SECURE / HARDENED (LOW RISK PROFILE)**

---

## 1. Threat Model & Security Posture

NetScope is designed as a hybrid network diagnostic tool and cybersecurity auditing platform. Because network utilities interact with external hosts, operating system networking stacks, and command-line system binaries, the attack surface requires stringent defensive controls.

### Core Threat Vectors Assessed
1. **Command Injection & Shell Escaping**: Exploitation of diagnostic utilities (`ping`, `traceroute`, `arp`) via malicious hostnames or IP inputs.
2. **Arbitrary Network Scanning & WAN Abuse**: Unauthorized scanning of external third-party internet targets.
3. **Subnet Flooding & DoS**: Flooding internal subnets through oversized CIDR sweeps (e.g. `/16` or `/8`).
4. **Privilege Escalation**: Unauthorized requirement or misuse of Administrator / root system capabilities.
5. **SQL Injection & Data Tampering**: Manipulation of SQLite database records storing metrics and audit logs.
6. **Cross-Origin & Reverse Proxy Exposure**: Unrestricted cross-origin requests or misconfigured Docker reverse proxies.
7. **Credential & Secret Leakage**: Accidental inclusion of API keys, private certificates, or internal tokens.

---

## 2. Security Controls & Defensive Implementations

### 2.1 Server-Side Network Scope Authorization (Anti-Abuse)
* **Rule**: Client checkboxes (`authorized: true`) are never treated as sufficient proof of authorization.
* **Implementation in `ports.py`**:
  - Targets are resolved and validated server-side via `is_target_authorized_scope()`.
  - Authorized targets are strictly restricted to: Loopback (`127.0.0.1`, `::1`), local adapter IPs, and private subnets (RFC 1918 / link-local).
  - External public WAN targets (e.g. `8.8.8.8`, `google.com`) are **strictly rejected with HTTP 403 Forbidden**.
* **Implementation in `discovery.py`**:
  - Subnet sweeps are strictly restricted to private RFC 1918 ranges or active local interface subnets via `is_network_authorized()`.
  - Public WAN CIDRs (e.g. `8.8.8.0/24`) are **strictly rejected with HTTP 403 Forbidden**.
  - Oversized subnets (> 256 addresses, e.g. `/16` or `/8`) are **strictly rejected with HTTP 422 Unprocessable Entity**.

### 2.2 Strict Port Boundary & Input Validation
* **Implementation in `schemas/network.py`**:
  - `@field_validator("ports")` strictly validates that every requested port number is an integer in the range `1 <= port <= 65535`. Port 0, negative values, and values > 65535 are rejected with HTTP 422.
  - `@field_validator("target")` strips input and rejects control characters and shell metacharacters.

### 2.3 Zero-Shell Execution Architecture
* **Rule**: The parameter `shell=True` is strictly prohibited throughout the codebase.
* **Implementation**: All system process invocations (`subprocess.run` or `asyncio.create_subprocess_exec`) utilize strictly tokenized argument vectors:
  ```python
  cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), target]
  proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
  ```
  Even if shell metacharacters (`&`, `;`, `|`, `` ` ``, `$`) are passed into `target`, the OS treats them as literal command arguments.

### 2.4 Mathematical IP Calculator (Zero Memory Exhaustion)
* **Implementation in `diagnostics.py`**:
  - Calculates host counts, usable ranges, and broadcast addresses purely mathematically without generating lists of addresses in memory.
  - Fully supports `/0`, `/8`, `/16`, `/24`, `/31` (RFC 3021 point-to-point 2-host links), `/32` (single host), and IPv6 prefixes (`/64`, `/128`).

### 2.5 Security Auditor Enhancements & Baseline Persistence
* **Gateway Baseline MAC**: Stored persistently in SQLite `application_settings` table (key: `gateway_baseline_mac`). If the gateway MAC changes compared to the persistent baseline, `SEC-001` (Potential ARP Poisoning) is triggered.
* **Duplicate IP Conflicts**: Tracks IP-to-MAC associations across raw ARP tables and discovery sweeps; triggers `SEC-002` if conflicting hardware addresses claim the same IP.
* **Verified Protocols**: Inspects banners to distinguish cleartext protocols from secured services:
  - Telnet (23): Flagged as critical/high with captured banner.
  - Plain FTP (21): Flagged if TLS/SSL is not enforced.
  - Gateway HTTP (80): Evaluates if HTTP safely redirects to HTTPS (`Location: https://`).
  - Database Services: Detects exposed MSSQL (1433), Oracle (1521), MySQL (3306), PostgreSQL (5432), Redis (6379), MongoDB (27017).

### 2.6 Docker Nginx Reverse Proxy Architecture
* **Implementation in `frontend/nginx.conf`**:
  - `/api/` proxied to `http://backend:8000/api/` with proxy headers and 60s timeout.
  - `/ws/` proxied to `http://backend:8000/ws/` with HTTP/1.1 Upgrade headers (`Upgrade $http_upgrade`, `Connection "upgrade"`) and 86400s timeout.
  - Eliminates CORS issues in containerized production environments.

### 2.7 Frontend WebSocket Resilience
* **Implementation in `useTelemetry.ts`**:
  - Relative same-origin host resolution via `${protocol}//${window.location.host}/ws/network`.
  - Exponential backoff retry (1s -> 1.5s -> 2.25s -> max 10s).
  - Explicit socket closure and listener cleanup on unmount to prevent connection leaks.

---

## 3. Automated Heuristic Rules Engine (SEC-001 to SEC-009)

| Rule Code | Threat Description | Detection Logic | Severity |
| :--- | :--- | :--- | :---: |
| **SEC-001** | Gateway ARP Spoofing | Persistent gateway MAC baseline mismatch against active ARP table. | **CRITICAL** |
| **SEC-002** | Duplicate IP Conflicts | Conflicting distinct MAC addresses claiming identical IP address. | **HIGH** |
| **SEC-003** | Rogue DNS Resolver | Upstream DNS server pointing to untrusted external unencrypted IP. | **LOW** |
| **SEC-004** | Cleartext Telnet Listener | Port 23 active with unencrypted terminal banner. | **CRITICAL** |
| **SEC-005** | Cleartext FTP Listener | Port 21 active without mandatory TLS encryption. | **MEDIUM** |
| **SEC-006** | Database Exposure | Database port open on network (1433, 1521, 3306, 5432, 6379, 27017). | **HIGH** |
| **SEC-007** | Gateway Admin HTTP | Router management interface open on HTTP without forced HTTPS redirect. | **MEDIUM** |
| **SEC-008** | Windows SMB Exposure | SMB port 445 / 139 active on network interface. | **MEDIUM** |
| **SEC-009** | Remote Desktop Exposure | RDP port 3389 active without VPN encapsulation. | **MEDIUM** |

---

## 4. Secrets, Credentials & Dependency Scan

1. **Hardcoded Secrets**: None. Zero passwords, tokens, API keys, or private certificates exist in source files.
2. **Environment Variables**: Managed via `pydantic-settings` from `.env` with safe defaults; `.env` excluded in `.gitignore`.
3. **CORS Policy**: Restricts origins to localhost and local network development ports.

---

## 5. Security Audit Conclusion

NetScope implements defense-in-depth security principles. Server-side authorization prevents abuse, input validation prevents command injection and memory exhaustion, and Docker Nginx reverse proxy ensures secure container communication.

**Final Assessment: APPROVED FOR DEPLOYMENT**
