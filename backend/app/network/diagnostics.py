import ipaddress
import platform
import re
import socket
import subprocess
import time
from typing import Dict, List, Optional, Any
import dns.resolver

from app.schemas.network import (
    PingResponse,
    DNSResponse,
    TracerouteHop,
    TracerouteResponse,
    IPInfoResponse
)
from app.network.gateway import get_default_gateway

def sanitize_target(target: str) -> str:
    """
    Strict RFC 1123 target sanitizer to prevent command injection or flag injection.
    """
    clean = target.strip()
    if not clean or len(clean) > 253:
        raise ValueError("Target must be between 1 and 253 characters.")
    # Disallow leading hyphens to prevent CLI argument injection
    if clean.startswith("-") or clean.startswith("/"):
        raise ValueError("Target cannot begin with flag indicators ('-' or '/').")
    # Allow valid domain characters, IPv4, IPv6
    if not re.match(r"^[a-zA-Z0-9\.\-_:]+$", clean):
        raise ValueError("Target contains illegal characters.")
    return clean

def run_ping(target: str, count: int = 4, timeout_ms: int = 1000) -> PingResponse:
    """
    Executes a genuine ICMP ping operation using tokenized system commands (zero shell injection).
    """
    target = sanitize_target(target)
    is_win = platform.system().lower() == "windows"
    cmd = (
        ["ping", "-n", str(count), "-w", str(timeout_ms), target]
        if is_win
        else ["ping", "-c", str(count), "-W", str(max(1, timeout_ms // 1000)), target]
    )

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=count * 3)
        raw_output = proc.stdout
    except subprocess.TimeoutExpired as e:
        raw_output = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "Ping timed out.")
    except Exception as e:
        return PingResponse(
            target=target,
            packets_transmitted=count,
            packets_received=0,
            packet_loss_pct=100.0,
            raw_output=f"Error executing ping: {str(e)}"
        )

    sent = count
    received = 0
    loss_pct = 100.0
    min_rtt = None
    avg_rtt = None
    max_rtt = None
    history: List[float] = []

    if is_win:
        loss_match = re.search(r"Sent\s*=\s*(\d+),\s*Received\s*=\s*(\d+),\s*Lost\s*=\s*(\d+)\s*\(([\d\.]+)%\s*loss\)", raw_output)
        if loss_match:
            sent = int(loss_match.group(1))
            received = int(loss_match.group(2))
            loss_pct = float(loss_match.group(4))

        rtt_match = re.search(r"Minimum\s*=\s*(\d+)ms,\s*Maximum\s*=\s*(\d+)ms,\s*Average\s*=\s*(\d+)ms", raw_output)
        if rtt_match:
            min_rtt = float(rtt_match.group(1))
            max_rtt = float(rtt_match.group(2))
            avg_rtt = float(rtt_match.group(3))

        times = re.findall(r"time[<=](\d+)ms", raw_output)
        history = [float(t) for t in times]
    else:
        loss_match = re.search(r"(\d+)\s+packets transmitted,\s+(\d+)\s+received", raw_output)
        if loss_match:
            sent = int(loss_match.group(1))
            received = int(loss_match.group(2))
            loss_pct = round(((sent - received) / sent) * 100.0, 1)

        rtt_match = re.search(r"rtt min/avg/max/mdev\s*=\s*([\d\.]+)/([\d\.]+)/([\d\.]+)", raw_output)
        if rtt_match:
            min_rtt = float(rtt_match.group(1))
            avg_rtt = float(rtt_match.group(2))
            max_rtt = float(rtt_match.group(3))

        times = re.findall(r"time=([\d\.]+)\s*ms", raw_output)
        history = [float(t) for t in times]

    return PingResponse(
        target=target,
        packets_transmitted=sent,
        packets_received=received,
        packet_loss_pct=loss_pct,
        min_rtt_ms=min_rtt,
        avg_rtt_ms=avg_rtt,
        max_rtt_ms=max_rtt,
        history=history,
        raw_output=raw_output
    )

def run_dns_lookup(domain: str, record_type: str = "ALL", custom_server: Optional[str] = None) -> DNSResponse:
    """
    Resolves domain records across A, AAAA, MX, NS, CNAME, TXT record types.
    """
    domain = sanitize_target(domain)
    resolver = dns.resolver.Resolver()
    if custom_server:
        custom_server = sanitize_target(custom_server)
        resolver.nameservers = [custom_server]

    resolved_by = custom_server or (resolver.nameservers[0] if resolver.nameservers else "Default System DNS")

    types_to_query = (
        ["A", "AAAA", "MX", "NS", "CNAME", "TXT"]
        if record_type.upper() == "ALL"
        else [record_type.upper()]
    )

    records: Dict[str, List[str]] = {}
    start = time.perf_counter()

    for r_type in types_to_query:
        try:
            answers = resolver.resolve(domain, r_type, lifetime=2.0)
            records[r_type] = [str(r.to_text()) for r in answers]
        except Exception:
            records[r_type] = []

    duration = round((time.perf_counter() - start) * 1000, 2)
    return DNSResponse(
        domain=domain,
        resolved_by=str(resolved_by),
        records=records,
        query_time_ms=duration
    )

def run_traceroute(target: str, max_hops: int = 15, timeout_ms: int = 1500) -> TracerouteResponse:
    """
    Executes hop-by-hop traceroute using tracert (Windows) or traceroute (Linux).
    Handles timeouts gracefully without dropping partial hops.
    """
    target = sanitize_target(target)
    is_win = platform.system().lower() == "windows"
    cmd = (
        ["tracert", "-d", "-h", str(max_hops), "-w", str(timeout_ms), target]
        if is_win
        else ["traceroute", "-n", "-m", str(max_hops), "-w", "1", target]
    )

    hops: List[TracerouteHop] = []
    raw_output = ""

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max_hops * 3)
        raw_output = proc.stdout
    except subprocess.TimeoutExpired as e:
        raw_output = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    except Exception:
        raw_output = ""

    for line in raw_output.splitlines():
        line = line.strip()
        hop_match = re.match(r"^\s*(\d+)\s+(.+)", line)
        if hop_match:
            hop_num = int(hop_match.group(1))
            rest = hop_match.group(2)

            if "Request timed out" in rest or "* * *" in rest:
                hops.append(TracerouteHop(hop=hop_num, timed_out=True))
            else:
                ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", rest)
                ip_addr = ip_match.group(1) if ip_match else None

                ms_match = re.search(r"(\d+)\s*ms", rest)
                rtt = float(ms_match.group(1)) if ms_match else None

                hops.append(
                    TracerouteHop(
                        hop=hop_num,
                        ip=ip_addr,
                        rtt_ms=rtt,
                        timed_out=False
                    )
                )

    return TracerouteResponse(
        target=target,
        total_hops=len(hops),
        hops=hops
    )

def calculate_ip_info(ip_or_cidr: str) -> IPInfoResponse:
    """
    Calculates IPv4 and IPv6 subnetting, usable host range, broadcast address,
    and binary formatting mathematically without memory allocation.
    """
    clean_input = ip_or_cidr.strip()
    try:
        if "/" in clean_input:
            net = ipaddress.ip_network(clean_input, strict=False)
            addr = net.network_address
        else:
            addr = ipaddress.ip_address(clean_input)
            suffix = "/32" if addr.version == 4 else "/128"
            net = ipaddress.ip_network(f"{clean_input}{suffix}", strict=False)
    except Exception as e:
        raise ValueError(f"Invalid IP/CIDR input '{clean_input}': {str(e)}")

    is_ipv4 = net.version == 4
    total_hosts = net.num_addresses

    if is_ipv4:
        netmask_str = str(net.netmask)
        prefix = net.prefixlen
        if prefix == 32:
            usable_count = 1
            usable_range = [str(net.network_address), str(net.network_address)]
            bcast_str = None
        elif prefix == 31:
            # RFC 3021: Point-to-point links have 2 usable addresses
            usable_count = 2
            usable_range = [str(net.network_address), str(net.broadcast_address)]
            bcast_str = str(net.broadcast_address)
        else:
            # prefix <= 30
            usable_count = (2 ** (32 - prefix)) - 2
            first_host = str(ipaddress.IPv4Address(int(net.network_address) + 1))
            last_host = str(ipaddress.IPv4Address(int(net.broadcast_address) - 1))
            usable_range = [first_host, last_host]
            bcast_str = str(net.broadcast_address)

        binary_rep = ".".join(f"{int(octet):08b}" for octet in str(addr).split("."))
    else:
        # IPv6
        netmask_str = str(net.netmask)
        prefix = net.prefixlen
        bcast_str = None  # IPv6 uses multicast, has no broadcast address
        if prefix == 128:
            usable_count = 1
            usable_range = [str(net.network_address), str(net.network_address)]
        else:
            usable_count = 2 ** (128 - prefix)
            first_host = str(net.network_address)
            last_host = str(ipaddress.IPv6Address(int(net.network_address) + (2 ** (128 - prefix) - 1)))
            usable_range = [first_host, last_host]

        binary_rep = bin(int(addr))[2:].zfill(128)

    return IPInfoResponse(
        input=clean_input,
        ip_version=net.version,
        network_address=str(net.network_address),
        netmask=netmask_str,
        broadcast_address=bcast_str,
        usable_host_range=usable_range,
        total_hosts=total_hosts,
        usable_hosts=usable_count,
        is_private=net.is_private,
        is_loopback=net.is_loopback,
        binary_representation=binary_rep
    )

def run_connectivity_test() -> Dict[str, Any]:
    """
    Executes a comprehensive 3-step connectivity benchmark:
    1. DNS resolution test (resolves google.com)
    2. Local gateway reachability test
    3. Global internet ping test (1.1.1.1)
    Returns structured results and diagnosis verdict.
    """
    start = time.perf_counter()
    gw_ip = get_default_gateway() or "192.168.1.1"

    # Step 1: DNS Test
    dns_ok = False
    dns_time_ms = None
    try:
        dns_res = run_dns_lookup("google.com", "A")
        if dns_res.records.get("A"):
            dns_ok = True
            dns_time_ms = dns_res.query_time_ms
    except Exception:
        pass

    # Step 2: Gateway Reachability
    gw_ok = False
    gw_time_ms = None
    try:
        gw_ping = run_ping(gw_ip, count=2, timeout_ms=500)
        if gw_ping.packets_received > 0:
            gw_ok = True
            gw_time_ms = gw_ping.avg_rtt_ms
    except Exception:
        pass

    # Step 3: Public Internet Ping
    inet_ok = False
    inet_time_ms = None
    try:
        inet_ping = run_ping("1.1.1.1", count=2, timeout_ms=1000)
        if inet_ping.packets_received > 0:
            inet_ok = True
            inet_time_ms = inet_ping.avg_rtt_ms
    except Exception:
        pass

    total_time = round((time.perf_counter() - start) * 1000, 2)

    # Determine Verdict
    if dns_ok and gw_ok and inet_ok:
        verdict = "HEALTHY"
        summary = "All network tiers operating optimally: DNS resolution, local router hop, and Internet WAN uplink confirmed."
    elif gw_ok and not inet_ok:
        verdict = "LOCAL_ONLY"
        summary = "Local gateway router reachable, but external Internet WAN uplink failed or is blocked."
    elif not gw_ok and inet_ok:
        verdict = "DEGRADED"
        summary = "Internet reachable, but default gateway does not respond to ICMP ping (may have ICMP disabled)."
    else:
        verdict = "OFFLINE"
        summary = "No connectivity detected. Check Wi-Fi/Ethernet cable and local router power."

    return {
        "verdict": verdict,
        "summary": summary,
        "dns": {"ok": dns_ok, "latency_ms": dns_time_ms, "tested_domain": "google.com"},
        "gateway": {"ok": gw_ok, "latency_ms": gw_time_ms, "gateway_ip": gw_ip},
        "internet": {"ok": inet_ok, "latency_ms": inet_time_ms, "tested_target": "1.1.1.1"},
        "benchmark_duration_ms": total_time
    }
