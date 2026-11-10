# NetScope Automated Test Execution & Results Log

**Project:** NetScope – Network Intelligence & Cybersecurity Monitoring Platform  
**Test Suite:** Backend Pytest API & Security Suite + Frontend Production Build Check  
**Date of Execution:** November 10, 2026  
**Test Runner:** Pytest 9.2.0 (anyio 4.16.0, asyncio 1.4.1.post1)  
**Execution Environment:** Windows 11 Enterprise x64, Python 3.14.5, Node.js 20+  
**Overall Result:** **ALL 30 TESTS PASSED (100% SUCCESS RATE)**

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
collecting ... collected 30 items

netscope\backend\tests\test_api.py::test_health_endpoint PASSED          [  3%]
netscope\backend\tests\test_api.py::test_interfaces_endpoint PASSED      [  6%]
netscope\backend\tests\test_api.py::test_overview_endpoint PASSED        [ 10%]
netscope\backend\tests\test_api.py::test_ip_info_calculator PASSED       [ 13%]
netscope\backend\tests\test_api.py::test_port_scan_unauthorized_rejected PASSED [ 16%]
netscope\backend\tests\test_api.py::test_port_scan_authorized_loopback PASSED [ 20%]
netscope\backend\tests\test_api.py::test_security_findings_endpoint PASSED [ 23%]
netscope\backend\tests\test_api.py::test_stop_scan_and_progress_endpoints PASSED [ 26%]
netscope\backend\tests\test_api.py::test_connectivity_benchmark_endpoint PASSED [ 30%]
netscope\backend\tests\test_api.py::test_input_validation_command_injection_rejected PASSED [ 33%]
netscope\backend\tests\test_api.py::test_history_endpoint PASSED         [ 36%]
netscope\backend\tests\test_api.py::test_metrics_history_endpoint PASSED [ 40%]
netscope\backend\tests\test_api.py::test_ip_calc_edge_cases PASSED       [ 43%]
netscope\backend\tests\test_api.py::test_port_scan_security_guardrails PASSED [ 46%]
netscope\backend\tests\test_api.py::test_discovery_security_scope_and_size_guardrails PASSED [ 50%]
netscope\backend\tests\test_api.py::test_security_headers_present PASSED [ 53%]
netscope\backend\tests\test_api.py::test_unrelated_private_network_rejection PASSED [ 56%]
netscope\backend\tests\test_api.py::test_gateway_baseline_lifecycle PASSED [ 60%]
netscope\backend\tests\test_api.py::test_security_findings_lifecycle PASSED [ 63%]
netscope\backend\tests\test_api.py::test_device_inventory_patch PASSED   [ 66%]
netscope\backend\tests\test_api.py::test_interface_selection PASSED      [ 70%]
netscope\backend\tests\test_api.py::test_report_exports PASSED           [ 73%]
netscope\backend\tests\test_api.py::test_topology_read_only PASSED       [ 76%]
netscope\backend\tests\test_api.py::test_gateway_baseline_mac_validation PASSED [ 80%]
netscope\backend\tests\test_api.py::test_csv_formula_injection_sanitization PASSED [ 83%]
netscope\backend\tests\test_api.py::test_dns_rebinding_rejected PASSED   [ 86%]
netscope\backend\tests\test_api.py::test_settings_endpoint_no_information_disclosure PASSED [ 90%]
netscope\backend\tests\test_api.py::test_interface_selection_validation PASSED [ 93%]
netscope\backend\tests\test_api.py::test_ip_info_binary_host_representation PASSED [ 96%]
netscope\backend\tests\test_api.py::test_security_audit_run_endpoint PASSED [100%]

============================= 30 passed in 10.04s =============================
```

---

## 2. Detailed Test Specifications & Assertions

### Core Diagnostic & Scoping Tests (1-23)
* **Test 1 (`test_health_endpoint`):** Asserts status `healthy` or `degraded`, database connectivity, version integrity.
* **Test 2 (`test_interfaces_endpoint`):** Asserts enumeration of physical adapters, IP, and status flags.
* **Test 3 (`test_overview_endpoint`):** Validates real network overview, latency, and bounded health score `[0, 100]`.
* **Test 4 (`test_ip_info_calculator`):** Verifies CIDR calculation, broadcast address, netmask, and usable hosts count.
* **Test 5 (`test_port_scan_unauthorized_rejected`):** Confirms non-authorized port scans are rejected with HTTP 403.
* **Test 6 (`test_port_scan_authorized_loopback`):** Asserts successful authorized port scan on loopback socket.
* **Test 7 (`test_security_findings_endpoint`):** Verifies active security findings schema and database persistence.
* **Test 8 (`test_stop_scan_and_progress_endpoints`):** Tests cooperative cancellation signal and progress polling.
* **Test 9 (`test_connectivity_benchmark_endpoint`):** Benchmarks genuine ICMP ping, TCP handshake, and DNS resolution.
* **Test 10 (`test_input_validation_command_injection_rejected`):** Confirms command injection payloads (`; rm -rf`, `&& calc.exe`) are rejected with HTTP 422.
* **Test 11 (`test_history_endpoint`):** Validates retrieval of persistent scan history.
* **Test 12 (`test_metrics_history_endpoint`):** Asserts persistence and sliding-window limit of throughput records.
* **Test 13 (`test_ip_calc_edge_cases`):** Validates `/31`, `/32`, and loopback CIDR calculations.
* **Test 14 (`test_port_scan_security_guardrails`):** Enforces rejection of foreign subnets and public WAN hosts.
* **Test 15 (`test_discovery_security_scope_and_size_guardrails`):** Enforces rejection of subnets larger than `/24`.
* **Test 16 (`test_security_headers_present`):** Asserts presence of `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, etc.
* **Test 17 (`test_unrelated_private_network_rejection`):** Confirms private RFC 1918 subnets not attached to local adapters are rejected with HTTP 403.
* **Test 18 (`test_gateway_baseline_lifecycle`):** Tests ARP baseline confirmation, uppercase MAC normalization, and reset lifecycle.
* **Test 19 (`test_security_findings_lifecycle`):** Verifies state machine transitions (`active` -> `acknowledged` -> `resolved`).
* **Test 20 (`test_device_inventory_patch`):** Verifies device metadata patching (`custom_name`, `notes`, `category`, `is_trusted`).
* **Test 21 (`test_interface_selection`):** Verifies setting active interface for live telemetry.
* **Test 22 (`test_report_exports`):** Asserts export generation for CSV and JSON across devices, security, and history.
* **Test 23 (`test_topology_read_only`):** Ensures React Flow topology generation is strictly read-only.

### Extended Security Hardening Tests (24-30)
* **Test 24 (`test_gateway_baseline_mac_validation`):**
  - **Objective:** Prevent malformed inputs and SQL injection in gateway baseline configuration.
  - **Assertions:** Malformed MAC strings (`invalid-mac`, `00:11:22`, `ZZ:ZZ:ZZ:ZZ:ZZ:ZZ`) return HTTP 422 Unprocessable Entity. Valid formats (`aa-bb-cc-11-22-33`) return HTTP 200 normalized to uppercase `AA:BB:CC:11:22:33`.
* **Test 25 (`test_csv_formula_injection_sanitization`):**
  - **Objective:** Neutralize Spreadsheet Formula Injection (CWE-1236) across CSV report generation.
  - **Assertions:** Devices seeded with dangerous spreadsheet prefixes (`=cmd`, `@SUM`, `-DangerousFormula`, `+Formula`) have each cell sanitized with a prepended single apostrophe `'`.
* **Test 26 (`test_dns_rebinding_rejected`):**
  - **Objective:** Neutralize Time-of-Check to Time-of-Use (TOCTOU) DNS Rebinding attacks.
  - **Assertions:** If a hostname's DNS resolution returns both a local loopback and an external public WAN IP (`93.184.216.34`), the port scanner detects the dual-stack rebinding attempt, rejects the scan with HTTP 403 Forbidden, and records the rebinding warning.
* **Test 27 (`test_settings_endpoint_no_information_disclosure`):**
  - **Objective:** Eliminate information exposure of internal server secrets via `/api/settings`.
  - **Assertions:** Confirms internal database connection strings, authorized network lists, and CORS origins are strictly excluded, while public operational parameters (`project_name`, `version`, `telemetry_interval`) are returned.
* **Test 28 (`test_interface_selection_validation`):**
  - **Objective:** Server-side validation of adapter selection.
  - **Assertions:** Selecting nonexistent adapters returns HTTP 404 with available adapter names; empty adapter inputs return HTTP 400.
* **Test 29 (`test_ip_info_binary_host_representation`):**
  - **Objective:** Mathematical precision of host IP binary visualization.
  - **Assertions:** Passing `192.168.1.50/24` accurately returns binary `11000000.10101000.00000001.00110010` representing host `.50` rather than masking to network `.0`.
* **Test 30 (`test_security_audit_run_endpoint`):**
  - **Objective:** Separation of concerns between audit evaluation and read-only finding retrieval.
  - **Assertions:** `POST /api/security/audit/run` evaluates all active heuristics (SEC-001 through SEC-009) and attaches confidence levels (`confirmed`, `potential`, `informational`).

---

## 3. Frontend Production Build & Code Splitting Verification

```text
> netscope-frontend@1.0.0 build
> tsc && vite build

vite v5.4.21 building for production...
transforming...
✓ 2128 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                                 1.31 kB │ gzip:   0.68 kB
dist/assets/TopologyPage-BnuhLJ6X.css          15.87 kB │ gzip:   2.67 kB
dist/assets/index-CyJyAV5H.css                 31.37 kB │ gzip:   6.19 kB
dist/assets/check-11dlQ0j-.js                   0.29 kB │ gzip:   0.24 kB
dist/assets/play-C6uSS75F.js                    0.30 kB │ gzip:   0.25 kB
dist/assets/laptop-VeJAsxal.js                  0.39 kB │ gzip:   0.29 kB
dist/assets/download-DOnPFjQd.js                0.43 kB │ gzip:   0.32 kB
dist/assets/shield-check-dMlO405X.js            0.49 kB │ gzip:   0.35 kB
dist/assets/router-SsgpHQXm.js                  0.55 kB │ gzip:   0.36 kB
dist/assets/ScanHistoryPage-C58vpLnd.js         3.10 kB │ gzip:   1.15 kB
dist/assets/SettingsPage-Cqvtv78u.js            5.88 kB │ gzip:   1.61 kB
dist/assets/PortDiagnosticsPage-mZfCXB3J.js     7.76 kB │ gzip:   2.51 kB
dist/assets/TrafficAnalyticsPage-DbTOLc2M.js    7.96 kB │ gzip:   2.84 kB
dist/assets/OverviewPage-D8rbWhJM.js            8.49 kB │ gzip:   2.56 kB
dist/assets/SecurityInsightsPage-DhGDZNrM.js   15.34 kB │ gzip:   4.13 kB
dist/assets/d3-interpolate-DfT3PiK8.js         15.48 kB │ gzip:   6.35 kB
dist/assets/DiagnosticsPage-BzXowmBP.js        21.83 kB │ gzip:   4.45 kB
dist/assets/DeviceDiscoveryPage-Dsfj0d3S.js    23.10 kB │ gzip:   5.86 kB
dist/assets/TopologyPage-q61DZdTg.js          183.51 kB │ gzip:  57.95 kB
dist/assets/index-Bgjz-rAg.js                 190.35 kB │ gzip:  58.11 kB
dist/assets/AreaChart-C8835ZUD.js             376.56 kB │ gzip: 101.94 kB
✓ built in 3.00s
```

* **TypeScript Compilation:** 0 errors, strict typing preserved.
* **Code Splitting:** Dynamic `React.lazy()` chunking successfully isolates heavyweight modules (`TopologyPage` @ 183 kB, `AreaChart` @ 376 kB, `DeviceDiscoveryPage` @ 23 kB). Initial entrypoint bundle is streamlined to 190 kB.
