import subprocess
import platform
import re
import time
import socket
import ipaddress
from typing import List, Dict, Optional, Any

from app.schemas.network import (
    PingResponse,
    DNSResponse,
    TracerouteResponse,
    TracerouteHop,
    IPInfoResponse
)

SUPPORTED_DNS_TYPES = {"A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA", "PTR", "ALL"}

def sanitize_target(target: str) -> str:
    """Validates target input preventing shell metacharacters and control characters."""
    clean = target.strip()
    if not clean:
        raise ValueError("Target host cannot be empty.")
    if clean.startswith("-") or clean.startswith("/"):
        raise ValueError("Invalid target format: flags and switches are not permitted.")
    if any(c in clean for c in [";", "&", "|", "`", "$", " ", "\n", "\r", "<", ">", "\t"]):
        raise ValueError("Target contains illegal shell or control characters.")
    return clean

def run_ping(target: str, count: int = 4, timeout_ms: int = 1000) -> PingResponse:
    """Executes ICMP ping with strict tokenized argument vectors."""
    target = sanitize_target(target)
    is_win = platform.system().lower() == "windows"
    cmd = (
        ["ping", "-n", str(count), "-w", str(timeout_ms), target]
        if is_win
        else ["ping", "-c", str(count), "-W", str(max(1, timeout_ms // 1000)), target]
    )

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=(count * (timeout_ms / 1000.0)) + 3.0)
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

    return PingResponse(
        target=target,
        packets_transmitted=sent,
        packets_received=received,
        packet_loss_pct=loss_pct,
        min_rtt_ms=min_rtt,
        avg_rtt_ms=avg_rtt,
        max_rtt_ms=max_rtt,
        raw_output=raw_output
    )

def run_dns_lookup(domain: str, record_type: str = "ALL", custom_server: Optional[str] = None) -> DNSResponse:
    """
    Resolves domain records across A, AAAA, MX, NS, CNAME, TXT, SOA, PTR types with
    strict input validation, returning structured statuses (success, no_answer, nxdomain, timeout, resolver_error).
    """
    import dns.resolver
    import dns.exception

    domain = sanitize_target(domain)
    r_type_clean = record_type.strip().upper()
    if r_type_clean not in SUPPORTED_DNS_TYPES:
        raise ValueError(
            f"Unsupported DNS record type '{record_type}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_DNS_TYPES))}."
        )

    resolver = dns.resolver.Resolver()
    if custom_server:
        custom_server = sanitize_target(custom_server)
        try:
            ipaddress.ip_address(custom_server)
        except ValueError:
            raise ValueError(f"Invalid custom DNS nameserver IP address: '{custom_server}'.")
        resolver.nameservers = [custom_server]

    resolved_by = custom_server or (resolver.nameservers[0] if resolver.nameservers else "Default System DNS")

    types_to_query = (
        ["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA"]
        if r_type_clean == "ALL"
        else [r_type_clean]
    )

    records: Dict[str, List[str]] = {}
    statuses_by_type: Dict[str, str] = {}
    overall_status = "success"
    start = time.perf_counter()

    for qtype in types_to_query:
        try:
            answers = resolver.resolve(domain, qtype, lifetime=2.0)
            records[qtype] = [str(r.to_text()) for r in answers]
            statuses_by_type[qtype] = "success" if records[qtype] else "no_answer"
        except dns.resolver.NXDOMAIN:
            records[qtype] = []
            statuses_by_type[qtype] = "nxdomain"
            overall_status = "nxdomain"
        except dns.resolver.NoAnswer:
            records[qtype] = []
            statuses_by_type[qtype] = "no_answer"
        except dns.exception.Timeout:
            records[qtype] = []
            statuses_by_type[qtype] = "timeout"
            if overall_status != "nxdomain":
                overall_status = "timeout"
        except Exception:
            records[qtype] = []
            statuses_by_type[qtype] = "resolver_error"
            if overall_status not in ("nxdomain", "timeout"):
                overall_status = "resolver_error"

    if overall_status == "success" and not any(records.values()):
        overall_status = "no_answer"

    duration = round((time.perf_counter() - start) * 1000, 2)
    return DNSResponse(
        domain=domain,
        record_type=r_type_clean,
        resolved_by=str(resolved_by),
        records=records,
        query_time_ms=duration,
        status=overall_status,
        statuses_by_type=statuses_by_type
    )

def run_traceroute(target: str, max_hops: int = 15, timeout_ms: int = 1500) -> TracerouteResponse:
    """
    Executes hop-by-hop traceroute using tracert (Windows) or traceroute (Linux).
    Handles timeouts gracefully without dropping partial hops, validating subprocess exit codes.
    """
    target = sanitize_target(target)
    is_win = platform.system().lower() == "windows"
    cmd = (
        ["tracert", "-d", "-h", str(max_hops), "-w", str(timeout_ms), target]
        if is_win
        else ["traceroute", "-n", "-m", str(max_hops), "-w", str(max(1, timeout_ms // 1000)), target]
    )

    timeout_seconds = max(5.0, (max_hops * (timeout_ms / 1000.0)) + 3.0)
    timed_out = False
    exit_code = 0
    err_msg = None

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
        raw_output = proc.stdout
        exit_code = proc.returncode
        if exit_code != 0:
            err_msg = proc.stderr.strip() if proc.stderr else f"Traceroute exited with code {exit_code}"
    except subprocess.TimeoutExpired as e:
        timed_out = True
        raw_output = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "Traceroute timed out.")
    except FileNotFoundError:
        raise RuntimeError("Traceroute system utility not found on this host.")
    except Exception as e:
        raise RuntimeError(f"Error executing traceroute: {str(e)}")

    hops: List[TracerouteHop] = []

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

    status_str = "completed"
    if timed_out:
        status_str = "timed_out"
    elif exit_code != 0 and not hops:
        status_str = "error"

    return TracerouteResponse(
        target=target,
        total_hops=len(hops),
        hops=hops,
        status=status_str,
        error_message=err_msg
    )

def calculate_ip_info(ip_or_cidr: str) -> IPInfoResponse:
    """
    Calculates IPv4 and IPv6 subnetting, usable host range, broadcast address,
    and binary formatting mathematically without memory allocation.
    Accurately represents the binary notation of the host address while preserving
    the network address separately.
    """
    clean_input = ip_or_cidr.strip()
    try:
        if "/" in clean_input:
            iface_obj = ipaddress.ip_interface(clean_input)
            host_ip = iface_obj.ip
            net = iface_obj.network
        else:
            host_ip = ipaddress.ip_address(clean_input)
            suffix = "/32" if host_ip.version == 4 else "/128"
            net = ipaddress.ip_network(f"{clean_input}{suffix}", strict=False)
    except Exception as e:
        raise ValueError(f"Invalid IP/CIDR input '{clean_input}': {str(e)}")

    is_ipv4 = net.version == 4
    total_hosts = net.num_addresses

    if is_ipv4:
        netmask_str = str(net.netmask)
        prefix = net.prefixlen
        wildcard_str = str(ipaddress.IPv4Address(int(ipaddress.IPv4Address("255.255.255.255")) - int(net.netmask)))
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

        # Binary representation corresponds to the host IP
        binary_rep = ".".join(f"{int(octet):08b}" for octet in str(host_ip).split("."))
    else:
        # IPv6
        netmask_str = str(net.netmask)
        prefix = net.prefixlen
        wildcard_str = None
        bcast_str = None  # IPv6 uses multicast, has no broadcast address
        if prefix == 128:
            usable_count = 1
            usable_range = [str(net.network_address), str(net.network_address)]
        else:
            usable_count = 2 ** (128 - prefix)
            first_host = str(net.network_address)
            last_host = str(ipaddress.IPv6Address(int(net.network_address) + (2 ** (128 - prefix) - 1)))
            usable_range = [first_host, last_host]

        binary_rep = bin(int(host_ip))[2:].zfill(128)

    return IPInfoResponse(
        input=clean_input,
        ip_version=net.version,
        network_address=str(net.network_address),
        netmask=netmask_str,
        wildcard_mask=wildcard_str,
        prefix_length=prefix,
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
    Executes a comprehensive 4-tier connectivity benchmark:
    1. Local loopback / Host internal network stack
    2. Default Gateway reachability & latency
    3. Internet public WAN latency & packet loss
    4. Genuine DNS resolution testing (A record query)
    """
    from app.network.gateway import (
        check_gateway_connectivity,
        check_internet_connectivity,
        get_default_gateway,
        measure_tcp_connect_latency
    )

    results: Dict[str, Any] = {}
    gw_ip = get_default_gateway()

    # Tier 1: Local Loopback
    loopback_ping = run_ping("127.0.0.1", count=2, timeout_ms=300)
    results["loopback"] = {
        "target": "127.0.0.1",
        "ok": loopback_ping.packet_loss_pct < 100.0,
        "latency_ms": loopback_ping.avg_rtt_ms
    }

    # Tier 2: Default Gateway
    gw_reachable, gw_rtt, gw_loss = check_gateway_connectivity(gw_ip)
    results["gateway"] = {
        "gateway_ip": gw_ip or "Unavailable",
        "ok": gw_reachable,
        "latency_ms": gw_rtt,
        "packet_loss_pct": gw_loss
    }

    # Tier 3: Internet Connectivity (ICMP + TCP Connect)
    net_reachable, net_rtt, net_loss = check_internet_connectivity()
    tcp_latency = measure_tcp_connect_latency("1.1.1.1", 53, 0.4)
    results["internet"] = {
        "tested_target": "1.1.1.1 / 8.8.8.8",
        "ok": net_reachable,
        "latency_ms": net_rtt,
        "tcp_latency_ms": tcp_latency,
        "packet_loss_pct": net_loss
    }

    # Tier 4: Genuine DNS Resolution
    dns_ok = False
    dns_time_ms = None
    dns_resolved_by = "System Resolver"
    dns_test_domain = "one.one.one.one"
    try:
        dns_res = run_dns_lookup(dns_test_domain, record_type="A")
        if dns_res.records and any(len(v) > 0 for v in dns_res.records.values()):
            dns_ok = True
            dns_time_ms = dns_res.query_time_ms
            dns_resolved_by = dns_res.resolved_by
    except Exception:
        dns_ok = False

    results["dns"] = {
        "ok": dns_ok,
        "latency_ms": dns_time_ms,
        "tested_domain": dns_test_domain,
        "resolved_by": dns_resolved_by
    }

    # Benchmark verdict
    if net_reachable and gw_reachable and dns_ok:
        verdict = "HEALTHY"
        summary = "All network tiers operating optimally with sub-second DNS resolution."
    elif gw_reachable and not net_reachable:
        verdict = "LOCAL_ONLY"
        summary = "Local gateway is responsive, but public Internet WAN is unreachable."
    elif not gw_reachable and not net_reachable:
        verdict = "OFFLINE"
        summary = "Host interface is isolated; gateway and Internet are unreachable."
    else:
        verdict = "DEGRADED"
        summary = "Partial network connectivity; DNS or packet loss degradation observed."

    results["verdict"] = verdict
    results["summary"] = summary
    return results
