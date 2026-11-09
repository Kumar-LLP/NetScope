import ipaddress
import platform
import re
import socket
import subprocess
import time
from typing import Dict, List, Optional
import dns.resolver

from app.schemas.network import (
    PingResponse,
    DNSResponse,
    TracerouteHop,
    TracerouteResponse,
    IPInfoResponse
)

def run_ping(target: str, count: int = 4, timeout_ms: int = 1000) -> PingResponse:
    """
    Executes a genuine ICMP ping operation using tokenized system commands (zero shell injection).
    Parses transmission statistics and RTT latency metrics.
    """
    # Strict validation of target
    if not re.match(r"^[a-zA-Z0-9\.\-_:]+$", target):
        raise ValueError("Invalid target format for ping operation")

    is_win = platform.system().lower() == "windows"
    cmd = (
        ["ping", "-n", str(count), "-w", str(timeout_ms), target]
        if is_win
        else ["ping", "-c", str(count), "-W", str(max(1, timeout_ms // 1000)), target]
    )

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=count * 3)
        raw_output = proc.stdout
    except Exception as e:
        return PingResponse(
            target=target,
            packets_transmitted=count,
            packets_received=0,
            packet_loss_pct=100.0,
            raw_output=f"Error executing ping: {str(e)}"
        )

    # Parse Windows ping output
    # Example: "Packets: Sent = 4, Received = 4, Lost = 0 (0% loss)"
    # "Minimum = 12ms, Maximum = 15ms, Average = 13ms"
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

        # Extract individual response times: "time=14ms" or "time<1ms"
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
    if not re.match(r"^[a-zA-Z0-9\.\-_]+$", domain):
        raise ValueError("Invalid domain name format")

    resolver = dns.resolver.Resolver()
    if custom_server:
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
    """
    if not re.match(r"^[a-zA-Z0-9\.\-_:]+$", target):
        raise ValueError("Invalid target format for traceroute")

    is_win = platform.system().lower() == "windows"
    cmd = (
        ["tracert", "-d", "-h", str(max_hops), "-w", str(timeout_ms), target]
        if is_win
        else ["traceroute", "-n", "-m", str(max_hops), "-w", "1", target]
    )

    hops: List[TracerouteHop] = []

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max_hops * 3)
        raw_output = proc.stdout
    except Exception:
        raw_output = ""

    for line in raw_output.splitlines():
        line = line.strip()
        # Windows match: e.g. "  1    <1 ms    <1 ms    <1 ms  192.168.1.254"
        # or "  3     *        *        *     Request timed out."
        hop_match = re.match(r"^\s*(\d+)\s+(.+)", line)
        if hop_match:
            hop_num = int(hop_match.group(1))
            rest = hop_match.group(2)

            if "Request timed out" in rest or "* * *" in rest:
                hops.append(TracerouteHop(hop=hop_num, timed_out=True))
            else:
                ip_match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", rest)
                ip_addr = ip_match.group(1) if ip_match else None

                # Extract first numeric latency
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
    Calculates IPv4 subnetting, usable host range, broadcast address, and binary formatting.
    """
    ip_or_cidr = ip_or_cidr.strip()
    try:
        if "/" in ip_or_cidr:
            net = ipaddress.ip_network(ip_or_cidr, strict=False)
            addr = net.network_address
        else:
            addr = ipaddress.ip_address(ip_or_cidr)
            net = ipaddress.ip_network(f"{ip_or_cidr}/32", strict=False)
    except Exception as e:
        raise ValueError(f"Invalid IP/CIDR input: {str(e)}")

    is_ipv4 = net.version == 4
    netmask_str = str(net.netmask) if is_ipv4 else "N/A"
    bcast_str = str(net.broadcast_address) if is_ipv4 and net.num_addresses > 1 else None

    # Usable host range
    hosts = list(net.hosts()) if net.num_addresses <= 65536 else []
    if hosts:
        usable_range = [str(hosts[0]), str(hosts[-1])]
        usable_count = len(hosts)
    else:
        usable_range = [str(net.network_address), str(net.network_address)]
        usable_count = 1

    # Binary string representation
    if is_ipv4:
        binary_rep = ".".join(f"{int(octet):08b}" for octet in str(addr).split("."))
    else:
        binary_rep = bin(int(addr))[2:]

    return IPInfoResponse(
        input=ip_or_cidr,
        ip_version=net.version,
        network_address=str(net.network_address),
        netmask=netmask_str,
        broadcast_address=bcast_str,
        usable_host_range=usable_range,
        total_hosts=net.num_addresses,
        usable_hosts=usable_count,
        is_private=net.is_private,
        is_loopback=net.is_loopback,
        binary_representation=binary_rep
    )
