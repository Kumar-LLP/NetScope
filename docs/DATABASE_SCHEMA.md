# NetScope Database Schema Specification

## 1. Overview & Architecture
NetScope uses **SQLite 3** configured in **Write-Ahead Logging (WAL)** mode (`PRAGMA journal_mode = WAL;`) through **SQLAlchemy 2.0 (Asyncio)**. This architecture ensures high-throughput, non-blocking telemetry writes from background monitoring loops while concurrently servicing read queries from the web dashboard. The schema is designed for full PostgreSQL compatibility should enterprise deployment be needed.

---

## 2. Entity-Relationship Diagram

```mermaid
erDiagram
    NetworkInterface ||--o{ NetworkMetric : records
    NetworkScan ||--o{ ScanResult : contains
    NetworkScan ||--o{ PortDiagnostic : logs
    NetworkDevice ||--o{ ScanResult : identified_in
    NetworkDevice ||--o{ SecurityFinding : associated_with

    NetworkInterface {
        int id PK
        string name
        string ip_address
        string netmask
        string mac_address
        boolean is_default
        boolean is_up
        int speed_mbps
        datetime updated_at
    }

    NetworkDevice {
        int id PK
        string ip_address
        string mac_address UK
        string vendor
        string hostname
        boolean is_gateway
        boolean is_local_host
        string status
        datetime first_seen
        datetime last_seen
    }

    NetworkScan {
        string id PK
        string scan_type
        string target_range
        string status
        int total_targets
        int found_targets
        float duration_seconds
        datetime created_at
    }

    ScanResult {
        int id PK
        string scan_id FK
        int device_id FK
        string ip_address
        string mac_address
        float response_time_ms
        datetime discovered_at
    }

    NetworkMetric {
        int id PK
        int interface_id FK
        float download_bytes_sec
        float upload_bytes_sec
        float latency_ms
        float packet_loss_pct
        int total_bytes_sent
        int total_bytes_recv
        datetime timestamp
    }

    PingResult {
        int id PK
        string target
        int packets_sent
        int packets_received
        float min_rtt_ms
        float avg_rtt_ms
        float max_rtt_ms
        float packet_loss_pct
        string raw_output
        datetime created_at
    }

    DNSResult {
        int id PK
        string domain
        string record_type
        string resolved_server
        string records_json
        float query_time_ms
        datetime created_at
    }

    PortDiagnostic {
        int id PK
        string scan_id FK
        string target_ip
        int port
        string state
        string service_name
        string banner
        float response_time_ms
        datetime created_at
    }

    SecurityFinding {
        int id PK
        int device_id FK
        string rule_id
        string severity
        string title
        string category
        text description
        text evidence
        text impact
        text remediation
        string status
        datetime created_at
    }

    ApplicationSettings {
        string key PK
        string value
        string description
        datetime updated_at
    }
```

---

## 3. Table Definitions & Constraints

### 3.1 `network_interfaces`
Tracks all physical and virtual network adapters discovered on the host system.
- `id` (INTEGER, Primary Key, Autoincrement)
- `name` (VARCHAR(128), Not Null, Index)
- `ip_address` (VARCHAR(45), Nullable)
- `netmask` (VARCHAR(45), Nullable)
- `mac_address` (VARCHAR(17), Nullable)
- `is_default` (BOOLEAN, Default False)
- `is_up` (BOOLEAN, Default True)
- `speed_mbps` (INTEGER, Nullable)
- `updated_at` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.2 `network_devices`
Maintains the inventory of discovered LAN devices across scans.
- `id` (INTEGER, Primary Key, Autoincrement)
- `ip_address` (VARCHAR(45), Not Null, Index)
- `mac_address` (VARCHAR(17), Unique, Nullable, Index)
- `vendor` (VARCHAR(255), Default "Unknown")
- `hostname` (VARCHAR(255), Nullable)
- `is_gateway` (BOOLEAN, Default False)
- `is_local_host` (BOOLEAN, Default False)
- `status` (VARCHAR(32), Default "online")
- `first_seen` (DATETIME, Default CURRENT_TIMESTAMP)
- `last_seen` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.3 `network_scans`
Records metadata for every executed subnet discovery or port diagnostic scan.
- `id` (VARCHAR(64), Primary Key)
- `scan_type` (VARCHAR(32), Not Null) -- 'device_discovery', 'port_scan'
- `target_range` (VARCHAR(128), Not Null)
- `status` (VARCHAR(32), Not Null) -- 'in_progress', 'completed', 'failed', 'stopped'
- `total_targets` (INTEGER, Default 0)
- `found_targets` (INTEGER, Default 0)
- `duration_seconds` (FLOAT, Default 0.0)
- `created_at` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.4 `scan_results`
Individual device observations linked to a parent `network_scan`.
- `id` (INTEGER, Primary Key, Autoincrement)
- `scan_id` (VARCHAR(64), Foreign Key `network_scans.id`, Index)
- `device_id` (INTEGER, Foreign Key `network_devices.id`, Nullable)
- `ip_address` (VARCHAR(45), Not Null)
- `mac_address` (VARCHAR(17), Nullable)
- `response_time_ms` (FLOAT, Nullable)
- `discovered_at` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.5 `network_metrics`
Time-series bandwidth and latency measurements captured by the telemetry background service.
- `id` (INTEGER, Primary Key, Autoincrement)
- `interface_id` (INTEGER, Foreign Key `network_interfaces.id`, Nullable)
- `download_bytes_sec` (FLOAT, Not Null)
- `upload_bytes_sec` (FLOAT, Not Null)
- `latency_ms` (FLOAT, Nullable)
- `packet_loss_pct` (FLOAT, Default 0.0)
- `total_bytes_sent` (BIGINT, Not Null)
- `total_bytes_recv` (BIGINT, Not Null)
- `timestamp` (DATETIME, Default CURRENT_TIMESTAMP, Index)

### 3.6 `ping_results`
Audit log of manual and scheduled ICMP ping operations.
- `id` (INTEGER, Primary Key, Autoincrement)
- `target` (VARCHAR(255), Not Null)
- `packets_sent` (INTEGER, Not Null)
- `packets_received` (INTEGER, Not Null)
- `min_rtt_ms` (FLOAT, Nullable)
- `avg_rtt_ms` (FLOAT, Nullable)
- `max_rtt_ms` (FLOAT, Nullable)
- `packet_loss_pct` (FLOAT, Not Null)
- `raw_output` (TEXT, Nullable)
- `created_at` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.7 `dns_results`
Audit log of DNS query operations and resolved record sets.
- `id` (INTEGER, Primary Key, Autoincrement)
- `domain` (VARCHAR(255), Not Null)
- `record_type` (VARCHAR(16), Not Null)
- `resolved_server` (VARCHAR(64), Nullable)
- `records_json` (TEXT, Not Null)
- `query_time_ms` (FLOAT, Nullable)
- `created_at` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.8 `port_diagnostics`
Results of targeted TCP connect scans.
- `id` (INTEGER, Primary Key, Autoincrement)
- `scan_id` (VARCHAR(64), Foreign Key `network_scans.id`, Nullable, Index)
- `target_ip` (VARCHAR(45), Not Null)
- `port` (INTEGER, Not Null)
- `state` (VARCHAR(16), Not Null) -- 'open', 'closed', 'filtered'
- `service_name` (VARCHAR(64), Nullable)
- `banner` (TEXT, Nullable)
- `response_time_ms` (FLOAT, Nullable)
- `created_at` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.9 `security_findings`
Automated auditing issues identified by the security analyzer.
- `id` (INTEGER, Primary Key, Autoincrement)
- `device_id` (INTEGER, Foreign Key `network_devices.id`, Nullable)
- `rule_id` (VARCHAR(32), Not Null)
- `severity` (VARCHAR(16), Not Null) -- 'critical', 'high', 'medium', 'low', 'info'
- `title` (VARCHAR(255), Not Null)
- `category` (VARCHAR(64), Not Null)
- `description` (TEXT, Not Null)
- `evidence` (TEXT, Not Null)
- `impact` (TEXT, Not Null)
- `remediation` (TEXT, Not Null)
- `status` (VARCHAR(32), Default "active")
- `created_at` (DATETIME, Default CURRENT_TIMESTAMP)

### 3.10 `application_settings`
Key-value configuration store for user preferences and scanning parameters.
- `key` (VARCHAR(128), Primary Key)
- `value` (TEXT, Not Null)
- `description` (VARCHAR(255), Nullable)
- `updated_at` (DATETIME, Default CURRENT_TIMESTAMP)

---

## 4. Indexing & Optimization Strategy
- Indexes created on `network_devices.ip_address` and `network_devices.mac_address` for instant ARP cache lookups.
- Composite index on `network_metrics(timestamp DESC)` for high-speed dashboard telemetry time-series slicing.
- Automatic vacuum and metric pruning: metrics older than 7 days can be pruned via a lightweight background task.
