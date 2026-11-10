# 🗄️ NetScope Database & Persistence Architecture

NetScope utilizes **SQLite 3** managed through **SQLAlchemy 2.0 Async** (`aiosqlite`) with schema migration tracking powered by **Alembic**.

---

## 🏗️ Storage Architecture

- **Engine**: SQLite 3 with Write-Ahead Logging (WAL)
- **Primary Database File**: `backend/data/netscope.db`
- **WAL Journal**: `backend/data/netscope.db-wal`
- **Shared Memory File**: `backend/data/netscope.db-shm`
- **Concurrency Mode**: `PRAGMA journal_mode=WAL` ensures non-blocking concurrent reads while background monitors and discovery workers execute write transactions.
- **Durability Mode**: `PRAGMA synchronous=NORMAL` optimizes disk I/O while guaranteeing database integrity across power interruptions.
- **Busy Timeout**: Configured to 5,000ms (`PRAGMA busy_timeout=5000`) to eliminate transient SQLite lock contention under high telemetry throughput.

---

## 📊 Database Schema Models & Entities

### 1. `network_interfaces`
Monitored hardware and virtual network adapters.
- `id` (INTEGER, Primary Key, Autoincrement)
- `name` (VARCHAR(128), Index)
- `ip_address` (VARCHAR(45), Nullable)
- `mac_address` (VARCHAR(17), Nullable)
- `netmask` (VARCHAR(45), Nullable)
- `broadcast` (VARCHAR(45), Nullable)
- `is_up` (BOOLEAN, Default: True)
- `speed_mbps` (INTEGER, Default: 0)
- `is_default` (BOOLEAN, Default: False)
- `created_at` (DATETIME, Default: utcnow)

### 2. `network_devices`
Discovered hosts inventory with trust classification and status.
- `id` (INTEGER, Primary Key, Autoincrement)
- `ip_address` (VARCHAR(45), Unique Index)
- `mac_address` (VARCHAR(17), Unique Index, Nullable)
- `vendor` (VARCHAR(128), Nullable)
- `hostname` (VARCHAR(255), Nullable)
- `custom_name` (VARCHAR(128), Nullable)
- `notes` (TEXT, Nullable)
- `category` (VARCHAR(64), Default: 'workstation')
- `is_trusted` (BOOLEAN, Default: False)
- `is_gateway` (BOOLEAN, Default: False)
- `is_local_host` (BOOLEAN, Default: False)
- `status` (VARCHAR(32), Default: 'online')
- `first_seen` (DATETIME, Default: utcnow)
- `last_seen` (DATETIME, Default: utcnow)

### 3. `network_scans`
Discovery sweeps and port scanning session history.
- `id` (VARCHAR(64), Primary Key)
- `scan_type` (VARCHAR(32)) — `'arp_ping'`, `'tcp_syn'`, `'port_scan'`, `'full_discovery'`
- `target_range` (VARCHAR(64)) — e.g. `'192.168.1.0/24'`
- `status` (VARCHAR(32), Default: 'running') — `'completed'`, `'partial'`, `'timed_out'`, `'failed'`
- `total_targets` (INTEGER, Default: 0)
- `found_targets` (INTEGER, Default: 0)
- `duration_seconds` (FLOAT, Default: 0.0)
- `created_at` (DATETIME, Default: utcnow)

### 4. `scan_results`
Individual host discovery outcome records linked to `network_scans`.
- `id` (INTEGER, Primary Key, Autoincrement)
- `scan_id` (VARCHAR(64), ForeignKey `network_scans.id`, Index)
- `ip_address` (VARCHAR(45), Index)
- `mac_address` (VARCHAR(17), Nullable)
- `hostname` (VARCHAR(255), Nullable)
- `vendor` (VARCHAR(128), Nullable)
- `response_time_ms` (FLOAT, Nullable)
- `created_at` (DATETIME, Default: utcnow)

### 5. `network_metrics`
Sliding window performance samples collected by `TrafficMonitor`.
- `id` (INTEGER, Primary Key, Autoincrement)
- `interface_name` (VARCHAR(128), Nullable, Index)
- `bytes_sent` (INTEGER)
- `bytes_recv` (INTEGER)
- `packets_sent` (INTEGER)
- `packets_recv` (INTEGER)
- `download_kbps` (FLOAT, Default: 0.0)
- `upload_kbps` (FLOAT, Default: 0.0)
- `ping_latency_ms` (FLOAT, Nullable)
- `tcp_latency_ms` (FLOAT, Nullable)
- `packet_loss_pct` (FLOAT, Default: 0.0)
- `timestamp` (DATETIME, Default: utcnow, Index)

### 6. `ping_results`
ICMP latency diagnostic trials.
- `id` (INTEGER, Primary Key, Autoincrement)
- `target` (VARCHAR(255), Index)
- `packets_transmitted` (INTEGER)
- `packets_received` (INTEGER)
- `packet_loss_pct` (FLOAT)
- `min_rtt_ms` (FLOAT, Nullable)
- `avg_rtt_ms` (FLOAT, Nullable)
- `max_rtt_ms` (FLOAT, Nullable)
- `created_at` (DATETIME, Default: utcnow)

### 7. `dns_results`
Domain resolution diagnostic outcomes.
- `id` (INTEGER, Primary Key, Autoincrement)
- `domain` (VARCHAR(255), Index)
- `query_type` (VARCHAR(16))
- `resolver` (VARCHAR(45))
- `resolution_time_ms` (FLOAT)
- `answers_json` (TEXT)
- `created_at` (DATETIME, Default: utcnow)

### 8. `port_diagnostics`
TCP connect scan service banner inspection results.
- `id` (INTEGER, Primary Key, Autoincrement)
- `scan_id` (VARCHAR(64), Nullable, Index)
- `target_ip` (VARCHAR(45), Index)
- `port` (INTEGER, Index)
- `state` (VARCHAR(16)) — `'open'`, `'closed'`, `'filtered'`
- `service_name` (VARCHAR(64), Nullable)
- `banner` (TEXT, Nullable)
- `response_time_ms` (FLOAT, Nullable)
- `created_at` (DATETIME, Default: utcnow)

### 9. `security_findings`
Deterministic heuristic audit findings with remediation recommendations.
- `id` (INTEGER, Primary Key, Autoincrement)
- `rule_id` (VARCHAR(32), Index) — e.g. `'SEC-001'`, `'SEC-002'`
- `severity` (VARCHAR(16), Index) — `'critical'`, `'high'`, `'medium'`, `'low'`, `'info'`
- `title` (VARCHAR(255))
- `category` (VARCHAR(64))
- `description` (TEXT)
- `evidence` (TEXT)
- `impact` (TEXT)
- `remediation` (TEXT)
- `status` (VARCHAR(32), Default: 'active') — `'active'`, `'acknowledged'`, `'resolved'`, `'dismissed'`
- `target` (VARCHAR(255), Nullable)
- `created_at` (DATETIME, Default: utcnow)
- `acknowledged_at` (DATETIME, Nullable)
- `resolved_at` (DATETIME, Nullable)

### 10. `application_settings`
Persistent operator preferences and calibration parameters.
- `key` (VARCHAR(64), Primary Key)
- `value` (TEXT, Nullable)
- `description` (VARCHAR(255), Nullable)
- `updated_at` (DATETIME, Default: utcnow)

### 11. `network_anomalies`
Dynamic sliding-window telemetry anomalies and threshold alerts.
- `id` (INTEGER, Primary Key, Autoincrement)
- `anomaly_type` (VARCHAR(64), Index) — `'traffic_spike'`, `'gateway_mac_change'`, `'packet_loss_surge'`, `'latency_surge'`
- `severity` (VARCHAR(16), Index) — `'critical'`, `'high'`, `'medium'`, `'low'`
- `title` (VARCHAR(255))
- `description` (TEXT)
- `evidence` (TEXT)
- `target` (VARCHAR(255), Nullable)
- `confidence` (VARCHAR(32), Default: 'high')
- `threshold_trigger` (VARCHAR(128), Nullable)
- `status` (VARCHAR(32), Default: 'active') — `'active'`, `'investigating'`, `'acknowledged'`, `'resolved'`
- `detected_at` (DATETIME, Default: utcnow, Index)
- `acknowledged_at` (DATETIME, Nullable)
- `resolved_at` (DATETIME, Nullable)
- `notes` (TEXT, Nullable)

### 12. `packet_capture_sessions`
Opt-in packet inspection sessions and protocol distribution telemetry.
- `id` (VARCHAR(64), Primary Key)
- `interface_name` (VARCHAR(128))
- `status` (VARCHAR(32), Default: 'capturing') — `'capturing'`, `'completed'`, `'stopped'`, `'error'`
- `total_packets` (INTEGER, Default: 0)
- `tcp_packets` (INTEGER, Default: 0)
- `udp_packets` (INTEGER, Default: 0)
- `icmp_packets` (INTEGER, Default: 0)
- `dns_packets` (INTEGER, Default: 0)
- `other_packets` (INTEGER, Default: 0)
- `total_bytes` (INTEGER, Default: 0)
- `duration_seconds` (FLOAT, Default: 0.0)
- `error_message` (TEXT, Nullable)
- `started_at` (DATETIME, Default: utcnow)
- `stopped_at` (DATETIME, Nullable)

### 13. `device_observations`
Point-in-time evidence model tracking host activity, IP shifts, and DHCP reassignment.
- `id` (INTEGER, Primary Key, Autoincrement)
- `device_id` (INTEGER, ForeignKey `network_devices.id`, Nullable, Index)
- `ip_address` (VARCHAR(45), Index)
- `mac_address` (VARCHAR(17), Nullable, Index)
- `interface_name` (VARCHAR(128), Nullable)
- `timestamp` (DATETIME, Default: utcnow, Index)
- `scan_id` (VARCHAR(64), ForeignKey `network_scans.id`, Nullable, Index)
- `source` (VARCHAR(32), Default: 'arp') — `'arp'`, `'tcp_probe'`, `'traffic_monitor'`, `'dhcp'`
- `response_status` (VARCHAR(32), Default: 'responding') — `'responding'`, `'unresponsive'`, `'conflict'`
- `confidence` (VARCHAR(32), Default: 'confirmed') — `'confirmed'`, `'high'`, `'heuristic'`

### 14. `intelligence_events`
Multi-domain correlated security events generated by the Central Intelligence Engine.
- `id` (INTEGER, Primary Key, Autoincrement)
- `event_id` (VARCHAR(64), Unique Index)
- `category` (VARCHAR(32), Index) — `'device'`, `'traffic'`, `'gateway'`, `'port'`, `'dns'`
- `severity` (VARCHAR(16), Index) — `'critical'`, `'high'`, `'medium'`, `'low'`, `'info'`
- `confidence` (VARCHAR(32), Default: 'high') — `'high'`, `'medium'`, `'low'`
- `timestamp` (DATETIME, Default: utcnow, Index)
- `affected_device_ip` (VARCHAR(45), Nullable, Index)
- `affected_device_mac` (VARCHAR(17), Nullable)
- `evidence_references` (TEXT) — JSON serialized references to underlying scan, metric, or diagnostic rows
- `explanation` (TEXT)
- `recommended_action` (TEXT)
- `investigation_status` (VARCHAR(32), Default: 'unreviewed') — `'unreviewed'`, `'investigating'`, `'acknowledged'`, `'resolved'`, `'dismissed'`
- `resolved_at` (DATETIME, Nullable)

---

## 🔄 Authoritative Alembic Migrations

NetScope manages all database schema changes strictly through Alembic:

1. **Authoritative Execution on Startup**:
   - `app.core.database.run_alembic_migrations()` executes `command.upgrade(alembic_cfg, "head")` before FastAPI accepts requests.
   - Idempotent schema operations prevent runtime race conditions and eliminate dual schema management.

2. **Migration Versions**:
   - `577e827427ad`: Initial baseline schema creating core tables (`network_interfaces`, `network_devices`, `network_scans`, `scan_results`, `network_metrics`, `ping_results`, `dns_results`, `port_diagnostics`, `security_findings`, `application_settings`).
   - `2ca1594d866b`: Incremental migration adding advanced intelligence tables (`network_anomalies`, `packet_capture_sessions`, `device_observations`, `intelligence_events`).

3. **CLI Commands**:
   ```bash
   cd backend
   # Inspect current migration state
   alembic current

   # Upgrade to head
   alembic upgrade head

   # Generate new migration
   alembic revision -m "add_custom_field"
   ```

---

## 💾 Backup, Checkpointing & Disaster Recovery

### 1. Online Hot Backup (Zero Downtime)
Because NetScope uses SQLite WAL mode, hot backups can be taken while the application is actively recording live metrics:

**Using Python `sqlite3` Online Backup API:**
```python
import sqlite3

src = sqlite3.connect("backend/data/netscope.db")
dst = sqlite3.connect("backend/data/netscope_backup.db")
with dst:
    src.backup(dst, pages=100)
dst.close()
src.close()
```

### 2. WAL Checkpointing
To flush the Write-Ahead Log into the main database file before archiving:
```sql
PRAGMA wal_checkpoint(TRUNCATE);
```

### 3. Automated Data Retention Pruning
NetScope includes an automated pruning endpoint (`POST /api/history/cleanup`):
```bash
# Prune metrics older than 7 days, diagnostics older than 14 days, scans older than 30 days
curl -X POST "http://127.0.0.1:8000/api/history/cleanup?metrics_retention_days=7&diagnostics_retention_days=14&scans_retention_days=30&security_retention_days=90"
```

### 4. Disaster Recovery Procedure
If database corruption occurs or the database file is lost:
1. Stop the NetScope backend service.
2. If restoring from a hot backup snapshot:
   ```bash
   cp backend/data/netscope_backup.db backend/data/netscope.db
   rm -f backend/data/netscope.db-wal backend/data/netscope.db-shm
   ```
3. If initializing a fresh database:
   ```bash
   rm -f backend/data/netscope.db*
   cd backend
   alembic upgrade head
   ```
4. Start the NetScope backend; Alembic will verify the schema and resume operation automatically.
