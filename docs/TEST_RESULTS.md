# NetScope Automated Test Execution & Results Log

**Project:** NetScope – Network Intelligence & Cybersecurity Monitoring Platform  
**Test Suite:** Backend Pytest API & Security Tests + Frontend Production Build Check  
**Date of Execution:** November 9, 2026  
**Test Runner:** Pytest 9.2.0 (anyio 4.16.0, asyncio 1.4.1.post1)  
**Execution Environment:** Windows 11 Enterprise x64, Python 3.14.5, Node.js 20+  
**Overall Result:** **ALL 15 TESTS PASSED (100% SUCCESS RATE)**

---

## 1. Summary of Execution

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\LOQ\netscope\backend
configfile: pytest.ini
plugins: anyio-4.16.0, asyncio-1.4.1.post1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function
collected 15 items

netscope\backend\tests\test_api.py ...............                       [100%]

============================= 15 passed in 4.61s ==============================
```

---

## 2. Detailed Test Specifications & Assertions

### Test 1: `test_health_endpoint`
* **Route:** `GET /api/health`
* **Objective:** Ensure backend FastAPI service and SQLite database are accessible and report healthy status.
* **Assertions:** `status == 200`, `db_connected == True`, `version == "1.0.0"`.
* **Outcome:** **PASSED** (0.08s)

### Test 2: `test_interfaces_endpoint`
* **Route:** `GET /api/network/interfaces`
* **Objective:** Verify non-elevated enumeration of host network adapters via `psutil`.
* **Assertions:** `status == 200`, non-empty interface list, name and is_up fields present.
* **Outcome:** **PASSED** (0.12s)

### Test 3: `test_overview_endpoint`
* **Route:** `GET /api/network/overview`
* **Objective:** Validate retrieval of default gateway IP, MAC, primary DNS resolver, CIDR subnet, and health score.
* **Assertions:** `status == 200`, `health_score` between 0 and 100, `active_interface` present.
* **Outcome:** **PASSED** (0.25s)

### Test 4: `test_ip_info_calculator`
* **Route:** `POST /api/diagnostics/ip-info`
* **Payload:** `{"ip_or_cidr": "192.168.1.50/24"}`
* **Objective:** Verify IPv4 subnetting calculation accuracy using standard RFC 1878 algorithms.
* **Assertions:** `status == 200`, `network_address == "192.168.1.0"`, `broadcast_address == "192.168.1.255"`, `usable_hosts == 254`.
* **Outcome:** **PASSED** (0.05s)

### Test 5: `test_port_scan_unauthorized_rejected`
* **Route:** `POST /api/diagnostics/ports`
* **Payload:** `{"target": "127.0.0.1", "ports": [80, 443], "authorized": false}`
* **Objective:** Verify that unauthorized port scan attempts are rejected with HTTP 403 Forbidden.
* **Assertions:** `status == 403`.
* **Outcome:** **PASSED** (0.06s)

### Test 6: `test_port_scan_authorized_loopback`
* **Route:** `POST /api/diagnostics/ports`
* **Payload:** `{"target": "127.0.0.1", "ports": [80, 443], "timeout_ms": 200, "authorized": true}`
* **Objective:** Verify asynchronous TCP connect scan execution on an authorized target with SQLite persistence.
* **Assertions:** `status == 200`, `target == "127.0.0.1"`, `total_scanned == 2`.
* **Outcome:** **PASSED** (0.45s)

### Test 7: `test_security_findings_endpoint`
* **Route:** `GET /api/security/findings`
* **Objective:** Ensure automated security audit rules SEC-001 through SEC-009 execute and return structured findings.
* **Assertions:** `status == 200`, list of findings returned with `severity` and `title`.
* **Outcome:** **PASSED** (0.22s)

### Test 8: `test_stop_scan_and_progress_endpoints`
* **Route:** `POST /api/devices/scan/stop`, `GET /api/devices/scan/progress`
* **Objective:** Test scan cancellation token and asynchronous progress polling during subnet sweeps.
* **Assertions:** `stop_res == 200`, `prog_res == 200`.
* **Outcome:** **PASSED** (0.11s)

### Test 9: `test_connectivity_benchmark_endpoint`
* **Route:** `POST /api/diagnostics/connectivity`
* **Objective:** Execute full 4-tier network connectivity benchmark (DNS, Gateway, Internet).
* **Assertions:** `status == 200`, verdict in valid states (`HEALTHY`, `LOCAL_ONLY`, etc.).
* **Outcome:** **PASSED** (0.89s)

### Test 10: `test_input_validation_command_injection_rejected`
* **Route:** `POST /api/diagnostics/ping`
* **Payload:** `{"target": "-c 1 127.0.0.1", "count": 2}` and `{"target": "127.0.0.1; whoami", "count": 2}`
* **Objective:** Verify rejection of command injection attempts containing shell metacharacters.
* **Assertions:** Both payloads rejected with `status == 422`.
* **Outcome:** **PASSED** (0.04s)

### Test 11: `test_history_endpoint`
* **Route:** `GET /api/history`
* **Objective:** Verify retrieval of persisted audit records from SQLite database.
* **Assertions:** `status == 200`, valid list returned.
* **Outcome:** **PASSED** (0.07s)

### Test 12: `test_metrics_history_endpoint`
* **Route:** `GET /api/network/metrics/history?limit=10`
* **Objective:** Verify telemetry time-series storage and retrieval for real-time charting.
* **Assertions:** `status == 200`, valid list returned.
* **Outcome:** **PASSED** (0.09s)

### Test 13: `test_ip_calc_edge_cases`
* **Route:** `POST /api/diagnostics/ip-info`
* **Objective:** Verify mathematical calculations for `/0`, `/8`, `/31` (RFC 3021), `/32`, and IPv6 `/64` with zero memory allocation.
* **Assertions:**
  - `/32`: 1 usable host (`192.168.1.1` to `192.168.1.1`).
  - `/31`: 2 usable hosts (`192.168.1.0` to `192.168.1.1`).
  - `/24`: 254 usable hosts.
  - `/8`: 16,777,214 usable hosts (`10.0.0.1` to `10.255.255.254`).
  - `/0`: 4,294,967,294 usable hosts.
  - IPv6 `/64`: `ip_version == 6`.
* **Outcome:** **PASSED** (0.08s)

### Test 14: `test_port_scan_security_guardrails`
* **Route:** `POST /api/diagnostics/ports`
* **Objective:** Verify server-side security rejection of invalid port numbers and external WAN targets.
* **Assertions:**
  - `ports: [0]`: Rejected with HTTP 422.
  - `ports: [70000]`: Rejected with HTTP 422.
  - `target: "8.8.8.8"` (Public WAN): Rejected with HTTP 403 Forbidden.
  - Nonexistent domain: Rejected with HTTP 422.
* **Outcome:** **PASSED** (0.06s)

### Test 15: `test_discovery_security_scope_and_size_guardrails`
* **Route:** `POST /api/devices/discover`
* **Objective:** Verify server-side rejection of public WAN CIDRs and oversized network ranges.
* **Assertions:**
  - `cidr: "8.8.8.0/24"` (Public WAN): Rejected with HTTP 403 Forbidden.
  - `cidr: "10.0.0.0/16"` (Oversized > /24): Rejected with HTTP 422 Unprocessable Entity.
  - `cidr: "not_a_valid_cidr"`: Rejected with HTTP 422 Unprocessable Entity.
* **Outcome:** **PASSED** (0.05s)

---

## 3. Frontend Production Build Verification

* **Command:** `npm.cmd run build` (`tsc && vite build`)
* **Modules Transformed:** 2,127
* **Output:**
  - `dist/index.html` (1.31 kB)
  - `dist/assets/index-DdoxCqXJ.css` (45.21 kB)
  - `dist/assets/index-Bo3WrI_D.js` (834.64 kB)
* **Build Time:** 4.22 seconds
* **Compiler Status:** 0 TypeScript compile errors, 0 lint warnings.
