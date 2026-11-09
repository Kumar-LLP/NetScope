import asyncio
import ipaddress
import platform
import re
import socket
import subprocess
import time
import uuid
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.network.interfaces import get_active_interface_ip, calculate_cidr, get_network_interfaces
from app.network.gateway import get_default_gateway, get_gateway_mac
from app.network.vendor import lookup_vendor
from app.schemas.network import DeviceSchema, DeviceDiscoverResponse

def get_arp_table() -> Dict[str, str]:
    """
    Parses the operating system's ARP cache.
    Returns mapping of {ip_address: mac_address}.
    """
    arp_entries: Dict[str, str] = {}
    try:
        res = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=3)
        for line in res.stdout.splitlines():
            line = line.strip()
            match = re.search(
                r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})",
                line
            )
            if match:
                ip = match.group(1)
                mac = match.group(2).replace("-", ":").upper()
                if not mac.startswith("FF:FF") and not ip.startswith("224.") and not ip.startswith("239.") and not ip.endswith(".255"):
                    arp_entries[ip] = mac
    except Exception:
        pass
    return arp_entries

def ping_host_fast(ip: str, timeout_ms: int = 150) -> Optional[float]:
    """
    Executes a fast ping probe to wake up the host and populate the OS ARP table.
    """
    is_win = platform.system().lower() == "windows"
    cmd = (
        ["ping", "-n", "1", "-w", str(timeout_ms), ip]
        if is_win
        else ["ping", "-c", "1", "-W", "1", ip]
    )
    start = time.perf_counter()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=0.3)
        if proc.returncode == 0:
            return round((time.perf_counter() - start) * 1000, 2)
    except Exception:
        pass
    return None

async def async_probe_host(ip: str) -> Optional[float]:
    """
    Tries async TCP connect to port 80/443 first (takes ~1-5ms if alive or rejected),
    falling back to threaded ping if needed.
    """
    start = time.perf_counter()
    for port in (80, 443, 135):
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=0.10
            )
            writer.close()
            await writer.wait_closed()
            return round((time.perf_counter() - start) * 1000, 2)
        except ConnectionRefusedError:
            # Active host rejected connection
            return round((time.perf_counter() - start) * 1000, 2)
        except Exception:
            continue

    # Fallback to single ping
    return await asyncio.to_thread(ping_host_fast, ip, 150)

async def resolve_hostname_safe(ip: str) -> Optional[str]:
    """
    Asynchronously resolves hostname with a tight 200ms timeout to prevent blocking.
    """
    try:
        def _lookup():
            return socket.gethostbyaddr(ip)[0]
        return await asyncio.wait_for(asyncio.to_thread(_lookup), timeout=0.20)
    except Exception:
        return None

async def discover_devices(
    target_cidr: Optional[str] = None,
    timeout_seconds: int = 10
) -> DeviceDiscoverResponse:
    """
    Discovers active devices on the local subnet using safe, non-privileged probes.
    """
    start_time = time.perf_counter()
    scan_id = str(uuid.uuid4())[:8]

    active_ip = get_active_interface_ip() or "127.0.0.1"
    gateway_ip = get_default_gateway()
    gateway_mac = get_gateway_mac(gateway_ip)

    # Determine default subnet CIDR if none provided
    if not target_cidr:
        interfaces = get_network_interfaces()
        def_iface = next((i for i in interfaces if i.is_default and i.ip_address), None)
        if def_iface and def_iface.ip_address:
            target_cidr, _ = calculate_cidr(def_iface.ip_address, def_iface.netmask)
        else:
            target_cidr = "192.168.1.0/24"

    try:
        network = ipaddress.IPv4Network(target_cidr, strict=False)
        all_hosts = list(network.hosts())[:256]
    except Exception:
        all_hosts = []

    initial_arp = get_arp_table()

    # Bounded concurrent sweep to wake up ARP
    semaphore = asyncio.Semaphore(60)

    async def sem_probe(host_ip: str):
        async with semaphore:
            rtt = await async_probe_host(host_ip)
            return host_ip, rtt

    probe_tasks = [sem_probe(str(h)) for h in all_hosts]
    probe_results = await asyncio.gather(*probe_tasks, return_exceptions=True)

    alive_ips: Dict[str, Optional[float]] = {}
    for res in probe_results:
        if isinstance(res, tuple):
            ip_str, rtt = res
            if rtt is not None:
                alive_ips[ip_str] = rtt

    # Refresh ARP table
    refreshed_arp = {**initial_arp, **get_arp_table()}

    if gateway_ip:
        alive_ips.setdefault(gateway_ip, 1.2)
        if gateway_mac:
            refreshed_arp[gateway_ip] = gateway_mac

    if active_ip and active_ip != "127.0.0.1":
        alive_ips.setdefault(active_ip, 0.1)

    candidate_ips = sorted(
        set(alive_ips.keys()).union(set(refreshed_arp.keys())),
        key=lambda x: [int(p) for p in x.split('.') if p.isdigit()]
    )

    # Resolve hostnames concurrently for discovered candidates
    hostname_tasks = [resolve_hostname_safe(ip) for ip in candidate_ips]
    hostnames = await asyncio.gather(*hostname_tasks, return_exceptions=True)
    hostname_map = {
        candidate_ips[i]: (hostnames[i] if isinstance(hostnames[i], str) else None)
        for i in range(len(candidate_ips))
    }

    devices: List[DeviceSchema] = []
    now = datetime.now(timezone.utc)

    for ip_str in candidate_ips:
        if ip_str.startswith("127.") or ip_str.endswith(".255"):
            continue

        mac = refreshed_arp.get(ip_str)
        is_gw = (ip_str == gateway_ip)
        is_local = (ip_str == active_ip)

        vendor_name = lookup_vendor(mac) if mac else ("Local Host Adapter" if is_local else "Unknown")
        hostname = hostname_map.get(ip_str)
        rtt = alive_ips.get(ip_str)

        devices.append(
            DeviceSchema(
                ip=ip_str,
                mac=mac,
                vendor=vendor_name,
                hostname=hostname,
                is_gateway=is_gw,
                is_local_host=is_local,
                status="online",
                response_time_ms=rtt,
                first_seen=now,
                last_seen=now,
            )
        )

    duration = round(time.perf_counter() - start_time, 2)
    return DeviceDiscoverResponse(
        scan_id=scan_id,
        total_discovered=len(devices),
        duration_seconds=duration,
        devices=devices
    )
