# ⚠️ NetScope Known Limitations & Platform Boundary Notes

This document describes technical constraints, architectural trade-offs, and driver boundaries inherent to operating NetScope across Windows and Linux environments.

---

## 1. Packet Capture Drivers & Zero-Admin Mode

### Windows 11 Npcap Driver Dependency
- Opt-in packet header capture utilizes Scapy.
- On Windows, raw L2/L3 packet sniffing requires **Npcap** installed in **WinPcap API-compatible mode** (`wpcap.dll`).
- In standard user environments without Npcap installed, NetScope automatically and honestly reports driver absence via `/api/packets/status` with `supported: false` and explanatory notes.
- The platform degrades gracefully to zero-admin mode, continuing to provide real-time socket diagnostics, `psutil` throughput monitoring, ICMP latency tracking, and subnet discovery without crashing or hanging.

### Linux Raw Socket Privileges
- On Linux, capturing raw packet headers requires the `CAP_NET_RAW` capability or root execution:
  ```bash
  sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
  ```
- If permissions are absent, NetScope operates in zero-privilege diagnostic mode.

---

## 2. DNS Transport Security Realities

### Plaintext Port 53 Transport vs. DoH/DoT
- Standard operating system resolver APIs (`getaddrinfo`, `socket.gethostbyname`) and DNS queries default to **UDP port 53 in plaintext**.
- Configuring a privacy-respecting public resolver IP (such as Cloudflare `1.1.1.1` or Google `8.8.8.8`) in your network adapter settings does **not** automatically encrypt your DNS queries.
- Unless an explicit local DNS-over-HTTPS (DoH) or DNS-over-TLS (DoT) proxy (such as `cloudflared`, `dnscrypt-proxy`, or `stubby`) is active, DNS lookups remain vulnerable to eavesdropping and ISP inspection on the local transit hop.
- NetScope's Security Auditor accurately reflects this transport exposure rather than falsely claiming encrypted status based solely on resolver IP addresses.

---

## 3. Gateway MAC Baseline & Roaming Behaviors

### ARP Spoofing vs. Legitimate AP Roaming
- When NetScope detects a mismatch between your confirmed gateway MAC baseline and the currently active ARP table MAC, it generates a **HIGH** confidence alert.
- **Root Cause Distinction**:
  - The alert confirms Layer-2 divergence with 100% mathematical certainty.
  - The underlying root cause may be malicious (ARP Cache Poisoning / Man-In-The-Middle attack).
  - Alternatively, legitimate causes include:
    1. Roaming between different Access Points on a multi-AP mesh Wi-Fi network (each AP BSSID has a distinct MAC).
    2. Switching between 2.4 GHz and 5 GHz bands on home routers.
    3. Hardware router replacement or gateway failover in high-availability environments.
- Operators can easily update or reset the baseline via the Security Insights UI once verified.

---

## 4. Platform Diagnostic Behavioral Differences

### Windows vs. Linux Diagnostics
- **Traceroute**:
  - Windows utilizes `tracert -d -h <hops> -w <timeout>` using ICMP Echo Request.
  - Linux utilizes `traceroute -n -m <hops> -w <timeout>` (typically UDP probes).
  - Intermediate routers configured to drop ICMP responses or TTL expiration packets will show asterisk `*` hops.
- **Ping Output Parsing**:
  - Windows outputs latency as `time<1ms` or `time=14ms`.
  - Linux outputs latency as `time=14.2 ms`.
  - NetScope's regex parsers handle both formats transparently.

---

## 5. Host Firewalls & Virtual Adapters

### Filtered vs. Closed Ports
- If a target host runs a firewall (such as Windows Defender Firewall) configured to drop incoming connection requests silently, port scans will report `filtered` after timeout.
- If the target host explicitly replies with a TCP RST packet, the port is reported as `closed`.

### Virtual Adapters & VPNs
- Virtual network adapters (such as Hyper-V, VMware, VirtualBox, or WSL vEthernet bridges) and VPN tunnels may report synthetic MAC addresses or overlapping RFC 1918 subnets.
- NetScope categorizes these adapters by type (`virtual`, `vpn`, `ethernet`, `wifi`) and scopes discovery sweeps to connected interfaces.

---

## 6. Hardware Sampling Frequencies

- **Telemetry Polling Interval**: Bandwidth telemetry is calculated via delta sampling over a 1.5-second interval. Very brief bursts (<100ms) will be averaged across the 1.5s window.
- **WebSocket Queue Buffering**: To prevent slow or stalled client connections from creating backpressure, WebSocket messages are delivered via isolated bounded client queues (`maxsize=10`), dropping older frames for lagging clients.
