# NetScope Security Architecture & Threat Modeling

## 1. Core Security Philosophy
NetScope is an educational, defensive, and operational observability platform. It is engineered with strict defensive guardrails to prevent it from being weaponized or misused as an unrestricted external scanning proxy, while delivering genuine, highly accurate network diagnostics.

---

## 2. Threat Modeling & Mitigation Matrix

| Threat Category | Potential Vector | NetScope Engineering Mitigation |
| :--- | :--- | :--- |
| **Command Injection** | Malicious hostnames or parameters injected into `ping`, `tracert`, or `arp` shell commands. | **Strict Zero-Shell Architecture**: All system commands use `subprocess.run(["cmd", "arg"])` with explicit tokenized argument lists. `shell=True` is strictly prohibited. Hostnames and IPs undergo strict regex and `ipaddress` parsing before reaching process executors. |
| **Abusive Port Scanning** | Users or automated scripts targeting external infrastructure without authorization. | **Scope & Target Guardrails**: By default, scans are constrained to private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) or loopback. Any scan targeting a non-private IP requires an explicit `authorized: true` confirmation flag in the request payload and UI confirmation modal. |
| **Privilege Escalation** | Requiring elevated Administrator / root rights, exposing the host system to driver or memory vulnerabilities. | **Zero Admin Requirement**: Standard operations rely on user-mode APIs (`psutil`, standard socket connects, user-accessible ARP cache reading). No kernel-mode packet injection or raw socket interception is required for normal operation. |
| **Denial of Service (DoS)** | Rapid multi-threaded scans overwhelming local routers or network switches. | **Concurrency & Timeout Limits**: Maximum concurrent port scan probes are throttled using `asyncio.Semaphore(50)`. Subnet sweep probes apply polite timeouts (200-500ms) with staggered task batches. |
| **Database Injection** | SQL injection via user-supplied search filters or device names. | **Parameterized ORM Queries**: All database queries are executed strictly via SQLAlchemy 2.0 ORM expressions and typed Pydantic models. Raw string formatting in SQL is prohibited. |
| **Information Disclosure** | Exposing sensitive packet payloads, credentials, or internal network topology to unauthorized origins. | **Zero Payload Storage**: NetScope monitors byte counts and metadata; it never captures, inspects, or logs plaintext payload packet bodies or credentials. CORS is locked to authorized local origins (`http://localhost:5173`, `http://127.0.0.1:5173`). |

---

## 3. Input Validation & Sanitization Specifications

### 3.1 IP Address & CIDR Sanitization
Every IP input must pass Python's `ipaddress.ip_address` or `ipaddress.ip_network(strict=False)` validation:
- Multicast addresses (`224.0.0.0/4`), reserved ranges (`240.0.0.0/4`), and broadcast addresses (`255.255.255.255`) are rejected for port diagnostics.
- Target CIDR masks for LAN discovery are constrained between `/20` and `/30` to prevent unintended massive scans.

### 3.2 Hostname Validation
Hostnames must conform strictly to RFC 1123:
- Allowed characters: alphanumeric ASCII `[a-zA-Z0-9]` and hyphens `-`.
- Labels separated by dots `.`, max label length 63 chars, max total length 253 chars.
- Characters like `;`, `&`, `|`, `` ` ``, `$`, `\n`, `\r` are immediately rejected with HTTP `422 Unprocessable Entity`.

### 3.3 Port Range Restrictions
- Port numbers must be integers between `1` and `65535`.
- Predefined port profiles allow rapid inspection of common services (e.g., HTTP 80/443, SSH 22, DNS 53, SMB 445, MySQL 3306) without requiring a full 65,535 port scan.

---

## 4. Security Insights & Auditing Rules
NetScope contains a built-in security evaluation engine (`SecurityAuditor`) that evaluates the host and network environment against baseline security rules:

1. **RULE-SEC-01 (Insecure Management Services)**:
   - *Trigger*: Port 21 (FTP), 23 (Telnet), or 80 (HTTP router admin) detected open on local network devices.
   - *Severity*: Medium / High.
   - *Impact*: Cleartext transmission of authentication credentials over local Wi-Fi / Ethernet.
2. **RULE-SEC-02 (Database / Remote Desktop Exposure)**:
   - *Trigger*: Port 3389 (RDP), 445 (SMB), 3306 (MySQL), 5432 (PostgreSQL) accessible across open LAN.
   - *Severity*: Medium.
   - *Impact*: Unintended internal exposure of sensitive databases or management consoles.
3. **RULE-SEC-03 (Default Gateway Inconsistency)**:
   - *Trigger*: Gateway MAC address differs from initial baseline scan or multiple IPs claim the same MAC (potential ARP cache poisoning).
   - *Severity*: Critical.
   - *Impact*: Potential Man-In-The-Middle (MITM) attack on local subnet.
4. **RULE-SEC-04 (Public/Rogue DNS Resolver)**:
   - *Trigger*: Active DNS resolver differs from expected gateway or known secure public resolvers (Cloudflare, Google, Quad9).
   - *Severity*: Low.
   - *Impact*: Unencrypted DNS queries routed to an untrusted local resolver.
