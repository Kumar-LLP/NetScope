# NetScope REST & WebSocket API Specification

## 1. Global Standards & Conventions
- **Base URL**: `/api`
- **Content-Type**: `application/json`
- **Error Response Format**:
  ```json
  {
    "detail": "Descriptive human-readable error message",
    "code": "ERROR_CODE_STRING",
    "timestamp": "2026-11-09T18:00:00Z"
  }
  ```
- **Validation**: Strict validation via Pydantic V2 schemas. Any invalid IP, port, or CIDR returns `422 Unprocessable Entity`.

---

## 2. API Endpoints

### 2.1 System & Health
#### `GET /api/health`
- **Description**: Returns backend health, current uptime, OS platform, and database status.
- **Response `200 OK`**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "platform": "Windows-11",
    "db_connected": true,
    "timestamp": "2026-11-09T18:00:00Z"
  }
  ```

---

### 2.2 Network Overview & Interfaces
#### `GET /api/network/interfaces`
- **Description**: Lists all physical and virtual network adapters detected via `psutil`.
- **Response `200 OK`**:
  ```json
  [
    {
      "name": "Wi-Fi",
      "ip_address": "192.168.1.15",
      "netmask": "255.255.255.0",
      "broadcast": "192.168.1.255",
      "mac_address": "E4:54:E8:2A:7B:1C",
      "is_up": true,
      "speed_mbps": 866,
      "is_default": true
    }
  ]
  ```

#### `GET /api/network/overview`
- **Description**: Provides comprehensive snapshot of active connection, gateway, external IP, latency, and overall network health score (0-100).
- **Response `200 OK`**:
  ```json
  {
    "active_interface": "Wi-Fi",
    "local_ip": "192.168.1.15",
    "public_ip": "203.0.113.45",
    "subnet_mask": "255.255.255.0",
    "cidr": "192.168.1.15/24",
    "default_gateway": "192.168.1.1",
    "gateway_mac": "3C:84:6A:12:34:56",
    "dns_servers": ["192.168.1.1", "1.1.1.1"],
    "internet_connected": true,
    "current_latency_ms": 14.2,
    "packet_loss_pct": 0.0,
    "download_kbps": 1240.5,
    "upload_kbps": 320.1,
    "health_score": 96,
    "connected_devices_count": 8
  }
  ```

---

### 2.3 Device Discovery
#### `POST /api/devices/discover`
- **Description**: Triggers safe local subnet scan using ARP table inspection and async ping probes.
- **Request Body**:
  ```json
  {
    "cidr": "192.168.1.0/24",
    "timeout_seconds": 10
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "scan_id": "d8b3-4f9e",
    "total_discovered": 6,
    "duration_seconds": 2.4,
    "devices": [
      {
        "ip": "192.168.1.1",
        "mac": "3C:84:6A:12:34:56",
        "vendor": "TP-Link Corporation",
        "hostname": "router.local",
        "is_gateway": true,
        "is_local_host": false,
        "response_time_ms": 1.2,
        "first_seen": "2026-11-09T17:50:00Z",
        "last_seen": "2026-11-09T18:00:00Z"
      }
    ]
  }
  ```

#### `GET /api/devices`
- **Description**: Returns all currently discovered and historically tracked LAN devices.
- **Query Parameters**: `include_offline=false`
- **Response `200 OK`**: Array of device objects.

---

### 2.4 Interactive Topology
#### `GET /api/topology`
- **Description**: Returns a graph structure formatted for direct rendering with React Flow.
- **Response `200 OK`**:
  ```json
  {
    "nodes": [
      {
        "id": "internet",
        "type": "internetNode",
        "data": { "label": "Internet", "status": "online", "ip": "1.1.1.1" },
        "position": { "x": 400, "y": 50 }
      },
      {
        "id": "gateway",
        "type": "gatewayNode",
        "data": { "label": "Default Gateway", "ip": "192.168.1.1", "vendor": "TP-Link" },
        "position": { "x": 400, "y": 180 }
      },
      {
        "id": "localhost",
        "type": "hostNode",
        "data": { "label": "Local PC (You)", "ip": "192.168.1.15", "os": "Windows 11" },
        "position": { "x": 400, "y": 320 }
      }
    ],
    "edges": [
      { "id": "e-gw-inet", "source": "gateway", "target": "internet", "animated": true },
      { "id": "e-host-gw", "source": "localhost", "target": "gateway", "animated": true }
    ]
  }
  ```

---

### 2.5 Diagnostic Suite
#### `POST /api/diagnostics/ping`
- **Request Body**:
  ```json
  {
    "target": "1.1.1.1",
    "count": 4,
    "timeout_ms": 1000
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "target": "1.1.1.1",
    "packets_transmitted": 4,
    "packets_received": 4,
    "packet_loss_pct": 0.0,
    "min_rtt_ms": 11.2,
    "avg_rtt_ms": 13.5,
    "max_rtt_ms": 16.1,
    "history": [11.2, 14.0, 16.1, 12.7],
    "raw_output": "Pinging 1.1.1.1 with 32 bytes of data..."
  }
  ```

#### `POST /api/diagnostics/dns`
- **Request Body**:
  ```json
  {
    "domain": "google.com",
    "record_type": "ALL",
    "custom_server": null
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "domain": "google.com",
    "resolved_by": "System DNS",
    "records": {
      "A": ["142.250.190.46"],
      "AAAA": ["2404:6800:4009:827::200e"],
      "MX": ["10 smtp.google.com."],
      "TXT": ["v=spf1 include:_spf.google.com ~all"],
      "NS": ["ns1.google.com.", "ns2.google.com."]
    },
    "query_time_ms": 18.4
  }
  ```

#### `POST /api/diagnostics/traceroute`
- **Request Body**:
  ```json
  {
    "target": "8.8.8.8",
    "max_hops": 15,
    "timeout_ms": 1500
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "target": "8.8.8.8",
    "total_hops": 8,
    "hops": [
      { "hop": 1, "ip": "192.168.1.1", "rtt_ms": 1.4, "hostname": "gateway" },
      { "hop": 2, "ip": "10.42.0.1", "rtt_ms": 4.8, "hostname": null },
      { "hop": 3, "ip": "*", "rtt_ms": null, "timed_out": true }
    ]
  }
  ```

#### `POST /api/diagnostics/ip-info`
- **Request Body**:
  ```json
  { "ip_or_cidr": "192.168.1.50/24" }
  ```
- **Response `200 OK`**:
  ```json
  {
    "input": "192.168.1.50/24",
    "ip_version": 4,
    "network_address": "192.168.1.0",
    "netmask": "255.255.255.0",
    "broadcast_address": "192.168.1.255",
    "usable_host_range": ["192.168.1.1", "192.168.1.254"],
    "total_hosts": 256,
    "usable_hosts": 254,
    "is_private": true,
    "is_loopback": false,
    "binary_representation": "11000000.10101000.00000001.00110010"
  }
  ```

---

### 2.6 Port Diagnostics
#### `POST /api/diagnostics/ports`
- **Security Check**: Requires `authorized: true` acknowledging ownership or permission.
- **Request Body**:
  ```json
  {
    "target": "127.0.0.1",
    "ports": [21, 22, 80, 443, 3306, 8000],
    "timeout_ms": 500,
    "authorized": true
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "target": "127.0.0.1",
    "total_scanned": 6,
    "open_count": 2,
    "results": [
      { "port": 8000, "state": "open", "service": "http-alt / FastAPI", "banner": "HTTP/1.1 200 OK", "rtt_ms": 1.2 },
      { "port": 443, "state": "closed", "service": "https", "banner": null, "rtt_ms": 2.5 }
    ]
  }
  ```

---

### 2.7 Security Insights
#### `GET /api/security/findings`
- **Description**: Runs security analysis rules against discovered inventory and interface configurations.
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "SEC-001",
      "severity": "medium",
      "title": "Unencrypted Web Management Interface Detected",
      "category": "service_exposure",
      "description": "Port 80 (HTTP) was detected open on router gateway without automatic HTTPS redirection.",
      "evidence": "192.168.1.1:80 responsive to unencrypted GET requests.",
      "impact": "Credentials sent across the local Wi-Fi may be intercepted in cleartext.",
      "remediation": "Enable HTTPS and disable unencrypted HTTP management in router settings.",
      "timestamp": "2026-11-09T18:00:00Z"
    }
  ]
  ```

---

## 3. WebSocket Telemetry: `/ws/network`
- **Endpoint**: `ws://localhost:8000/ws/network`
- **Interval**: Pushed every 1.5 seconds.
- **Payload Schema**:
  ```json
  {
    "type": "telemetry_update",
    "timestamp": "2026-11-09T18:00:01.500Z",
    "bandwidth": {
      "download_bytes_per_sec": 128500,
      "upload_bytes_per_sec": 34100,
      "download_formatted": "128.5 KB/s",
      "upload_formatted": "34.1 KB/s"
    },
    "ping_ms": 14.2,
    "packet_loss_pct": 0.0,
    "interface": "Wi-Fi",
    "is_connected": true
  }
  ```
