# NetScope Automated Test Execution & Results Log

**Project:** NetScope – Network Intelligence & Cybersecurity Monitoring Platform  
**Test Suite:** Backend Pytest API & Security Suite + Frontend Production Build Check  
**Date of Execution:** November 10, 2026  
**Test Runner:** Pytest 9.2.0 (anyio 4.16.0, asyncio 1.4.1.post1)  
**Execution Environment:** Windows 11 Enterprise x64, Python 3.14.5, Node.js 20+  
**Overall Result:** **ALL 23 TESTS PASSED (100% SUCCESS RATE)**

---

## 1. Summary of Execution

```text
============================= test session starts =============================
platform win32 -- Python 3.14.5, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\LOQ\netscope\backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\LOQ\netscope\backend
configfile: pytest.ini
plugins: anyio-4.16.0, asyncio-1.4.1.post1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collecting ... collected 23 items

netscope\backend\tests\test_api.py::test_health_endpoint PASSED          [  4%]
netscope\backend\tests\test_api.py::test_interfaces_endpoint PASSED      [  8%]
netscope\backend\tests\test_api.py::test_overview_endpoint PASSED        [ 13%]
netscope\backend\tests\test_api.py::test_ip_info_calculator PASSED       [ 17%]
netscope\backend\tests\test_api.py::test_port_scan_unauthorized_rejected PASSED [ 21%]
netscope\backend\tests\test_api.py::test_port_scan_authorized_loopback PASSED [ 26%]
netscope\backend\tests\test_api.py::test_security_findings_endpoint PASSED [ 30%]
netscope\backend\tests\test_api.py::test_stop_scan_and_progress_endpoints PASSED [ 34%]
netscope\backend\tests\test_api.py::test_connectivity_benchmark_endpoint PASSED [ 39%]
netscope\backend\tests\test_api.py::test_input_validation_command_injection_rejected PASSED [ 43%]
netscope\backend\tests\test_api.py::test_history_endpoint PASSED         [ 47%]
netscope\backend\tests\test_api.py::test_metrics_history_endpoint PASSED [ 52%]
netscope\backend\tests\test_api.py::test_ip_calc_edge_cases PASSED       [ 56%]
netscope\backend\tests\test_api.py::test_port_scan_security_guardrails PASSED [ 60%]
netscope\backend\tests\test_api.py::test_discovery_security_scope_and_size_guardrails PASSED [ 65%]
netscope\backend\tests\test_api.py::test_security_headers_present PASSED [ 69%]
netscope\backend\tests\test_api.py::test_unrelated_private_network_rejection PASSED [ 73%]
netscope\backend\tests\test_api.py::test_gateway_baseline_lifecycle PASSED [ 78%]
netscope\backend\tests\test_api.py::test_security_findings_lifecycle PASSED [ 82%]
netscope\backend\tests\test_api.py::test_device_inventory_patch PASSED   [ 86%]
netscope\backend\tests\test_api.py::test_interface_selection PASSED      [ 91%]
netscope\backend\tests\test_api.py::test_report_exports PASSED           [ 95%]
netscope\backend\tests\test_api.py::test_topology_read_only PASSED       [100%]

============================= 23 passed in 7.67s ==============================
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
* **Route:** `GET /api/network/metrics/history`
* **Objective:** Verify telemetry time-series storage retrieval from database.
* **Assertions:** `status == 200`, valid list returned.
* **Outcome:** **PASSED** (0.09s)

### Test 13: `test_ip_calc_edge_cases`
* **Route:** `POST /api/diagnostics/ip-info`
* **Objective:** Mathematical zero-memory verification for `/0`, `/8`, `/31`, `/32`, and IPv6 `/64`.
* **Assertions:** All sizes compute accurately without memory allocation.
* **Outcome:** **PASSED** (0.08s)

### Test 14: `test_port_scan_security_guardrails`
* **Route:** `POST /api/diagnostics/ports`
* **Objective:** Prohibit external public scanning (8.8.8.8) and invalid ports (0, 70000).
* **Assertions:** External target returns HTTP 403; invalid ports return HTTP 422.
* **Outcome:** **PASSED** (0.06s)

### Test 15: `test_discovery_security_scope_and_size_guardrails`
* **Route:** `POST /api/devices/discover`
* **Objective:** Prohibit public WAN sweeps (8.8.8.0/24) and oversized subnets.
* **Assertions:** Public sweep rejected with HTTP 403; malformed CIDR rejected with HTTP 422.
* **Outcome:** **PASSED** (0.05s)

### Test 16: `test_security_headers_present`
* **Route:** `GET /api/health`
* **Objective:** Verify standard OWASP HTTP security headers.
* **Assertions:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=()`.
* **Outcome:** **PASSED** (0.04s)

### Test 17: `test_unrelated_private_network_rejection`
* **Route:** `POST /api/devices/discover`
* **Payload:** `{"cidr": "10.254.254.0/24"}`
* **Objective:** Strict subnet scoping check: reject RFC 1918 subnets not attached to any host network adapter.
* **Assertions:** Rejected with HTTP 403 Forbidden.
* **Outcome:** **PASSED** (0.05s)

### Test 18: `test_gateway_baseline_lifecycle`
* **Route:** `GET/POST /api/security/gateway-baseline/*`
* **Objective:** Verify operator-confirmed baseline workflow (inspect, confirm MAC, check mismatch, reset).
* **Assertions:** Baseline confirms accurately and resets cleanly.
* **Outcome:** **PASSED** (0.15s)

### Test 19: `test_security_findings_lifecycle`
* **Route:** `POST /api/security/findings/{id}/acknowledge` and `resolve`
* **Objective:** Validate finding state transitions (`active` -> `acknowledged` -> `resolved`).
* **Assertions:** Finding status updates persisted in SQLite and retrieved in audit history.
* **Outcome:** **PASSED** (0.18s)

### Test 20: `test_device_inventory_patch`
* **Route:** `PATCH /api/devices/{id}`
* **Objective:** Validate user custom classification (custom_name, notes, category, is_trusted).
* **Assertions:** HTTP 200, persisted and returned in inventory queries.
* **Outcome:** **PASSED** (0.14s)

### Test 21: `test_interface_selection`
* **Route:** `POST /api/network/interfaces/select`
* **Objective:** Validate runtime switching of monitored network interface adapter.
* **Assertions:** Returns HTTP 200 and switches active telemetry target.
* **Outcome:** **PASSED** (0.07s)

### Test 22: `test_report_exports`
* **Route:** `GET /api/reports/*/export?format=csv` and `json`
* **Objective:** Verify genuine downloadable reports for devices, security findings, and scan history.
* **Assertions:** Content-Disposition headers present, valid CSV and JSON formats returned.
* **Outcome:** **PASSED** (0.19s)

### Test 23: `test_topology_read_only`
* **Route:** `GET /api/topology`
* **Objective:** Verify read-only network topology generation without triggering unexpected scans.
* **Assertions:** HTTP 200, valid node and edge arrays returned.
* **Outcome:** **PASSED** (0.08s)
