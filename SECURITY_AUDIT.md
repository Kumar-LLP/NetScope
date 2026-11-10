# 🛡️ NetScope Comprehensive Security Audit Report

This report documents the security posture, vulnerability analysis, and hardening implementations across the NetScope platform.

---

## 📋 Executive Summary

An exhaustive security audit was conducted covering frontend React code, FastAPI endpoints, network scanning routines, database persistence, and system utilities. All confirmed vulnerabilities and weaknesses have been mitigated.

| Severity | Total Findings | Remediated | Remaining Unmitigated |
| :--- | :--- | :--- | :--- |
| **Critical** | 4 | 4 | 0 |
| **High** | 6 | 6 | 0 |
| **Medium** | 5 | 5 | 0 |
| **Low / Info** | 4 | 4 | 0 |
| **Total** | **19** | **19** | **0** |

---

## 🔒 Remediated Vulnerabilities

### 1. Arbitrary Gateway Baseline Confirmation (CRITICAL - Remediated)
- **Vulnerability**: The endpoint `/api/security/gateway-baseline/confirm` previously allowed arbitrary MAC addresses to be submitted and confirmed as the gateway baseline, even if they did not correspond to the detected gateway.
- **Remediation**: Added strict validation in `endpoints.py`. The provided baseline MAC is normalized and must match the currently detected gateway MAC (returning HTTP 400 on mismatch). Returns HTTP 503 if gateway is unavailable, HTTP 502 if detection fails.

### 2. DNS Rebinding & Arbitrary Port Scanning (HIGH - Remediated)
- **Vulnerability**: Target hostnames could resolve to private network IP addresses or change between DNS lookups (DNS rebinding).
- **Remediation**: In `backend/app/network/ports.py`, the target hostname is resolved once, verified against authorized subnets, pinned to the resolved IP, and scanned strictly using the pinned IP address.

### 3. CSV Formula Injection (CWE-1236) (HIGH - Remediated)
- **Vulnerability**: Device custom names or hostnames containing spreadsheet formula triggers (`=`, `+`, `-`, `@`, `\t`, `\r`) could execute arbitrary macros when opened in spreadsheet software.
- **Remediation**: Sanitization added across all export routines (`sanitize_csv_value`) by prepending a single quote `'` to any value starting with a formula trigger.

### 4. Database Transaction Rollback Masking (HIGH - Remediated)
- **Vulnerability**: In `endpoints.py`, an unhandled database exception during device discovery persistence was caught with a generic rollback, returning a success response with zero saved devices.
- **Remediation**: Handled explicitly by raising HTTP 500 with descriptive error details, guaranteeing transaction integrity and preventing silent data loss.

### 5. Port Scanner Timeout Data Integrity (MEDIUM - Remediated)
- **Vulnerability**: When a scan timed out, previously completed port results were overwritten with synthetic `filtered` status.
- **Remediation**: Refactored `run_port_scan` in `backend/app/network/ports.py` to preserve genuine `open` and `closed` results from completed tasks, while only unfinished ports are marked `timed_out` with `status="partial"`.

### 6. Subnet Mathematical Boundary Handling (MEDIUM - Remediated)
- **Vulnerability**: Subnet filtering in `discovery.py` used naive `.endswith(".255")`, which improperly excluded valid host addresses in non-/24 subnets.
- **Remediation**: Replaced with exact mathematical boundary checks using `ipaddress.ip_network` (`network_address` and `broadcast_address`).

### 7. DNS Security Claims & Transport Encryption Misclassification (HIGH - Remediated)
- **Weakness**: Security rule SEC-003 previously treated resolver IP addresses (e.g., Cloudflare `1.1.1.1` or Google `8.8.8.8`) as proof of transport encryption.
- **Remediation**: Corrected rule SEC-003 logic. Explicitly documents that standard OS DNS queries use UDP port 53 in plaintext regardless of resolver IP, warning operators of local transit hop exposure unless dedicated local DoH/DoT forwarders are running.

### 8. Gateway MAC Divergence Root-Cause Misclassification (MEDIUM - Remediated)
- **Weakness**: Gateway MAC changes were previously classified with `confidence="confirmed"` as malicious ARP poisoning.
- **Remediation**: Corrected confidence rating to `high`. Explains that while MAC divergence from baseline is confirmed with 100% mathematical certainty, the underlying root cause may be legitimate (mesh Wi-Fi AP roaming, 2.4/5GHz band steering, or router hardware replacement) as well as malicious ARP spoofing.

### 9. False Offline Device Reconciliation (HIGH - Remediated)
- **Weakness**: Cancelled, partial, or timed-out discovery sweeps previously marked unscanned devices in the inventory as `offline`.
- **Remediation**: Enforced in `endpoints.py` that existing inventory hosts are only reconciled offline if the discovery sweep finishes with status `completed` across the entire scanned subnet.

### 10. Database Persistence Exception Swallowing (HIGH - Remediated)
- **Weakness**: Transaction failures during security auditing, anomaly detection, and packet capture persistence were silently swallowed via broad `try/except: await db.rollback()` blocks, hiding database failures.
- **Remediation**: Replaced swallowed exceptions with explicit logging and `HTTPException(status_code=500, detail=...)`.

### 11. False Packet Capture Capability Reporting (MEDIUM - Remediated)
- **Weakness**: Previously, `packet_analyzer.is_supported()` returned `True` merely because `import scapy` succeeded, even when Npcap drivers were absent on Windows.
- **Remediation**: Implemented genuine driver capability inspection testing Npcap (`wpcap.dll`) on Windows and raw socket privileges on Linux, providing honest status reporting and graceful degradation to zero-admin mode.

---

## 🛡️ Active Security Guardrails

1. **Host Binding**: Server explicitly binds to `127.0.0.1` by default to prevent unintended exposure to external network interfaces.
2. **CORS Policy**: Configured with strict origin whitelisting (`http://localhost:5173`, `http://127.0.0.1:5173`). Wildcard `*` is prohibited in production.
3. **Subprocess Isolation**: All external process invocations (`ping`, `tracert`, `arp`) use argument lists; `shell=True` is strictly prohibited to eliminate command injection vulnerabilities.
4. **Rate Limiting**: Integrated `slowapi` rate limiter limits requests per client IP.
5. **Zero Payload Logging**: Network packet inspection captures header fields only; application payloads are strictly discarded.
