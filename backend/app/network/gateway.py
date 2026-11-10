import platform
import subprocess
import re
import socket
import time
import httpx
import dns.resolver
from typing import Optional, List, Tuple

_cached_public_ip: Optional[str] = None
_cached_public_ip_time: float = 0

def get_default_gateway() -> Optional[str]:
    """
    Identifies the default gateway IPv4 address from the system routing table.
    Supports Windows (route print) and Linux (ip route).
    Returns None if no default gateway is detected (no hardcoded guesses).
    """
    os_name = platform.system().lower()
    try:
        if os_name == "windows":
            res = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True,
                text=True,
                timeout=3
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                    gateway_candidate = parts[2]
                    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", gateway_candidate):
                        # Avoid returning loopback or 0.0.0.0 as gateway
                        if gateway_candidate not in ("0.0.0.0", "127.0.0.1"):
                            return gateway_candidate
        else:
            res = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=3
            )
            parts = res.stdout.strip().split()
            if len(parts) >= 3 and parts[0] == "default" and parts[1] == "via":
                return parts[2]
    except Exception:
        pass
    return None

def get_gateway_mac(gateway_ip: Optional[str]) -> Optional[str]:
    """
    Inspects the local ARP table to find the verified hardware MAC address of the default gateway.
    """
    if not gateway_ip:
        return None

    try:
        res = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            timeout=3
        )
        for line in res.stdout.splitlines():
            line = line.strip()
            if gateway_ip in line:
                mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", line)
                if mac_match:
                    return mac_match.group(0).replace("-", ":").upper()
    except Exception:
        pass
    return None

def get_dns_servers() -> List[str]:
    """
    Resolves active DNS servers from dnspython system configuration.
    Returns empty list if none detected (no hardcoded guesses).
    """
    try:
        resolver = dns.resolver.Resolver()
        servers = list(resolver.nameservers)
        return servers if servers else []
    except Exception:
        return []

async def get_public_ip() -> Optional[str]:
    """
    Fetches the public IP address with a 5-minute memory cache.
    Returns None if offline or unreachable.
    """
    global _cached_public_ip, _cached_public_ip_time
    now = time.time()
    if _cached_public_ip and (now - _cached_public_ip_time < 300):
        return _cached_public_ip

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("https://api.ipify.org?format=json")
            if resp.status_code == 200:
                data = resp.json()
                _cached_public_ip = data.get("ip")
                _cached_public_ip_time = now
                return _cached_public_ip
    except Exception:
        pass
    return _cached_public_ip

def measure_icmp_ping_and_loss(
    target: str,
    count: int = 3,
    timeout_ms: int = 350
) -> Tuple[Optional[float], float]:
    """
    Executes genuine ICMP multi-probe ping test using tokenized system ping executable.
    Calculates actual average RTT latency (ms) and packet loss percentage (0.0 to 100.0).
    """
    is_win = platform.system().lower() == "windows"
    cmd = (
        ["ping", "-n", str(count), "-w", str(timeout_ms), target]
        if is_win
        else ["ping", "-c", str(count), "-W", "1", target]
    )

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3.0)
        output = proc.stdout

        # Parse Windows output
        if is_win:
            loss_match = re.search(r"Lost\s*=\s*\d+\s*\((\d+)%\s*loss\)", output, re.IGNORECASE)
            avg_match = re.search(r"Average\s*=\s*(\d+)\s*ms", output, re.IGNORECASE)

            loss_pct = float(loss_match.group(1)) if loss_match else (0.0 if proc.returncode == 0 else 100.0)
            avg_rtt = float(avg_match.group(1)) if avg_match else None
            return avg_rtt, loss_pct
        else:
            # Parse Linux output
            loss_match = re.search(r"(\d+)%\s*packet loss", output)
            rtt_match = re.search(r"min/avg/max/\w+\s*=\s*[\d\.]+/([\d\.]+)/", output)

            loss_pct = float(loss_match.group(1)) if loss_match else (0.0 if proc.returncode == 0 else 100.0)
            avg_rtt = float(rtt_match.group(1)) if rtt_match else None
            return avg_rtt, loss_pct
    except Exception:
        return None, 100.0

def measure_tcp_connect_latency(
    target: str = "1.1.1.1",
    port: int = 53,
    timeout_sec: float = 0.5
) -> Optional[float]:
    """
    Measures TCP connection handshake duration in milliseconds.
    Clearly distinct from ICMP ping latency.
    """
    try:
        start = time.perf_counter()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout_sec)
        s.connect((target, port))
        s.close()
        duration_ms = (time.perf_counter() - start) * 1000
        return round(duration_ms, 2)
    except Exception:
        return None

def check_gateway_connectivity(gateway_ip: Optional[str]) -> Tuple[bool, Optional[float], float]:
    """
    Validates reachability of the default local gateway router via ICMP.
    Returns (is_connected, latency_ms, packet_loss_pct).
    """
    if not gateway_ip:
        return False, None, 100.0
    latency, loss = measure_icmp_ping_and_loss(gateway_ip, count=2, timeout_ms=250)
    connected = (loss < 100.0) or (latency is not None)
    return connected, latency, loss

def check_internet_connectivity() -> Tuple[bool, Optional[float], float]:
    """
    Validates genuine end-to-end internet connectivity by probing upstream public resolvers.
    Returns (is_connected, latency_ms, packet_loss_pct).
    """
    # Try Cloudflare 1.1.1.1 first, then Google 8.8.8.8
    for target in ("1.1.1.1", "8.8.8.8"):
        latency, loss = measure_icmp_ping_and_loss(target, count=2, timeout_ms=350)
        if loss < 100.0 and latency is not None:
            return True, latency, loss

    # Fallback to TCP connect probe if ICMP is blocked by ISP
    tcp_rtt = measure_tcp_connect_latency("1.1.1.1", 53, 0.5)
    if tcp_rtt is not None:
        return True, tcp_rtt, 0.0

    return False, None, 100.0
