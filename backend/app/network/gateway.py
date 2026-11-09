import platform
import subprocess
import re
import socket
import time
import httpx
import dns.resolver
from typing import Optional, List, Tuple
from app.network.interfaces import get_active_interface_ip

_cached_public_ip: Optional[str] = None
_cached_public_ip_time: float = 0

def get_default_gateway() -> Optional[str]:
    """
    Identifies the default gateway IPv4 address.
    Supports Windows (route print) and Linux (ip route).
    """
    os_name = platform.system().lower()
    try:
        if os_name == "windows":
            # Safe tokenized execution without shell=True
            res = subprocess.run(
                ["route", "print", "0.0.0.0"],
                capture_output=True,
                text=True,
                timeout=3
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split()
                # Line matching: 0.0.0.0 0.0.0.0 <Gateway> <Interface> <Metric>
                if len(parts) >= 5 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                    gateway_candidate = parts[2]
                    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", gateway_candidate):
                        return gateway_candidate
        else:
            res = subprocess.run(
                ["ip", "route", "show", "default"],
                capture_output=True,
                text=True,
                timeout=3
            )
            # Default via 192.168.1.1 dev eth0
            parts = res.stdout.strip().split()
            if len(parts) >= 3 and parts[0] == "default" and parts[1] == "via":
                return parts[2]
    except Exception:
        pass
    return None

def get_gateway_mac(gateway_ip: Optional[str]) -> Optional[str]:
    """
    Inspects the local ARP table to find the MAC address of the default gateway.
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
                # Match MAC format: XX-XX-XX-XX-XX-XX or XX:XX:XX:XX:XX:XX
                mac_match = re.search(r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})", line)
                if mac_match:
                    return mac_match.group(0).replace("-", ":").upper()
    except Exception:
        pass
    return None

def get_dns_servers() -> List[str]:
    """
    Resolves active DNS servers from dnspython system configuration.
    """
    try:
        resolver = dns.resolver.Resolver()
        return list(resolver.nameservers)
    except Exception:
        return ["1.1.1.1", "8.8.8.8"]

async def get_public_ip() -> Optional[str]:
    """
    Fetches the public IP address with a 5-minute memory cache.
    Fails gracefully if internet is unavailable.
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

def measure_target_latency(target: str = "1.1.1.1", port: int = 53, timeout_sec: float = 1.0) -> Optional[float]:
    """
    Measures TCP connection latency in milliseconds to a reliable target (default Cloudflare DNS 1.1.1.1:53).
    Does not require Administrator or raw ICMP permissions.
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
