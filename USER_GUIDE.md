# 📖 NetScope User & Operations Guide

Welcome to the **NetScope User Guide**. This document explains each module, user interface control, and monitoring workflow in NetScope.

---

## 🧭 Navigation & Layout

NetScope provides a cyber-themed, high-contrast dark interface optimized for Network Operations Centers (NOC). The primary navigation sidebar includes:

1. **Overview**: Real-time interface bandwidth metrics, ping latency, health score, and network gateway status.
2. **Device Discovery**: Fast, safe local subnet ARP and socket discovery sweep with vendor identification and customizable device naming.
3. **Network Topology**: Interactive React Flow diagram showing connected hosts, gateway, and internet uplink with live inspection.
4. **Diagnostic Tools**: Interactive Ping, multi-record DNS resolution, hop-by-hop Traceroute, and IPv4 CIDR subnet calculator.
5. **Port Diagnostics**: Controlled TCP port scanner with quick service presets, anti-rebinding guardrails, and banner grabbing.
6. **Traffic Analytics**: Live telemetry stream, latency jitter charts, and real-time Packet & Protocol Inspection engine.
7. **Security Insights**: Heuristic anomaly analysis, gateway MAC spoofing detection, active risk resolution, and audit re-runs.
8. **Scan History**: Historical log of network sweeps and diagnostic runs with CSV and JSON data export.
9. **Settings**: Platform runtime configuration, non-elevated safety status, and historical database pruning.
10. **Learning Center**: Built-in educational drawer explaining key networking concepts with live metric hooks.

---

## ⚡ Overview Dashboard

- **Health Score**: A composite metric (0-100) calculated from latency, packet loss, and critical security findings.
- **Hardware Telemetry**: Displays current Download/Upload rates (KB/s), ICMP RTT (ms), and packet loss percentage.
- **Gateway & IP Cards**: Shows your current local IP, subnet CIDR, default gateway IP, and resolved MAC address.

---

## 🔍 Device Discovery

1. **Subnet Input**: By default, NetScope automatically detects your local subnet CIDR (e.g. `192.168.1.0/24`). You can enter any local subnet CIDR within the detected network.
2. **Start Discovery Sweep**: Initiates concurrent, non-blocking TCP socket probes (ports 80, 443, 22, 445, 139) followed by ARP cache inspection.
3. **Device Inventory**:
   - Lists IP address, MAC address, detected vendor (from IEEE OUI database), and host status.
   - Click any device to edit its custom name, assign a category (Workstation, Server, IoT, Router), or mark it as trusted.
   - Quick action buttons allow initiating a Ping or Port Scan directly against the device IP.

---

## 🕸️ Network Topology Canvas

- **Interactive Canvas**: Pan, zoom, and drag nodes to visualize your local network architecture.
- **Hierarchical Layout**: Internet Uplink → Default Gateway → Local Host → Discovered Subnet Devices.
- **Live Node Inspection**: Click any node to open the detail drawer showing latency, MAC vendor, and connection status.

---

## 🧰 Diagnostic Suite

### Ping Utility
- Supports hostnames and IP addresses.
- Measures Min, Avg, and Max round-trip times (RTT) with per-packet latency sparklines.

### DNS Query Tool
- Query record types: `A`, `AAAA`, `MX`, `NS`, `TXT`, `CNAME`, or `ALL`.
- Optionally specify a custom upstream resolver (e.g. `8.8.8.8` or `1.1.1.1`).
- Returns structured statuses (`success`, `no_answer`, `nxdomain`, `timeout`, `resolver_error`).

### Traceroute
- Hop-by-hop path visualization with IP addresses, hostnames, and per-hop latencies.
- Detects unreachable hops and timeout boundaries.

### Subnet Calculator
- Enter any IPv4 address or CIDR notation (e.g. `192.168.1.10/24`).
- Calculates network address, broadcast address, netmask, wildcard mask, prefix length, usable host range, total hosts, and 32-bit binary representation.

---

## 🎯 Port Diagnostics

1. **Target Specification**: Enter a target IP or hostname (strictly guarded by anti-rebinding authorization checks).
2. **Preset Profiles**: Select from Top 20 Common, Web Services (80, 443, 8080), Database Ports (3306, 5432, 27017), or enter custom comma-separated ports.
3. **Authorization Checkbox**: NetScope enforces explicit user confirmation prior to socket dispatch.
4. **Results**: Clear breakdown of ports by distinct state (`open`, `closed`, `filtered`, `timed_out`, `error`), along with service banners and response RTT.

---

## 📊 Traffic Analytics & Packet Inspection

- **Telemetry Charts**: Real-time bandwidth utilization and latency jitter stream updated over WebSockets at 1Hz.
- **Packet & Protocol Inspection Engine**:
  - Click **Start Capture (500 Pkts)** to capture network layer packet headers.
  - View real-time protocol distribution (TCP, UDP, ICMP, DNS, Other).
  - Inspect recent packet flows showing source/destination IPs, ports, and packet byte lengths.
  - Zero payload capture guarantee ensures user privacy.

---

## 🛡️ Security Insights & Gateway Baseline

- **Gateway MAC Baseline**:
  - NetScope records your initial gateway MAC address as a baseline.
  - If a different MAC address responds as the gateway, NetScope immediately flags a **CRITICAL** ARP spoofing risk.
  - Use **Confirm Baseline** or **Reset** to maintain the authorized baseline.
- **Rule-Based Findings**:
  - Unencrypted management ports (Telnet 23, FTP 21).
  - Duplicate IP addresses and abnormal latency spikes.
  - Findings can be marked as **Acknowledged** or **Resolved**.
- **Data Export**:
  - Export discovered devices, security findings, and metric histories as CSV or JSON with built-in spreadsheet formula injection protection.

---

## 🎓 Learning Center

- Click **Learning Center** at the bottom of the sidebar to slide out the interactive networking educational drawer.
- Filter by topic: Addressing, Hardware, Routing, Resolution, Security, Performance.
- Review explanations, key engineering takeaways, and live NetScope metric linkages.
