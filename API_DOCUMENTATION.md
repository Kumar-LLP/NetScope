# 📡 NetScope REST & WebSocket API Specification

This document provides complete documentation for the NetScope REST API and WebSocket streaming interface.

Base URL: `http://127.0.0.1:8000/api`

---

## 🔍 System & Health

### `GET /api/health`
Returns the operational status of the NetScope engine.
- **Response**:
  ```json
  {
    "status": "healthy",
    "version": "1.3.0",
    "platform": "Windows-11-10.0.26100-SP0",
    "db_connected": true,
    "timestamp": "2026-11-10T08:30:00Z"
  }
  ```

### `GET /api/settings`
Returns safe platform configuration metadata (sanitized; no secrets or private keys).

---

## 🌐 Network Telemetry & Interfaces

### `GET /api/network/interfaces`
Lists all active and inactive network adapters, including IPv4/IPv6 addresses, MAC addresses, speeds, adapter types, and default routing flags.

### `POST /api/network/interfaces/select`
Switches the active monitoring interface.
- **Request**:
  ```json
  { "interface_name": "Wi-Fi" }
  ```

### `GET /api/network/overview`
Returns high-level network state: local IP, public IP, default gateway, subnet mask, DNS servers, latency, packet loss, and connected device count.

### `GET /api/network/metrics`
Returns current sliding window bandwidth metrics.

### `GET /api/network/metrics/history?limit=50`
Returns database-persisted historical metrics snapshots.

---

## 🔍 Device Discovery & Inventory

### `POST /api/devices/discover`
Initiates a subnet discovery sweep.
- **Request**:
  ```json
  {
    "cidr": "192.168.1.0/24",
    "timeout_seconds": 10
  }
  ```

### `POST /api/devices/scan/stop`
Cancels any currently running discovery sweep.

### `GET /api/devices/scan/progress`
Returns progress of active discovery (`scanned`, `total`, `status`).

### `GET /api/devices`
Returns all discovered devices in inventory. Supports optional query filters: `search`, `status`, `vendor`, `category`, `sort_by`.

### `GET /api/devices/paginated`
Returns paginated devices list with `page`, `page_size`, `total`, `total_pages`, `items`.

### `PATCH /api/devices/{device_id}`
Updates customizable device attributes:
```json
{
  "custom_name": "Living Room TV",
  "category": "IoT",
  "notes": "Smart TV connected via 5GHz Wi-Fi",
  "is_trusted": true
}
```

---

## 🧰 Network Diagnostics

### `POST /api/diagnostics/ping`
Executes ICMP ping with packet loss calculation and latency statistics.
```json
{ "target": "1.1.1.1", "count": 4, "timeout_ms": 1000 }
```

### `POST /api/diagnostics/dns`
Performs DNS record resolution with structured status reporting (`success`, `no_answer`, `nxdomain`, `timeout`, `resolver_error`).
```json
{ "domain": "google.com", "record_type": "A", "custom_server": null }
```

### `POST /api/diagnostics/traceroute`
Performs hop-by-hop traceroute with timeout resilience.
```json
{ "target": "8.8.8.8", "max_hops": 15, "timeout_ms": 1500 }
```

### `POST /api/diagnostics/ip-info`
Subnet calculator returning netmask, wildcard mask, prefix length, usable host range, total hosts, and binary representation.
```json
{ "ip_or_cidr": "192.168.1.100/24" }
```

### `POST /api/diagnostics/connectivity`
Comprehensive connectivity benchmark testing DNS, default gateway, and public Internet reachability.

### `POST /api/diagnostics/ports`
Controlled TCP port scanner with target verification, anti-rebinding guardrails, and distinct state tracking (`open`, `closed`, `filtered`, `timed_out`, `error`).
```json
{
  "target": "127.0.0.1",
  "ports": [80, 443, 8000],
  "timeout_ms": 500,
  "authorized": true
}
```

---

## 🛡️ Cybersecurity & Anomaly Engine

### `POST /api/security/audit/run`
Executes heuristic security audit rules against discovered devices and interface settings.

### `GET /api/security/findings`
Returns active security findings.

### `GET /api/security/findings/history?limit=100`
Returns all security findings including acknowledged and resolved items.

### `POST /api/security/findings/{finding_id}/acknowledge`
Acknowledges a security finding.

### `POST /api/security/findings/{finding_id}/resolve`
Marks a security finding as resolved.

### `GET /api/security/gateway-baseline`
Returns the gateway baseline status (`confirmed`, `unconfirmed`, `mismatch`, `no_gateway`).

### `POST /api/security/gateway-baseline/confirm`
Confirms the gateway baseline. Requires supplied MAC to match detected gateway.
```json
{ "baseline_mac": "00:11:22:33:44:55" }
```

### `POST /api/security/gateway-baseline/reset`
Resets the confirmed gateway baseline.

### `GET /api/security/anomalies`
Returns detected network anomalies (throughput spikes, gateway swaps, packet loss surges).

### `POST /api/security/anomalies/tune`
Updates anomaly detection thresholds.

---

## 📦 Packet Analysis & Learning Mode

### `GET /api/packets/status`
Returns packet capture engine status, protocol breakdown, and recent header flows.

### `POST /api/packets/start?max_packets=500`
Starts opt-in non-invasive packet capture.

### `POST /api/packets/stop`
Stops running packet capture.

### `GET /api/learning/topics`
Returns educational networking topics linked to live telemetry keys.

---

## 📁 Data Export & Maintenance

### `GET /api/reports/devices/export?format=csv`
Exports device inventory as CSV or JSON with formula injection protection.

### `GET /api/reports/security/export?format=csv`
Exports security findings as CSV or JSON.

### `GET /api/reports/history/export?format=csv`
Exports historical telemetry metrics as CSV or JSON.

### `POST /api/history/cleanup?retention_days=30`
Prunes telemetry metrics and diagnostics older than the retention threshold.

---

## 📡 WebSocket API

### `GET /ws/network`
Broadcasts real-time network telemetry every 1.5 seconds:
```json
{
  "type": "telemetry",
  "timestamp": "2026-11-10T08:30:00Z",
  "bandwidth": {
    "download_bytes_per_sec": 15420,
    "upload_bytes_per_sec": 3200,
    "download_formatted": "15.1 KB/s",
    "upload_formatted": "3.1 KB/s"
  },
  "ping_ms": 14.2,
  "tcp_latency_ms": 15.0,
  "packet_loss_pct": 0.0,
  "interface": "Wi-Fi",
  "is_connected": true
}
```
