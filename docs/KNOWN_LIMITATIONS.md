# NetScope Technical Specifications & Known Limitations

**Product:** NetScope – Network Intelligence & Cybersecurity Monitoring Platform  
**Document Classification:** Technical Architecture & Environmental Boundaries  
**Last Updated:** November 10, 2026

---

## 1. Operating System Permission Boundaries

### User-Mode Execution by Design
NetScope is intentionally engineered to operate **without requiring Windows Administrator privileges or Linux root credentials** for all standard Network Operations Center (NOC) and diagnostic features.

| Feature | Implementation Mechanism | Privileges Required |
| :--- | :--- | :---: |
| **Interface Enumeration** | `psutil.net_if_addrs()` & `psutil.net_if_stats()` | Standard User |
| **Default Gateway Detection** | Routing table inspection (`ip route` / `route print`) | Standard User |
| **LAN Device Discovery** | Safe OS ARP table cache + concurrent TCP connect sweep | Standard User |
| **ICMP Ping Diagnostics** | Tokenized system `ping` executable (`ping.exe` / `ping`) | Standard User |
| **DNS Resolution** | `dnspython` recursive UDP resolver | Standard User |
| **Traceroute** | Tokenized system `tracert -d` (Windows) / `traceroute -n` (Linux) | Standard User |
| **Port Diagnostics** | Full three-way TCP handshake (`asyncio.open_connection`) | Standard User |
| **Throughput Telemetry** | High-frequency sampling of network adapter counters via `psutil` | Standard User |

### Advanced Raw Packet Captures (Future Consideration)
* **SYN Half-Open / Stealth Scanning**: Standard Windows user accounts cannot construct raw IP packets or craft custom TCP headers without administrative rights and the Npcap/WinPcap kernel driver installed in WinPcap compatibility mode.
* **Promiscuous Packet Sniffing**: Deep packet inspection (DPI) of neighbor-to-neighbor traffic requires raw socket hooks. NetScope intentionally avoids requiring kernel drivers so that students, developers, and IT administrators can immediately clone, run, and explore their network safely.

---

## 2. Subnet Discovery & LAN Sweeping Limits

### Scope Boundaries (/24 Default) & Interface Subnet Scoping
* The automated device discovery sweeper restricts single-run active sweeps to `/24` subnets (maximum 254 candidate IP addresses). Subnet masks larger than `/24` are rejected with HTTP 422 to avoid network congestion.
* **Strict Interface Scope Boundary**: NetScope strictly enforces that target subnets must be attached to an active local network interface. Probing arbitrary or foreign RFC 1918 subnets (e.g., `10.254.254.0/24` when the host is only attached to `192.168.1.0/24`) is rejected with HTTP 403 Forbidden. Operators requiring multi-homed or routed scanning can declare subnets in `AUTHORIZED_NETWORKS` in `.env`.
* **Evidence-Based Device Status**: Hosts confirmed responsive to ICMP/TCP probes during sweeps are marked `status = "online"`. Hosts identified only via operating system ARP tables that fail to respond to active probes are accurately marked `status = "stale"`, reflecting passive cache entries rather than verified active transceivers.

### Hostname Reverse DNS (PTR) Delays
* On consumer routers or unmanaged Wi-Fi access points, many IoT devices and mobile phones do not register PTR records in local DNS.
* Synchronous reverse DNS calls on Windows can block for several seconds per non-responsive host.
* **NetScope Mitigation**: Hostname resolution is offloaded to asynchronous background worker threads with an enforced 200ms timeout per candidate host, preventing discovery stalls.

### TOCTOU DNS Rebinding & Anti-Spoofing Scoping
* Diagnostic port scanning resolves all A/AAAA records for hostnames and pins the validated numeric IP. Any resolution yielding an external public address aborts the scan immediately to prevent DNS rebinding attacks.

---

## 3. External API & Rate Limit Handling

### Public IP Resolution Caching
* The public IP address and ISP metadata are queried from external providers (`https://api.ipify.org`).
* To avoid rate limits and permit offline LAN testing, public IP results are cached in memory for 30 minutes. If an Internet uplink is unavailable, NetScope cleanly reports `Offline / Air-gapped` without degrading local LAN telemetry.

---

## 4. Diagnostics & Traceroute Behavior

### Intermediate Router ICMP Filtering
* During traceroute analysis, certain intermediate transit routers or enterprise firewalls drop ICMP "TTL Exceeded" error messages or rate-limit ICMP responses.
* Hops displaying `* * * Request timed out` reflect standard carrier routing policies and do not represent a flaw in NetScope's parser.

### ICMP Ping Privileges on Windows
* Calling Windows `ping.exe` via safe, tokenized subprocess execution is the recommended and universally reliable method on Windows 11. It eliminates the need for raw ICMP socket handles while providing precise min/avg/max millisecond latency and packet loss metrics.

### Port Scanner Concurrency Guards
* Port scans are limited to a maximum of 2 concurrent scans globally (`MAX_CONCURRENT_ACTIVE_SCANS = 2`) to prevent socket descriptor depletion on Windows workstations.
* Port scanning targets are restricted to loopback and active interface subnets; scanning external WAN addresses is blocked server-side.

---

## 5. Database Concurrency & Storage Architecture

* SQLite is configured in **WAL (Write-Ahead Logging)** mode with `PRAGMA synchronous = NORMAL` and `PRAGMA foreign_keys = ON`. This allows concurrent read operations by REST endpoints while the background telemetry collector appends metrics every 2 seconds.
* Automatic schema migration helper executes on startup, allowing transparent schema upgrades without deleting existing operational data.

---

## 6. Summary & Best Practices

1. **Firewalls**: Ensure local Windows Defender Firewall permits incoming and outgoing connections for Python and Node.js on local ports `8000` and `5173`.
2. **Wi-Fi vs Ethernet**: Running NetScope over a wired Ethernet connection provides optimal packet-level accuracy and lower jitter compared to congested 2.4GHz Wi-Fi bands.
3. **Monitored Interface Switching**: Use the adapter selector on the Traffic Analytics page to switch between physical Ethernet, Wi-Fi, and virtual adapters (e.g. WSL/vEthernet).
