# ⚠️ NetScope Known Limitations & Platform Boundary Notes

This document describes technical constraints and architectural trade-offs inherent to operating NetScope without elevated privileges across Windows and Linux environments.

---

## 1. Non-Elevated Execution Model (Windows 11)

### Standard User Privileges
NetScope is designed to run with standard (non-administrator) privileges. While this improves security posture, certain operations are subject to OS constraints:
- **Raw Socket Creation**: On Windows, creating raw sockets (`socket.SOCK_RAW`) requires Administrator privileges or Npcap/WinPcap drivers. In standard user mode, NetScope's `PacketAnalyzer` falls back to high-frequency socket polling and psutil telemetry.
- **ARP Table Refresh Rate**: ARP cache updates rely on the Windows OS cache management. If an idle host hasn't communicated recently, it may take a few seconds after a socket probe for the OS ARP table to reflect its MAC address.

---

## 2. Platform Behavioral Differences

### Windows vs. Linux Diagnostics
- **Traceroute**:
  - Windows utilizes `tracert -d -h <hops> -w <timeout>`.
  - Linux utilizes `traceroute -n -m <hops> -w <timeout>`.
  - ICMP responses may be filtered by intermediate firewalls, leading to asterisk `*` hops.
- **Ping Output Parsing**:
  - Windows outputs latency as `time<1ms` or `time=14ms`.
  - Linux outputs latency as `time=14.2 ms`.
  - NetScope's regex parsers handle both formats transparently.

---

## 3. Network Environment & Firewalls

### Host Firewall Behavior
- **Filtered vs. Closed Ports**:
  - If a target device runs a host firewall (such as Windows Defender Firewall) configured to drop incoming packets silently, port scans will report `filtered` after timeout.
  - If the host explicitly sends TCP RST packets, the port is reported as `closed`.

### Virtual Adapters & VPNs
- Virtual network adapters (such as Hyper-V, VMware, VirtualBox, or WSL vEthernet bridges) and VPN tunnels may report synthetic MAC addresses or overlapping subnets. NetScope categorizes these adapters by type (`virtual`, `vpn`, `ethernet`, `wifi`).

---

## 4. Hardware Sampling Frequencies

- **Telemetry Polling Interval**: Bandwidth telemetry is calculated via delta sampling over a 1.5-second interval. Very brief bursts (<100ms) will be averaged across the 1.5s window.
