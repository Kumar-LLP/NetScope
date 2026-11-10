# 🗄️ NetScope Database & Persistence Architecture

NetScope utilizes **SQLite 3** managed through **SQLAlchemy 2.0 Async** (`aiosqlite`) with schema migration tracking powered by **Alembic**.

---

## 🏗️ Storage Architecture

- **Engine**: SQLite 3
- **File Location**: `backend/data/netscope.db`
- **WAL Mode**: Enabled by default via `PRAGMA journal_mode=WAL` to ensure non-blocking reads during active writes.
- **Synchronous Setting**: `PRAGMA synchronous=NORMAL` for optimal write performance while preserving durability.
- **Busy Timeout**: 5000ms to eliminate SQLite lock contention.

---

## 📊 Database Schema Models

### 1. `discovered_devices`
Tracks network hosts discovered on monitored subnets.
- `id` (INTEGER, Primary Key)
- `ip` (VARCHAR(45), Unique Index)
- `mac` (VARCHAR(17), Index)
- `vendor` (VARCHAR(100))
- `hostname` (VARCHAR(255))
- `custom_name` (VARCHAR(100), Nullable)
- `notes` (TEXT, Nullable)
- `category` (VARCHAR(50), Default: 'unknown')
- `is_trusted` (BOOLEAN, Default: False)
- `is_gateway` (BOOLEAN, Default: False)
- `is_local_host` (BOOLEAN, Default: False)
- `status` (VARCHAR(20), Default: 'online')
- `response_time_ms` (FLOAT, Nullable)
- `first_seen` (DATETIME, Default: utcnow)
- `last_seen` (DATETIME, Default: utcnow)

### 2. `metric_snapshots`
Sliding window performance samples.
- `id` (INTEGER, Primary Key)
- `interface_name` (VARCHAR(100))
- `download_kbps` (FLOAT)
- `upload_kbps` (FLOAT)
- `ping_latency_ms` (FLOAT, Nullable)
- `tcp_latency_ms` (FLOAT, Nullable)
- `packet_loss_pct` (FLOAT, Default: 0.0)
- `recorded_at` (DATETIME, Index)

### 3. `security_findings`
Automated security audit findings and alerts.
- `id` (INTEGER, Primary Key)
- `rule_id` (VARCHAR(50))
- `severity` (VARCHAR(20), Index)
- `title` (VARCHAR(200))
- `category` (VARCHAR(50))
- `description` (TEXT)
- `evidence` (TEXT)
- `impact` (TEXT)
- `remediation` (TEXT)
- `status` (VARCHAR(20), Default: 'active')
- `target` (VARCHAR(100), Nullable)
- `created_at` (DATETIME)
- `acknowledged_at` (DATETIME, Nullable)
- `resolved_at` (DATETIME, Nullable)

### 4. `gateway_baseline`
Confirmed Layer 2 gateway MAC baseline.
- `id` (INTEGER, Primary Key)
- `gateway_ip` (VARCHAR(45))
- `baseline_mac` (VARCHAR(17))
- `confirmed_at` (DATETIME)
- `notes` (TEXT, Nullable)

### 5. `packet_logs`
Non-invasive packet header logs (zero payload).
- `id` (INTEGER, Primary Key)
- `timestamp` (DATETIME, Index)
- `protocol` (VARCHAR(10))
- `src_ip` (VARCHAR(45))
- `dst_ip` (VARCHAR(45))
- `src_port` (INTEGER, Nullable)
- `dst_port` (INTEGER, Nullable)
- `length` (INTEGER)
- `summary` (VARCHAR(255))

### 6. `network_anomalies`
Heuristic anomaly events.
- `id` (INTEGER, Primary Key)
- `type` (VARCHAR(50))
- `severity` (VARCHAR(20))
- `title` (VARCHAR(200))
- `description` (TEXT)
- `evidence_json` (TEXT)
- `detected_at` (DATETIME, Index)

---

## 🔄 Alembic Migrations

To inspect current database migration status:
```bash
cd backend
alembic current
```

To upgrade to the latest schema:
```bash
alembic upgrade head
```

To create a new schema migration:
```bash
alembic revision --autogenerate -m "description_of_change"
```
