# NetScope Technical Specifications & Known Limitations

**Product:** NetScope – Network Intelligence & Cybersecurity Monitoring Platform  
**Document Classification:** Technical Architecture & Environmental Boundaries  
**Last Updated:** November 9, 2026

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

### Scope Boundaries (/24 Default)
* The automated device discovery sweeper restricts single-run active sweeps to `/24` subnets (maximum 254 candidate IP addresses).
* Attempting to actively sweep `/16` (65,534 hosts) or `/8` (16,777,214 hosts) subnets would cause local Wi-Fi router buffer bloat and excessive ARP table churn.
* Users with multi-subnet enterprise environments can specify target subnets explicitly in the CIDR input field.

### Hostname Reverse DNS (PTR) Delays
* On consumer routers or unmanaged Wi-Fi access points, many IoT devices and mobile phones do not register PTR records in local DNS.
* Synchronous reverse DNS calls on Windows can block for several seconds per non-responsive host.
* **NetScope Mitigation**: Hostname resolution is offloaded to asynchronous background worker threads with an enforced 200ms timeout per candidate host, preventing discovery stalls.

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
* Calling Windows `ping.exe` via safe, tokenized subprocess execution is the recommended and universally reliable method on Windows 11. It eliminates the need for raw ICMP socket handles while providing precise millisecond latency metrics.

---

## 5. Summary & Best Practices

1. **Firewalls**: Ensure local Windows Defender Firewall permits incoming and outgoing connections for Python and Node.js on local ports `8000` and `5173`.
2. **Wi-Fi vs Ethernet**: Running NetScope over a wired Ethernet connection provides optimal packet-level accuracy and lower jitter compared to congested 2.4GHz Wi-Fi bands.
3. **Database Maintenance**: Telemetry metric snapshots are stored in SQLite. For continuous 24/7 long-term deployments, users can manage history pruning via the Settings module.